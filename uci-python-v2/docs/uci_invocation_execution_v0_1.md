# UCI Invocation & Execution Semantics
### Draft v0.1
________________________________________
### 1. Purpose

This document defines how UCI-compatible actions behave during execution.

It standardizes:

-	invocation lifecycle, 
-	execution state semantics, 
-	response behavior, 
-	retry handling, 
-	timeout behavior, 
-	cancellation, 
-	rollback semantics, 
-	and execution guarantees. 

The goal is to ensure:

-	deterministic orchestration, 
-	predictable interoperability, 
-	safe execution behavior, 
-	and governance-aware runtime consistency. 
________________________________________
### 2. Execution Philosophy

UCI execution semantics are intentionally:

-	explicit, 
-	conservative, 
-	deterministic, 
-	governance-aware, 
-	transport-independent, 
-	and fail-closed.
  
Execution behavior MUST prioritize:

-	predictability, 
-	auditability, 
-	compatibility, 
-	and operator authority
  
over automation convenience. 
________________________________________
### 3. Invocation Definition

An invocation is a request to execute a declared action.

An invocation MUST reference:

-	target node, 
-	target capability, 
-	target action, 
-	input payload, 
-	execution context, 
-	caller identity, 
-	governance metadata. 
________________________________________
### 4. Canonical Invocation Structure

Example:
```json
{
  "invocation_id": "invoke-0001",
  "timestamp": "2026-05-27T12:00:00Z",
  "caller": {
    "node_id": "niles"
  },
  "target": {
    "node_id": "librarian_pro",
    "capability_id": "document_search",
    "action_id": "search_index"
  },
  "payload": {
    "query": "UCI specification"
  },
  "context": {
    "session_id": "session-001",
    "risk_posture": "normal"
  }
}
```
________________________________________
### 5. Invocation Lifecycle

Canonical lifecycle:
```text
REQUESTED
    ↓
VALIDATING
    ↓
GOVERNANCE_EVALUATING
    ↓
APPROVED
    ↓
QUEUED
    ↓
EXECUTING
    ↓
COMPLETED
```
Possible alternative terminal states:
```text
DENIED
FAILED
CANCELLED
TIMED_OUT
ROLLED_BACK
PARTIALLY_COMPLETED
```
________________________________________
### 6. Execution States

### Canonical States

| State	                | Meaning                         | 
|:----------------------|:--------------------------------|
| requested	            | Invocation created              | 
| validating	          | Schema and structure validation | 
| governance_evaluating	| Policy evaluation active        | 
| approved	            | Governance approved             | 
| denied            	  | Governance denied               | 
| queued            	  | Awaiting execution              | 
| executing         	  | Action currently running        | 
| completed	            | Successfully completed          | 
| failed	              | Execution failed                | 
| cancelled	            | Execution cancelled             | 
| timed_out	            | Execution exceeded timeout      | 
| rolled_back       	  | Changes reverted                | 
| partially_completed  	| Partial success occurred        | 

States SHOULD be auditable.
________________________________________
### 7. Synchronous Execution


In synchronous execution:

-	caller waits for completion, 
-	provider returns terminal outcome directly. 

### Characteristics

| Property	        | Behavior  | 
|:------------------|:----------|
| Response timing 	| Immediate | 
| Caller blocking  	| Yes       | 
| State visibility	| Direct    | 
| Complexity	      | Low       | 

v0.1 orchestrators SHOULD prioritize synchronous execution support first.
________________________________________
### 8. Asynchronous Execution

In asynchronous execution:

-	invocation returns immediately, 
-	execution continues independently.
  
Async actions MUST expose:

-	execution identifiers, 
-	execution state visibility, 
-	completion tracking.
-	
Example Async Response
```json
{
  "status": "accepted",
  "execution_id": "exec-001",
  "state": "queued"
}
```
________________________________________
### 9. Streaming Execution

Streaming execution allows incremental outputs.

Examples:

-	speech synthesis, 
-	token streaming, 
-	live transcription, 
-	telemetry.
  
Streaming actions SHOULD:

-	define stream format, 
-	define completion semantics, 
-	define interruption behavior. 
________________________________________
### 10. Scheduled Execution

Scheduled execution occurs at a future time.

UCI v0.1 does NOT define:

-	scheduling engines, 
-	cron semantics, 
-	calendar standards. 

It only defines execution classification semantics.
________________________________________
### 11. Event-Driven Execution

Event-driven execution is triggered by external events.

Examples:

-	file changes, 
-	network events, 
-	registry updates, 
-	sensor signals. 

UCI defines event-driven semantics only.

It does NOT define event transport systems.
________________________________________
### 12. Timeout Semantics

Actions SHOULD declare expected timeout behavior.

Timeouts MUST be explicit.
________________________________________
### 12.1 Timeout Outcome

If timeout occurs:
```text
state = timed_out
```
Timeout MUST generate audit visibility.
________________________________________
### 12.2 Timeout Rules

Providers SHOULD:

-	terminate safely, 
-	preserve consistency, 
-	avoid undefined partial state. 

Orchestrators SHOULD:

-	treat timeout as non-success, 
-	reevaluate retries carefully. 
________________________________________
### 13. Retry Semantics

Retries MAY occur for:

-	transport failure, 
-	temporary provider unavailability, 
-	transient execution failure. 

Retries SHOULD NOT occur automatically for:

-	destructive actions, 
-	irreversible actions, 
-	unknown execution state, 
-	non-idempotent actions. 
________________________________________
### 14. Idempotency

An idempotent action produces the same outcome when repeated.

Example:

-	repeated read operation.
	
Non-idempotent example:

-	repeated financial transfer. 
________________________________________
### 14.1 Idempotency Declaration

Actions MUST declare:
```json
{
  "idempotent": true
}
```
Orchestrators SHOULD use idempotency information during retry evaluation.
________________________________________
### 15. Execution Guarantees

UCI v0.1 recognizes the following execution guarantees:

| Guarantee	    | Meaning                        |
|:--------------|:-------------------------------|
| best_effort  	| No strict guarantee            |
| at_most_once	| Never intentionally duplicated |
| at_least_once	| Retry permitted                |
| exactly_once	| Strong duplicate prevention    |

Providers SHOULD declare supported guarantees.

Orchestrators MUST NOT assume stronger guarantees than declared.
________________________________________
### 16. Cancellation Semantics

An invocation MAY support cancellation.

Cancellation support MUST be explicitly declared.

Example
```json
{
  "supports_cancellation": true
}
```
________________________________________
### 16.1 Cancellation Outcome

Successful cancellation results in:
```text
state = cancelled
```
Cancellation SHOULD preserve system consistency.
________________________________________
### 17. Rollback Semantics

Rollback reverses execution effects.

Rollback support MUST be explicitly declared.

Example
```json
{
  "rollback_supported": true
}
```
________________________________________
### 17.1 Rollback Requirements

Rollback SHOULD:

-	preserve consistency, 
-	avoid partial corruption, 
-	generate audit visibility. 

Rollback is NOT required in v0.1.
________________________________________
### 18. Partial Failure Handling

Actions MAY partially succeed.

Example:

-	batch operation where some items fail. 

Partial completion MUST be explicit.
________________________________________
### 18.1 Partial Completion State

If partial completion occurs:

state = partially_completed

Providers SHOULD expose:

-	successful items, 
-	failed items, 
-	remaining state consistency. 
________________________________________
### 19. Execution Context

Execution context provides surrounding runtime metadata.

Possible context fields:

-	session identity, 
-	operator identity, 
-	policy profile, 
-	network zone, 
-	execution environment, 
-	risk posture, 
-	correlation ID, 
-	audit ID. 

Context SHOULD remain transport-independent.
________________________________________
### 20. Response Semantics

Responses SHOULD include:

