# UCI Patch 6 — Compliance Suite

## Purpose

Add a formal compliance suite that verifies UCI *protocol behaviour*,
not just implementation correctness. This is the test file you hand to
anyone implementing UCI in another language: if these pass, you're compliant.

## New File

- `test_rig/scenarios/test_compliance.py` — 63 compliance tests

## Compliance Rules Verified

| Group | Rules | Description |
|---|---|---|
| C-MAN | 001–012 | Manifest structure, enums, round-trip |
| C-GOV | 001–010 | Fail-closed, deny-by-default, trust enforcement, audit coverage |
| C-HSK | 001–009 | Handshake stages, fail-closed, audit trail |
| C-RSP | 001–012 | Envelope shape, assert_success, correlation ID, wire survival |
| C-AUD | 001–010 | Append-only, chain hashing, tamper detection, session export |
| C-SCH | 001–008 | All three objects pass JSON Schema; legacy values rejected |
| C-INT | 001–002 | Full session compliance, restricted node compliance |

## Bug Found and Fixed

C-HSK-008 revealed that handshake validation failures were emitting
`manifest_validation_failed` but not the terminal `handshake_failed`
event. Fixed by refactoring all early-return failure paths through a
`_fail()` helper that always emits `handshake_failed` before returning.

## Test Result

```
284 passed (221 existing + 63 new)
0 failed
```
