# UCI Registry & Discovery Index Model
### Draft v0.1
________________________________________
### 1. Purpose

This document defines the registry and discovery index semantics of the Universal Capability Interface (UCI).

It standardizes:

-	registry behavior, 
-	node indexing semantics, 
-	capability indexing semantics, 
-	discovery metadata, 
-	registry trust expectations, 
-	and interoperability-safe discovery behavior. 

The goal is to ensure:

-	predictable node discovery, 
-	scalable capability indexing, 
-	transport-independent discovery semantics, 
-	and governance-preserving interoperability. 
________________________________________
### 2. Registry Philosophy

A UCI registry is an advisory discovery system.

A registry:

-	helps locate nodes, 
-	helps expose metadata, 
-	helps support interoperability. 

A registry does NOT:

-	automatically establish trust, 
-	bypass governance, 
-	override operator authority, 
-	or guarantee correctness. 
________________________________________
### 3. Core Principles
| Principle              	| Meaning                                            |
|:------------------------|:---------------------------------------------------|
| Advisory Only         	| Registries provide metadata, not authority         |
| No Implicit Trust     	| Registry presence does NOT imply trust             |
| Discovery Independence	| Discovery remains separate from execution approval |
| Governance Preservation	| Registry behavior MUST NOT bypass governance       |
| Semantic Stability	    | Indexed metadata SHOULD preserve canonical meaning |
| Transport Neutrality	  | Registry semantics remain transport-independent    |
| Explicit Visibility	    | Registry state SHOULD remain auditable             |
________________________________________
### 4. Registry Definition

A registry is a system that maintains indexed metadata about UCI nodes.

Registries MAY store:

-	node identities, 
-	manifest references, 
-	capability metadata, 
-	transport declarations, 
-	trust metadata, 
-	compatibility metadata, 
-	discovery history, 
-	audit references. 
________________________________________
### 5. Registry Roles

Possible registry roles include:

| Role	              | Meaning                              | 
|:--------------------|:-------------------------------------|
| Local Registry	    | Local environment index              | 
| Organizational      | Registry	Shared enterprise registry | 
| Public Registry	    | Broadly accessible registry          | 
| Offline Registry  	| Air-gapped discovery index           | 
| Temporary Registry	| Ephemeral discovery store            | 
| Embedded Registry	  | Integrated runtime registry          | 
________________________________________
### 6. Registry Scope

Registries MAY index:

-	local nodes, 
-	remote nodes, 
-	relayed nodes, 
-	transient nodes, 
-	offline nodes, 
-	adapters, 
-	orchestration services, 
-	governance services. 

Registry scope SHOULD remain explicit.
________________________________________
### 7. Registry Entries

A registry entry represents indexed node metadata.

Example:
```json
{
  "node_id": "librarian_pro",
  "instance_id": "librarian-local-001",
  "manifest_version": "0.1",
  "transports": [],
  "capabilities": [],
  "trust_state": "verified"
}
```
________________________________________
### 8. Required Registry Metadata

Recommended registry metadata:

| Field	              | Meaning                    |
|:--------------------|:---------------------------|
| node_id	            | Logical node identity      |
| instance_id	        | Runtime instance identity  |
| manifest_version  	| Supported manifest version |
| capabilities      	| Indexed capabilities       |
| transports	        | Available transports       |
| trust_state	        | Current trust state        |
| registry_timestamp	| Last update time           |
________________________________________
### 9. Capability Indexing

Registries MAY index capability metadata.

Example:
```json
{
  "capability_id": "document_search",
  "category": "retrieval",
  "version": "1.0"
}
```
Capability indexing SHOULD preserve canonical taxonomy semantics.
________________________________________
### 10. Discovery Metadata

Registries MAY expose discovery metadata.

Examples:

-	network locality, 
-	discovery source, 
-	registration time, 
-	visibility scope, 
-	compatibility hints. 

Discovery metadata MUST NOT override governance policy.
________________________________________
### 11. Registry Trust Semantics

Registry inclusion does NOT imply:

-	trust, 
-	approval, 
-	compatibility, 
-	or execution permission. 

Nodes discovered through registries MUST still undergo:

-	manifest validation, 
-	governance evaluation, 
-	trust assignment, 
-	capability compatibility evaluation. 
________________________________________
### 12. Registry Trust States

Registries MAY track trust states.

Canonical trust states:

```text
unknown
discovered
verified
trusted
restricted
suspended
revoked
```
Registry trust state visibility SHOULD remain explicit.
________________________________________
### 13. Registry Freshness

Registry data MAY become stale.

Implementations SHOULD consider:

-	manifest age, 
-	heartbeat age, 
-	last verification time, 
-	transport availability, 
-	capability version drift. 

Stale metadata SHOULD be handled conservatively.
________________________________________
### 14. Manifest References

Registries MAY store:

-	manifests, 
-	manifest URLs, 
-	manifest hashes, 
-	manifest signatures, 
-	manifest version metadata. 

Registries SHOULD preserve manifest integrity visibility where possible.
________________________________________
### 15. Registration Models

Possible registration models include:

