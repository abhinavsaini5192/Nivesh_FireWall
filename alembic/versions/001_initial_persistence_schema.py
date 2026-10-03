"""001_initial_persistence_schema

Revision ID: 001_initial_schema
Revises: None
Create Date: 2026-10-03 10:00:00.000000

Initial persistent schema for Nivesh Firewall Phase 14.2:
- analyses
- policy_decisions
- analysis_results
- engine_executions
- fingerprints
- fingerprint_observations
- sessions
- session_events
- audit_records
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. analyses table
    op.create_table(
        'analyses',
        sa.Column('analysis_id', sa.String(length=64), primary_key=True),
        sa.Column('session_id', sa.String(length=64), nullable=True),
        sa.Column('pipeline_status', sa.String(length=32), nullable=False),
        sa.Column('created_at', sa.String(length=64), nullable=False),
        sa.Column('completed_at', sa.String(length=64), nullable=True),
        sa.Column('duration_ms', sa.Float(), nullable=True, server_default='0.0'),
        sa.Column('input_type', sa.String(length=32), nullable=False),
        sa.Column('channel', sa.String(length=64), nullable=False),
        sa.Column('content_id', sa.String(length=64), nullable=True),
        sa.Column('content_summary', sa.Text(), nullable=True),
        sa.Column('contains_financial_content', sa.Boolean(), nullable=True, server_default='1'),
        sa.Column('idempotency_key', sa.String(length=128), nullable=True),
    )
    op.create_index('ix_analyses_session_id', 'analyses', ['session_id'])
    op.create_index('ix_analyses_pipeline_status', 'analyses', ['pipeline_status'])
    op.create_index('ix_analyses_created_at', 'analyses', ['created_at'])
    op.create_index('ix_analyses_channel', 'analyses', ['channel'])
    op.create_index('ix_analyses_idempotency_key', 'analyses', ['idempotency_key'], unique=True)

    # 2. policy_decisions table
    op.create_table(
        'policy_decisions',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('decision_id', sa.String(length=64), nullable=True),
        sa.Column('analysis_id', sa.String(length=64), sa.ForeignKey('analyses.analysis_id', ondelete='CASCADE'), nullable=False),
        sa.Column('decision', sa.String(length=32), nullable=False),
        sa.Column('severity', sa.String(length=32), nullable=False),
        sa.Column('primary_reason', sa.Text(), nullable=False),
        sa.Column('reason_codes', sa.JSON(), nullable=False),
        sa.Column('user_message', sa.Text(), nullable=False),
        sa.Column('technical_message', sa.Text(), nullable=False),
        sa.Column('actions_required', sa.JSON(), nullable=False),
        sa.Column('required_user_confirmation', sa.Boolean(), nullable=True, server_default='0'),
        sa.Column('cooldown_seconds', sa.Integer(), nullable=True),
        sa.Column('policy_version', sa.String(length=32), nullable=False, server_default='8.0.0'),
        sa.Column('created_at', sa.String(length=64), nullable=False),
    )
    op.create_index('ix_policy_decisions_analysis_id', 'policy_decisions', ['analysis_id'], unique=True)
    op.create_index('ix_policy_decisions_decision_id', 'policy_decisions', ['decision_id'], unique=True)
    op.create_index('ix_policy_decisions_decision', 'policy_decisions', ['decision'])

    # 3. analysis_results table
    op.create_table(
        'analysis_results',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('analysis_id', sa.String(length=64), sa.ForeignKey('analyses.analysis_id', ondelete='CASCADE'), nullable=False),
        sa.Column('content_summary_json', sa.JSON(), nullable=False),
        sa.Column('claims_json', sa.JSON(), nullable=False),
        sa.Column('actions_json', sa.JSON(), nullable=False),
        sa.Column('evidence_json', sa.JSON(), nullable=False),
        sa.Column('identity_json', sa.JSON(), nullable=False),
        sa.Column('threat_json', sa.JSON(), nullable=False),
        sa.Column('fingerprint_json', sa.JSON(), nullable=False),
        sa.Column('behaviour_json', sa.JSON(), nullable=False),
        sa.Column('provenance_json', sa.JSON(), nullable=False),
        sa.Column('warnings_json', sa.JSON(), nullable=False),
        sa.Column('errors_json', sa.JSON(), nullable=False),
    )
    op.create_index('ix_analysis_results_analysis_id', 'analysis_results', ['analysis_id'], unique=True)

    # 4. engine_executions table
    op.create_table(
        'engine_executions',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('analysis_id', sa.String(length=64), sa.ForeignKey('analyses.analysis_id', ondelete='CASCADE'), nullable=False),
        sa.Column('engine_key', sa.String(length=64), nullable=False),
        sa.Column('engine_name', sa.String(length=128), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False),
        sa.Column('started_at', sa.String(length=64), nullable=False),
        sa.Column('completed_at', sa.String(length=64), nullable=True),
        sa.Column('duration_ms', sa.Float(), nullable=True, server_default='0.0'),
        sa.Column('output_id', sa.String(length=128), nullable=True),
        sa.Column('error_type', sa.String(length=128), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('metadata_json', sa.JSON(), nullable=False),
    )
    op.create_index('ix_engine_executions_analysis_id', 'engine_executions', ['analysis_id'])
    op.create_index('ix_engine_executions_engine_key', 'engine_executions', ['engine_key'])

    # 5. fingerprints table
    op.create_table(
        'fingerprints',
        sa.Column('fingerprint_id', sa.String(length=64), primary_key=True),
        sa.Column('schema_version', sa.String(length=16), nullable=False, server_default='1.0'),
        sa.Column('identity_patterns', sa.JSON(), nullable=False),
        sa.Column('claim_patterns', sa.JSON(), nullable=False),
        sa.Column('action_patterns', sa.JSON(), nullable=False),
        sa.Column('channel_patterns', sa.JSON(), nullable=False),
        sa.Column('technical_patterns', sa.JSON(), nullable=False),
        sa.Column('threat_patterns', sa.JSON(), nullable=False),
        sa.Column('attack_stages', sa.JSON(), nullable=False),
        sa.Column('attack_transitions', sa.JSON(), nullable=False),
        sa.Column('evidence_patterns', sa.JSON(), nullable=False),
        sa.Column('threat_families', sa.JSON(), nullable=False),
        sa.Column('canonical_features', sa.JSON(), nullable=False),
        sa.Column('exact_signature', sa.String(length=128), nullable=False),
        sa.Column('semantic_signature', sa.String(length=128), nullable=False),
        sa.Column('attack_path_signature', sa.String(length=256), nullable=False),
        sa.Column('created_at', sa.String(length=64), nullable=False),
        sa.Column('updated_at', sa.String(length=64), nullable=False),
        sa.Column('first_seen', sa.String(length=64), nullable=False),
        sa.Column('last_seen', sa.String(length=64), nullable=False),
        sa.Column('observation_count', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('distinct_channels', sa.JSON(), nullable=False),
        sa.Column('distinct_variants', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='NEW'),
        sa.Column('dispute_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('dispute_notes', sa.JSON(), nullable=False),
        sa.Column('status_change_history', sa.JSON(), nullable=False),
        sa.Column('related_fingerprint_ids', sa.JSON(), nullable=False),
        sa.Column('content_hashes', sa.JSON(), nullable=False),
        sa.Column('description', sa.Text(), nullable=False, server_default=''),
    )
    op.create_index('ix_fingerprints_exact_signature', 'fingerprints', ['exact_signature'])
    op.create_index('ix_fingerprints_semantic_signature', 'fingerprints', ['semantic_signature'])
    op.create_index('ix_fingerprints_attack_path_signature', 'fingerprints', ['attack_path_signature'])
    op.create_index('ix_fingerprints_status', 'fingerprints', ['status'])

    # 6. fingerprint_observations table
    op.create_table(
        'fingerprint_observations',
        sa.Column('observation_id', sa.String(length=64), primary_key=True),
        sa.Column('fingerprint_id', sa.String(length=64), sa.ForeignKey('fingerprints.fingerprint_id', ondelete='CASCADE'), nullable=False),
        sa.Column('content_id', sa.String(length=64), nullable=False),
        sa.Column('observed_at', sa.String(length=64), nullable=False),
        sa.Column('channel', sa.String(length=64), nullable=True),
        sa.Column('features', sa.JSON(), nullable=False),
        sa.Column('content_hash', sa.String(length=128), nullable=True),
        sa.Column('is_duplicate_origin', sa.Boolean(), nullable=True, server_default='0'),
        sa.Column('match_type', sa.String(length=32), nullable=False),
        sa.Column('match_confidence', sa.Float(), nullable=False),
        sa.Column('matched_dimensions', sa.JSON(), nullable=False),
        sa.Column('provenance', sa.JSON(), nullable=False),
    )
    op.create_index('ix_fingerprint_observations_fingerprint_id', 'fingerprint_observations', ['fingerprint_id'])
    op.create_index('ix_fingerprint_observations_content_hash', 'fingerprint_observations', ['content_hash'])
    op.create_index('ix_fingerprint_observations_observed_at', 'fingerprint_observations', ['observed_at'])

    # 7. sessions table
    op.create_table(
        'sessions',
        sa.Column('session_id', sa.String(length=64), primary_key=True),
        sa.Column('started_at', sa.String(length=64), nullable=True),
        sa.Column('last_event_at', sa.String(length=64), nullable=True),
        sa.Column('event_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('source_type', sa.String(length=64), nullable=True),
        sa.Column('created_at', sa.String(length=64), nullable=False),
        sa.Column('updated_at', sa.String(length=64), nullable=False),
    )

    # 8. session_events table
    op.create_table(
        'session_events',
        sa.Column('event_id', sa.String(length=64), primary_key=True),
        sa.Column('session_id', sa.String(length=64), sa.ForeignKey('sessions.session_id', ondelete='CASCADE'), nullable=False),
        sa.Column('timestamp', sa.String(length=64), nullable=False),
        sa.Column('event_type', sa.String(length=64), nullable=False),
        sa.Column('action_id', sa.String(length=64), nullable=True),
        sa.Column('claim_id', sa.String(length=64), nullable=True),
        sa.Column('decision_id', sa.String(length=64), nullable=True),
        sa.Column('channel', sa.String(length=64), nullable=True),
        sa.Column('sequence_index', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('user_initiated', sa.Boolean(), nullable=True, server_default='0'),
        sa.Column('system_initiated', sa.Boolean(), nullable=True, server_default='1'),
        sa.Column('source_type', sa.String(length=64), nullable=True),
        sa.Column('metadata_json', sa.JSON(), nullable=False),
    )
    op.create_index('ix_session_events_session_id', 'session_events', ['session_id'])
    op.create_index('ix_session_events_timestamp', 'session_events', ['timestamp'])

    # 9. audit_records table
    op.create_table(
        'audit_records',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('analysis_id', sa.String(length=64), nullable=True),
        sa.Column('session_id', sa.String(length=64), nullable=True),
        sa.Column('event_type', sa.String(length=64), nullable=False),
        sa.Column('actor', sa.String(length=64), nullable=False, server_default='system'),
        sa.Column('details', sa.JSON(), nullable=False),
        sa.Column('timestamp', sa.String(length=64), nullable=False),
    )
    op.create_index('ix_audit_records_analysis_id', 'audit_records', ['analysis_id'])
    op.create_index('ix_audit_records_session_id', 'audit_records', ['session_id'])
    op.create_index('ix_audit_records_event_type', 'audit_records', ['event_type'])
    op.create_index('ix_audit_records_timestamp', 'audit_records', ['timestamp'])


def downgrade() -> None:
    op.drop_table('audit_records')
    op.drop_table('session_events')
    op.drop_table('sessions')
    op.drop_table('fingerprint_observations')
    op.drop_table('fingerprints')
    op.drop_table('engine_executions')
    op.drop_table('analysis_results')
    op.drop_table('policy_decisions')
    op.drop_table('analyses')
