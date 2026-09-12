**Bulk Input — Preview & Validation**

- **Purpose:** Rapidly paste many targets, preview parsing/validation results, and add selected items to the authorized scope.

- **Primary view sections:**
  - Left: `Paste Targets` textarea with quick options (Resolve DNS, Remove Duplicates)
  - Right: `Preview & Validation` with summary badges, per-target rows, status indicators, and action buttons

- **Key interactions:**
  - Paste many targets → click `Parse Preview` → client calls `POST /api/targets/bulk/preview` with raw text.
  - Server returns parsed items with `canonical`, `type`, `validation` and `overlaps`.
  - UI shows rows with: original, canonical, type, validation status (OK / Warning / Invalid), hints and DNS resolution if requested.
  - User can select/deselect rows, edit canonical value inline, assign tags/environment/owner per selection.
  - `Add to Scope` persists selected targets via `POST /api/targets/` (bulk endpoint to be implemented) and shows import summary.

- **Validation rules (client + server):**
  - IP syntax, IPv4/IPv6, CIDR correctness
  - Range format
  - Domain syntax
  - URL correctness
  - Duplicate detection (original & canonical)
  - CIDR overlap detection
  - Optional DNS resolution when requested

- **Bulk UX details:**
  - Keyboard: `Ctrl+V` to paste, `Ctrl+Enter` to parse, `Shift+Enter` to toggle resolve option.
  - Quick filters: show only `Invalid`, `Warn`, `OK`, `Duplicates`, `Overlaps`.
  - Preview rows support inline edit and quick actions (Mark Excluded, Approve, Add Tag).

- **API notes:**
  - `POST /api/targets/bulk/preview` → accepts `{ "text": "...", "resolve": bool }` returns `{ count, items[], overlaps[] }`.
  - `POST /api/targets/` → create single target (already implemented); add a bulk create endpoint later.

- **Accessibility & Performance:**
  - Support pasting 500+ lines smoothly using web workers for parsing.
  - Announce validation counts with ARIA live regions.

- **Edge cases:**
  - Large CIDR ranges: warn and require explicit confirmation for ranges containing > 256 addresses.
  - Discovered assets flagged as `DISCOVERED — NOT AUTHORIZED` and not auto-added.

- **Next steps:**
  - Implement `bulk create` endpoint with transactional import and history entries.
  - Wire frontend component to `backend/app/api/routes/targets.py` and reuse existing `parse_bulk` service.
