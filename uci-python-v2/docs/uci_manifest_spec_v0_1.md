# UCI Reference Manifest Specification
### Draft v0.1
________________________________________
### 1. Purpose

This document defines the canonical manifest structure for the Universal Capability Interface (UCI).

It standardizes:

-	manifest structure, 
-	node declaration semantics, 
-	capability declaration semantics, 
-	transport declarations, 
-	governance metadata, 
-	extension metadata, 
-	and interoperability-safe manifest behavior. 

The goal is to ensure:

-	predictable interoperability, 
-	inspectable declarations, 
-	deterministic compatibility evaluation, 
-	and implementation-independent capability discovery. 
________________________________________
### 2. Manifest Philosophy

A UCI manifest is a declarative interoperability document.
A manifest:
-	describes, 
-	identifies, 
-	advertises, 
-	and declares. 

A manifest does NOT:

-	execute logic, 
-	orchestrate workflows, 
-	make governance decisions, 
-	or alter protocol semantics. 

Manifests SHOULD remain:

-	human-readable, 
-	machine-readable, 
-	deterministic, 
-	and semantically explicit. 
________________________________________
### 3. Core Principles

| Principle               	| Meaning                                        | 
|:--------------------------|:-----------------------------------------------|
| Declarative Structure   	| Manifests describe, not execute                | 
| Human Readability       	| Manifests SHOULD remain inspectable            | 
| Semantic Explicitness   	| Capabilities SHOULD remain clearly declared    | 
| Compatibility Visibility	| Supported behavior SHOULD remain visible       | 
| Governance Visibility	    | Governance requirements SHOULD remain explicit | 
| Transport Neutrality	    | Transport declarations SHOULD remain abstract  | 
| Extension Isolation	      | Extensions SHOULD remain namespaced            | 
________________________________________
### 4. Canonical Manifest Structure

Example high-level structure:

```json
{
  "uci_manifest_version": "0.1",
  "node": {},
  "capabilities": [],
  "transports": [],
  "governance": {},
  "compatibility": {},
  "compliance": {},
  "audit": {},
  "extensions": {}
}
```
________________________________________
### 5. Required Top-Level Fields

| Field	                | Required	| Meaning                        | 
|:----------------------|:----------|:-------------------------------|
| uci_manifest_version	| yes	      | Manifest specification version | 
| node	                | yes	      | Node identity metadata         | 
| capabilities        	| yes     	| Capability declarations        | 
| transports	          | yes	      | Transport declarations         | 
| governance	          | yes      	| Governance metadata            | 
| compatibility	        | yes     	| Compatibility metadata         | 
| compliance	          | yes     	| Compliance metadata            | 
| audit               	| yes     	| Audit metadata                 | 
| extensions          	| yes	      | Extension metadata             | 
________________________________________
### 6. Node Section

The node section identifies the logical provider.
________________________________________
### 6.1 Canonical Node Structure

```json
{
  "node": {
    "node_id": "librarian_pro",
    "instance_id": "librarian-local-001",
    "display_name": "Librarian Pro",
    "description": "Offline sovereign retrieval engine"
  }
}
```
________________________________________
### 6.2 Node Rules

Node metadata SHOULD:

-	remain stable, 
-	avoid collisions, 
-	remain semantically clear, 
-	avoid implementation leakage. 
________________________________________
### 7. Capability Declaration Section

Capabilities define broad functional abilities exposed by the node.
________________________________________
### 7.1 Capability Structure

```json
{
  "capability_id": "document_search",
  "version": "1.0",
  "category": "retrieval",
  "description": "Search indexed documents",
  "actions": []
}
```
________________________________________
### 7.2 Capability Rules

Capabilities SHOULD:

-	use canonical naming conventions, 
-	remain vendor-neutral, 
-	preserve semantic stability, 
-	declare supported actions explicitly. 
________________________________________
### 8. Action Declaration Section

Actions define executable operations within a capability.
________________________________________
### 8.1 Canonical Action Structure

