# UCI Error Model & Response Envelope
### Draft v0.1
________________________________________
### 1. Purpose

This document defines the canonical response and error semantics for UCI-compatible systems.

It standardizes:

-	response envelopes, 
-	success responses, 
-	failure responses, 
-	partial completion behavior, 
-	confirmation/defer responses, 
-	canonical error codes, 
-	retryability semantics, 
-	and audit correlation.
  
The goal is to ensure:

-	predictable interoperability, 
-	machine-readable failure handling, 
-	deterministic orchestration behavior, 
-	and governance-aware execution consistency. 
________________________________________
### 2. Design Philosophy

UCI responses MUST be:

-	explicit, 
-	machine-readable, 
-	deterministic, 
-	transport-independent, 
-	auditable, 
-	and safe to interpret conservatively.
  
Failures MUST NOT be silently implied.
Ambiguous outcomes SHOULD default to failure semantics.
________________________________________
### 3. Core Principles

| Principle	                  | Meaning                                                  | 
|:----------------------------|:---------------------------------------------------------|
| Explicit State	            | Responses MUST declare execution state                   | 
| Canonical Errors	          | Standardized error codes SHOULD be used                  | 
| Correlation Visibility    	| Responses SHOULD support traceability                    | 
| Human + Machine Readability	| Errors SHOULD support both                               | 
| Fail-Closed Interpretation	| Unknown states SHOULD be treated conservatively          | 
| Transport Independence	    | Semantics are independent from protocol implementation   | 
________________________________________
### 4. Canonical Response Envelope

Every UCI response MUST use a canonical response envelope.
________________________________________
### 4.1 Canonical Envelope Structure
```json
{
  "uci_response_version": "0.1",
  "invocation_id": "invoke-0001",
  "correlation_id": "corr-abc-001",
  "timestamp": "2026-05-27T12:00:03Z",
  "state": "completed",
  "success": true,
  "provider": {
    "node_id": "librarian_pro"
  },
  "output": {},
  "error": null,
  "audit": {
    "audit_id": "audit-0001"
  }
}
```
________________________________________
### 5. Required Envelope Fields

| Field               	| Required	| Meaning                        |
|:----------------------|:----------|:-------------------------------|
| uci_response_version	| yes	      | Response specification version |
| invocation_id	        | yes     	| Invocation identifier          |
| correlation_id	      | yes	      | Cross-system trace identifier  |
| timestamp	            | yes     	| Response timestamp             |
| state	                | yes     	| Canonical execution state      |
| success	              | yes	      | Boolean success indicator      |
| provider	            | yes     	| Provider identity              |
| output	              | yes     	| Output payload or null         |
| error	                | yes	      | Error object or null           |
| audit	                | yes     	| Audit reference metadata       |
________________________________________
### 6. Canonical Execution States

| State	              | Meaning                        |
|:--------------------|:-------------------------------|
| completed          	| Successful completion          |
| failed	            | Execution failure              |
| denied	            | Governance denied              |
| cancelled	          | Execution cancelled            |
| timed_out	          | Timeout occurred               |
| partially_completed	| Partial success                |
| deferred	          | Awaiting external approval     |
| queued	            | Accepted but not executing yet |
| executing	          | Currently running              |
| rolled_back       	| Execution reverted             |

Unknown states MUST be treated conservatively.
________________________________________
### 7. Success Responses

Successful responses MUST:

-	set success = true, 
-	include terminal or active state, 
-	include valid output payload, 
-	include null error field. 
________________________________________
### 7.1 Successful Completion Example
```json
{
  "uci_response_version": "0.1",
  "invocation_id": "invoke-001",
  "correlation_id": "corr-001",
  "timestamp": "2026-05-27T12:00:03Z",
  "state": "completed",
  "success": true,
  "provider": {
    "node_id": "librarian_pro"
  },
  "output": {
    "results": []
  },
  "error": null,
  "audit": {
    "audit_id": "audit-001"
  }
}
```
________________________________________
### 8. Failure Responses

Failure responses MUST:

-	set success = false, 
-	include terminal failure state, 
-	include error object, 
-	include null or partial output payload. 
________________________________________
### 8.1 Failure Response Example
```json
{
  "uci_response_version": "0.1",
  "invocation_id": "invoke-002",
  "correlation_id": "corr-002",
  "timestamp": "2026-05-27T12:00:05Z",
  "state": "failed",
  "success": false,
  "provider": {
    "node_id": "vault_service"
  },
  "output": null,
  "error": {
    "code": "execution_error",
    "severity": "medium",
    "message": "Document indexing failed.",
    "retryable": false
  },
  "audit": {
    "audit_id": "audit-002"
  }
}
```
________________________________________
### 9. Deferred Responses

Deferred responses indicate operator or policy review is required.

Deferred responses MUST:

-	set success = false, 
-	set state = deferred, 
-	explain defer reason. 
________________________________________
### 9.1 Deferred Response Example
```json
{
  "uci_response_version": "0.1",
  "invocation_id": "invoke-003",
  "correlation_id": "corr-003",
  "timestamp": "2026-05-27T12:00:07Z",
  "state": "deferred",
  "success": false,
  "provider": {
    "node_id": "niles"
  },
  "output": null,
  "error": {
    "code": "confirmation_required",
    "severity": "low",
    "message": "Operator approval required.",
    "retryable": true
  },
  "audit": {
    "audit_id": "audit-003"
  }
}
```
________________________________________
### 10. Partial Completion Responses

Partial completion indicates mixed success.

Partial completion MUST:

-	use state = partially_completed, 
-	explicitly identify incomplete operations where possible. 
________________________________________
### 10.1 Partial Completion Example
```json
{
  "uci_response_version": "0.1",
  "invocation_id": "invoke-004",
  "correlation_id": "corr-004",
  "timestamp": "2026-05-27T12:00:10Z",
  "state": "partially_completed",
  "success": false,
  "provider": {
    "node_id": "batch_processor"
  },
  "output": {
    "successful_items": 8,
    "failed_items": 2
  },
  "error": {
    "code": "partial_failure",
    "severity": "medium",
    "message": "Some items failed processing.",
    "retryable": true
  },
  "audit": {
    "audit_id": "audit-004"
  }
}
```
________________________________________
### 11. Canonical Error Object

Every error response MUST include a canonical error object.
________________________________________
### 11.1 Canonical Error Structure
```json
{
  "code": "validation_error",
  "severity": "low",
  "message": "Input payload invalid.",
  "retryable": false,
  "details": {}
}
```
________________________________________
### 12. Required Error Fields

| Field	    | Required	| Meaning                        | 
|:----------|:----------|:-------------------------------|
| code	    | yes     	| Canonical error identifier     | 
| severity	| yes	      | Error severity                 | 
| message  	| yes	      | Human-readable description     | 
| retryable	| yes	      | Whether retry MAY succeed      | 
| details 	| yes	      | Additional structured metadata | 
________________________________________
### 13. Canonical Error Codes

### Validation Errors
```text
validation_error
schema_error
unsupported_version
invalid_invocation
```
________________________________________
### Governance Errors
```text
permission_denied
policy_denied
trust_failure
confirmation_required
node_revoked
node_suspended
```
________________________________________
### Execution Errors
```text
execution_error
timeout_error
provider_unavailable
transport_error
cancellation_error
rollback_error
partial_failure
```
________________________________________
### Compatibility Errors
```text
unsupported_action
unsupported_capability
unsupported_transport
version_mismatch
incompatible_schema
```
________________________________________
### 14. Error Severity Levels

| Severity	| Meaning                            |
|:----------|:-----------------------------------|
| info	    | Informational                      |
| low	      | Minor issue                        |
| medium	  | Moderate operational issue         |
| high	    | Significant issue                  |
| critical	| Severe or system-threatening issue |

Severity does NOT override governance policy.
________________________________________
### 15. Retryability Semantics

Responses MUST explicitly declare retryability.

Retryable Example
```json
{
  "retryable": true
}
```
________________________________________
### 15.1 Suggested Retryable Errors

Typically retryable:
```text
transport_error
provider_unavailable
timeout_error
partial_failure
```
Typically non-retryable:
```text
permission_denied
trust_failure
unsupported_action
validation_error
```
________________________________________
### 16. Human vs Machine Readability

Responses SHOULD support:

| Audience	        | Purpose                           |
|:------------------|:----------------------------------|
| Machine-readable	| Deterministic orchestration       |
| Human-readable   	| Debugging and operator visibility |

The code field is authoritative for automation.

The message field is advisory for humans.
________________________________________
### 17. Correlation IDs

A correlation_id links related events across systems.

Correlation IDs SHOULD remain stable across:

-	retries, 
-	orchestration chains, 
-	delegated invocations, 
-	audit events. 
________________________________________
### 18. Audit References

Responses SHOULD include audit references.

Example:
```json
{
  "audit": {
    "audit_id": "audit-001"
  }
}
```
Audit systems are implementation-specific.
________________________________________
### 19. Provider Responsibilities

Providers MUST:

-	return canonical response envelopes, 
-	declare explicit states, 
-	return canonical error structures, 
-	preserve correlation identifiers, 
-	avoid ambiguous failure semantics. 

Providers MUST NOT:

-	silently swallow errors, 
-	return malformed envelopes, 
-	hide terminal execution state. 
________________________________________
### 20. Orchestrator Responsibilities

Orchestrators MUST:

-	validate response structure, 
-	interpret canonical states correctly, 
-	respect retryability semantics, 
-	preserve correlation identifiers, 
-	treat unknown terminal states conservatively. 

Orchestrators MUST NOT:

-	assume success without explicit success indicators, 
-	ignore canonical error semantics. 
________________________________________
### 21. Unknown Error Handling

Unknown error codes SHOULD be treated conservatively.

Recommended behavior:
```text
unknown_error
→ treat as failed
→ preserve auditability
→ avoid automatic retries
```
________________________________________
### 22. Transport Independence

The error model defines:

-	semantics, 
-	structure, 
-	and compatibility expectations. 

It does NOT define:

-	HTTP status codes, 
-	WebSocket frames, 
-	gRPC error mapping, 
-	queue semantics, 
-	serialization formats beyond logical structure. 

Transport mappings are implementation-specific.
________________________________________
### 23. Minimal Safe Response Principle

Minimum safe response requires:
```text
canonical state
+
success indicator
+
correlation identifier
+
output or error object
```
Responses lacking these SHOULD be treated as invalid.
________________________________________
### 24. Design Boundary

The UCI Error Model & Response Envelope specification defines:

-	canonical response structure, 
-	execution state semantics, 
-	canonical error semantics, 
-	retryability semantics, 
-	and correlation behavior. 

It does NOT define:

-	transport-layer status mappings, 
-	authentication systems, 
-	orchestration logic, 
-	workflow reasoning, 
-	distributed tracing implementations, 
-	or audit storage systems. 

Those belong to separate implementations or specifications.

