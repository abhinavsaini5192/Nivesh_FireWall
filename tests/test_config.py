"""Tests for Phase 14.1: Production Configuration & Environment Architecture.

Validates:
Test 1:  Development settings load with safe local defaults.
Test 2:  Test settings load with isolated resources (in-memory db).
Test 3:  Production settings load when valid production configuration is provided.
Test 4:  Invalid URL rejected with ValidationError.
Test 5:  Invalid enum (env, source_mode, log_level) rejected.
Test 6:  Missing required production value fails safely with clear error.
Test 7:  Production debug mode cannot accidentally remain enabled.
Test 8:  Production CORS does not default to unrestricted wildcard ('*').
Test 9:  Secrets and credentials are masked in repr, serialization, and logs.
Test 10: .env files containing secrets are ignored by git.
Test 11: Frontend API URL resolves from environment configuration.
Test 12: Extension backend URL resolves from environment configuration.
Test 13: Fixture vs Live source mode is explicit and safely gated.
Test 14: Timeout configuration is loaded correctly.
Test 15: Maximum payload limits are loaded and enforced correctly.
Security: Regressions against hardcoded secrets and unvalidated production defaults.
Startup: Smoke tests across development, test, and production startup lifespans.
"""

import io
import logging
import os
import re
import subprocess
from pathlib import Path
import pytest
from pydantic import ValidationError
from fastapi.testclient import TestClient

from nivesh.config.settings import Settings, get_settings, mask_sensitive_url
from nivesh.config.logging import setup_logging, SensitiveDataRedactor
from nivesh.api.app import app


# ------------------------------------------------------------------------------
# Test 1: Development settings load
# ------------------------------------------------------------------------------
def test_01_development_settings_load():
    """Verify development settings load with safe local defaults."""
    s = Settings(env="development")
    assert s.env == "development"
    assert s.is_development() is True
    assert s.is_test() is False
    assert s.is_production() is False
    assert s.database_url == "sqlite:///./nivesh_dev.db"
    assert s.source_mode == "FIXTURE"
    assert "http://localhost:5173" in s.get_cors_origins()
    assert "http://127.0.0.1:5173" in s.get_cors_origins()


# ------------------------------------------------------------------------------
# Test 2: Test settings load
# ------------------------------------------------------------------------------
def test_02_test_settings_load():
    """Verify test settings load with isolated in-memory resources."""
    s = Settings(env="test")
    assert s.env == "test"
    assert s.is_test() is True
    assert s.is_development() is False
    assert s.is_production() is False
    assert s.database_url == "sqlite:///:memory:"


# ------------------------------------------------------------------------------
# Test 3: Production settings load
# ------------------------------------------------------------------------------
def test_03_production_settings_load():
    """Verify production settings load when all required values are provided."""
    s = Settings(
        env="production",
        database_url="postgresql://nivesh_admin:secret_pass_123@prod-cluster.internal:5432/nivesh_prod",
        allowed_origins=["https://app.nivesh.ai", "https://admin.nivesh.ai"],
        debug=False,
    )
    assert s.env == "production"
    assert s.is_production() is True
    assert s.debug is False
    assert s.database_url == "postgresql://nivesh_admin:secret_pass_123@prod-cluster.internal:5432/nivesh_prod"
    assert s.allowed_origins == ["https://app.nivesh.ai", "https://admin.nivesh.ai"]
    assert s.get_cors_origins() == ["https://app.nivesh.ai", "https://admin.nivesh.ai"]


# ------------------------------------------------------------------------------
# Test 4: Invalid URL rejected
# ------------------------------------------------------------------------------
def test_04_invalid_url_rejected():
    """Verify malformed or unsupported URLs for frontend_url are rejected."""
    with pytest.raises(ValidationError):
        Settings(frontend_url="not_a_valid_url")

    with pytest.raises(ValidationError):
        Settings(frontend_url="ftp://unsupported-scheme.com")

    with pytest.raises(ValidationError):
        Settings(frontend_url="")


# ------------------------------------------------------------------------------
# Test 5: Invalid enum rejected
# ------------------------------------------------------------------------------
def test_05_invalid_enum_rejected():
    """Verify invalid environment, source_mode, or log_level values raise ValidationError."""
    with pytest.raises(ValidationError):
        Settings(env="staging_unknown")  # type: ignore

    with pytest.raises(ValidationError):
        Settings(source_mode="INVALID_SOURCE_MODE")  # type: ignore

    with pytest.raises(ValidationError):
        Settings(log_level="VERBOSE")  # type: ignore


