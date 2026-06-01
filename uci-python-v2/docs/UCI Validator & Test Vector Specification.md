# UCI Validator & Test Vector Specification
### Draft v0.1
________________________________________
### 1. Purpose

This document defines validation and test vector semantics for UCI manifests.

It standardizes:

-	validator behavior, 
-	validation result structure, 
-	pass/fail/warning semantics, 
-	schema validation expectations, 
-	semantic validation expectations, 
-	and canonical test vector behavior. 

The goal is to ensure UCI compatibility can be verified consistently.
________________________________________
### 2. Validator Philosophy

A UCI validator exists to determine whether a manifest is structurally and semantically acceptable.

A validator SHOULD be:

-	deterministic, 
-	explainable, 
-	conservative, 
-	repeatable, 
-	machine-readable, 
-	and human-readable. 

A validator MUST NOT silently accept malformed core semantics.
________________________________________
### 3. Validation Outcome Types

| Outcome           	| Meaning                                        | 
|:--------------------|:-----------------------------------------------|
| pass	              | Manifest is valid                              | 
| pass_with_warnings	| Manifest is usable but has non-fatal issues    | 
| fail	              | Manifest is invalid                            | 
| unsupported        	| Manifest cannot be evaluated by this validator | 
________________________________________
### 4. Validation Layers

A validator MAY evaluate multiple layers:

1. Parse validation
2. JSON Schema validation
3. Canonical enum validation
4. Identifier validation
5. Semantic validation
6. Compatibility validation
7. Extension validation
8. Policy-readiness validation
________________________________________
### 5. Minimal Validator Requirements

A minimal UCI validator SHOULD check:

```text
parseable JSON
required top-level fields
uci_manifest_version
node block
capabilities array
action contracts
transport declarations
governance block
canonical enum values
identifier patterns
```
________________________________________
### 6. Validation Result Envelope
```
{
  "validator_version": "0.1",
  "manifest_version": "0.1",
  "outcome": "pass",
  "errors": [],
  "warnings": [],
  "summary": {
    "capabilities_checked": 1,
    "actions_checked": 1,
    "transports_checked": 1
  }
}
```
________________________________________
### 7. Validation Error Object

```json
{
  "code": "missing_required_field",
  "severity": "high",
  "path": "$.node.node_id",
  "message": "Required field node_id is missing."
}
```
Required fields:
```text
code
severity
path
message
```
________________________________________
### 8. Validation Warning Object
```
{
  "code": "non_recommended_policy",
  "severity": "medium",
  "path": "$.governance.default_action_policy",
  "message": "default_action_policy is allow; deny is recommended."
}
```
Warnings do not necessarily invalidate a manifest.
________________________________________
### 9. Canonical Validation Error Codes
```
parse_error
schema_error
missing_required_field
invalid_type
invalid_enum
invalid_identifier
invalid_version
invalid_capability
invalid_action
invalid_transport
invalid_governance
invalid_extension
semantic_conflict
unsupported_manifest_version
```
________________________________________
### 10. Canonical Validation Warning Codes
```
non_recommended_policy
missing_optional_metadata
deprecated_field
deprecated_capability
unknown_optional_extension
weak_transport_security
limited_audit_visibility
partial_compatibility
```
________________________________________
### 11. Deterministic Validation Principle

Given the same:
```text
manifest
validator version
schema version
configuration
```
a validator SHOULD produce the same result.
________________________________________
### 12. Schema Validation

Schema validation determines whether the manifest matches the reference JSON Schema.

Schema validation failure SHOULD produce:

```text
outcome = fail
```
________________________________________
### 13. Semantic Validation

Semantic validation checks whether declared meaning is internally consistent.

Examples:

| Case                                                              	| Recommended Outcome | 
|:--------------------------------------------------------------------|:--------------------|
| requires_confirmation = false but operator_confirmation = required	| warning or fail     |
| risk.level = critical but operator_confirmation = none	            | warning or fail     |
| side_effects = false but risk category includes destructive       	| fail                |
| rollback_supported = true but irreversible risk category declared	  | warning or fail     |
| audit_required = true but audit disabled	                          | fail                |
________________________________________
### 14. Compatibility Validation

Compatibility validation checks whether:

-	manifest version is supported, 
-	capability versions are understood, 
-	action execution modes are supported, 
-	required extensions are supported. 

Unsupported required semantics SHOULD fail.

