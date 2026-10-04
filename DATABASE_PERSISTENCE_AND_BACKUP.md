# Nivesh Firewall — Database Persistence, Connection Pooling & Backup/Restore Guide

## Phase 16.2: Production Database Infrastructure

### 1. Architecture Overview

Nivesh Firewall requires **PostgreSQL 15+** for production persistence. In development and unit-test environments, isolated SQLite databases (`sqlite:///./nivesh_dev.db` and `sqlite:///:memory:`) are supported, but SQLite is strictly forbidden and rejected at application startup when `NIVESH_ENV=production`.

The persistent relational schema stores:
1. **Analyses (`analyses`)**: Primary metadata, processing timeline, input modality, channel, and idempotency key.
2. **Policy Decisions (`policy_decisions`)**: Engine 8 safety decisions, severity, reason codes, required user confirmations, and messages (`ON DELETE CASCADE`).
3. **Analysis Results (`analysis_results`)**: Full multi-engine structured intelligence snapshots across all 10 engines (`ON DELETE CASCADE`).
4. **Engine Executions (`engine_executions`)**: Telemetry, execution timestamps, duration, output identifiers, error messages, and retry counters (`ON DELETE CASCADE`).
5. **Scam Fingerprints (`fingerprints`)**: Collective threat memory, structural signatures, attack paths, observation counters, and dispute history.
6. **Fingerprint Observations (`fingerprint_observations`)**: Individual sightings with content hashes, match confidence, and provenance (`ON DELETE CASCADE`).
7. **Sessions (`sessions`)**: Multi-turn interaction metadata, event counts, and timestamps.
8. **Session Events (`session_events`)**: Individual interaction steps within a user sequence (`ON DELETE CASCADE`).
9. **Audit Records (`audit_records`)**: Security and administrative audit trail with actor, action, status, and IP address.

---

### 2. Connection Management & Pooling

The database engine is configured via centralized environment variables using SQLAlchemy's connection pooling:

| Environment Variable | Default | Purpose |
| :--- | :--- | :--- |
| `NIVESH_DATABASE_URL` | None | PostgreSQL connection URI (`postgresql://user:password@host:5432/dbname`) |
| `NIVESH_DB_POOL_SIZE` | `10` | Persistent connection pool size (`QueuePool`) |
| `NIVESH_DB_MAX_OVERFLOW` | `20` | Bounded connection overflow during traffic spikes |
| `NIVESH_DB_POOL_TIMEOUT` | `30.0` | Seconds to wait before timing out on connection checkout |
| `NIVESH_DB_POOL_RECYCLE` | `1800` | Connection recycling interval (30 min) to prevent stale firewall drops |
| `NIVESH_DB_SSL_MODE` | `prefer` | SSL mode (`require`, `verify-ca`, `verify-full`, `prefer`, `disable`) |

**Engine Safeguards**:
- `pool_pre_ping=True`: Detects and recycles disconnected/stale connections before handing them to a session.
- Context-managed sessions (`get_db_session()`): Guarantees automatic commit on success, automatic rollback on exception, and session closure in all cases.
- Failed transactions emit rollback telemetry (`metrics.persistence_rollbacks_total`) and do not contaminate connection pool state.

---

### 3. Alembic Migration Lifecycle

Database migrations are managed via **Alembic** (`alembic.ini` and `alembic/versions/`):
- Current migration head: `001_initial_schema`.
- Schema migrations run automatically during application preflight startup:
  ```bash
  python scripts/entrypoint.py
  ```
- **Fresh Database Lifecycle**:
  ```text
  Empty PostgreSQL DB → Alembic upgrade head → Tables & Indexes Created → Application Ready
  ```
- **Existing Database Lifecycle**:
  ```text
  Existing PostgreSQL DB → Check alembic_version → Apply pending revisions → Application Ready
  ```
- **Idempotence**: Running migrations repeatedly against an already-migrated database is safe and performs zero unnecessary modifications.

---

### 4. Controlled Failure Handling & Health Probes

1. **Database Unavailability**:
   - Lightweight probe `check_database_health()` executes `SELECT 1` with error capture.
   - If PostgreSQL is down, the `/health/ready` probe returns `503 Service Unavailable`:
     ```json
     {
       "status": "not_ready",
       "dependencies": {
         "database": {
           "status": "unavailable",
           "dialect": "postgresql"
         }
       },
       "reasons": ["Database connectivity failed in production environment."]
     }
     ```
   - Liveness probe (`/health/live`) continues to return `200 OK` (process is alive without persistent I/O).
2. **Credential Redaction**:
   - `mask_database_url()` and `mask_sensitive_url()` strip passwords from logging and error messages.
   - Database health check reports only the dialect name (e.g. `postgresql`), never database hostnames, usernames, or connection strings.

---

### 5. Production Backup Procedure

To perform a consistent, non-blocking logical backup of the PostgreSQL database:

```bash
# Set credentials securely in environment
export PGPASSWORD="your_production_db_password"

# Logical backup using custom compressed format (-F c)
pg_dump -h <DB_HOST> \
        -p 5432 \
        -U nivesh_user \
        -d nivesh_db \
        -F c \
        -b \
        -v \
        -f "nivesh_backup_$(date +%Y%m%d_%H%M%S).dump"
```

**Docker Compose Shortcut**:
```bash
docker compose exec -T postgres pg_dump -U nivesh_user -d nivesh_db -F c > "nivesh_backup_$(date +%Y%m%d_%H%M%S).dump"
```

---

### 6. Production Restore Procedure

To restore a backup into a clean or replacement PostgreSQL instance:

```bash
# 1. Create a clean database if restoring to a new cluster
export PGPASSWORD="your_production_db_password"
createdb -h <DB_HOST> -p 5432 -U nivesh_user nivesh_db_restored

# 2. Restore schema, tables, and data from backup file
pg_restore -h <DB_HOST> \
           -p 5432 \
           -U nivesh_user \
           -d nivesh_db_restored \
           --clean \
           --if-exists \
           -v "nivesh_backup_20261004_120000.dump"
```

**Docker Compose Shortcut**:
```bash
docker compose exec -T postgres pg_restore -U nivesh_user -d nivesh_db --clean --if-exists < backup.dump
```

---

### 7. Post-Restore Verification Checklist

After restoration, execute the following operational steps:
1. **Run Migration / Preflight Validator**:
   ```bash
   python scripts/entrypoint.py --check-only
   ```
2. **Verify Database Health via HTTP**:
   ```bash
   curl -f http://127.0.0.1:8000/health/ready
   ```
3. **Verify Existing Analysis Retrieval**:
   ```bash
   curl -f -H "Authorization: Bearer <TOKEN>" http://127.0.0.1:8000/api/v1/firewall/analysis/<KNOWN_ANALYSIS_ID>
   ```
