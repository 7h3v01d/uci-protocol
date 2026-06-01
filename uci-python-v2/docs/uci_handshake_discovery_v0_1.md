# UCI Handshake & Discovery Protocol
### Draft v0.1
________________________________________
### 1. Purpose

This document defines the canonical process by which UCI-compatible nodes:

-	discover each other, 
-	exchange manifests, 
-	validate compatibility, 
-	establish trust state, 
-	negotiate governance requirements, 
-	and mount usable capabilities. 

The handshake protocol exists to ensure:

-	deterministic interoperability, 
-	explicit capability awareness, 
-	and governance-aware execution safety. 
________________________________________
### 2. Design Philosophy

The UCI handshake is intentionally:

-	conservative, 
-	explicit, 
-	fail-closed, 
-	deterministic, 
-	and transport-independent.

The handshake MUST prioritize:

-	compatibility validation, 
-	governance enforcement, 
-	and operator authority

before execution is permitted. 
________________________________________
### 3. Core Principles

### 3.1 No Assumed Trust

Discovery does NOT imply trust.

A discovered node MUST begin in an untrusted state.
________________________________________
### 3.2 No Assumed Capability

Capabilities MUST be declared through a manifest.

An orchestrator MUST NOT infer undeclared abilities.
________________________________________
### 3.3 Validation Before Mounting

Capabilities MUST NOT be mounted until:

-	manifest validation succeeds, 
-	compatibility is confirmed, 
-	governance checks pass, 
-	and trust state requirements are satisfied. 
________________________________________
### 3.4 Fail-Closed Behavior

Validation failure MUST result in:

-	rejection, 
-	deferment, 
-	or restricted state. 

Never implicit acceptance.
________________________________________
### 4. Canonical Handshake Lifecycle
```text
DISCOVERED
    ↓
MANIFEST_RETRIEVED
    ↓
MANIFEST_VALIDATED
    ↓
COMPATIBILITY_EVALUATED
    ↓
GOVERNANCE_EVALUATED
    ↓
TRUST_ASSIGNED
    ↓
CAPABILITIES_MOUNTED
    ↓
READY
```
Failure at any stage MUST halt progression.
________________________________________
### 5. Node Discovery

Discovery is the process of becoming aware of a node.

UCI does not mandate a specific discovery mechanism.

Possible discovery methods include:

-	static configuration, 
-	local registry, 
-	multicast, 
-	DNS/service discovery, 
-	manual registration, 
-	registry query, 
-	QR/bootstrap tokens, 
-	IPC enumeration, 
-	hardware enumeration, 
-	direct endpoint entry. 
________________________________________
### 6. Discovery State

Immediately after discovery:

trust_state = discovered

The node:

-	MUST NOT be trusted, 
-	MUST NOT be auto-mounted, 
-	MUST NOT be auto-executed. 

Discovery only establishes visibility.
________________________________________
### 7. Manifest Retrieval

After discovery, the orchestrator retrieves the node manifest.

Requirements

The manifest:

-	MUST be retrievable through at least one declared transport, 
-	MUST be machine-readable, 
-	MUST identify the manifest version, 
-	MUST contain required core sections. 
________________________________________
### 8. Manifest Validation

The orchestrator validates the manifest against the supported UCI schema.

### Validation MUST include:
```text
- syntax validation
- schema validation
- required fields
- capability structure
- action structure
- governance structure
- transport structure
- canonical enums
- identifier validity
```
Validation failure MUST terminate the handshake.
________________________________________
### 9. Compatibility Evaluation

After validation, compatibility is evaluated.
________________________________________
### 9.1 Manifest Version Compatibility

The orchestrator compares:
```text
provider_manifest_version
vs
supported_manifest_versions
```
Possible outcomes:

| Result                    | Meaning               | 
|:--------------------------|:----------------------|
| compatible  	            | Fully supported       | 
| compatible_with_warnings	| Partial support       | 
| unsupported	            | Cannot operate safely | 
| rejected	                | Explicitly denied     | 

Unsupported manifests MUST NOT be mounted.
________________________________________
### 9.2 Capability Compatibility

Each capability is evaluated independently.

Possible outcomes:

| Result                | Meaning                   | 
|:----------------------|:--------------------------|
| mountable	            | Fully supported           |
| partially_supported	| Some actions unsupported  |
| unsupported 	        | Capability rejected       |

Capabilities MAY be partially mounted.
________________________________________
### 9.3 Action Compatibility

Actions are compatible only if:

-	execution mode is supported, 
-	schemas are understood, 
-	permissions semantics are understood, 
-	risk semantics are understood, 
-	governance semantics are understood.
  
Unsupported actions MUST NOT be invokable.
________________________________________
### 10. Governance Evaluation

Governance evaluation determines whether the node may operate under local policy.

The orchestrator or policy engine evaluates:

-	trust requirements, 
-	required permissions, 
-	risk levels, 
-	operator authority requirements, 
-	audit requirements, 
-	network policy, 
-	execution restrictions, 
-	local governance policy. 
________________________________________
### 11. Policy Decision Outcomes

Possible governance outcomes:

| Outcome                   | Meaning                     | 
|:--------------------------|:----------------------------|
| allow	                    | Operation permitted         | 
| allow_with_restrictions	| Limited operation permitted | 
| defer	                    | Awaiting operator decision  | 
| deny	                    | Operation forbidden         | 
A deny outcome MUST prevent mounting.
________________________________________
### 12. Trust Assignment

After successful governance evaluation, a trust state is assigned.

Canonical Trust States