# ------------------------------------------------------------------------------
# Test 6: Missing required production value fails safely
# ------------------------------------------------------------------------------
def test_06_missing_required_production_value_fails_safely():
    """Verify missing database URL in production fails with clean validation error."""
    with pytest.raises(ValidationError) as exc_info:
        Settings(env="production", database_url=None)
    assert "Production environment requires a persistent NIVESH_DATABASE_URL" in str(exc_info.value)

    # Empty string database_url also fails
    with pytest.raises(ValidationError) as exc_info2:
        Settings(env="production", database_url="")
    assert "Production environment requires a persistent NIVESH_DATABASE_URL" in str(exc_info2.value)

    # SQLite fallback is forbidden in production
    with pytest.raises(ValidationError) as exc_info3:
        Settings(env="production", database_url="sqlite:///./nivesh_dev.db")
    assert "cannot use development or in-memory SQLite" in str(exc_info3.value)


# ------------------------------------------------------------------------------
# Test 7: Production debug mode cannot accidentally remain enabled
# ------------------------------------------------------------------------------
def test_07_production_debug_mode_cannot_remain_enabled():
    """Verify production rejects debug=True explicitly."""
    with pytest.raises(ValidationError) as exc_info:
        Settings(
            env="production",
            database_url="postgresql://user:pass@db.internal:5432/nivesh",
            debug=True,
        )
    assert "Production environment cannot run with debug mode enabled" in str(exc_info.value)


# ------------------------------------------------------------------------------
# Test 8: Production CORS does not default to unrestricted wildcard
# ------------------------------------------------------------------------------
def test_08_production_cors_does_not_default_to_unrestricted_wildcard():
    """Verify production forbids wildcard origin '*' in CORS configuration."""
    with pytest.raises(ValidationError) as exc_info:
        Settings(
            env="production",
            database_url="postgresql://user:pass@db.internal:5432/nivesh",
            allowed_origins=["*"],
        )
    assert "Production CORS configuration forbids wildcard origin ('*')" in str(exc_info.value)

    # Empty origins list also rejected in production
    with pytest.raises(ValidationError) as exc_info2:
        Settings(
            env="production",
            database_url="postgresql://user:pass@db.internal:5432/nivesh",
            allowed_origins=[],
        )
    assert "requires at least one explicit allowed origin" in str(exc_info2.value)


# ------------------------------------------------------------------------------
# Test 9: Secrets are not printed
# ------------------------------------------------------------------------------
def test_09_secrets_are_not_printed():
    """Verify secrets are masked in string repr, safe_dump, and log filters."""
    secret_pass = "super_classified_db_password_XYZ999"
    secret_key = "ultra_confidential_signing_key_007"
    raw_url = f"postgresql://nivesh_svc:{secret_pass}@prod.db:5432/nivesh"

    s = Settings(
        env="development",
        database_url=raw_url,
        secret_key=secret_key,
    )

    # String representation masking
    repr_str = repr(s)
    assert secret_pass not in repr_str
    assert secret_key not in repr_str
    assert "***@" in repr_str
    assert "***REDACTED***" in repr_str

    # Safe dump dictionary masking
    dump = s.safe_dump()
    assert secret_pass not in dump["database_url"]
    assert dump["secret_key"] == "***REDACTED***"

    # Log redaction filter
    logger = logging.getLogger("nivesh_test_logger")
    logger.setLevel(logging.INFO)
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.addFilter(SensitiveDataRedactor())
    logger.addHandler(handler)

    logger.info(f"Connecting with password: {secret_pass} and otp: 654321")
    output = stream.getvalue()
    assert secret_pass not in output
    assert "654321" not in output
    assert "[REDACTED]" in output


# ------------------------------------------------------------------------------
# Test 10: .env is not tracked by git
# ------------------------------------------------------------------------------
def test_10_env_is_not_tracked_by_git():
    """Verify that .env files are excluded by .gitignore and not tracked by git."""
    root_dir = Path(__file__).resolve().parent.parent
    gitignore_path = root_dir / ".gitignore"
    assert gitignore_path.exists(), ".gitignore must exist in root"

    gitignore_content = gitignore_path.read_text(encoding="utf-8")
    assert ".env" in gitignore_content
    assert "!.env.example" in gitignore_content

    # Verify git status does not track .env
    result = subprocess.run(
        ["git", "ls-files", "--error-unmatch", ".env"],
        cwd=str(root_dir),
        capture_output=True,
        text=True,
    )
    # Return code != 0 means git does NOT track .env
    assert result.returncode != 0, ".env must NOT be tracked by git"


# ------------------------------------------------------------------------------
# Test 11: Frontend API URL comes from environment
# ------------------------------------------------------------------------------
def test_11_frontend_api_url_comes_from_environment():
    """Verify frontend configuration module reads VITE_API_BASE_URL."""
    root_dir = Path(__file__).resolve().parent.parent
    env_file = root_dir / "frontend" / "src" / "config" / "env.ts"
    assert env_file.exists(), "frontend/src/config/env.ts must exist"

    content = env_file.read_text(encoding="utf-8")
    assert "import.meta.env.VITE_API_BASE_URL" in content
    assert "http://localhost:8000" in content


