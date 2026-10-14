# Infrastructure

This directory contains infrastructure and local environment configuration.

`postgres/docker-compose.yml` provides PostgreSQL / pgvector services for local L0 research. Start them with `make db-up` from the repository root. Database migrations are in `alembic/`.

This configuration is intended for local development. Production deployment still requires decisions on deployment region, tenant isolation, authentication, data retention, and recovery requirements.
