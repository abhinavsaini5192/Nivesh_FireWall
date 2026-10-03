#!/usr/bin/env python3
"""Nivesh Firewall — Production Application Entrypoint & Startup Validator.

Phase 14.5: Deployment, Performance & Production Validation

Executes pre-flight operational checks:
1. Validates production configuration and security requirements.
2. Applies database migrations to head via Alembic.
3. Tests database connectivity and health probe.
4. Verifies initialization of all 10 intelligence engines.
5. Launches Uvicorn ASGI server with production concurrency.
"""

import sys
import os
import logging
from typing import NoReturn

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def setup_startup_logger() -> logging.Logger:
    logging.basicConfig(
        level=logging.INFO,
        format='{"timestamp":"%(asctime)s","level":"%(levelname)s","service":"nivesh-startup","message":"%(message)s"}',
    )
    return logging.getLogger("nivesh.startup")


def run_preflight_checks(logger: logging.Logger) -> None:
    logger.info("Executing Nivesh Firewall production preflight checks...")

    # Step 1: Configuration Validation
    from nivesh.config import get_settings
    settings = get_settings()

    if settings.is_production():
        try:
            settings.validate_production_readiness()
            logger.info("Production configuration validation passed.")
        except Exception as e:
            logger.critical("Production readiness check failed: %s", e)
            sys.exit(1)
    else:
        logger.warning("Running in non-production environment: %s", settings.env)

    # Step 2: Database Migration Check
    try:
        from nivesh.storage.database import run_migrations, check_database_health
        logger.info("Applying database migrations to head...")
        run_migrations()
        logger.info("Database schema migrations successfully applied.")

        # Step 3: Health Probe Verification
        health = check_database_health()
        if not health.get("connected"):
            logger.critical("Database health probe failed: %s", health.get("error"))
            sys.exit(1)
        logger.info("Database connection established: dialect=%s", health.get("dialect"))
    except Exception as e:
        logger.critical("Database preflight initialization failed: %s", e)
        sys.exit(1)

    # Step 4: Engine Readiness Check
    try:
        from nivesh.orchestrator.service import ProductOrchestrator
        orchestrator = ProductOrchestrator()
        logger.info("All 10 intelligence engines successfully initialized.")
    except Exception as e:
        logger.critical("Intelligence engine preflight failed: %s", e)
        sys.exit(1)

    logger.info("All preflight checks passed. Application ready to serve production traffic.")


def main() -> None:
    logger = setup_startup_logger()
    run_preflight_checks(logger)

    # If run as standalone validator, exit with 0
    if len(sys.argv) > 1 and sys.argv[1] == "--check-only":
        logger.info("Preflight validation complete (--check-only). Exiting.")
        sys.exit(0)

    # Otherwise launch Uvicorn
    import uvicorn
    from nivesh.config import get_settings
    settings = get_settings()

    uvicorn.run(
        "nivesh.api.app:app",
        host=settings.host,
        port=settings.port,
        workers=4 if settings.is_production() else 1,
        log_level=settings.log_level.lower(),
        access_log=True,
    )


if __name__ == "__main__":
    main()
