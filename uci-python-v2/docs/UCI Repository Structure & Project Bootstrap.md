# UCI Repository Structure & Project Bootstrap
### Draft v0.1

```text
uci/
├── README.md
├── LICENSE
├── SPEC.md
├── CHANGELOG.md
├── CONTRIBUTING.md
├── SECURITY.md
│
├── docs/
│   ├── uci_core_proposal_v0_1.md
│   ├── uci_ontology_v0_1.md
│   ├── uci_capability_schema_v0_1.md
│   ├── uci_manifest_spec_v0_1.md
│   ├── uci_json_schema_v0_1.md
│   ├── uci_handshake_discovery_v0_1.md
│   ├── uci_governance_model_v0_1.md
│   ├── uci_policy_decision_model_v0_1.md
│   ├── uci_invocation_execution_v0_1.md
│   ├── uci_error_response_model_v0_1.md
│   ├── uci_transport_model_v0_1.md
│   ├── uci_security_identity_model_v0_1.md
│   ├── uci_registry_model_v0_1.md
│   ├── uci_audit_observability_model_v0_1.md
│   ├── uci_extension_namespace_model_v0_1.md
│   ├── uci_versioning_compatibility_v0_1.md
│   ├── uci_taxonomy_naming_v0_1.md
│   └── uci_compliance_conformance_v0_1.md
│
├── schemas/
│   └── uci_manifest_0_1.schema.json
│
├── examples/
│   ├── minimal_provider_manifest.json
│   ├── standard_provider_manifest.json
│   ├── orchestrator_manifest.json
│   ├── registry_manifest.json
│   ├── policy_engine_manifest.json
│   ├── adapter_manifest.json
│   └── non_ai_service_manifest.json
│
├── test_vectors/
│   ├── valid/
│   │   ├── minimal_provider_manifest.json
│   │   └── standard_provider_manifest.json
│   ├── invalid/
│   │   ├── missing_node_id.json
│   │   ├── empty_capabilities.json
│   │   ├── invalid_identifier.json
│   │   ├── governance_contradiction.json
│   │   └── unknown_required_extension.json
│   └── warnings/
│       ├── critical_risk_without_confirmation.json
│       └── weak_transport_security.json
│
└── sdk/
    └── python/
        ├── pyproject.toml
        ├── README.md
        ├── src/
        │   └── uci_sdk/
        │       ├── __init__.py
        │       ├── manifest.py
        │       ├── schema_validator.py
        │       ├── semantic_validator.py
        │       ├── capability.py
        │       ├── invocation.py
        │       ├── response.py
        │       ├── audit.py
        │       ├── policy.py
        │       ├── handshake.py
        │       ├── extensions.py
        │       └── errors.py
        └── tests/
            ├── test_manifest_loader.py
            ├── test_schema_validator.py
            ├── test_semantic_validator.py
            ├── test_capability_registry.py
            ├── test_invocation.py
            ├── test_response_envelope.py
            ├── test_audit_events.py
            ├── test_handshake.py
            └── test_extensions.py
```
### Repository Principle

The UCI repository should be:

>specification-first, SDK-second.

The repo must remain useful even before any SDK exists.

### Top-Level Files

#### README.md

Purpose:

-	explains what UCI is, 
-	gives quick examples, 
-	links to the spec, 
-	explains status and licensing. 

LICENSE

Recommended:
```text
Apache License 2.0
```

#### SPEC.md

Purpose:

-	acts as the canonical entry point, 
-	links all specification documents in reading order. 

#### CHANGELOG.md

Tracks:

-	version changes, 
-	spec changes, 
-	schema changes, 
-	compatibility changes. 

#### CONTRIBUTING.md

Explains:

-	contribution rules, 
-	naming discipline, 
-	compatibility expectations, 
-	extension proposal process. 

#### SECURITY.md

Explains:

-	how to report vulnerabilities, 
-	security expectations, 
-	responsible disclosure. 

### Recommended Reading Order

```text
1. README.md
2. SPEC.md
3. docs/uci_core_proposal_v0_1.md
4. docs/uci_ontology_v0_1.md
5. docs/uci_capability_schema_v0_1.md
6. docs/uci_manifest_spec_v0_1.md
7. schemas/uci_manifest_0_1.schema.json
8. examples/
9. sdk/python/
```

### Bootstrap Principle

UCI should be understandable at three levels:

```text
Casual reader

    → README.md

Implementer
    → SPEC.md + examples/

Tool builder
    → schemas/ + sdk/
```

### Minimal First Commit

Recommended first commit contents:

```text
README.md
LICENSE
SPEC.md
docs/
schemas/
examples/
```

SDK can come second.

That keeps the public release clean and avoids making the protocol look dependent on Python.