Unsupported optional semantics MAY warn.
________________________________________
### 15. Extension Validation

Extensions SHOULD be checked for:
```
namespace validity
reserved prefix misuse
required/optional status
known support
semantic override attempts
```
Unknown optional extensions MAY produce warnings.

Unknown required extensions SHOULD fail.
________________________________________
### 16. Policy-Readiness Validation

Policy-readiness validation checks whether governance metadata is sufficient for policy evaluation.

Examples:
```text
required permissions exist
minimum trust state declared
operator confirmation declared
risk level declared
```
Missing policy-critical metadata SHOULD fail.

________________________________________
### 17. Valid Test Vector: Minimal Provider

Expected outcome:

```text
pass
```

Required checks:

-	manifest parseable 
-	required top-level fields present 
-	one capability declared 
-	one action declared 
-	transport declared 
-	governance declared 
________________________________________
### 18. Valid Test Vector: Standard Provider

Expected outcome:

```text
pass
```

Required checks:

-	standard compliance profile 
-	audit enabled 
-	canonical errors declared 
-	transport security declared 
-	compatibility metadata declared 
________________________________________
### 19. Invalid Test Vector: Missing Node ID

Mutation:

```json
{
  "node": {
    "instance_id": "example_001"
  }
}
```
Expected outcome:

```json
fail
```

Expected error:

```json
missing_required_field
```
________________________________________
### 20. Invalid Test Vector: Empty Capabilities
Mutation:

```json
{
  "capabilities": []
}
```

Expected outcome:

```text
fail
```

Expected error:

```text
schema_error
```
________________________________________
### 21. Invalid Test Vector: Invalid Identifier

Mutation:

```json
{
  "node": {
    "node_id": "Bad-ID"
  }
}
```

Expected outcome:

```text
fail
```

Expected error:

```text
invalid_identifier
```
________________________________________
### 22. Invalid Test Vector: Critical Risk Without Confirmation

Mutation:

```json
{
  "risk": {
    "level": "critical"
  },
  "permissions": {
    "operator_confirmation": "none"
  }
}
```

Expected outcome:
```text
pass_with_warnings
```

or implementation-specific fail.

Recommended warning:
```text
non_recommended_policy
```

________________________________________
### 23. Invalid Test Vector: Governance Contradiction

Mutation:
```json
{
  "governance": {
    "audit_required": true
  },
  "audit": {
    "audit_enabled": false
  }
}
```
Expected outcome:
```text
fail
```
Expected error:
```text
semantic_conflict
```
________________________________________
### 24. Invalid Test Vector: Unknown Required Extension

Expected outcome:

```text
fail
```
Expected error:

```text
invalid_extension
```
________________________________________
### 25. Warning Test Vector: Weak Transport Security

Mutation:

```json
{
  "transports": [
    {
      "type": "http",
      "security": {
        "auth_required": false,
        "tls_required": false
      }
    }
  ]
}
```
Expected outcome:

```text
pass_with_warnings
```
Expected warning:

```text
weak_transport_security
```
________________________________________
### 26. Validator Output Requirements

Validator output SHOULD include:

```text
outcome
errors
warnings
summary
validator_version
manifest_version
```
Validator output SHOULD be machine-readable.
________________________________________
### 27. Validator Strictness Modes

Implementations MAY support strictness modes:

| Mode	      | Meaning                                    |
|:------------|:-------------------------------------------|
| permissive  | Schema-focused, fewer warnings as failures |
| standard	  | Balanced validation                        |
| strict	    | Converts high-risk warnings into failures  |
| compliance	| Full conformance validation                |
________________________________________
### 28. Validator Non-Goals

A UCI validator does NOT prove:

-	provider honesty, 
-	runtime safety, 
-	cryptographic identity, 
-	operator approval, 
-	policy correctness, 
-	execution correctness, 
-	security integrity. 

Validation is one gate, not the whole trust model.
________________________________________
### 29. Minimal Safe Validation Principle

Minimum safe validation requires:

```text
parse
+
schema check
+
canonical enums
+
identifier validation
+
required governance metadata
```
________________________________________
### 30. Design Boundary

The UCI Validator & Test Vector Specification defines:

-	validation semantics, 
-	validator output expectations, 
-	deterministic validation principles, 
-	and canonical test vector behavior. 

It does NOT define:

-	validator implementation language, 
-	CI/CD systems, 
-	certification authorities, 
-	runtime governance, 
-	or execution safety guarantees.

