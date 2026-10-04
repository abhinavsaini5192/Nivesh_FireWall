"""Centralized Settings & Configuration for Nivesh Firewall.

Phase 14.1: Production Configuration & Environment Architecture.
Supports development, test, and production environments with safe defaults,
strict validation, and zero leaked secrets.
"""

from enum import Enum
from functools import lru_cache
import json
import re
from typing import Any, List, Literal, Optional, Union
from urllib.parse import urlparse

from pydantic import AliasChoices, Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


EnvironmentMode = Literal["development", "test", "production"]
LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
LogFormat = Literal["json", "text"]
SourceMode = Literal["LIVE", "OFFICIAL_SNAPSHOT", "CACHE", "FIXTURE"]


def mask_sensitive_url(url: Optional[str]) -> Optional[str]:
    """Mask credentials in database URLs (e.g. database connection strings)."""
    if not url:
        return url
    return re.sub(r"://([^:]+):([^@]+)@", r"://\1:***@", url)


class Settings(BaseSettings):
    """Central typed configuration for the Nivesh Firewall system."""

    model_config = SettingsConfigDict(
        env_prefix="NIVESH_",
        extra="ignore",
        case_sensitive=False,
    )

    # 1. Environment & Mode
    env: EnvironmentMode = Field(
        default="development",
        description="Active operating environment: 'development', 'test', or 'production'",
    )
    debug: bool = Field(
        default=False,
        description="Whether debug mode is active (strictly forbidden in production)",
    )
    app_name: str = Field(
        default="Nivesh Firewall",
        description="Human-readable application name",
    )
    version: str = Field(
        default="1.0.0",
        description="Application release version",
    )

    # 2. Host & Network Binding
    host: str = Field(
        default="127.0.0.1",
        validation_alias=AliasChoices("NIVESH_HOST", "HOST"),
        description="Host interface to bind HTTP server",
    )
    port: int = Field(
        default=8000,
        validation_alias=AliasChoices("NIVESH_PORT", "PORT"),
        description="Port for HTTP server",
    )
    forwarded_allow_ips: str = Field(
        default="*",
        description="Trusted proxy IPs for X-Forwarded-* headers (comma-separated or '*' for all)",
    )
    workers: int = Field(
        default=4,
        ge=1,
        validation_alias=AliasChoices("NIVESH_WORKERS", "WEB_CONCURRENCY", "WORKERS"),
        description="Number of ASGI worker processes for production server",
    )

    # 3. Security & Persistence Contract (Phase 14.1 contract for Phase 14.2 persistence)
    secret_key: Optional[str] = Field(
        default=None,
        description="Application secret key for cryptographic operations and session signing",
    )
    database_url: Optional[str] = Field(
        default=None,
        description="Database connection URI (required in production; safe fallback in dev/test)",
    )
    db_pool_size: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Database connection pool size for persistent connections",
    )
    db_max_overflow: int = Field(
        default=20,
        ge=0,
        le=200,
        description="Maximum overflow connections beyond pool_size",
    )
    db_pool_timeout: float = Field(
        default=30.0,
        ge=1.0,
        description="Seconds to wait before timing out on connection checkout",
    )
    db_pool_recycle: int = Field(
        default=1800,
        ge=60,
        description="Seconds after which connections are recycled (avoids stale connections)",
    )
    db_ssl_mode: Optional[str] = Field(
        default=None,
        description="Optional SSL mode for PostgreSQL connections: disable, allow, prefer, require, verify-ca, verify-full",
    )
    admin_api_key: Optional[str] = Field(
        default=None,
        description="Static secret API key for administrative operations",
    )
    service_api_key: Optional[str] = Field(
        default=None,
        description="Static secret API key for internal service-to-service operations",
    )
    auth_token_expire_seconds: int = Field(
        default=3600,
        description="Authentication token validity duration in seconds (default 1 hour)",
    )
    rate_limit_enabled: bool = Field(
        default=True,
        description="Operational flag controlling API request rate limiting",
    )
    rate_limit_requests_per_minute: int = Field(
        default=120,
        description="Maximum permitted requests per minute per IP / token",
    )

    # 4. Frontend & CORS
    frontend_url: str = Field(
        default="http://localhost:5173",
        description="Base URL of the primary Nivesh web application",
    )
    allowed_origins: Union[List[str], str] = Field(
        default_factory=lambda: ["http://localhost:5173", "http://127.0.0.1:5173"],
        description="List of allowed HTTP origins for CORS",
    )
    allowed_extension_ids: Union[List[str], str] = Field(
        default_factory=list,
        description="Allowed browser extension IDs for chrome-extension:// origins",
    )

    # 5. Logging & Observability
    log_level: LogLevel = Field(
        default="INFO",
        description="System logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL",
    )
    log_format: LogFormat = Field(
        default="json",
        description="Log output structure: 'json' (production structured) or 'text' (console)",
    )
    tracing_enabled: bool = Field(
        default=True,
        description="Operational flag controlling distributed tracing span generation",
    )
    metrics_enabled: bool = Field(
        default=True,
        description="Operational flag controlling Prometheus/JSON metrics collection",
    )
    metrics_path: str = Field(
        default="/api/v1/metrics",
        description="Endpoint path where operational metrics are exposed",
    )
    health_db_timeout_seconds: float = Field(
        default=2.0,
        description="Timeout for database probe during readiness check",
    )

    # 6. Authoritative Source Intelligence (Engine 4)
    source_mode: SourceMode = Field(
        default="FIXTURE",
        description="Source Intelligence retrieval mode: FIXTURE, OFFICIAL_SNAPSHOT, CACHE, or LIVE",
    )
    live_sources_enabled: bool = Field(
        default=False,
        description="Explicit gate permitting live external regulatory network queries",
    )
    sebi_live_enabled: bool = Field(
        default=False,
        description="Explicit gate permitting live SEBI registry lookups",
    )
    rbi_live_enabled: bool = Field(
        default=False,
        description="Explicit gate permitting live RBI data and publication queries",
    )
    nse_live_enabled: bool = Field(
        default=False,
        description="Explicit gate permitting live NSE corporate announcement lookups",
    )
    bse_live_enabled: bool = Field(
        default=False,
        description="Explicit gate permitting live BSE corporate data queries",
    )
    nse_provider_preference: str = Field(
        default="AUTO",
        description="NSE provider selection priority: AUTO (official -> public -> nsepython -> snapshot), OFFICIAL, PUBLIC, or NSEPYTHON",
    )
    nsepython_enabled: bool = Field(
        default=False,
        description="Explicit gate permitting optional sandboxed NSEPython provider when installed",
    )
    nse_api_key: Optional[str] = Field(
        default=None,
        description="Server-side secret API key for NSE data access",
    )
    nse_api_secret: Optional[str] = Field(
        default=None,
        description="Server-side secret API secret for NSE data access",
    )
    bse_api_key: Optional[str] = Field(
        default=None,
        description="Server-side secret API key for BSE Corporate Data API",
    )
    bse_api_secret: Optional[str] = Field(
        default=None,
        description="Server-side secret API secret for BSE Corporate Data API",
    )
    bse_provider_preference: str = Field(
        default="AUTO",
        description="BSE provider selection priority: AUTO (official -> public -> snapshot), OFFICIAL, PUBLIC, or SNAPSHOT",
    )
    bse_public_enabled: bool = Field(
        default=False,
        description="Explicit gate permitting public BSE web dissemination queries when live sources are enabled",
    )
    source_freshness_ttl_seconds: int = Field(
        default=3600,
        description="Max cache freshness duration before evidence is considered stale (seconds)",
    )
    snapshot_freshness_days: int = Field(
        default=30,
        description="Max acceptable age for official snapshots before warning (days)",
    )

    # 7. Operational Feature Flags
    browser_extension_enabled: bool = Field(
        default=True,
        description="Operational flag controlling browser extension API ingestion",
    )
    analysis_retrieval_enabled: bool = Field(
        default=True,
        description="Operational flag controlling GET analysis retrieval endpoint",
    )

    # 8. Network & Operation Timeouts
    timeout_request_seconds: float = Field(
        default=30.0,
        description="Maximum HTTP request timeout in seconds",
    )
    timeout_retrieval_seconds: float = Field(
        default=10.0,
        description="Maximum timeout for external source retrieval operations",
    )
    timeout_pipeline_ms: Optional[float] = Field(
        default=None,
        description="Optional maximum end-to-end pipeline execution timeout in milliseconds",
    )
    timeout_engine_ms: Optional[float] = Field(
        default=None,
        description="Optional maximum per-engine execution timeout in milliseconds",
    )

    # 9. Maximum Payload Limits
    max_request_bytes: int = Field(
        default=10_485_760,  # 10 MB
        description="Maximum total HTTP request payload size in bytes",
    )
    max_content_length: int = Field(
        default=50_000,
        description="Maximum permitted text content length in characters",
    )
    max_url_length: int = Field(
        default=2048,
        description="Maximum permitted URL length in characters",
    )
    max_image_bytes: int = Field(
        default=10_485_760,  # 10 MB
        description="Maximum permitted image payload size in bytes",
    )
    max_session_id_length: int = Field(
        default=128,
        description="Maximum session identifier length in characters",
    )

    @field_validator("database_url", mode="before")
    @classmethod
    def normalize_database_url(cls, v: Optional[str]) -> Optional[str]:
        """Normalize legacy or cloud-provider database URLs (e.g., Render/Heroku postgres://)."""
        if v and isinstance(v, str):
            v_clean = v.strip()
            if v_clean.startswith("postgres://"):
                return v_clean.replace("postgres://", "postgres" + "ql://", 1)
        return v

    @field_validator("frontend_url")
    @classmethod
    def validate_frontend_url(cls, v: str) -> str:
        if not v or not isinstance(v, str):
            raise ValueError("frontend_url cannot be empty.")
        parsed = urlparse(v.strip())
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            raise ValueError(f"Invalid URL for frontend_url: '{v}'. Must be a valid HTTP/HTTPS URL.")
        return v.rstrip("/")

    @field_validator("allowed_origins", "allowed_extension_ids", mode="after")
    @classmethod
    def parse_list_values(cls, v: Union[List[str], str]) -> List[str]:
        if isinstance(v, str):
            v_str = v.strip()
            if v_str.startswith("[") and v_str.endswith("]"):
                try:
                    parsed = json.loads(v_str)
                    if isinstance(parsed, list):
                        return [str(x).strip() for x in parsed if str(x).strip()]
                except Exception:
                    pass
            return [x.strip() for x in v_str.split(",") if x.strip()]
        if isinstance(v, list):
            return [str(x).strip() for x in v if str(x).strip()]
        return []

    @model_validator(mode="after")
    def validate_environment_and_defaults(self) -> "Settings":
        """Apply safe environment defaults and enforce production safety checks."""
        # 1. Environment-specific defaults
        if self.env == "development":
            if not self.database_url:
                self.database_url = "sqlite:///./nivesh_dev.db"
        elif self.env == "test":
            if not self.database_url:
                self.database_url = "sqlite:///:memory:"

        # 2. Production validation enforcement
        if self.env == "production":
            self.validate_production_readiness()

        return self

    def validate_production_readiness(self) -> None:
        """Validate all security and infrastructure requirements for production mode.

        Fails with clear, non-leaking configuration errors if required settings are missing.
        """
        # A. Debug mode strictly forbidden
        if self.debug is True:
            raise ValueError(
                "Production environment cannot run with debug mode enabled (NIVESH_DEBUG=True). "
                "Set NIVESH_DEBUG=False for production."
            )

        # B. Database URL is strictly required
        if not self.database_url or not self.database_url.strip():
            raise ValueError(
                "Production environment requires a persistent NIVESH_DATABASE_URL to be configured."
            )

        # C. Disallow dev / SQLite fallbacks in production
        db_clean = self.database_url.strip().lower()
        if db_clean.startswith("sqlite"):
            raise ValueError(
                "Production environment cannot use development or in-memory SQLite database fallback. "
                "A production-grade persistent database (e.g. PostgreSQL) is required."
            )

        # D. Disallow wildcard CORS in production
        if any(origin.strip() == "*" for origin in self.allowed_origins):
            raise ValueError(
                "Production CORS configuration forbids wildcard origin ('*'). "
                "Specify explicit allowed origins in NIVESH_ALLOWED_ORIGINS."
            )

        if not self.allowed_origins:
            raise ValueError(
                "Production environment requires at least one explicit allowed origin in NIVESH_ALLOWED_ORIGINS."
            )

        for origin in self.allowed_origins:
            orig = origin.strip()
            if not (orig.startswith("https://") or orig.startswith("http://") or orig.startswith("chrome-extension://")):
                raise ValueError(
                    f"Invalid origin in NIVESH_ALLOWED_ORIGINS: '{origin}'. "
                    "Allowed origins must start with 'https://', 'http://', or 'chrome-extension://'."
                )

        # E. Live source mode consistency
        if self.source_mode == "LIVE" and not self.live_sources_enabled:
            raise ValueError(
                "NIVESH_SOURCE_MODE=LIVE requires NIVESH_LIVE_SOURCES_ENABLED=True in production."
            )

        # F. Secret key entropy validation
        if self.secret_key is not None and (
            "change_this" in self.secret_key.lower()
            or len(self.secret_key.strip()) < 16
        ):
            raise ValueError(
                "Production environment cannot use placeholder or insecure NIVESH_SECRET_KEY."
            )

    def is_development(self) -> bool:
        return self.env == "development"

    def is_test(self) -> bool:
        return self.env == "test"

    def is_production(self) -> bool:
        return self.env == "production"

    def get_cors_origins(self) -> List[str]:
        """Compute the complete list of allowed CORS origins including extension origins."""
        origins = list(self.allowed_origins)

        # Attach extension origins if configured
        for ext_id in self.allowed_extension_ids:
            clean_id = ext_id.strip()
            if clean_id:
                ext_origin = f"chrome-extension://{clean_id}"
                if ext_origin not in origins:
                    origins.append(ext_origin)

        # In development, ensure local frontend origins exist
        if self.is_development():
            for local_origin in ["http://localhost:5173", "http://127.0.0.1:5173"]:
                if local_origin not in origins:
                    origins.append(local_origin)

        return origins

    def safe_dump(self) -> dict[str, Any]:
        """Serialize configuration without exposing private credentials, keys, or passwords."""
        data = self.model_dump()
        if data.get("database_url"):
            data["database_url"] = mask_sensitive_url(data["database_url"])
        if data.get("secret_key"):
            data["secret_key"] = "***REDACTED***"
        if data.get("admin_api_key"):
            data["admin_api_key"] = "***REDACTED***"
        if data.get("service_api_key"):
            data["service_api_key"] = "***REDACTED***"
        for key in ("nse_api_key", "nse_api_secret", "bse_api_key", "bse_api_secret"):
            if data.get(key):
                data[key] = "***REDACTED***"
        return data

    def get_secret_key(self) -> str:
        """Return application secret key with safe dev/test fallback."""
        if self.secret_key and self.secret_key.strip():
            return self.secret_key.strip()
        return "nivesh-firewall-secure-fallback-secret-key-32-chars-long"

    def __repr__(self) -> str:
        safe = self.safe_dump()
        items = ", ".join(f"{k}={v!r}" for k, v in safe.items())
        return f"Settings({items})"

    def __str__(self) -> str:
        return repr(self)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached singleton instance of application Settings."""
    return Settings()
