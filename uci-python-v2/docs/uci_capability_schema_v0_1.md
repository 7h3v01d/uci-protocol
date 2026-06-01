# UCI Capability Schema Specification
### Draft v0.1

### 1. Purpose

This document defines the canonical structure for a UCI Manifest.

A UCI Manifest is the machine-readable declaration that allows a node to describe:

-	who it is, 
-	what it can do, 
-	how it may be contacted, 
-	what actions it exposes, 
-	what risks those actions carry, 
-	what governance rules apply, 
-	and how an orchestrator may safely evaluate it. 
________________________________________
### 2. Normative Language

The following terms are authoritative:

| Term	      | Meaning                     | 
|:------------|:----------------------------|
| MUST   	    | Required for UCI compliance | 
| MUST NOT	  | Forbidden                   | 
| SHOULD	    | Strongly recommended        | 
| SHOULD NOT	| Strongly discouraged        | 
| MAY    	    | Optional                    | 
________________________________________
### 3. Design Principles

A UCI Manifest MUST be:

-	explicit, 
-	deterministic, 
-	human-readable, 
-	machine-validatable, 
-	transport-aware but transport-independent, 
-	governance-aware, 
-	versioned, 
-	and safe to reject. 

A malformed manifest MUST be rejected.

An incomplete manifest MUST NOT be partially trusted.
________________________________________
### 4. Canonical Top-Level Manifest Structure
```json
{
  "uci_manifest_version": "0.1",
  "node": {},
  "capabilities": [],
  "governance": {},
  "transports": [],
  "health": {},
  "extensions": {}
}
```
Minimum required fields:
```text
uci_manifest_version
node
capabilities
governance
transports
health
```
________________________________________
### 5. Node Block

The node block identifies the provider.

#### Required Fields
```json
{
  "node_id": "librarian_pro",
  "node_name": "Librarian Pro",
  "node_type": "application",
  "vendor": "Keystone AI",
  "version": "2.4.0",
  "instance_id": "local-librarian-001"
}
```

### Field Definitions
| Field	      | Required	| Meaning
|:------------|:----------|:----------------------------------------|
| node_id	    | yes	      | Stable machine-readable node identifier |
| node_name 	| yes	      | Human-readable name                     |
| node_type  	| yes	      | Type of node                            |
| vendor	    | yes     	| Provider or author                      |
| version    	| yes	      | Application version                     |
| instance_id	| yes     	| Unique runtime instance identifier      | 

### Allowed node_type Values
```text
application
service
agent
daemon
adapter
hardware_bridge
orchestrator
policy_engine
registry
```

A node MAY have multiple roles, but node_type SHOULD describe its primary role.
________________________________________
### 6. Capability Block

The capabilities array declares broad functional abilities.

A manifest MUST declare at least one capability.

### Capability Structure
```json
{
  "capability_id": "document_search",
  "name": "Document Search",
  "category": "retrieval",
  "description": "Search indexed documents and return ranked results.",
  "version": "1.0",
  "actions": []
}
```

### Required Fields

| Field	          | Required	| Meaning                                       |
|:----------------|:----------|:----------------------------------------------|
| capability_id 	| yes	      | Stable machine-readable capability identifier |
| name	          | yes     	| Human-readable capability name                |
| category	      | yes	      | Capability category                           |
| description	    | yes	      | Plain-language description                    |
| version	        | yes	      | Capability version                            |
| actions	        | yes	      | List of executable actions                    |

Allowed Capability Categories v0.1
```text
retrieval
storage
generation
transformation
analysis
communication
execution
governance
monitoring
media
vision
audio
identity
utility
other
```

A capability MUST NOT be directly invoked.

Only actions are invocable.
________________________________________
### 7. Action Block

An action is an executable operation under a capability.

### Action Structure
```json
{
  "action_id": "search_index",
  "name": "Search Index",
  "description": "Search the document index.",
  "execution": {},
  "input_schema": {},
  "output_schema": {},
  "risk": {},
  "permissions": {},
  "errors": []
}
```

