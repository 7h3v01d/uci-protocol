# UCI Interoperability Report

| | |
|---|---|
| Schema Compatibility | ✓ PASS |
| Manifest Interop | ✓ PASS |
| Invocation Interop | ✓ PASS |
| Response Interop | ✓ PASS |
| Audit Session Interop | ✓ PASS |
| Semantic Validation | ✓ PASS |
| Chain Hash Cross-Language | ✓ PASS |

> This document is generated automatically by `uci-interop/generate_report.py`.
> It proves that the Python and TypeScript UCI implementations can exchange
> canonical protocol objects and validate each other's output.

---

## Result

| | |
|---|---|
| **Verdict** | **✓ PASS** |
| Run ID | `b4b8c189` |
| Timestamp | 2026-06-01T23:03:15Z |
| Total checks | 87/87 passed |
| Python → TypeScript | ✓ PASS |
| TypeScript → Python | ✓ PASS |

---

## What was tested

Each implementation independently produces five canonical UCI objects as JSON.
The other implementation then validates them — using its own stack, its own
schema validator, and its own chain hash implementation.

Neither implementation calls the other's code.
The only shared surface is the UCI specification and JSON schemas.

| Object | Validated |
|---|---|
| `UCIManifest` | Schema + semantic validation |
| `UCIInvocation` | Structure + field completeness |
| `UCIResponse` (success) | Schema + field semantics |
| `UCIResponse` (failure) | Schema + error code canonicality |
| `UCIAuditSession` | Schema + session hash + chain hash integrity |

---

## Step results

### ✓ Python produces canonical objects

8/8 checks passed

| Check | Result |
|---|---|
| Python producer exits cleanly | ✓ |
| Produced python_manifest.json | ✓ |
| Produced python_invocation.json | ✓ |
| Produced python_response_success.json | ✓ |
| Produced python_response_failure.json | ✓ |
| Produced python_audit_session.json | ✓ |
| Python audit integrity self-check | ✓ |
| Python session hash self-check | ✓ |

### ✓ TypeScript validates Python output

29/29 checks passed

| Check | Result |
|---|---|
| Schema valid | ✓ |
| node_id non-empty | ✓ |
| display_name non-empty | ✓ |
| Has capabilities | ✓ |
| Has transports | ✓ |
| health block present | ✓ |
| version is 0.1 | ✓ |
| Has invocation_id | ✓ |
| Has correlation_id | ✓ |
| Has caller.node_id | ✓ |
| Has target.node_id | ✓ |
| version is 0.1 | ✓ |
| Schema valid | ✓ |
| success == true | ✓ |
| state == completed | ✓ |
| output present | ✓ |
| error is null | ✓ |
| Schema valid | ✓ |
| success == false | ✓ |
| state == denied | ✓ |
| error.code canonical | ✓ |
| error.retryable is bool | ✓ |
| error.severity present | ✓ |
| Schema valid | ✓ |
| Session hash verifies | ✓ |
| Chain integrity intact | ✓ |
| node_discovered present | ✓ |
| trust_assigned present | ✓ |
| node_ready present | ✓ |

### ✓ TypeScript produces canonical objects

8/8 checks passed

| Check | Result |
|---|---|
| TypeScript producer exits cleanly | ✓ |
| Produced typescript_manifest.json | ✓ |
| Produced typescript_invocation.json | ✓ |
| Produced typescript_response_success.json | ✓ |
| Produced typescript_response_failure.json | ✓ |
| Produced typescript_audit_session.json | ✓ |
| TypeScript audit integrity self-check | ✓ |
| TypeScript session hash self-check | ✓ |

### ✓ Python validates TypeScript output

42/42 checks passed

| Check | Result |
|---|---|
| Schema validation passes | ✓ |
| Semantic validation passes | ✓ |
| node_id is non-empty | ✓ |
| display_name is non-empty | ✓ |
| Has capabilities | ✓ |
| Has transports | ✓ |
| node_type is canonical | ✓ |
| Has uci_invocation_version | ✓ |
| Has invocation_id | ✓ |
| Has correlation_id | ✓ |
| Has timestamp | ✓ |
| Has caller block | ✓ |
| Has target block | ✓ |
| Has payload | ✓ |
| Schema validation passes | ✓ |
| success == True | ✓ |
| state == 'completed' | ✓ |
| output is present | ✓ |
| error is None | ✓ |
| Has invocation_id | ✓ |
| Has correlation_id | ✓ |
| provider.node_id non-empty | ✓ |
| governance.outcome present | ✓ |
| audit snapshot present | ✓ |
| Schema validation passes | ✓ |
| success == False | ✓ |
| state == 'denied' | ✓ |
| error is present | ✓ |
| error.code is lowercase | ✓ |
| error.code is canonical | ✓ |
| error.retryable is bool | ✓ |
| error.severity is present | ✓ |
| output is None | ✓ |
| Schema validation passes | ✓ |
| Has records | ✓ |
| Session hash is present | ✓ |
| Session hash verifies | ✓ |
| Chain integrity intact | ✓ |
| Contains node_discovered | ✓ |
| Contains trust_assigned | ✓ |
| Contains node_ready | ✓ |
| Contains invocation records | ✓ |

---

## Chain hash algorithm

The audit chain hash is computed as:

```
SHA-256(canonical_json({
  previous_hash, sequence, event_id, event_type,
  node_id, timestamp, actor, outcome, detail
}))
```

Where `canonical_json` means: **sorted keys, no whitespace**.

- Python: `json.dumps(payload, sort_keys=True, separators=(',', ':'))`
- TypeScript: recursive object serialisation with `Object.keys().sort()`

Both produce byte-identical output for the same input.
This was verified by the interoperability test.

---

## Schemas

All objects validated against canonical schemas at `uci-spec.org`:

| Schema | URI |
|---|---|
| Manifest | `https://uci-spec.org/schemas/uci_manifest_v0_1.json` |
| Response | `https://uci-spec.org/schemas/uci_response_v0_1.json` |
| Audit Session | `https://uci-spec.org/schemas/uci_audit_session_v0_1.json` |

---

*Generated by `uci-interop/generate_report.py` · UCI v0.1.0-alpha · 2026-06-01T23:03:15Z*
