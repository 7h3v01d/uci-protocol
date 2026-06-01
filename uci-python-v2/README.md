# UCI — Universal Capability Interface
### Python Reference Implementation · v0.1.0-alpha

> *"What USB did for peripheral connectivity, UCI does for programs, AI agents, and services."*

> *UCI is a governance-aware capability contract layer that allows software nodes to declare, negotiate, and expose executable abilities to orchestrators under explicit policy and operator authority.*

---

## The four protocol objects

Everything in UCI flows through four canonical objects:

| Object | Role | What it answers |
|---|---|---|
| `UCIManifest` | Identity | Who am I? What can I do? What are my rules? |
| `UCIInvocation` | Request | Do this action, for this caller, with this payload |
| `UCIResponse` | Answer | What happened? What was the output? What did governance decide? |
| `UCIAuditSession` | Record | What happened in this session, provably and tamper-evidently? |

---

## Cross-language interoperability

**[Interoperability Report](https://github.com/uci-protocol/uci-interop/blob/main/INTEROP_REPORT.md)** — Python ↔ TypeScript: 87/87 checks passing

| | |
|---|---|
| Schema Compatibility | ✓ PASS |
| Manifest Interop | ✓ PASS |
| Invocation Interop | ✓ PASS |
| Response Interop | ✓ PASS |
| Audit Session Interop | ✓ PASS |
| Semantic Validation | ✓ PASS |
| Chain Hash Cross-Language | ✓ PASS |

Neither implementation calls the other's code.
The only shared surface is the UCI specification and JSON schemas.

---

## What is UCI?

UCI is an open protocol for **capability-based interoperability** between software nodes — programs, AI agents, services, hardware bridges, and orchestrators. It defines how nodes discover each other, negotiate trust, invoke actions through a governance layer, and produce verifiable audit records.

Think of it as a universal handshake contract. Any node that speaks UCI can connect to any orchestrator that speaks UCI — regardless of language, platform, or vendor — with governance, trust, and accountability built in from the start.

---

## How it works

```
  Provider Node                          Orchestrator
  ─────────────                          ────────────
  UCIManifest ──── Handshake ──────────► Registry
  (identity)       discover                │
                   validate                │
                   govern              Trust assigned
                   mount               (trusted / restricted)
                      │                    │
                      │◄─── UCIInvocation ─┘
                      │     caller identity
                      │     target node / capability / action
                      │     payload · context · correlation_id
                      │
                   Governance gate
                   (allow / allow_with_restrictions / defer / deny)
                      │
                      ▼
  UCIResponse ◄────────────────────────── caller
  state · success · output · error
  governance snapshot · audit reference
                      │
                      ▼
  UCIAuditSession ── chain-hashed, exportable, verifiable
  (tamper-evident record of everything that happened)
```

---

## Quick start

```bash
git clone <repo>
cd uci-python
pip install pytest jsonschema
```

**Run the demo:**
```bash
python run_rig.py
```

**Run the tests:**
```bash
python -m pytest test_rig/
```

**Validate a manifest:**
```bash
python uci_validate.py example_manifests/valid_document_service.json
python uci_validate.py example_manifests/ --strict
python uci_validate.py my_manifest.json --json
```

---

## The demo

`run_rig.py` shows the full UCI lifecycle in five phases:

```
PHASE 1 — Handshake Lifecycle
  ✓ Provider Alpha  trust=trusted   caps=[document_search, system_health]
  ✓ Provider Beta   trust=restricted  caps=[voice_tts]
  ⚠ Capability 'file_operations' not mounted — high-risk actions, restricted trust
  ✗ gamma_missing_node_id  — failed at manifest_validated
  ✗ provider_gamma_version — failed at manifest_validated

PHASE 2 — Governance in Action
  ✓ search_index → 2 result(s)
  ✓ health_check → status=healthy
  ✓ Correctly denied: nonexistent capability
  ✓ Correctly deferred: high-risk action without operator
  ✓ delete_file approved by operator → deleted=True

PHASE 3 — Trust Lifecycle
  ✓ provider_alpha trust → REVOKED
  ✓ Invocation correctly denied after revocation

PHASE 4 — Audit Trail
  49 events · 6 denials · chain intact

PHASE 5 — Registry State
  3 nodes registered · 1 ready
```

---

## Project structure

```
uci-python/
├── docs/                            # All 23 specification documents
│   ├── uci_core_proposal_v0_1.md
│   ├── uci_manifest_spec_v0_1.md
│   ├── uci_governance_model_v0_1.md
│   ├── uci_handshake_discovery_v0_1.md
│   ├── uci_invocation_execution_v0_1.md
│   ├── uci_error_response_model_v0_1.md
│   ├── uci_audit_observability_model_v0_1.md
│   └── ... (22 total)
├── uci/
│   ├── core/
│   │   ├── manifest.py        # UCIManifest — identity and capability contract
│   │   ├── invocation.py      # UCIInvocation — canonical request object
│   │   ├── response.py        # UCIResponse — canonical answer envelope
│   │   ├── audit.py           # AuditLog, UCIAuditSession — chain-hashed event log
│   │   ├── trust.py           # TrustState, TrustRecord — state machine
│   │   ├── governance.py      # PolicyEngine — allow / restrict / defer / deny
│   │   ├── handshake.py       # HandshakeEngine — 9-stage lifecycle
│   │   ├── registry.py        # UCIRegistry — in-memory node index
│   │   ├── schema_validator.py# JSON Schema validation layer
│   │   └── errors.py          # Typed UCI error hierarchy
│   ├── schemas/
│   │   ├── uci_manifest_v0_1.json
│   │   ├── uci_response_v0_1.json
│   │   └── uci_audit_session_v0_1.json
│   └── sdk/
│       └── provider.py        # UCIProvider, UCIOrchestrator base classes
├── test_rig/
│   ├── mock_providers/
│   │   ├── provider_alpha.py  # Fully compliant trusted node
│   │   ├── provider_beta.py   # Restricted trust, high-risk actions
│   │   └── provider_gamma.py  # Malformed / bad-actor variants
│   └── scenarios/
│       ├── test_compliance.py           # Formal compliance suite
│       ├── test_patch7_spec_alignment.py# Spec alignment verification
│       ├── test_handshake.py
│       ├── test_governance.py
│       ├── test_response.py
│       ├── test_audit_envelope.py
│       ├── test_schema_validator.py
│       ├── test_trust_and_invocation.py
│       ├── test_spec_alignment.py
│       └── test_validator.py
├── test_vectors/
│   ├── valid/                 # Known-good manifests
│   ├── invalid/               # Known-bad manifests (should be rejected)
│   └── warnings/              # Valid-but-warn manifests
├── example_manifests/
├── uci_validate.py            # CLI manifest validator
├── run_rig.py                 # Demo runner
├── LICENSE
├── CONTRIBUTING.md
└── SECURITY.md
```

---

## Core concepts

### Trust states

Nodes move through a defined trust ladder. No stage can be skipped.

```
unknown → discovered → verified → trusted
                                ↘ restricted
             any state → suspended  (reversible)
             any state → revoked    (permanent — terminal)
```

Only `trusted` and `restricted` nodes may execute actions. `revoked` is permanent and irrecoverable in a session.

### Governance outcomes

Every action invocation is evaluated by the policy engine before execution:

| Outcome | Meaning |
|---|---|
| `allow` | Proceed |
| `allow_with_restrictions` | Proceed under limitations (restricted trust) |
| `defer` | Requires operator confirmation before proceeding |
| `deny` | Blocked — no execution |

### The handshake lifecycle

Nine stages, fail-closed at each one:

```
1. pending                Initial state — handshake not yet started
2. discovered             Node endpoint reached
3. manifest_retrieved     Manifest fetched from node
4. manifest_validated     Manifest passes structural and spec validation
5. compatibility_checked  Manifest version is supported
6. governance_evaluated   Policy engine evaluates the manifest
7. trust_assigned         Trust state set (trusted or restricted)
8. capabilities_mounted   Approved capabilities registered
9. ready                  Node available for invocation
```

Any failure produces a `handshake_failed` audit event and leaves the node unregistered.

### UCIInvocation — the canonical request

`UCIInvocation` is the first-class request object. It carries caller identity, target, payload, execution context, and governance hints in a single portable, serialisable structure.

```python
from uci.core.invocation import UCIInvocation

inv = UCIInvocation.create(
    node_id       = "my_service",
    capability_id = "document_search",
    action_id     = "search_index",
    payload       = {"query": "UCI protocol"},
    caller_node_id= "niles",
    session_id    = "sess-001",
    correlation_id= "trace-abc-123",
)

# Canonical invocation path
r = orch.invoke_with(inv)

# Convenience path (same result)
r = orch.invoke("my_service", "document_search", "search_index",
                {"query": "UCI protocol"})
```

### The response envelope

`orchestrator.invoke()` and `invoke_with()` **never raise**. Every outcome is a `UCIResponse`:

```python
r = orch.invoke_with(inv)

if r.success:
    print(r.output)                 # action output
    print(r.provider.node_id)       # who answered
    print(r.governance.trust_state) # what trust level was used
    print(r.audit.invocation_id)    # audit reference

# Or: raise UCIError on failure, return output on success
output = r.assert_success()
```

**Response states** (all 10 spec-defined values):
`completed` · `failed` · `denied` · `cancelled` · `timed_out` ·
`partially_completed` · `deferred` · `queued` · `executing` · `rolled_back`

### Canonical error codes

All error codes are `lowercase_snake_case` as defined in the spec taxonomy:

```python
from uci.core.response import UCIErrorCode

# Governance
UCIErrorCode.PERMISSION_DENIED      # "permission_denied"
UCIErrorCode.TRUST_FAILURE          # "trust_failure"
UCIErrorCode.CONFIRMATION_REQUIRED  # "confirmation_required"
UCIErrorCode.POLICY_DENIED          # "policy_denied"

# Execution
UCIErrorCode.EXECUTION_ERROR        # "execution_error"
UCIErrorCode.TIMEOUT_ERROR          # "timeout_error"
UCIErrorCode.PROVIDER_UNAVAILABLE   # "provider_unavailable"

# Compatibility
UCIErrorCode.VERSION_MISMATCH       # "version_mismatch"
UCIErrorCode.UNSUPPORTED_ACTION     # "unsupported_action"
```

### Chain-hashed audit log

Every audit record is sealed with a SHA-256 hash chaining it to the previous record. Tampering with any field breaks the chain at that point and is detected by `verify_integrity()`.

```python
# Verify integrity
report = audit.verify_integrity()
assert report.valid

# Export a portable, verifiable session
session = audit.export(seal=True)    # UCIAuditSession
wire    = session.to_json()          # send over the wire

# Reimport and verify
session2 = UCIAuditSession.from_json(wire)
assert session2.verify_session_hash()
```

---

## Building a provider

```python
from uci.sdk.provider import UCIProvider
from uci.core.manifest import (
    UCIManifest, UCINode, UCICapability, UCIAction,
    UCIExecution, UCIRisk, UCIPermissions, UCITransport,
    UCIGovernanceMeta, UCIHealth,
)

class MyService(UCIProvider):

    def __init__(self):
        super().__init__()
        self.register_action("my_capability", "my_action", self._handle)

    def build_manifest(self) -> UCIManifest:
        return UCIManifest(
            uci_manifest_version = "0.1",
            node = UCINode(
                node_id      = "my_service",
                instance_id  = "my_service_001",
                display_name = "My Service",        # required
                node_type    = "service",
                version      = "1.0.0",
                vendor       = "KeystoneAI",
            ),
            capabilities = [
                UCICapability(
                    capability_id = "my_capability",
                    version       = "1.0",
                    category      = "retrieval",
                    description   = "Does something useful.",
                    actions = [
                        UCIAction(
                            action_id   = "my_action",
                            description = "Retrieves a result.",
                            execution   = UCIExecution(mode="sync", timeout_ms=5000),
                            risk        = UCIRisk(level="low", categories=["read_only"]),
                            permissions = UCIPermissions(
                                required_permissions  = ["data.read"],
                                operator_confirmation = "none",
                                minimum_trust_state   = "trusted",
                            ),
                        )
                    ],
                )
            ],
            transports = [
                UCITransport(
                    transport_id = "local_ipc",
                    type         = "ipc",
                    endpoint     = "uci://local/my_service",
                )
            ],
            governance = UCIGovernanceMeta(
                default_action_policy = "deny",
                audit_required        = True,
            ),
            health = UCIHealth(),           # required top-level block
        )

    def _handle(self, **kwargs):
        return {"result": "done", "input": kwargs}
```

## Connecting and invoking

```python
from uci.core.audit import AuditLog
from uci.core.registry import UCIRegistry
from uci.core.governance import PolicyEngine
from uci.core.invocation import UCIInvocation
from uci.sdk.provider import UCIOrchestrator

audit    = AuditLog()
registry = UCIRegistry()
policy   = PolicyEngine(audit=audit)
orch     = UCIOrchestrator(policy=policy, registry=registry, audit=audit)

# Connect — runs the full 9-stage handshake
result = orch.connect(MyService())
print(result.trust_state)          # "trusted"
print(result.mounted_capabilities) # ["my_capability"]

# Canonical invocation — using UCIInvocation
inv = UCIInvocation.create(
    node_id       = "my_service",
    capability_id = "my_capability",
    action_id     = "my_action",
    payload       = {"key": "value"},
    caller_node_id= "my_orchestrator",
)
r = orch.invoke_with(inv)
print(r.success)             # True
print(r.output)              # {"result": "done", "input": {"key": "value"}}
print(r.governance.outcome)  # "allow"
print(r.error)               # None
```

---

## Validating manifests

```bash
python uci_validate.py my_manifest.json           # single file
python uci_validate.py example_manifests/          # directory
python uci_validate.py my_manifest.json --strict   # warnings → errors
python uci_validate.py my_manifest.json --json     # machine-readable output
python uci_validate.py example_manifests/ --quiet  # one line per manifest
```

Exit codes: `0` = all valid · `1` = one or more invalid · `2` = usage error

The validator runs eight stages: JSON parse → schema validation → structural checks → semantic validation → deep warnings. Schema violations include precise JSON path locations (`capabilities[0].actions[0].execution.mode`).

---

## JSON Schemas

The three canonical schemas in `uci/schemas/` are the language-agnostic source of truth, hosted at `uci-spec.org`. Any UCI implementation in any language can validate against them directly.

| Schema | Covers |
|---|---|
| `uci_manifest_v0_1.json` | Node identity, capabilities, transports, governance, health block, all v0.1 enum values |
| `uci_response_v0_1.json` | Envelope shape, all 10 response states, error structure with severity and retryable |
| `uci_audit_session_v0_1.json` | Session structure, record fields, chain_hash length, correlation_id |

```python
from uci.core.schema_validator import (
    validate_manifest_schema,
    validate_response_schema,
    validate_audit_session_schema,
)

result = validate_manifest_schema(my_manifest_dict)
if not result.valid:
    for issue in result.issues:
        print(f"{issue.path}: {issue.message}")
```

---

## Compliance suite

`test_rig/scenarios/test_compliance.py` contains 63 formal compliance rules. If you implement UCI in another language, these rules define what "compliant" means:

| Group | Rules | Verifies |
|---|---|---|
| C-MAN | 001–012 | Manifest structure, canonical enums, serialisation |
| C-GOV | 001–010 | Fail-closed, deny-by-default, trust enforcement |
| C-HSK | 001–009 | Handshake stages, ordering, audit completeness |
| C-RSP | 001–012 | Envelope shape, never-raises contract, wire survival |
| C-AUD | 001–010 | Append-only, chain integrity, session export |
| C-SCH | 001–008 | All three objects pass JSON Schema |
| C-INT | 001–002 | Full session compliance end-to-end |

---

## Test coverage

```
331 tests · 0 failures

test_compliance.py               63   Formal protocol compliance
test_patch7_spec_alignment.py    47   Spec document alignment verification
test_response.py                 50   UCIResponse envelope
test_audit_envelope.py           38   Chain hashing, UCIAuditSession
test_schema_validator.py         42   JSON Schema validation
test_validator.py                35   CLI validator
test_trust_and_invocation.py     25   Trust state machine, invocation
test_handshake.py                18   Handshake lifecycle
test_governance.py               13   Governance engine
test_spec_alignment.py            8   Locked v0.1 constants (patch 1)
```

---

## Spec constants (v0.1)

```python
VALID_NODE_TYPES = {
    "application", "service", "agent", "daemon",
    "adapter", "hardware_bridge", "orchestrator",
    "policy_engine", "registry"
}

VALID_EXECUTION_MODES = {
    "sync", "async", "streaming", "scheduled", "event_driven"
}

VALID_TRANSPORT_TYPES = {
    "http", "https", "websocket", "ipc",
    "grpc", "message_bus", "local_socket", "custom"
}

VALID_RISK_LEVELS = {"none", "low", "medium", "high", "critical"}

VALID_CAPABILITY_CATEGORIES = {
    "retrieval", "storage", "generation", "analysis",
    "transformation", "communication", "execution",
    "governance", "monitoring", "vision", "audio",
    "identity", "network", "security", "utility", "other"
}

# Canonical error codes (lowercase_snake_case)
UCIErrorCode.PERMISSION_DENIED       # "permission_denied"
UCIErrorCode.TRUST_FAILURE           # "trust_failure"
UCIErrorCode.CONFIRMATION_REQUIRED   # "confirmation_required"
UCIErrorCode.EXECUTION_ERROR         # "execution_error"
UCIErrorCode.VALIDATION_ERROR        # "validation_error"
UCIErrorCode.VERSION_MISMATCH        # "version_mismatch"
# ... full list in uci/core/response.py
```

---

## Specification

The full protocol specification lives in `docs/` — 23 documents covering every aspect of UCI:

| Document | Covers |
|---|---|
| `uci_core_proposal_v0_1.md` | Architecture overview and philosophy |
| `uci_ontology_v0_1.md` | Canonical definitions — what every term means |
| `uci_manifest_spec_v0_1.md` | Manifest structure and rules |
| `uci_governance_model_v0_1.md` | Authority hierarchy and policy outcomes |
| `uci_handshake_discovery_v0_1.md` | Handshake lifecycle and trust negotiation |
| `uci_invocation_execution_v0_1.md` | Invocation structure and execution semantics |
| `uci_error_response_model_v0_1.md` | Response envelope and canonical error codes |
| `uci_audit_observability_model_v0_1.md` | Audit semantics and observability |
| `uci_compliance_conformance_v0_1.md` | Compliance profiles and conformance expectations |
| `uci_json_schema_v0_1.md` | Reference JSON Schema |
| `uci_taxonomy_naming_v0_1.md` | Naming conventions and semantic rules |
| `uci_transport_model_v0_1.md` | Transport abstraction |
| `uci_versioning_compatibility_v0_1.md` | Evolution and compatibility rules |

---

## Roadmap

The v0.1.0-alpha protocol surface is feature-frozen pending review and interoperability testing.

- **HTTP transport layer** — real over-the-wire UCI between processes
- **Niles/NYALS integration** — first production UCI node in the Keystone ecosystem
- **UCI Registry service** — shared node discovery
- **Interoperability validation** — Python ↔ Go ↔ TypeScript implementations proving UCI is genuinely language-neutral
- **Multi-language reference implementations** — Go, TypeScript
- **v0.1.0 stable release** — after external review and interoperability testing

---

## Contributing

The single most valuable contribution is an **external implementation** — build a UCI node or orchestrator in Go or TypeScript using only the JSON schemas and compliance suite as your guide. If it passes the compliance rules, it's compliant.

See `CONTRIBUTING.md` for details.

---

## Author

**Leon Priest** · [KeystoneAI](https://keystoneai.dev)

UCI is an open protocol. The specification, schemas, and this reference implementation are freely available for adoption. If you build something with UCI, get in touch.

---

*UCI Reference Implementation · Python · v0.1.0-alpha · © Leon Priest / KeystoneAI*
