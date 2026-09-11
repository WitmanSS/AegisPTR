# AegisPTR Architecture

## 1. Purpose
AegisPTR is a Pentest-to-Remediation orchestration platform designed to turn raw security findings into validated, prioritized, and actionable remediation workflows. The platform is built for authorized security testing, with explicit scope controls, audit logging, and human approval gates for high-impact operations.

## 2. Core Architecture
The system is organized around six primary layers:

1. Presentation layer
2. API and orchestration layer
3. Security intelligence layer
4. Data and evidence layer
5. Tool execution layer
6. Integration and reporting layer

```text
Client / Browser
    ↓
React + TypeScript UI
    ↓
FastAPI API Gateway
    ↓
Core Services:
  - Assessment Management
  - Scope Engine
  - Tool Orchestration
  - Correlation Engine
  - Risk Engine
  - Remediation Engine
  - Retest Engine
  - KPI Engine
  - AI Engine
    ↓
PostgreSQL + Redis + Object Storage
    ↓
Security Tool Adapters
  - Nmap
  - Nuclei
  - ZAP
  - Nessus/OpenVAS
  - Metasploit (optional)
```

## 3. Component Architecture
### 3.1 Web UI
The frontend is a React + TypeScript application with a dark enterprise UI optimized for security operations workflows. It exposes dashboards, assessment management, findings, remediation tracking, retests, AI Copilot, and reporting pages.

### 3.2 API Layer
FastAPI provides all backend APIs and OpenAPI documentation. Endpoints are grouped by domain and protected by authentication, RBAC, rate limits, and validation.

### 3.3 Core Engines
- Assessment Engine: creates, tracks, and manages assessment lifecycle states.
- Scope Engine: validates targets, ports, domains, CIDR, exclusions, and policy constraints.
- Tool Orchestration Engine: manages execution queues, concurrency, tool health, and task state.
- Correlation Engine: identifies same vulnerability across multiple tool outputs using deterministic rules and AI-assisted similarity.
- Risk Engine: computes contextual risk based on exposure, exploitability, asset criticality, and business context.
- Remediation Engine: creates tasks and playbooks with approval gates.
- Retest Engine: verifies remediations and compares before/after states.
- KPI Engine: calculates operational metrics such as MTTD, MTTR, closure rate, and risk reduction.
- AI Engine: offers grounded analysis and recommendations from evidence-bound context only.

## 4. Database Architecture
PostgreSQL is the system of record for structured entities. Redis is used for queueing and caching. Object storage is used for raw tool output, evidence attachments, and screenshots.

Key entities include:
- users
- roles
- permissions
- assessments
- assessment_scopes
- assets
- services
- technologies
- tools
- tool_runs
- findings
- finding_sources
- finding_evidence
- vulnerabilities
- cves
- risk_scores
- remediation_tasks
- remediation_playbooks
- retests
- kpis
- reports
- audit_logs
- ai_sessions
- ai_messages
- integrations
- webhooks

UUIDs are used for primary identifiers. Alembic manages migrations.

## 5. Event Architecture
A lightweight event-driven design is used for asynchronous task workflows and UI updates.

Example events:
- AssessmentStarted
- ToolStarted
- ToolCompleted
- AssetDiscovered
- FindingCreated
- FindingCorrelated
- FindingValidated
- RiskCalculated
- RemediationCreated
- RemediationCompleted
- RetestStarted
- RetestCompleted
- FindingClosed

These events are delivered through Redis or an internal event bus, enabling decoupled processing and monitoring.

## 6. Security Architecture
The platform is security-first and explicitly limited to authorized testing.

Key controls:
- scope-based execution validation
- approval gates for active scans and exploitation workflows
- immutable audit logging
- least-privilege RBAC
- safe command execution with strict argument validation
- secret redaction and secure storage
- input validation and protection against injection and traversal attacks
- tenant or assessment isolation for AI context
- explicit human approval before destructive or disruptive actions

The system must never execute shell commands constructed from raw, untrusted input.

## 7. AI Architecture
The AI subsystem is evidence-grounded and provider-agnostic.

Supported modes:
- Cloud API
- Local model via Ollama
- Disabled

The AI abstraction layer exposes methods such as:
- analyze_finding
- correlate_findings
- calculate_context
- generate_remediation
- generate_report

All outputs are classified as FACT, INFERENCE, RECOMMENDATION, or UNCERTAIN. No AI-generated output may fabricate CVEs, CVSS scores, exploitability, or remediation facts without supporting evidence.

## 8. Tool Adapter Architecture
Each tool implements a standardized interface:
- detect
- validate
- build_command
- execute
- parse_output
- normalize
- health_check

Adapters are plugin-based and isolated from the core application. The architecture supports tools across reconnaissance, scanning, web testing, exploitation validation, and reporting.

Initial adapters include:
- Nmap
- Nuclei
- ZAP
- Nessus/OpenVAS
- Burp import
- Metasploit
- Nikto
- httpx/ffuf/Gobuster
- whois/dig/Amass

## 9. Data Flow
1. Create assessment and define authorized scope.
2. Discover assets and services.
3. Execute approved tools in parallel.
4. Ingest raw output and parse into structured records.
5. Normalize findings into a canonical schema.
6. Deduplicate and correlate related results.
7. Validate and score risk.
8. Prioritize findings and assign remediation tasks.
9. Retest after remediation and compare before/after states.
10. Update KPIs and generate reports.

## 10. Deployment Architecture
The project supports:
- local development via Python and React
- Docker Compose for service orchestration
- install.sh and start.sh for quick startup

Local default endpoints:
- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- API docs: http://localhost:8000/docs

## 11. Security and Compliance Orientation
AegisPTR is designed for authorized security testing and remediation management. It is not a general-purpose vulnerability scanner. Its focus is operational intelligence: convert raw evidence into contextualized, prioritized, and verifiable remediation action.

## 12. MVP Scope
The first implementation milestone focuses on:
- authentication
- dashboard
- assessment and scope management
- tool detection
- Nmap adapter
- Nuclei adapter
- ZAP adapter
- tool execution engine
- result ingestion
- normalized finding model
- deduplication
- correlation
- risk scoring
- finding management

This staged approach keeps the code maintainable and aligned with the project’s security requirements.