### Required Fields

| Field       	| Required	| Meaning                                   | 
|:--------------|:----------|:------------------------------------------|
| action_id   	| yes	      | Stable machine-readable action identifier |
| name        	| yes	      | Human-readable action name                |
| description 	| yes	      | Plain-language action description         |
| execution   	| yes	      | Execution semantics                       |
| input_schema	| yes	      | Input contract                            |
| output_schema	| yes     	| Output contract                           |
| risk	        | yes	      | Risk profile                              |
| permissions  	| yes	      | Permission requirements                   |
| errors      	| yes	      | Declared error behavior                   |

An action MUST have a contract.

An orchestrator MUST NOT invoke undeclared actions.
________________________________________
### 8. Execution Block

The execution block defines how an action behaves at runtime.

Example
```json
{
  "mode": "sync",
  "timeout_ms": 10000,
  "idempotent": true,
  "side_effects": false,
  "rollback_supported": false,
  "requires_confirmation": false
}
```
### Required Fields

| Field	                | Required	| Meaning                                     | 
|:----------------------|:----------|:--------------------------------------------|
| mode	                | yes	      | Execution mode                              |
| timeout_ms	          | yes	      | Maximum expected runtime                    |
| idempotent	          | yes	      | Whether repeated calls have the same effect |
| side_effects	        | yes	      | Whether the action changes state            |
| rollback_supported	  | yes	      | Whether state changes can be reversed       |
| requires_confirmation	| yes	      | Whether operator approval is required       |

Allowed mode Values
```text
sync
async
streaming
scheduled
event_driven
```
For v0.1, orchestrators SHOULD support sync first.
________________________________________
### 9. Input Schema Block

The input_schema defines accepted input.

UCI v0.1 SHOULD use JSON Schema style semantics.

Example
```json
{
  "type": "object",
  "required": ["query"],
  "properties": {
    "query": {
      "type": "string",
      "description": "Search query"
    },
    "top_k": {
      "type": "integer",
      "default": 10,
      "minimum": 1,
      "maximum": 100
    }
  }
}
```
An invocation payload MUST validate against the declared input schema.
________________________________________
### 10. Output Schema Block

The output_schema defines expected output.

Example
```json
{
  "type": "object",
  "required": ["status", "results"],
  "properties": {
    "status": {
      "type": "string"
    },
    "results": {
      "type": "array"
    }
  }
}
```
A provider SHOULD return outputs matching its declared output schema.

An orchestrator MAY reject non-conforming outputs.
________________________________________
### 11. Risk Block

The risk block defines the impact profile of an action.

Example
```json
{
  "level": "low",
  "categories": ["read_only"],
  "description": "Searches indexed documents without modifying state."
}
```

### Required Fields

| Field       | Required | Meaning                         |
| :-----------|:---------|:--------------------------------|
| level	      | yes	     | Canonical risk level            |
| categories	| yes	     | Risk categories                 |
| description	| yes	     | Human-readable risk explanation |

### Allowed Risk Levels
```text
none
low
medium
high
critical
```

### Suggested Risk Categories
```text
read_only
state_modifying
destructive
external_communication
sensitive_data_access
financial
legal
security_sensitive
network_access
filesystem_access
code_execution
operator_visible
irreversible
```
Risk levels MUST be conservative.

A provider MUST NOT understate risk.
________________________________________
### 12. Permissions Block

The permissions block declares required authority.

Example
```json
{
  "required_permissions": ["documents.read"],
  "operator_confirmation": "none",
  "minimum_trust_state": "verified"
}
```

### Required Fields

| Field	                | Required	| Meaning                     |
|:----------------------|:----------|:----------------------------|
| required_permissions	| yes     	| Permission strings required | 
| operator_confirmation	| yes     	| Confirmation requirement    | 
| minimum_trust_state 	| yes     	| Minimum trust state needed  | 

