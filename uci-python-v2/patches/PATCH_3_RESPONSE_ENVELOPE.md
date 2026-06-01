# UCI Patch 3 — Canonical Response Envelope

## Purpose

Introduce `UCIResponse` as a first-class protocol object. Every invocation
now returns exactly one `UCIResponse` — no raw dicts, no bare exceptions.

## New Files

- `uci/core/response.py` — UCIResponse, UCIResponseError, UCIResponseProvider,
  UCIResponseGovernance, UCIResponseAudit, ResponseState
- `test_rig/scenarios/test_response.py` — 50 response envelope tests

## Changed Files

- `uci/sdk/provider.py` — UCIOrchestrator.invoke() now returns UCIResponse
- `test_rig/scenarios/test_governance.py` — updated for UCIResponse
- `test_rig/scenarios/test_trust_and_invocation.py` — updated for UCIResponse

## Response Shape

```json
{
  "uci_response_version": "0.1",
  "invocation_id":  "<uuid4>",
  "correlation_id": "<uuid4 or caller-supplied>",
  "timestamp":      "<ISO-8601 UTC>",
  "state":          "completed | failed | deferred | partial",
  "success":        true,
  "provider": {
    "node_id": "...", "instance_id": "...",
    "capability_id": "...", "action_id": "..."
  },
  "output":     { ... },
  "error":      null,
  "governance": { "outcome": "allow", "trust_state": "trusted", "restrictions": [], "operator_id": null },
  "audit":      { "invocation_id": "...", "node_id": "...", "timestamp": "...", "outcome": "allow", "actor": "..." }
}
```

## Factories

| Factory | When to use |
|---|---|
| `UCIResponse.success_response(...)` | Action completed successfully |
| `UCIResponse.failure_response(...)` | Action ran but governance or runtime denied |
| `UCIResponse.deferred_response(...)` | Governance deferred — awaiting operator |
| `UCIResponse.from_exception(exc)` | Unexpected exception during invocation |

## Invoke behaviour change

`orchestrator.invoke()` no longer raises — all outcomes are envelopes:
- Success → `response.success == True`, `response.output` has data
- Governance deny → `response.error.code == "GOVERNANCE_DENIED"`
- Governance defer → `response.state == "deferred"`, `response.error.code == "GOVERNANCE_DEFERRED"`
- Node not found → `response.error.code == "NODE_NOT_FOUND"`

Use `response.assert_success()` to get output or raise `UCIError` on failure.

## Test Result

```
141 passed
0 failed
```
