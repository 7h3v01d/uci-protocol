# UCI Patch 7 — Spec Alignment

## Purpose

Align the Python reference implementation precisely with the 23 specification
documents. Every gap identified after reading the full spec has been closed.

## Gaps Closed

### Gap 1 — Canonical error codes (lowercase_snake_case)
`UCIResponseError.code` was ad-hoc SCREAMING_SNAKE.
Spec (taxonomy_naming §10, error_response_model §13) defines lowercase_snake_case.
Added `UCIErrorCode` class with all spec-defined canonical codes.

### Gap 2 — Error object missing `severity` and `retryable`
Spec (error_response_model §12) requires both as mandatory fields.
Added to `UCIResponseError` with appropriate defaults.

### Gap 3 — ResponseState missing 7 canonical states
Spec (error_response_model §6) defines 10 states.
Added: `denied`, `cancelled`, `timed_out`, `partially_completed`,
`queued`, `executing`, `rolled_back`.
Governance denials now produce `state=denied` (not `failed`).

### Gap 4 — UCIInvocation as first-class object
Spec (invocation_execution §3-4) defines the canonical invocation structure.
Added `UCIInvocation` with `UCIInvocationCaller`, `UCIInvocationTarget`,
`UCIInvocationContext`. `orchestrator.invoke_with(inv)` added as canonical path.

### Gap 5 — AuditRecord missing spec-required fields
Spec (audit_observability §7) requires: `audit_event_version`, `correlation_id`,
`severity`, `source`. All added to `AuditRecord` and `AuditLog.append()`.

### Gap 6 — `health` block missing from manifest
Spec (capability_schema §4) lists `health` as a required top-level block.
`UCIHealth` dataclass added. `health` now required in manifest and JSON schema.

### Gap 7 — `display_name` not required in node
Spec (json_schema §node) marks `display_name` as required.
`UCINode.validate()` now enforces it.

### Gap 8 — JSON schema $id URIs
Spec proposes `uci-spec.org` as canonical URI.
All three schemas updated from `uci-spec.org` to `uci-spec.org`.

### Gap 9 — Repository structure
Spec (repository_structure) defines: `docs/`, `test_vectors/`, `LICENSE`,
`CONTRIBUTING.md`, `SECURITY.md`. All added. All 23 spec documents
are now included under `docs/`.

## New Files

- `uci/core/invocation.py` — UCIInvocation first-class protocol object
- `docs/` — all 23 spec documents
- `test_vectors/valid/` — valid manifest test vectors
- `test_vectors/invalid/` — invalid manifest test vectors
- `test_vectors/warnings/` — warning-producing test vectors
- `test_rig/scenarios/test_patch7_spec_alignment.py` — 47 spec alignment tests
- `LICENSE` — Apache-2.0
- `CONTRIBUTING.md`
- `SECURITY.md`

## The four protocol objects

After Patch 7, UCI has four first-class protocol objects:

| Object | File | Role |
|---|---|---|
| `UCIManifest` | `manifest.py` | Identity |
| `UCIInvocation` | `invocation.py` | Request |
| `UCIResponse` | `response.py` | Answer |
| `UCIAuditSession` | `audit.py` | Record |

## Test Result

```
331 passed (284 existing + 47 new)
0 failed
```