| State  	    | Meaning                         | 
|:--------------|:--------------------------------|
| unknown	    | No validation performed         |
| discovered	| Node detected                   |
| verified	    | Identity and manifest validated |
| trusted	    | Approved for standard operation |
| restricted	| Limited permissions             |
| suspended  	| Temporarily disabled            |
| revoked	    | Explicitly denied               |
________________________________________
### 13. Trust Escalation Rules

Trust escalation SHOULD require:
```text
1. successful manifest validation
2. governance evaluation
3. compatibility confirmation
4. optional operator approval
```
Trust MUST NOT automatically escalate from:

-	discovered

to 

-	trusted 

without policy approval.
________________________________________
### 14. Capability Mounting

Mounted capabilities become available for orchestration.

Mounting:

-	does NOT imply execution permission, 
-	does NOT bypass governance, 
-	does NOT bypass confirmation requirements. 

Mounted capabilities remain subject to policy evaluation at invocation time.
________________________________________
### 15. Mount States

A capability MAY exist in one of the following states:

| State	        | Meaning              | 
|:--------------|:---------------------|
| unmounted	    | Not available        | 
| mounted	    | Available            | 
| restricted	| Limited access       | 
| suspended	    | Temporarily disabled | 
| revoked	    | Permanently denied   | 
________________________________________
### 16. Handshake Completion

A handshake is complete only when:
```text
- manifest validated
- compatibility accepted
- governance approved
- trust assigned
- capabilities mounted
```
At that point:
```text
node_state = ready
```
________________________________________
### 17. Canonical Handshake Sequence
```text
1. Discover node
2. Retrieve manifest
3. Validate manifest
4. Evaluate manifest compatibility
5. Evaluate capability compatibility
6. Evaluate governance requirements
7. Assign trust state
8. Mount approved capabilities
9. Enter READY state
```
________________________________________
### 18. Revalidation

Nodes SHOULD support revalidation.

Revalidation MAY occur:

-	periodically, 
-	on manifest change, 
-	on transport change, 
-	on trust change, 
-	on policy update, 
-	on operator request, 
-	after failure events. 
________________________________________
### 19. Manifest Change Handling

If a manifest changes:

The orchestrator SHOULD:
```text
1. detect change
2. revalidate manifest
3. reevaluate compatibility
4. reevaluate governance
5. remount/restrict/revoke capabilities as needed
```
Capabilities MUST NOT silently change semantics.
________________________________________
### 20. Revocation

A node MAY be revoked if:

-	policy violation occurs, 
-	manifest integrity fails, 
-	incompatible changes appear, 
-	malicious behavior detected, 
-	operator revokes trust, 
-	security violations occur. 

Revoked nodes MUST NOT be invokable.
________________________________________
### 21. Suspension

Suspension is temporary denial.

Suspended nodes:

-	remain known, 
-	remain indexed, 
-	but MUST NOT execute actions. 

Suspension MAY be reversible.
________________________________________
### 22. Discovery Registries

A registry MAY maintain:

-	node identities, 
-	manifest versions, 
-	trust states, 
-	transport endpoints, 
-	capability metadata, 
-	audit history. 

Registries are advisory only.

Registries MUST NOT override governance policy.
________________________________________
### 23. Operator Authority

Operator authority supersedes:

-	automatic trust assignment, 
-	automatic mounting, 
-	automatic invocation. 

An operator MAY:

-	approve, 
-	deny, 
-	suspend, 
-	restrict, 
-	or revoke

any node regardless of automated evaluation. 
________________________________________
### 24. Audit Requirements

Handshake events SHOULD generate audit records.

Suggested audit events:

```text
node_discovered
manifest_retrieved
manifest_validation_failed
compatibility_accepted
compatibility_rejected
trust_assigned
capability_mounted
capability_revoked
node_suspended
node_ready
```
________________________________________
### 25. Failure Handling

Handshake failure MUST:

-	fail closed, 
-	prevent execution, 
-	preserve auditability. 

Partial failure MUST NOT silently degrade governance.
________________________________________
### 26. Retry Behavior

Retries MAY occur for:

-	transport failures, 
-	temporary unavailability, 
-	timeout events. 

Retries SHOULD NOT bypass:

-	validation, 
-	governance, 
-	or trust requirements. 
________________________________________
### 27. Transport Independence

The handshake protocol defines:

-	semantics, 
-	lifecycle, 
-	and state transitions. 

It does NOT mandate:

-	HTTP, 
-	WebSocket, 
-	IPC, 
-	or any specific transport implementation. 
________________________________________
### 28. Security Considerations

The handshake protocol SHOULD support future:

-	signed manifests, 
-	cryptographic identity, 
-	attestation, 
-	certificate validation, 
-  	secure trust anchors. 

These are NOT mandatory in v0.1.
________________________________________
### 29. Minimal Safe Handshake Principle

The minimum safe handshake requires:
```text
discover
→ retrieve manifest
→ validate
→ evaluate governance
→ assign trust
→ mount
```
Execution MUST NOT occur before completion.
________________________________________
### 30. Design Boundary

The UCI Handshake Protocol defines:

-	discovery semantics, 
-	manifest exchange, 
-	compatibility evaluation, 
-	governance sequencing, 
-	trust assignment, 
-	and mounting lifecycle. 

It does NOT define:

-	orchestration logic, 
-	AI reasoning, 
-	workflow generation, 
-	distributed consensus, 
-	authentication systems, 
-	transport protocols, 
-	or business logic execution. 

Those belong to separate implementations or specifications.