-	invocation identifier, 
-	terminal state, 
-	timestamp, 
-	output payload, 
-	error information, 
-	audit reference. 
________________________________________
### 21. Successful Response Example
```json
{
  "invocation_id": "invoke-0001",
  "state": "completed",
  "timestamp": "2026-05-27T12:00:03Z",
  "output": {
    "results": []
  }
}
```
________________________________________
### 22. Error Propagation

Errors MUST be explicit.

Providers SHOULD return canonical UCI error codes where possible.
________________________________________
### 22.1 Canonical Error Codes

| Error               	| Meaning                  |
|:----------------------|:-------------------------|
| validation_error	    | Invalid input            |
| permission_denied	    | Insufficient permission  |
| trust_failure       	| Trust requirements unmet |
| transport_error	      | Communication failure    |
| execution_error	      | Runtime failure          |
| timeout_error	        | Timeout occurred         |
| unsupported_action	  | Action unsupported       |
| provider_unavailable	| Provider unavailable     |
| cancellation_error	  | Cancellation failed      |
| rollback_error	      | Rollback failed          |
________________________________________
### 23. Audit Requirements

Invocation lifecycle events SHOULD generate audit records.

Suggested audit events:
```text
invocation_requested
validation_started
validation_failed
governance_denied
execution_started
execution_completed
execution_failed
execution_cancelled
execution_timed_out
rollback_started
rollback_completed
partial_completion_detected
```
________________________________________
### 24. Concurrency Considerations

Providers MAY limit concurrency.

Concurrency behavior SHOULD be explicit where possible.

UCI v0.1 does NOT define:

-	locking semantics, 
-	distributed coordination, 
-	transactional scheduling. 
________________________________________
### 25. Provider Responsibilities

Providers MUST:

-	validate inputs, 
-	honor declared contracts, 
-	preserve execution consistency, 
-	report terminal state, 
-	expose declared semantics accurately. 

Providers MUST NOT:

-	silently alter execution semantics, 
-	expose undeclared actions, 
-	bypass governance expectations. 
________________________________________
### 26. Orchestrator Responsibilities

Orchestrators MUST:

-	validate invocation structure, 
-	evaluate governance, 
-	honor declared execution semantics, 
-	respect timeout behavior, 
-	respect idempotency declarations, 
-	avoid unsafe retries. 

Orchestrators MUST NOT:

-	assume undeclared capabilities, 
-	assume undeclared guarantees, 
-	bypass governance restrictions. 
________________________________________
### 27. Failure Handling

Execution failure SHOULD:

-	fail explicitly, 
-	preserve auditability, 
-	avoid undefined state. 

Undefined silent failure behavior is strongly discouraged.
________________________________________
### 28. Recovery Behavior

Recovery MAY include:

-	retry, 
-	rollback, 
-	escalation, 
-	deferment, 
-	operator notification. 

Recovery strategy is implementation-specific.
________________________________________
### 29. Minimal Safe Execution Principle

Minimum safe execution requires:
```
validated invocation
+
governance approval
+
declared execution semantics
+
explicit terminal state
```
Execution MUST NOT bypass these requirements.
________________________________________
### 30. Transport Independence

Execution semantics define:

-	behavior, 
-	lifecycle, 
-	guarantees, 
-	and compatibility expectations. 

They do NOT define:

-	HTTP APIs, 
-	WebSocket protocols, 
-	queue systems, 
-	broker implementations, 
-	runtime frameworks. 
________________________________________
### 31. Design Boundary

The UCI Invocation & Execution Semantics specification defines:

-	invocation lifecycle, 
-	execution states, 
-	retry semantics, 
-	timeout behavior, 
-	cancellation semantics, 
-	rollback semantics, 
-	response behavior, 
-	and execution guarantees. 

It does NOT define:

-	orchestration intelligence, 
-	workflow planning, 
-	distributed transactions, 
-	consensus systems, 
-	transport protocols, 
-	scheduling engines, 
-	or provider business logic. 

Those belong to separate implementations or specifications.

