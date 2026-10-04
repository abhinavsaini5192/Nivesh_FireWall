"""Alembic environment configuration for Nivesh Firewall.

Connects to the central Nivesh configuration (NIVESH_DATABASE_URL)
and targets Base.metadata from nivesh.storage.models.
"""

from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

from nivesh.config import get_settings
from nivesh.storage.models import Base
from nivesh.storage.database import get_engine

config = context.config

import logging

# Interpret the config file for Python logging if present and not already configured
if config.config_file_name is not None and not logging.getLogger().handlers:
    fileConfig(config.config_file_name, disable_existing_loggers=False)

target_metadata = Base.metadata


def get_configured_url() -> str:
    """Retrieve database URL from alembic config override, falling back to Nivesh settings."""
    cfg_url = config.get_main_option("sqlalchemy.url")
    if cfg_url and cfg_url.strip() and not cfg_url.startswith("driver://") and not cfg_url.startswith("sqlite:///./nivesh_dev.db"):
        url = cfg_url
    else:
        db_url = get_settings().database_url
        url = db_url if db_url and db_url.strip() else (cfg_url or "sqlite:///./nivesh_dev.db")
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return url


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode without an active DBAPI connection."""
    url = get_configured_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode using Nivesh database engine."""
    # Use Nivesh's configured engine directly to ensure dialect options (e.g. check_same_thread) match
    target_url = get_configured_url()
    connectable = get_engine(target_url)

    try:
        with connectable.connect() as connection:
            context.configure(
                connection=connection,
                target_metadata=target_metadata,
                render_as_batch=connection.dialect.name == "sqlite",
            )

            with context.begin_transaction():
                context.run_migrations()
    finally:
        from nivesh.storage.database import _ENGINE
        if connectable is not _ENGINE:
            connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
