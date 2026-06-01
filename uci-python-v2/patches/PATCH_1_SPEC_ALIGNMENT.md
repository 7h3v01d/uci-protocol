# UCI Patch 1 — Spec Alignment Constants + Manifest Validation

## Purpose

Align the existing UCI Python test rig with the locked UCI v0.1 specification while preserving current runtime behaviour.

## Changes

- Replaced legacy execution mode `stream` with canonical `streaming`.
- Added canonical execution modes: `scheduled`, `event_driven`.
- Replaced legacy node types such as `tool`, `plugin`, and `workflow` with locked v0.1 node types.
- Added canonical transport types and replaced legacy `local` transport usage with `ipc`.
- Added canonical capability category validation.
- Added canonical risk category validation.
- Required manifests to declare at least one capability.
- Required manifests to declare at least one transport.
- Required capabilities to declare at least one action.
- Updated `to_dict()` to include v0.1 top-level blocks: `transports`, `compliance`, `audit`, and `extensions`.
- Preserved existing handshake, governance, registry, trust, and invocation behaviour.
- Updated the empty-capability test case to fail closed, matching locked v0.1 semantics.
- Added `test_spec_alignment.py` with locked enum and manifest-shape tests.

## Test Result

```text
56 passed
0 failed
```

## Notes

This patch intentionally does not add JSON Schema validation, canonical response envelopes, or a CLI validator. Those should be handled in the next patch to keep the alignment change small and safe.
