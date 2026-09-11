# Findings Explorer — Component Spec (AegisPTR)

## Overview
This document describes the components, interactions, data contract, and UI behaviors for the Findings Explorer (list + detail). Use this spec to implement the frontend, wire events, and integrate backend endpoints.

## Layout
- Two-column responsive layout:
  - Left column: Findings list (compact, paginated)
  - Right column: Finding Detail panel (tabbed: Summary / Evidence / Correlation / Remediation / History)
- Top bar: global search
- Contextual AI Copilot floating card (bottom-right of detail panel)

## Components

1. Findings List (component: `FindingsList`)
   - Props: `filters`, `page`, `sort`
   - Row fields: `severityBadge`, `title`, `assetLink`, `riskScore`, `confidence`, `trustLabel`, `evidenceCount`, `status`, `owner`
   - Actions: select, multi-select, open detail, quick-assign, bulk-create-remediation
   - Keyboard: up/down, Enter open, Space select, M assign, R remediate

2. Finding Detail (component: `FindingDetail`)
   - Tabs: Summary, Evidence, Correlation, Remediation, History
   - Summary: title, why-important visual (stacked factor bars), action buttons
   - Evidence: timeline list with expandable raw output and link to artifact
   - Correlation: matched_rules, fuzzy_score, merged_from, allow split/merge
   - Remediation: proposed actions, one-click-safe flow (preview -> dry-run -> approve -> execute)
   - History: append-only events

3. Why-Important Visual (`WhyStack`)
   - Input: array of `{label, weight, explanation}` sorted by weight
   - Visual: horizontal stacked bars with hover tooltip linking to evidence

4. Evidence Timeline (`EvidenceTimeline`)
   - Sorted by timestamp desc
   - Each item: tool, timestamp, short excerpt, open artifact
   - Raw viewer opens in modal with provenance and download

5. Correlation Provenance (`CorrelationCard`)
   - matched_rules: list with weight + rule description
   - fuzzy_score: numeric (0-1)
   - merged_from: list of obs_ids (links to evidence)
   - manual_overrides

6. AI Copilot Pane (`AICopilot`) — read-only suggestions unless approved
   - Inputs: current finding context + evidence + history
   - Outputs: recommendations (remediation steps, retest plan), confidence, explanation
   - Actions: generate remediation draft, copy to ticket, open approval modal

## Interactions & Flows
- Opening a finding detail subscribes UI to WS channel `finding:{finding_id}` for live updates.
- Creating a remediation calls `POST /api/remediations` and emits `remediation.created` (event bus).
- Approving/executing remediation requires elevated permission; UI displays policy warnings from `GET /api/policy/check`.
- Splitting a correlated finding triggers `POST /api/findings/{id}/split` and updates list on event `finding.created`.

## API Endpoints (minimal)
- `GET /api/findings?filters...&page=&size=` → paginated list
- `GET /api/findings/{id}` → full finding model
- `POST /api/findings/{id}/actions` → body `{action, payload}`
- `POST /api/findings/bulk/actions` → bulk operations
- `GET /api/findings/{id}/evidence/{obs_id}` → artifact
- `POST /api/remediations` → create remediation
- `POST /api/retests` → schedule retest

## WebSocket Topics
- `finding:{finding_id}` — granular updates for the detail pane
- `assessment:{assessment_id}` — feed for list and dashboard
- `asset:{asset_id}` — asset-centric events

Message format (WS):
```json
{ "topic": "finding:F-000123", "event": "finding.updated", "payload": { ... } }
```

## Data Schema (summary)
- `Finding` (see design note): id, title, description, severity, risk_score, confidence, trust, asset, attack_vector, cves, cwe, cvss, exploitability, status, owner, first_seen, last_seen, sources[], correlation{}, remediation{}, retest{}, audit[]
- `Source/Observation`: obs_id, tool, raw_output_url, parsed, timestamp, trust

## UX Constraints
- Default sort: severity desc, trust desc, last_seen desc
- Pagination + virtualized rows — do not render full list client-side
- Rate-limit WS updates; show aggregated "N new observations" if updates are high-volume
- All destructive or high-risk operations must surface policy and require explicit approval

## Accessibility
- All interactions keyboard-operable
- ARIA labels for timeline and evidence modal
- Color contrast must meet WCAG AA

## KPI / Telemetry hooks
- Track time-to-assign, time-to-remediate, retest-coverage, false-positive-rate (if marked)
- UI events: `view_finding`, `create_remediation`, `approve_remediation`, `split_finding`

## Implementation Notes
- Subscribe to `finding:{id}` when detail opens; unsubscribe on close
- Use server-sent event IDs to deduplicate evidence/observations
- Cache finding summaries for list view; request full detail on open

---

Files created:
- `design/findings_wireframe.svg`
- `design/findings_component_spec.md` (this file)

Next: I can generate OpenAPI JSON Schema for the `Finding` model and the event payloads, or scaffold FastAPI route stubs and Pydantic models to match this contract. Which do you prefer?