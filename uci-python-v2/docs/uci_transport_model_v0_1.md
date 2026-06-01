# UCI Transport Abstraction & Communication Model
### Draft v0.1
________________________________________
### 1. Purpose

This document defines the transport abstraction and communication semantics of the Universal Capability Interface (UCI).

It standardizes:

-	transport abstraction behavior, 
-	communication expectations, 
-	request/response semantics, 
-	streaming semantics, 
-	transport negotiation, 
-	delivery expectations, 
-	and transport-independent interoperability behavior. 

The goal is to ensure:

-	transport-neutral interoperability, 
-	stable semantics across communication mechanisms, 
-	governance-aware communication consistency, 
-	and implementation-independent orchestration behavior. 
________________________________________
### 2. Transport Philosophy

UCI is transport-aware but transport-independent.

Transport mechanisms:

-	carry UCI semantics, 
-	but do NOT define UCI semantics. 

UCI semantics MUST remain stable regardless of:

-	transport protocol, 
-	runtime environment, 
-	serialization method, 
-	communication topology, 
-	or implementation technology. 
________________________________________
### 3. Core Principles

| Principle	                  | Meaning                                           |
|:----------------------------|:--------------------------------------------------|
| Transport Neutrality	      | UCI semantics MUST survive transport replacement  | 
| Semantic Stability	        | Communication semantics MUST remain consistent    | 
| Explicit Communication	    | Communication behavior SHOULD be explicit         | 
| Fail-Closed Behavior	      | Transport ambiguity SHOULD default conservatively | 
| Implementation Independence	| UCI does NOT mandate transport technology         | 
| Governance Preservation   	| Transport MUST NOT bypass governance semantics    | 
| Delivery Awareness	        | Delivery expectations SHOULD be explicit          | 
________________________________________
### 4. Transport Abstraction Principle

Transport implementations:

-	move messages, 
-	preserve metadata, 
-	maintain delivery semantics. 

Transports MUST NOT redefine:

-	governance semantics, 
-	trust semantics, 
-	invocation semantics, 
-	execution semantics, 
-	capability semantics. 
________________________________________
### 5. Communication Roles

UCI communication involves the following logical roles:

| Role	        | Meaning                  |
|:--------------|:-------------------------|
| Provider      |	Exposes capabilities     |
| Consumer      |	Invokes capabilities     |
| Orchestrator  |	Coordinates interactions |
| Policy Engine |	Evaluates governance     |
| Registry      |	Maintains node metadata  |
| Adapter       |	Bridges external systems |

A node MAY fulfill multiple roles.
________________________________________
### 6. Canonical Communication Models

UCI v0.1 recognizes the following communication models:

| Model           	| Meaning                     |
|:------------------|:----------------------------|
| request_response	| Direct request and reply    |
| streaming     	  | Incremental response flow   |
| asynchronous	    | Deferred execution          |
| event_driven	    | Triggered by events         |
| broadcast	        | One-to-many notification    |
| relay	            | Routed through intermediary |

UCI defines semantics only. 

Transport implementations remain implementation-specific.
________________________________________
### 7. Request/Response Model

The request/response model is the baseline communication pattern.

Characteristics:

| Property                      	| Behavior |
|:--------------------------------|:---------|
| Caller initiated	              | Yes      |
| Direct response	                | Yes      |
| Deterministic correlation	      | Yes      |
| Compatible with sync execution	| Yes      |

v0.1 implementations SHOULD support request/response behavior first.
________________________________________
### 8. Streaming Model

Streaming allows incremental data delivery.

Examples:

-	speech synthesis, 
-	transcription, 
-	telemetry, 
-	token generation. 

Streaming transports SHOULD preserve:

-	ordering, 
-	correlation identifiers, 
-	terminal completion state. 
________________________________________
### 9. Asynchronous Communication Model

Asynchronous communication allows:

-	non-blocking execution, 
-	delayed completion, 
-	queue-based processing, 
-	deferred orchestration. 

Async semantics MUST preserve:

-	invocation identity, 
-	execution state visibility, 
-	eventual terminal state. 
________________________________________
### 10. Event-Driven Model

Event-driven communication reacts to observable state changes.

Examples:

-	node discovered, 
-	manifest updated, 
-	execution completed, 
-	trust revoked. 

UCI defines event semantics only.

Event transport systems remain implementation-specific.
________________________________________
### 11. Delivery Guarantees

UCI v0.1 recognizes the following delivery expectations:

| Guarantee   	| Meaning                     | 
|:--------------|:----------------------------|
| best_effort	  | Delivery not guaranteed     |
| at_most_once	| Duplicate delivery avoided  |
| at_least_once	| Retry delivery permitted    |
| exactly_once	| Strong duplicate prevention |

Providers SHOULD declare supported guarantees. 

Orchestrators MUST NOT assume undeclared guarantees. 
________________________________________
### 12. Reliability Expectations

Reliability expectations SHOULD be explicit.

Possible reliability metadata:
```json
{
  "delivery_guarantee": "at_most_once",
  "ordering_guarantee": true,
  "retry_supported": true
}
```
________________________________________
### 13. Session Semantics

UCI does NOT require persistent sessions.

A transport MAY support:

-	stateless interaction, 
-	stateful sessions, 
-	temporary connections, 
-	persistent channels. 

Session semantics are implementation-specific.
________________________________________
### 14. Connection State Semantics

Possible connection states:

| State	        | Meaning                     |
|:--------------|:----------------------------|
| disconnected	| No communication available  |
| connecting	  | Establishing communication  |
| connected	    | Communication available     |
| degraded	    | Reduced reliability         |
| suspended	    | Temporarily disabled        |
| revoked	      | Explicitly denied           |

Connection state does NOT override governance policy.
________________________________________
### 15. Serialization Independence

UCI semantics are serialization-independent.

Possible serialization formats include:

-	JSON 
-	CBOR 
-	MessagePack 
-	Protobuf 
-	XML 
-	binary formats 

UCI v0.1 examples use JSON for readability only.

Serialization format does NOT define semantics.
________________________________________
### 16. Transport Capability Declaration

Nodes MUST declare supported transports.

Example:
```json
{
  "transport_id": "local_http",
  "type": "http",
  "endpoint": "http://127.0.0.1:8080",
  "security": {
    "tls_required": false,
    "auth_required": true
  }
}
```
________________________________________
### 17. Supported Transport Types
Canonical transport types v0.1:
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
Implementations MAY define additional transport types.
________________________________________
### 18. Multi-Transport Nodes

A node MAY expose multiple transports simultaneously.

Example:
```text
HTTP for orchestration
IPC for local execution
WebSocket for streaming
```
All transports MUST preserve UCI semantics consistently.
________________________________________
### 19. Transport Negotiation

Transport negotiation determines:

-	which transport is used, 
-	under what conditions, 
-	with what restrictions. 

Negotiation MAY consider:

-	local policy, 
-	trust state, 
-	latency, 
-	security requirements, 
-	topology, 
-	transport availability. 

UCI v0.1 does NOT define negotiation algorithms.
________________________________________
### 20. Local vs Remote Semantics

UCI semantics MUST remain stable between:

-	local execution, 
-	LAN execution, 
-	remote execution, 
-	relayed execution. 

Governance MAY apply different policy constraints depending on locality.
________________________________________
### 21. Transport Security Considerations

Transport security MAY include:

-	TLS, 
-	authentication, 
-	signed invocations, 
-	encrypted channels, 
-	secure relays, 
-	network isolation. 

UCI defines security semantics only.

It does NOT mandate specific cryptographic systems in v0.1.
________________________________________
### 22. Transport Failure Handling

Transport failure SHOULD:

-	fail explicitly, 
-	preserve auditability, 
-	preserve invocation traceability. 

Transport failure MUST NOT imply:

-	execution success, 
-	rollback, 
-	or governance bypass. 
________________________________________
### 23. Fallback Behavior

Fallback behavior MAY include:

-	alternate transport selection, 
-	deferred execution, 
-	retry, 
-	degraded operation. 

Fallback behavior MUST preserve:

-	governance semantics, 
-	trust requirements, 
-	invocation identity. 
________________________________________
### 24. Discovery Independence

Discovery mechanisms are independent from transport semantics.

Examples:

-	registry discovery, 
-	multicast discovery, 
-	static configuration, 
-	manual registration. 

Discovery does NOT imply:

-	transport trust, 
-	execution permission, 
-	governance approval. 
________________________________________
### 25. Transport Adapters

Adapters MAY translate external systems into UCI-compatible transports.

Examples:
```text 
REST API → UCI Adapter
MQTT → UCI Bridge
Legacy IPC → UCI Wrapper
```
Adapters MUST preserve:

-	governance semantics, 
-	capability semantics, 
-	trust semantics, 
-	invocation semantics. 

Adapters MUST NOT silently alter meaning.
________________________________________
### 26. Communication Topologies

Possible topologies include:

| Topology	    | Meaning                       |
|:--------------|:------------------------------|
| local       	| Same host                     | 
| peer_to_peer	| Direct node communication     |
| orchestrated	| Central orchestration         |
| relayed	      | Routed through intermediary   |
| mesh	        | Distributed multi-node        |
| offline	      | Temporarily disconnected      |

UCI v0.1 defines topology semantics only.
________________________________________
### 27. Governance Preservation Principle

Transport implementations MUST NOT:

-	bypass governance, 
-	bypass policy evaluation, 
-	bypass trust validation, 
-	bypass operator authority. 

Governance semantics remain authoritative above transport behavior.
________________________________________
### 28. Semantic Preservation Principle

Transport replacement MUST NOT fundamentally alter:

-	invocation semantics, 
-	capability semantics, 
-	execution semantics, 
-	error semantics, 
-	governance semantics. 

Example:
```text
HTTP → IPC
```
SHOULD preserve operational meaning.
________________________________________
### 29. Minimal Safe Communication Principle

Minimum safe communication requires:
```text
stable invocation identity
+
preserved governance semantics
+
preserved correlation identifiers
+
explicit terminal states
```
Communication lacking these SHOULD be treated conservatively.
________________________________________
### 30. Non-Goals

UCI v0.1 does NOT define:

-	broker standards, 
-	queue implementations, 
-	federation protocols, 
-	cluster management, 
-	distributed consensus, 
-	routing protocols, 
-	service mesh architecture, 
-	transport protocol standards. 

These belong to separate systems or future extensions.
________________________________________
### 31. Design Boundary

The UCI Transport Abstraction & Communication Model specification defines:

-	communication semantics, 
-	transport abstraction behavior, 
-	delivery expectations, 
-	transport negotiation semantics, 
-	and topology semantics. 

It does NOT define:

-	transport implementations, 
-	orchestration intelligence, 
-	workflow systems, 
-	cryptographic standards, 
-	network architecture, 
-	distributed coordination, 
-	or runtime execution engines. 
Those belong to separate implementations or specifications.

