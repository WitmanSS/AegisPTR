# AegisPTR

AegisPTR is a Pentest-to-Remediation intelligence and orchestration platform. It supports authorized scanning, evidence ingestion, deduplication, correlation, contextual risk analysis, remediation planning, retesting, and KPI reporting.

## Overview
This repository provides the foundation for a production-oriented cybersecurity platform designed for authorized security work, with a modular backend, plugin-based tool adapters, and an enterprise-style frontend shell.

## Quick start

```bash
./install.sh
./start.sh
```

Optional Docker workflow:

```bash
cp .env.example .env
# Set production secrets in .env before starting the stack.
docker compose up -d --build
```

The Docker stack runs PostgreSQL, Redis, the FastAPI backend, a finding-enrichment
worker, and the compiled React frontend behind Nginx. The backend applies the
idempotent SQL migrations on startup. Set `ADMIN_USER` and `ADMIN_PASS` in `.env`
to seed an initial admin.
The frontend is available at `http://localhost:3000` and proxies `/api` to the
backend service, so browser requests do not depend on a hardcoded localhost API.
PostgreSQL and Redis are private to the Compose network and are not published on
host ports. For internet-facing production, terminate HTTPS at a trusted reverse
proxy or load balancer in front of the frontend service.
Replace every `replace-with-*` value in `.env` with independently generated
URL-safe secrets before deployment. The browser keeps its bearer token in memory only, so
sign-in is required again after a page reload. The monitoring endpoint currently
returns configured KPI values rather than metrics calculated from persisted findings.

To stop the stack while keeping its database volumes:

```bash
docker compose down
```

For a full local reset, including database and Redis data:

```bash
docker compose down -v
```

## Default local endpoints
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- OpenAPI docs: http://localhost:8000/docs

## Project structure

```text
.
├── ARCHITECTURE.md
├── docker-compose.yml
├── .env.example
├── Makefile
├── install.sh
├── start.sh
├── backend/
│   ├── app/
│   ├── migrations/
│   ├── tests/
│   └── requirements.txt
├── frontend/
│   ├── src/
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   └── index.html
└── README.md
```

## Security focus
- authorized-only assessment execution
- explicit scope validation
- permission-aware command execution
- immutable audit trail
- evidence-grounded AI analysis

## License
This project is built for authorized security workflows and research-oriented pentest-to-remediation tooling. Ensure all uses remain within proper scope and authorization.