### Allowed Confirmation Values
```text
none
recommended
required
required_with_reason
multi_party_required
```
### Allowed Minimum Trust States
```text
unknown
discovered
verified
trusted
restricted
suspended
revoked
```
A revoked node MUST NOT be invoked.

A suspended node MUST NOT be invoked unless explicitly restored.
________________________________________
### 13. Error Declaration Block

Each action MUST declare possible canonical errors.

Example
```json
[
  {
    "code": "validation_error",
    "description": "Input payload failed schema validation."
  },
  {
    "code": "permission_denied",
    "description": "Caller lacks required permission."
  }
]
```
### Canonical Error Codes v0.1

```text
validation_error
permission_denied
trust_failure
transport_error
execution_error
timeout_error
unsupported_action
version_mismatch
provider_unavailable
confirmation_required
policy_denied
output_schema_error
```
________________________________________
### 14. Governance Block

The governance block declares global governance behavior for the node.

Example
```json
{
  "requires_policy_check": true,
  "audit_required": true,
  "signed_invocations_required": false,
  "operator_authority_required": true,
  "default_action_policy": "deny"
}
```
### Required Fields

| Field	                      | Required	| Meaning                                           | 
|:----------------------------|:----------|:--------------------------------------------------|
| requires_policy_check	      | yes 	    | Whether policy evaluation is mandatory            | 
| audit_required	            | yes	      | Whether audit events are required                 | 
| signed_invocations_required	| yes     	| Whether calls must be signed                      | 
| operator_authority_required	| yes	      | Whether operator authority is recognized          | 
| default_action_policy	      | yes	      | Default behavior for undeclared/ambiguous actions | 

Allowed default_action_policy Values
```text
deny
defer
allow
```
For UCI compliance, deny SHOULD be the default.
________________________________________
### 15. Transport Declaration Block

The transports array declares how the node may be contacted.

Example

```json
[
  {
    "transport_id": "local_http",
    "type": "http",
    "endpoint": "http://127.0.0.1:8080",
    "security": {
      "tls_required": false,
      "auth_required": true
    }
  }
]
```
### Required Fields

| Field	        | Required	| Meaning                |
|:--------------|:----------|:-----------------------|
| transport_id	| yes     	| Stable identifier      |
| type	        | yes	      | Transport type         |
| endpoint	    | yes	      | Contact endpoint       |
| security    	| yes	      | Security requirements  |

### Allowed Transport Types v0.1

```text
http
https
websocket
ipc
grpc
message_bus
local_socket
custom
```
The manifest MUST NOT require a specific transport globally.

Transport choice is implementation-specific.
________________________________________
### 16. Health Block

The health block declares how health can be checked.

Example

```json
{
  "health_action": "system.health.check",
  "status_values": ["online", "degraded", "offline"],
  "heartbeat_supported": true
}
```
### Required Fields

| Field	              | Required	| Meaning                                   | 
|:--------------------|:----------|:------------------------------------------|
| health_action	      | yes	      | Action or endpoint used for health checks | 
| status_values       | yes     	| Declared possible health states           | 
| heartbeat_supported	| yes     	| Whether heartbeat checks are supported    | 
________________________________________
### 17. Extensions Block

The extensions block allows implementation-specific metadata.

Example

```json
{
  "keystone": {
    "policy_profile": "strict_local",
    "audit_sink": "local_append_only"
  }
}
```
Rules:

  -	Extensions MUST be namespaced. 
  -	Extensions MUST NOT override core UCI fields. 
  -	Extensions MUST NOT be required for basic UCI compliance. 
  -	Orchestrators MAY ignore unknown extensions. 
________________________________________
### 18. Validation Rules

A UCI-compliant orchestrator MUST validate:
```text
1. Manifest is parseable.
2. Manifest version is supported.
3. Required top-level fields exist.
4. Node identity is valid.
5. At least one capability exists.
6. Every capability has at least one action.
7. Every action has execution, schema, risk, permission, and error blocks.
8. Risk level is canonical.
9. Trust states are canonical.
10. Transport declarations are valid.
11. Unknown required core fields are rejected.
12. Extensions do not override core behavior.
```
A failed validation MUST prevent mounting.
________________________________________
### 19. Compatibility Rules