```json
{
  "action_id": "search_index",
  "description": "Search indexed content",
  "input_schema": {},
  "output_schema": {},
  "risk_level": "low",
  "idempotent": true,
  "supports_cancellation": false,
  "rollback_supported": false
}
```
________________________________________
### 8.2 Action Rules

Actions SHOULD:

-	remain semantically explicit, 
-	preserve stable meaning, 
-	expose execution semantics clearly, 
-	avoid ambiguous behavior. 
________________________________________
### 9. Governance Metadata Section

Governance metadata declares governance expectations.
________________________________________
### 9.1 Governance Structure

```json
{
  "governance": {
    "default_policy_profile": "strict_local",
    "operator_confirmation_required": false
  }
}
```
________________________________________
### 9.2 Governance Rules

Governance metadata MAY declare:

-	confirmation requirements, 
-	trust expectations, 
-	policy profiles, 
-	execution restrictions. 

Governance metadata does NOT override local governance authority.
________________________________________
### 10. Transport Declaration Section

Transport declarations expose supported communication mechanisms.
________________________________________
### 10.1 Canonical Transport Structure

```json
{
  "transport_id": "local_http",
  "type": "http",
  "endpoint": "http://127.0.0.1:8080",
  "security": {
    "auth_required": true,
    "tls_required": false
  }
}
```
________________________________________
### 10.2 Transport Rules

Transport declarations SHOULD:

-	remain transport-neutral semantically, 
-	avoid implementation assumptions, 
-	expose security visibility clearly. 

Transport declarations do NOT imply trust.
________________________________________
### 11. Compatibility Metadata Section

Compatibility metadata declares supported interoperability expectations.
________________________________________
### 11.1 Compatibility Structure

```json
{
  "compatibility": {
    "supported_manifest_versions": [
      "0.1"
    ],
    "supported_extensions": []
  }
}
```
________________________________________
### 11.2 Compatibility Rules

Compatibility metadata SHOULD expose:

-	supported versions, 
-	extension support, 
-	compatibility limitations, 
-	interoperability expectations. 
________________________________________
### 12. Compliance Metadata Section

Compliance metadata declares implementation conformance level.
________________________________________
### 12.1 Compliance Structure

```text
{
  "compliance": {
    "profile": "standard",
    "supported_features": [
      "governance",
      "audit",
      "registry"
    ]
  }
}
```
________________________________________
### 12.2 Compliance Rules
Compliance metadata SHOULD:
-	remain explicit, 
-	avoid unsupported claims, 
-	preserve interoperability visibility. 
________________________________________
### 13. Audit Metadata Section

Audit metadata exposes observability expectations.
________________________________________
### 13.1 Audit Structure

```json
{
  "audit": {
    "audit_enabled": true,
    "supported_event_categories": [
      "governance",
      "execution",
      "transport"
    ]
  }
}
```
________________________________________
### 13.2 Audit Rules

Audit metadata SHOULD:

-	preserve visibility expectations, 
-	expose supported audit behavior, 
-	remain semantically explicit. 
________________________________________
### 14. Extension Declaration Section

Extensions declare vendor-specific or experimental behavior.
________________________________________
### 14.1 Extension Structure

```json
{
  "extensions": {
    "keystone.audit_profile": {
      "enabled": true
    }
  }
}
```
________________________________________
### 14.2 Extension Rules

Extensions MUST:

-	remain namespaced, 
-	avoid overriding core semantics, 
-	preserve interoperability safety. 

Unknown required extensions SHOULD be handled conservatively.
________________________________________
### 15. Manifest Validation Rules

Valid manifests MUST:

-	contain required top-level fields, 
-	preserve canonical structure, 
-	use canonical identifier rules, 
-	preserve semantic clarity, 
-	avoid malformed metadata. 

Validation SHOULD remain deterministic.
________________________________________
### 16. Required vs Optional Fields

Required fields define:

-	minimum interoperability semantics. 

Optional fields define:

-	additional interoperability metadata. 

Unknown required fields SHOULD fail conservatively.

Unknown optional fields MAY be ignored safely.
________________________________________
### 17. Canonical Field Semantics

