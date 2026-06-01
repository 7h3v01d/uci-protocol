# UCI Specification — v0.1

> UCI is a governance-aware capability contract layer that allows software nodes to declare, negotiate, and expose executable abilities to orchestrators under explicit policy and operator authority.

This document is the index to the UCI v0.1 specification. The full specification lives in [`docs/`](docs/) and comprises 23 documents covering every aspect of the protocol.

---

## Protocol summary

UCI defines how software nodes — programs, AI agents, services, hardware bridges — discover each other, negotiate trust, invoke capabilities through a governance layer, and produce verifiable audit records.

The protocol is built on four canonical objects:

| Object | Role |
|---|---|
| `UCIManifest` | A node's machine-readable declaration of identity, capabilities, and governance requirements |
| `UCIInvocation` | A canonical request to execute a declared action |
| `UCIResponse` | The canonical answer — state, output, governance snapshot, audit reference |
| `UCIAuditSession` | A tamper-evident, chain-hashed record of all lifecycle events |

---

## Core principles

| Principle | Meaning |
|---|---|
| Declarative capability exposure | Systems explicitly declare what they can do |
| Externalized governance | Policy and authority exist outside application logic |
| Fail-closed security | Undefined behaviour defaults to denial |
| Operator authority | Human approval remains authoritative over automation |
| Transport agnostic | UCI semantics are independent of communication transport |
| Modular interoperability | Any compliant system can integrate dynamically |

---

## Specification documents

### Foundations
| Document | Description |
|---|---|
| [uci_core_proposal_v0_1.md](docs/uci_core_proposal_v0_1.md) | Architecture overview, philosophy, and long-term vision |
| [uci_ontology_v0_1.md](docs/uci_ontology_v0_1.md) | Canonical definitions — what every term means precisely |
| [uci_taxonomy_naming_v0_1.md](docs/uci_taxonomy_naming_v0_1.md) | Naming conventions, semantic stability rules, identifier format |

### Protocol objects
| Document | Description |
|---|---|
| [uci_manifest_spec_v0_1.md](docs/uci_manifest_spec_v0_1.md) | Manifest structure, required fields, validation rules |
| [uci_capability_schema_v0_1.md](docs/uci_capability_schema_v0_1.md) | Capability and action contract specification |
| [uci_invocation_execution_v0_1.md](docs/uci_invocation_execution_v0_1.md) | Invocation structure, execution states, retry and cancellation semantics |
| [uci_error_response_model_v0_1.md](docs/uci_error_response_model_v0_1.md) | Response envelope, canonical error codes, retryability semantics |
| [uci_audit_observability_model_v0_1.md](docs/uci_audit_observability_model_v0_1.md) | Audit event semantics, observability, correlation |

### Governance & trust
| Document | Description |
|---|---|
| [uci_governance_model_v0_1.md](docs/uci_governance_model_v0_1.md) | Authority hierarchy, trust states, policy outcomes |
| [uci_policy_decision_model_v0_1.md](docs/uci_policy_decision_model_v0_1.md) | Policy evaluation lifecycle, context-aware decisions |
| [uci_security_identity_model_v0_1.md](docs/uci_security_identity_model_v0_1.md) | Identity domains, manifest integrity, invocation authenticity |

### Discovery & transport
| Document | Description |
|---|---|
| [uci_handshake_discovery_v0_1.md](docs/uci_handshake_discovery_v0_1.md) | Handshake lifecycle, trust negotiation, capability mounting |
| [uci_registry_model_v0_1.md](docs/uci_registry_model_v0_1.md) | Registry semantics, discovery indexing, advisory-only principle |
| [uci_transport_model_v0_1.md](docs/uci_transport_model_v0_1.md) | Transport abstraction, communication semantics, neutrality rules |

### Schemas & validation
| Document | Description |
|---|---|
| [uci_json_schema_v0_1.md](docs/uci_json_schema_v0_1.md) | Reference JSON Schema for manifest validation |
| [UCI Validator & Test Vector Specification.md](docs/UCI%20Validator%20&%20Test%20Vector%20Specification.md) | Validator behaviour, test vector semantics |
| [UCI Reference Manifest Pack.md](docs/UCI%20Reference%20Manifest%20Pack.md) | Canonical example manifests |

### Ecosystem
| Document | Description |
|---|---|
| [uci_compliance_conformance_v0_1.md](docs/uci_compliance_conformance_v0_1.md) | Compliance profiles, conformance expectations |
| [uci_extension_namespace_model_v0_1.md](docs/uci_extension_namespace_model_v0_1.md) | Extension namespacing, vendor isolation |
| [uci_versioning_compatibility_v0_1.md](docs/uci_versioning_compatibility_v0_1.md) | Versioning philosophy, semantic stability, deprecation |
| [UCI Minimal Reference SDK Architecture.md](docs/UCI%20Minimal%20Reference%20SDK%20Architecture.md) | Reference SDK design principles |
| [UCI Repository Structure & Project Bootstrap.md](docs/UCI%20Repository%20Structure%20%26%20Project%20Bootstrap.md) | Canonical repository layout |

---

## JSON Schemas

The canonical machine-readable schemas live in [`uci/schemas/`](uci/schemas/):

| Schema | URI |
|---|---|
| Manifest | `https://uci-spec.org/schemas/uci_manifest_v0_1.json` |
| Response | `https://uci-spec.org/schemas/uci_response_v0_1.json` |
| Audit Session | `https://uci-spec.org/schemas/uci_audit_session_v0_1.json` |

Any UCI implementation in any language can validate against these schemas directly.

---

## Compliance

A UCI implementation is conformant when it passes the formal compliance suite. The rules are defined in [`test_rig/scenarios/test_compliance.py`](test_rig/scenarios/test_compliance.py).

| Group | Rules | Verifies |
|---|---|---|
| C-MAN | 001–012 | Manifest structure and canonical enums |
| C-GOV | 001–010 | Governance fail-closed behaviour |
| C-HSK | 001–009 | Handshake lifecycle and ordering |
| C-RSP | 001–012 | Response envelope and never-raises contract |
| C-AUD | 001–010 | Audit integrity and session export |
| C-SCH | 001–008 | All objects pass JSON Schema |
| C-INT | 001–002 | Full session compliance end-to-end |

---

## Normative language

Throughout the specification:

| Term | Meaning |
|---|---|
| MUST | Required for UCI compliance |
| MUST NOT | Forbidden |
| SHOULD | Strongly recommended |
| SHOULD NOT | Strongly discouraged |
| MAY | Optional |

---

## Version

This specification is **v0.1 — feature-frozen pending review and interoperability testing.**

Changes to v0.1 semantics require a new version number.
Extensions must use the vendor namespace model (`vendor.extension_name`).

---

*UCI Specification · v0.1 · © Leon Priest / KeystoneAI · MIT License*
