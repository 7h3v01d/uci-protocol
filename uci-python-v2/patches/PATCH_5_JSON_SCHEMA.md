# UCI Patch 5 — JSON Schema Validator Integration

## Purpose

Add language-agnostic JSON Schemas for all three canonical UCI objects,
and integrate schema validation as a first-class stage in the CLI validator.
Any UCI implementation in any language can now validate against these schemas.

## New Files

### Schemas (uci/schemas/)
- `uci_manifest_v0_1.json`     — Manifest schema (Draft 2020-12)
- `uci_response_v0_1.json`     — Response envelope schema
- `uci_audit_session_v0_1.json`— Audit session schema

### Code
- `uci/core/schema_validator.py` — Schema loading, validation API,
  SchemaIssue, SchemaValidationResult
- `test_rig/scenarios/test_schema_validator.py` — 42 schema tests

## Schema Coverage

| Schema | Enforces |
|---|---|
| Manifest | version enum, node_type enum, execution mode enum, transport type enum, capability category enum, risk level enum, risk category enum, node_id pattern, minItems on capabilities/transports/actions, timeout_ms >= 1 |
| Response | state enum, governance outcome enum, trust_state enum, error oneOf null/object |
| Audit session | chain_hash length = 64, sequence >= 1, record_count present |

## Validation pipeline (uci_validate.py)

Stage 3a now runs between structural pre-checks and from_dict():
```
Stage 3:  Top-level block presence
Stage 3a: JSON Schema validation  ← NEW
Stage 4:  UCIManifest.from_dict() deserialisation
Stage 5:  manifest.validate() semantic checks
Stage 6:  Deep semantic warnings
```

Schema violations surface as SCHEMA_VIOLATION error codes with
precise JSON path locations (e.g. capabilities[0].actions[0].execution.mode).

## API

```python
from uci.core.schema_validator import (
    validate_manifest_schema,
    validate_response_schema,
    validate_audit_session_schema,
)

result = validate_manifest_schema(data)   # SchemaValidationResult
if not result.valid:
    for issue in result.issues:
        print(issue.path, issue.message)
```

## Test Result

```
221 passed (179 existing + 42 new)
0 failed
```