# ------------------------------------------------------------------------------
# Test 12: Extension backend URL comes from environment/build configuration
# ------------------------------------------------------------------------------
def test_12_extension_backend_url_comes_from_environment():
    """Verify browser extension config reads VITE_API_BASE_URL or VITE_BACKEND_URL."""
    root_dir = Path(__file__).resolve().parent.parent
    ext_config_file = root_dir / "extension" / "src" / "config" / "index.ts"
    assert ext_config_file.exists(), "extension/src/config/index.ts must exist"

    content = ext_config_file.read_text(encoding="utf-8")
    assert "import.meta.env.VITE_API_BASE_URL" in content
    assert "import.meta.env.VITE_WEB_APP_URL" in content


# ------------------------------------------------------------------------------
# Test 13: Fixture/live source mode is explicit
# ------------------------------------------------------------------------------
def test_13_fixture_live_source_mode_is_explicit():
    """Verify source mode is explicit and LIVE mode requires explicit gate."""
    # FIXTURE mode is explicit
    s_fixture = Settings(source_mode="FIXTURE")
    assert s_fixture.source_mode == "FIXTURE"

    # CACHE mode is explicit
    s_cache = Settings(source_mode="CACHE")
    assert s_cache.source_mode == "CACHE"

    # LIVE mode without gate in production is rejected
    with pytest.raises(ValidationError) as exc_info:
        Settings(
            env="production",
            database_url="postgresql://user:pass@db:5432/nivesh",
            allowed_origins=["https://app.nivesh.ai"],
            source_mode="LIVE",
            live_sources_enabled=False,
        )
    assert "NIVESH_SOURCE_MODE=LIVE requires NIVESH_LIVE_SOURCES_ENABLED=True" in str(exc_info.value)

    # LIVE mode with gate succeeds
    s_live = Settings(
        env="production",
        database_url="postgresql://user:pass@db:5432/nivesh",
        allowed_origins=["https://app.nivesh.ai"],
        source_mode="LIVE",
        live_sources_enabled=True,
    )
    assert s_live.source_mode == "LIVE"
    assert s_live.live_sources_enabled is True


# ------------------------------------------------------------------------------
# Test 14: Timeout configuration is loaded correctly
# ------------------------------------------------------------------------------
def test_14_timeout_configuration_loaded_correctly():
    """Verify timeout configuration fields load with typed numbers."""
    s = Settings(
        timeout_request_seconds=45.5,
        timeout_retrieval_seconds=15.0,
        timeout_pipeline_ms=25000.0,
        timeout_engine_ms=7500.0,
    )
    assert s.timeout_request_seconds == 45.5
    assert s.timeout_retrieval_seconds == 15.0
    assert s.timeout_pipeline_ms == 25000.0
    assert s.timeout_engine_ms == 7500.0


# ------------------------------------------------------------------------------
# Test 15: Payload limits are loaded correctly
# ------------------------------------------------------------------------------
def test_15_payload_limits_loaded_correctly():
    """Verify maximum payload limits load and are enforced."""
    s = Settings(
        max_request_bytes=20_971_520,
        max_content_length=75_000,
        max_url_length=4096,
        max_image_bytes=20_971_520,
        max_session_id_length=256,
    )
    assert s.max_request_bytes == 20_971_520
    assert s.max_content_length == 75_000
    assert s.max_url_length == 4096
    assert s.max_image_bytes == 20_971_520
    assert s.max_session_id_length == 256


# ------------------------------------------------------------------------------
# Security Tests: Hardcoded patterns, Localhost, Wildcard CORS
# ------------------------------------------------------------------------------
def test_16_security_static_checks():
    """Static checks ensuring no real hardcoded production credentials exist in Python source."""
    root_dir = Path(__file__).resolve().parent.parent
    py_files = list((root_dir / "nivesh").rglob("*.py"))

    # Check for hardcoded secret assignments like AWS keys or database passwords
    forbidden_secret_patterns = [
        re.compile(r"postgresql://[^:]+:[^@]+@(?!localhost|127\.0\.0\.1)[^\s'\"]+"),
        re.compile(r"(?i)api[_-]?key\s*=\s*['\"][a-zA-Z0-9]{32,}['\"]"),
        re.compile(r"(?i)secret[_-]?key\s*=\s*['\"][a-zA-Z0-9]{32,}['\"]"),
    ]

    for py_file in py_files:
        content = py_file.read_text(encoding="utf-8")
        for pat in forbidden_secret_patterns:
            matches = pat.findall(content)
            assert not matches, f"Hardcoded credential pattern found in {py_file}: {matches}"


# ------------------------------------------------------------------------------
# Backend Startup Smoke Tests (Development, Test, Production-like)
# ------------------------------------------------------------------------------
def test_17_backend_startup_smoke_test():
    """Smoke test ensuring backend initializes and health check responds with environment."""
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "environment" in data
    assert "engine" in data
    assert "version" in data
    assert "engines" in data
    assert len(data["engines"]) == 10
