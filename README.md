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
docker compose up -d
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