Field meaning MUST remain stable over time.

Example:

```json
risk_level
```

MUST continue representing:

-	execution risk semantics. 

It MUST NOT silently mutate meaning.
________________________________________
### 18. Reserved Fields

Reserved fields MAY exist for future expansion.

Reserved fields:

-	SHOULD remain documented, 
-	MUST NOT silently change semantics, 
-	SHOULD preserve forward compatibility. 
________________________________________
### 19. Manifest Integrity Metadata

Manifest integrity metadata MAY include:

-	signatures, 
-	checksums, 
-	integrity hashes, 
-	attestation metadata. 

Example:

```json
{
  "integrity": {
    "signed": true
  }
}
```

UCI v0.1 defines semantics only.
________________________________________
### 20. Manifest Lifecycle

Manifest lifecycle MAY include:

```text
draft
active
deprecated
restricted
revoked
retired
```
Lifecycle semantics SHOULD remain visible where practical.
________________________________________
### 21. Example Minimal Manifest

```json
{
  "uci_manifest_version": "0.1",
  "node": {
    "node_id": "simple_search"
  },
  "capabilities": [],
  "transports": [],
  "governance": {},
  "compatibility": {},
  "compliance": {},
  "audit": {},
  "extensions": {}
}
```
________________________________________
### 22. Example Standard Manifest

```json
{
  "uci_manifest_version": "0.1",
  "node": {
    "node_id": "librarian_pro",
    "instance_id": "librarian-local-001",
    "display_name": "Librarian Pro"
  },
  "capabilities": [
    {
      "capability_id": "document_search",
      "version": "1.0",
      "category": "retrieval",
      "actions": [
        {
          "action_id": "search_index",
          "risk_level": "low",
          "idempotent": true
        }
      ]
    }
  ],
  "transports": [
    {
      "transport_id": "local_http",
      "type": "http",
      "endpoint": "http://127.0.0.1:8080"
    }
  ],
  "governance": {
    "default_policy_profile": "strict_local"
  },
  "compatibility": {
    "supported_manifest_versions": [
      "0.1"
    ]
  },
  "compliance": {
    "profile": "standard"
  },
  "audit": {
    "audit_enabled": true
  },
  "extensions": {}
}
```
________________________________________
### 23. Anti-Patterns

The following are strongly discouraged:
________________________________________
### 23.1 Manifest Logic Injection

Bad:

```text
Executable orchestration logic inside manifests
```
________________________________________
### 23.2 Vendor-Coupled Core Semantics

Bad:

```text
gpt_execution_mode
```

inside canonical core structures.
________________________________________
### 23.3 Hidden Capabilities

Bad:

```text
Undeclared executable actions
```
________________________________________
### 23.4 Semantic Ambiguity

Bad:

```text
magic_mode
do_action
super_capability
```
________________________________________
### 24. Minimal Safe Manifest Principle

Minimum safe manifest behavior requires:

```text
explicit identity
+
explicit capability declarations
+
explicit transport declarations
+
explicit governance metadata
+
canonical structure
```
________________________________________
### 25. Transport Independence

Manifest semantics are independent from:

-	transport implementation, 
-	serialization format, 
-	runtime framework, 
-	communication topology. 

Manifest meaning MUST survive transport replacement.
________________________________________
### 26. Non-Goals

UCI v0.1 does NOT define:

-	orchestration logic, 
-	workflow systems, 
-	execution engines, 
-	deployment systems, 
-	package management, 
-	registry synchronization protocols, 
-	vendor marketplaces. 

These belong to implementations or future specifications.
________________________________________
### 27. Design Boundary

The UCI Reference Manifest Specification defines:

-	canonical manifest structure, 
-	declaration semantics, 
-	interoperability-safe metadata, 
-	and manifest validation expectations. 

It does NOT define:

-	orchestration intelligence, 
-	transport protocols, 
-	provider business logic, 
-	runtime execution systems, 
-	or governance authority structures. 

Those belong to separate implementations or specifications.