| Model	                  | Meaning                          |
|:------------------------|:---------------------------------|
| Manual Registration	    | Explicit operator registration   |
| Automatic Registration	|	Self-registration                |
| Registry Pull	          |	Registry retrieves metadata      |
| Registry Push	          |	Node submits metadata            |
| Hybrid Registration	    |	Combined approach                |

UCI v0.1 defines semantics only.
________________________________________
### 16. Self-Registration

Nodes MAY self-register.

Self-registration MUST NOT imply:

-	trust, 
-	automatic mounting, 
-	governance approval. 

Self-registration SHOULD remain auditable.
________________________________________
### 17. Registry Validation

Registries MAY validate:

-	manifest structure, 
-	schema compatibility, 
-	capability taxonomy compliance, 
-	transport declarations. 

Registry validation does NOT replace orchestrator validation.
________________________________________
### 18. Registry Discovery Sources

Possible discovery sources include:

```text
manual_configuration
local_scan
network_discovery
multicast
dns_service_discovery
registry_sync
operator_import
adapter_bridge
```

Discovery source SHOULD remain visible where practical.
________________________________________
### 19. Registry Query Semantics

Registries MAY support queries by:

-	node identity, 
-	capability, 
-	category, 
-	transport type, 
-	trust state, 
-	compatibility version, 
-	topology, 
-	namespace. 

Query semantics remain implementation-specific.
________________________________________
### 20. Registry Synchronization

Registries MAY synchronize metadata.

Synchronization MAY include:

-	node metadata, 
-	capability metadata, 
-	trust metadata, 
-	compatibility metadata. 

UCI v0.1 does NOT define synchronization protocols.
________________________________________
### 21. Multi-Registry Environments

Environments MAY use multiple registries simultaneously.

Examples:
```yext
local_registry
enterprise_registry
offline_registry
public_registry
```
Registry disagreement SHOULD be resolved conservatively.
________________________________________
### 22. Registry Conflict Handling

Conflicts MAY occur due to:

-	stale manifests, 
-	differing trust states, 
-	incompatible metadata, 
-	duplicate identities. 

Conflicts SHOULD:

-	remain visible, 
-	preserve auditability, 
-	avoid silent resolution. 
________________________________________
### 23. Registry Visibility Levels

Registries MAY support visibility scopes.

Examples:

| Scope	        | Meaning                     | 
|:--------------|:----------------------------|
| local       	| Same host or runtime        | 
| organization	| Shared trusted environment  | 
| public	      | Broadly visible             | 
| restricted  	| Limited access              | 
| private   	  | Operator-controlled         | 

Visibility semantics are implementation-specific.
________________________________________
### 24. Revocation Visibility

Registries SHOULD expose:

-	suspended nodes, 
-	revoked nodes, 
-	incompatible nodes, 
-	deprecated nodes. 

Revocation visibility SHOULD preserve ecosystem safety.
________________________________________
### 25. Registry Security Considerations

Registries MAY support:

-	signed manifests, 
-	signed entries, 
-	authenticated queries, 
-	encrypted transport, 
-	access restrictions. 

UCI defines registry security semantics only.

Security implementation remains implementation-specific.
________________________________________
### 26. Audit Requirements

Registry events SHOULD generate audit records.

Suggested audit events:
```text
node_registered
node_updated
node_removed
manifest_changed
registry_sync_completed
registry_conflict_detected
trust_state_changed
node_revoked
```
________________________________________
### 27. Registry Topologies

Possible registry topologies include:

| Topology	  | Meaning                     | 
|:------------|:----------------------------|
| centralized	| Single registry authority   | 
| federated  	| Multiple linked registries  |
| distributed	| Shared discovery mesh       |
| isolated	  | Offline or segmented        |
| embedded	  | Runtime-local registry      |

UCI v0.1 defines semantics only.
________________________________________
### 28. Discovery Independence Principle

Discovery MUST remain independent from:

-	governance approval, 
-	execution authorization, 
-	trust assignment, 
-	orchestration permission. 

Discovery only establishes awareness.
________________________________________
### 29. Minimal Safe Registry Principle

Minimum safe registry behavior requires:

```text
explicit metadata
+
manifest visibility
+
trust visibility
+
governance independence
```
Registry presence alone MUST NOT authorize execution.
________________________________________
### 30. Transport Independence

Registry semantics are independent from:

-	transport implementation, 
-	serialization format, 
-	runtime framework, 
-	network architecture. 

Registry meaning MUST survive transport replacement.
________________________________________
### 31. Non-Goals

UCI v0.1 does NOT define:

-	registry synchronization protocols, 
-	distributed consensus, 
-	global registry governance, 
-	package repositories, 
-	deployment systems, 
-	routing systems, 
-	orchestration intelligence, 
-	registry monetization models. 

These belong to separate implementations or future specifications.
________________________________________
### 32. Design Boundary

The UCI Registry & Discovery Index Model specification defines:

-	registry semantics, 
-	discovery indexing semantics, 
-	capability indexing semantics, 
-	registry trust expectations, 
-	and discovery visibility behavior. 

It does NOT define:

-	registry implementations, 
-	synchronization protocols, 
-	orchestration logic, 
-	governance policy engines, 
-	transport protocols, 
-	or provider business logic. 

Those belong to separate implementations or specifications.

