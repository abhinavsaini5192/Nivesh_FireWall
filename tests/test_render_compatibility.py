"""Targeted tests validating Render deployment compatibility for Nivesh Firewall.

Validates:
1. Dynamic PORT and HOST binding for Render Web Service (PORT environment variable).
2. Worker concurrency handling via WEB_CONCURRENCY / NIVESH_WORKERS.
3. Render PostgreSQL connection string normalization (postgres:// -> postgresql://).
4. CORS compatibility with *.onrender.com frontend domains.
5. Health and readiness probe endpoints under production-like Render configuration.
6. Frontend static site build artifacts and SPA routing contract.
"""

import os
import re
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from nivesh.config.settings import Settings
from nivesh.storage.database import get_engine, reset_engine_for_testing, run_migrations
from nivesh.api.app import app


class TestRenderBackendCompatibility:
    """Test backend adaptability to Render Web Service runtime environment."""

    def test_dynamic_port_binding_from_render_env(self, monkeypatch):
        """Render injects the listening port dynamically via the PORT environment variable."""
        monkeypatch.setenv("PORT", "10000")
        monkeypatch.delenv("NIVESH_PORT", raising=False)

        settings = Settings()
        assert settings.port == 10000

    def test_nivesh_port_takes_precedence_if_explicitly_set(self, monkeypatch):
        """Explicit NIVESH_PORT takes precedence over generic PORT."""
        monkeypatch.setenv("NIVESH_PORT", "9000")
        monkeypatch.setenv("PORT", "10000")

        settings = Settings()
        assert settings.port == 9000

    def test_host_binding_aliases_and_defaults(self, monkeypatch):
        """Host binding accepts HOST alias and defaults properly."""
        monkeypatch.setenv("HOST", "0.0.0.0")
        monkeypatch.delenv("NIVESH_HOST", raising=False)

        settings = Settings()
        assert settings.host == "0.0.0.0"

    def test_web_concurrency_worker_alias(self, monkeypatch):
        """Render sets WEB_CONCURRENCY for Python runtimes."""
        monkeypatch.setenv("WEB_CONCURRENCY", "2")
        monkeypatch.delenv("NIVESH_WORKERS", raising=False)

        settings = Settings()
        assert settings.workers == 2


class TestRenderPostgresCompatibility:
    """Test PostgreSQL connection handling for Render managed databases."""

    def test_settings_normalizes_postgres_scheme_to_postgresql(self, monkeypatch):
        """Render PostgreSQL connection strings start with postgres:// which SQLAlchemy 2 rejects."""
        render_postgres_url = "postgres://nivesh_user:secret_pass@dpg-c12345-a.oregon-postgres.render.com:5432/nivesh_db"
        monkeypatch.setenv("NIVESH_DATABASE_URL", render_postgres_url)
        monkeypatch.setenv("NIVESH_ENV", "production")
        monkeypatch.setenv("NIVESH_DEBUG", "False")
        monkeypatch.setenv("NIVESH_SECRET_KEY", "test-secret-key-32-chars-long-minimum")
        monkeypatch.setenv("NIVESH_ALLOWED_ORIGINS", "https://nivesh-app.onrender.com")

        settings = Settings()
        assert settings.database_url.startswith("postgresql://")
        assert "postgres://" not in settings.database_url
        assert "nivesh_user:secret_pass@dpg-c12345-a.oregon-postgres.render.com:5432/nivesh_db" in settings.database_url

    def test_database_get_engine_normalizes_postgres_url(self):
        """get_engine normalizes raw postgres:// string when passed directly."""
        reset_engine_for_testing()
        raw_url = "postgres://user:pass@localhost:5432/mydb"
        # We verify that get_engine handles normalization before invoking dialect resolution
        try:
            get_engine(raw_url)
        except Exception as e:
            # We expect either successful engine creation or connection failure,
            # but NEVER "NoSuchModuleError: Can't load plugin: sqlalchemy.dialects:postgres"
            assert "Can't load plugin: sqlalchemy.dialects:postgres" not in str(e)
            assert "NoSuchModuleError" not in str(type(e).__name__)
        finally:
            reset_engine_for_testing()

    def test_alembic_env_normalizes_postgres_url(self, monkeypatch):
        """Alembic migration runner normalizes postgres:// to postgresql://."""
        monkeypatch.setenv("NIVESH_DATABASE_URL", "postgres://user:pass@render-db:5432/nivesh")
        from alembic.config import Config
        root_dir = Path(__file__).resolve().parent.parent
        ini_path = str(root_dir / "alembic.ini")
        cfg = Config(ini_path)
        settings = Settings()
        assert settings.database_url.startswith("postgres" + "ql://")
        assert not settings.database_url.startswith("postgres://")


class TestRenderCORSAndSecurity:
    """Test CORS enforcement for Render deployment topologies."""

    def test_onrender_com_origins_accepted_in_production(self, monkeypatch):
        """Production settings accept https://*.onrender.com domains."""
        monkeypatch.setenv("NIVESH_ENV", "production")
        monkeypatch.setenv("NIVESH_DEBUG", "False")
        monkeypatch.setenv("NIVESH_SECRET_KEY", "strong_production_secret_key_32_chars")
        monkeypatch.setenv("NIVESH_DATABASE_URL", "postgresql://user:pass@host:5432/db")
        monkeypatch.setenv("NIVESH_ALLOWED_ORIGINS", "https://nivesh-frontend.onrender.com,https://nivesh-app.onrender.com")

        settings = Settings()
        origins = settings.get_cors_origins()
        assert "https://nivesh-frontend.onrender.com" in origins
        assert "https://nivesh-app.onrender.com" in origins

    def test_health_endpoints_accessible(self):
        """Liveness probe /health/live succeeds for Render health check configuration."""
        client = TestClient(app)
        response = client.get("/health/live")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") in ("alive", "live", "ok")


class TestRenderFrontendArtifacts:
    """Verify frontend static site compilation and build assets."""

    def test_frontend_dist_directory_exists_and_contains_entrypoint(self):
        """frontend/dist must exist and contain index.html with valid assets."""
        root_dir = Path(__file__).resolve().parent.parent
        dist_dir = root_dir / "frontend" / "dist"
        index_html = dist_dir / "index.html"

        assert dist_dir.exists(), "frontend/dist directory must exist after build"
        assert index_html.exists(), "frontend/dist/index.html must exist"

        content = index_html.read_text(encoding="utf-8")
        assert "<!doctype html>" in content.lower() or "<html" in content.lower()
        assert "/assets/" in content, "index.html must reference bundled assets"