### Manifest Version Compatibility

An orchestrator MUST compare uci_manifest_version against supported versions.

Allowed outcomes:
```text
compatible
compatible_with_warnings
unsupported
rejected
```
### Capability Version Compatibility

Capabilities SHOULD be independently versioned.

An orchestrator MAY mount compatible capabilities and reject incompatible ones.

### Action Compatibility

An action is compatible only if:

  -	its schema is understood, 
  -	its risk level is understood, 
  -	its permission requirements are understood, 
  -	and its execution mode is supported. 
________________________________________
### 20. Naming Rules

Machine-readable identifiers SHOULD use:

```text
lowercase_snake_case
```
Examples:
```text
document_search
search_index
text_to_speech
policy_validate
```
Identifiers MUST be stable across versions unless semantics change.

Human-readable names MAY use normal title casing.
________________________________________
### 21. Minimal Valid Manifest Example

```json
{
  "uci_manifest_version": "0.1",
  "node": {
    "node_id": "minimal_search_service",
    "node_name": "Minimal Search Service",
    "node_type": "service",
    "vendor": "Example Vendor",
    "version": "1.0.0",
    "instance_id": "search-local-001"
  },
  "capabilities": [
    {
      "capability_id": "document_search",
      "name": "Document Search",
      "category": "retrieval",
      "description": "Search indexed documents.",
      "version": "1.0",
      "actions": [
        {
          "action_id": "search_index",
          "name": "Search Index",
          "description": "Search the local document index.",
          "execution": {
            "mode": "sync",
            "timeout_ms": 10000,
            "idempotent": true,
            "side_effects": false,
            "rollback_supported": false,
            "requires_confirmation": false
          },
          "input_schema": {
            "type": "object",
            "required": ["query"],
            "properties": {
              "query": {
                "type": "string"
              }
            }
          },
          "output_schema": {
            "type": "object",
            "required": ["status", "results"],
            "properties": {
              "status": {
                "type": "string"
              },
              "results": {
                "type": "array"
              }
            }
          },
          "risk": {
            "level": "low",
            "categories": ["read_only"],
            "description": "Read-only search operation."
          },
          "permissions": {
            "required_permissions": ["documents.read"],
            "operator_confirmation": "none",
            "minimum_trust_state": "verified"
          },
          "errors": [
            {
              "code": "validation_error",
              "description": "Invalid search request."
            },
            {
              "code": "execution_error",
              "description": "Search execution failed."
            }
          ]
        }
      ]
    }
  ],
  "governance": {
    "requires_policy_check": true,
    "audit_required": true,
    "signed_invocations_required": false,
    "operator_authority_required": true,
    "default_action_policy": "deny"
  },
  "transports": [
    {
      "transport_id": "local_http",
      "type": "http",
      "endpoint": "http://127.0.0.1:8080",
      "security": {
        "tls_required": false,
        "auth_required": false
      }
    }
  ],
  "health": {
    "health_action": "health_check",
    "status_values": ["online", "degraded", "offline"],
    "heartbeat_supported": true
  },
  "extensions": {}
}
```
________________________________________
### 22. Compliance Statement

A node is UCI v0.1 manifest-compliant only if:

1. It exposes a valid manifest.
2. The manifest passes schema validation.
3. All declared actions include complete contracts.
4. Governance metadata is present.
5. Transport metadata is present.
6. Health metadata is present.
7. No undeclared executable actions are exposed as UCI actions.
________________________________________
### 23. Design Boundary

UCI v0.1 defines the manifest contract only.

It does not define:

-	how transports are implemented, 
-	how policy engines are internally built, 
-	how orchestrators reason, 
-	how providers execute business logic, 
-	how identities are cryptographically verified, 
-	or how registries synchronize.
  
Those belong to separate specifications or implementations.

