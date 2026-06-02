# UCI Ontology & Definitions
### Draft v0.1

### 1. Purpose

This document defines the core terms of the Universal Capability Interface so every UCI-compatible system uses the same language, structure, and responsibility boundaries.
UCI must avoid vague words like “tool,” “agent,” or “plugin” unless they are formally defined.
________________________________________
### 2. Core Ontology
```text
System
 └── Node
      └── Manifest
           └── Capability
                └── Action
                     └── Contract
                          ├── Input Schema
                          ├── Output Schema
                          ├── Risk Profile
                          ├── Permission Requirements
                          └── Execution Semantics
```
________________________________________
### 3. Authoritative Definitions
### 3.1 System

A System is the total UCI-aware environment.

Example:

```text
UCI Protocol ecosystem
```

A system may contain:

-	orchestrators 
-	applications 
-	services 
-	agents 
-	policy engines 
-	registries 
-	operators 
________________________________________
### 3.2 Node

A Node is any UCI-compatible runtime participant.

A node may be:

-	an application 
-	a service 
-	an AI agent 
-	a local tool 
-	a remote endpoint 
-	a hardware bridge 
-	a background daemon
  
Examples:
```text
Niles
Librarian Pro
Voice Gateway
UCI Vault
AXIS
```
A node must expose a UCI manifest.
________________________________________
### 3.3 Manifest

A Manifest is the machine-readable declaration of a node.

It defines:

-	identity 
-	version 
-	capabilities 
-	governance requirements 
-	trust metadata 
-	supported transports 
-	health endpoints 
-	action contracts
  
The manifest is the source of truth for what the node claims it can do.
________________________________________
### 3.4 Capability

A Capability is a declared functional ability of a node.

A capability describes a broad class of work.

Examples:

```
document_search
text_to_speech
speech_to_text
file_storage
reasoning_assistance
policy_validation
```

A capability is not directly executed.

It groups one or more executable actions.
________________________________________
### 3.5 Action

An Action is an executable operation exposed under a capability.

Example capability:

```text
document_search
```

Possible actions:

```text
search_index
retrieve_document
summarize_result
get_citation
```

An action must have a contract.
________________________________________
### 3.6 Contract

A Contract is the formal definition of how an action may be called.

It defines:

-	inputs 
-	outputs 
-	validation rules 
-	permission requirements 
-	risk level 
-	confirmation requirements 
-	timeout behavior 
-	error model 
-	audit requirements
  
No action may be executed without a valid contract.
________________________________________
### 3.7 Input Schema

An Input Schema defines the required and optional fields accepted by an action.

Example:
```json
{
  "query": "string",
  "top_k": "integer",
  "filters": "object"
}
```
________________________________________
### 3.8 Output Schema

An Output Schema defines the expected structure returned by an action.

Example:
```json
{
  "results": "array",
  "count": "integer",
  "status": "string"
}
```
________________________________________
### 3.9 Orchestrator

An Orchestrator is a node that discovers, evaluates, coordinates, and invokes other nodes.

Examples:

```texr
Niles
AXIS
UCI Runtime Controller
```

An orchestrator may not assume capabilities.

It must read and validate manifests.
________________________________________
### 3.10 Operator

An Operator is the human authority over the system.

The operator may:

-	approve actions 
-	deny actions 
-	grant trust 
-	revoke trust 
-	configure policy 
-	review audit logs 

UCI treats operator authority as superior to agent autonomy.
________________________________________
### 3.11 Policy Engine

A Policy Engine evaluates whether a requested action is allowed.

It considers:

-	node identity 
-	action risk 
-	operator permissions 
-	trust state 
-	runtime context 
-	governance rules 

The policy engine may allow, deny, defer, or require confirmation.
________________________________________
### 3.12 Trust State

A Trust State describes the current security relationship between the system and a node.

Baseline trust states:

| State	         | Meaning                             |
|:---------------|:------------------------------------|
| Unknown     	 | Node has not been validated         | 
| Discovered	   | Node is visible but not approved    | 
| Verified	     | Identity and manifest are valid     | 
| Trusted	       | Node is approved for normal use     | 
| Restricted	   | Node has limited capability access  | 
| Suspended	     | Node is temporarily blocked         | 
| Revoked        | Node is denied access               | 
________________________________________
### 3.13 Transport

A Transport is the communication mechanism used to reach a node.

Examples:

-	HTTP 
-	HTTPS 
-	WebSocket 
-	IPC 
-	gRPC 
-	message bus 
-	local socket 

UCI is transport-agnostic.

The contract must remain stable even if the transport changes.
________________________________________
### 3.14 Adapter

An Adapter translates a node’s native interface into UCI-compliant form.

Adapters are useful when existing programs were not originally designed for UCI.

Example:
```text
Legacy app API → UCI adapter → UCI orchestrator
```

An adapter must not invent capabilities beyond what the underlying application can actually perform.
________________________________________
### 3.15 Provider

A Provider is a node that exposes capabilities for others to use.

Examples:

```text
Librarian Pro provides document_search
Voice Appliance provides text_to_speech
Vault provides governed_storage
```
________________________________________
### 3.16 Consumer

A Consumer is a node that requests or invokes capabilities from another node.

Example:

```text
Niles consumes Librarian Pro search capabilities.
```
A node can be both a provider and a consumer.
________________________________________
### 3.17 Registry

A Registry is an index of known UCI nodes and manifests.

It may store:

-	node identities 
-	manifest versions 
-	trust states 
-	transport locations 
-	capability metadata 
-	approval history
  
A registry is not automatically trusted.

________________________________________
### 3.18 Handshake

A Handshake is the initial compatibility and trust negotiation between nodes.

Minimum handshake sequence:
```text
1. Discover node
2. Retrieve manifest
3. Validate manifest schema
4. Validate identity
5. Check protocol compatibility
6. Evaluate governance policy
7. Assign trust state
8. Mount approved capabilities
```
________________________________________
### 3.19 Mount

To Mount a capability means the orchestrator has accepted it into its usable capability space.

Mounting does not mean unrestricted execution.

Mounted actions still require policy checks.
________________________________________
### 3.20 Invocation

An Invocation is a specific request to execute an action.

An invocation includes:

-	caller identity 
-	target node 
-	action name 
-	input payload 
-	context 
-	requested permissions 
-	audit ID 
________________________________________
### 3.21 Execution Context

An Execution Context is the surrounding state for an invocation.

It may include:

-	user/session identity 
-	current task 
-	environment 
-	time 
-	permissions 
-	active policy profile 
-	risk posture 
-	network boundary 
________________________________________
### 3.22 Risk Profile

A Risk Profile describes the potential impact of an action.

Baseline risk levels:

| Level	   | Meaning                                                                             | 
|:---------|:------------------------------------------------------------------------------------|
| none    	| No meaningful system impact                                                         | 
| low	     | Read-only or harmless operation                                                     | 
| medium	  | Modifies reversible state                                                           | 
| high	    | Modifies important state or accesses sensitive data                                 | 
| critical	| Irreversible, destructive, external, financial, legal, or security-sensitive action | 
________________________________________
### 3.23 Confirmation Requirement

A Confirmation Requirement defines whether human approval is needed before execution.

Possible values:

```text
none
recommended
required
required_with_reason
multi_party_required
```
________________________________________
### 3.24 Audit Event

An Audit Event is a recorded fact about UCI activity.

Examples:

-	node discovered 
-	manifest validated 
-	capability mounted 
-	action requested 
-	action denied 
-	operator approved 
-	execution completed 
-	trust revoked
  
Audit events should be append-only.
________________________________________
### 3.25 Error Model

An Error Model defines how failures are represented.

Baseline error classes:

| Error	             | Meaning                       |                       
|:-------------------|:------------------------------|
| validation_error	  | Input or schema invalid       | 
| permission_denied	 | Policy denied execution       | 
| trust_failure	     | Node trust insufficient       | 
| transport_error	   | Communication failed          | 
| execution_error	   | Target action failed          | 
| timeout_error	     | Execution exceeded time limit | 
| unsupported_action	| Action not available          | 
| version_mismatch	  | Protocol or schema mismatch   | 
________________________________________
### 4. Terms to Avoid or Restrict

### “Tool”

Use only as a casual user-facing synonym.

In UCI documents, prefer:

```text
Capability
Action
Provider
Node
```
________________________________________
### “Plugin”

Use only when referring to a loadable software extension.

A plugin may expose UCI capabilities, but a UCI capability is not necessarily a plugin.
________________________________________
### “Agent”

Use only for autonomous or semi-autonomous reasoning systems.

Not every UCI node is an agent.
________________________________________
### “API”

Use only for implementation details.

UCI is broader than an API because it includes:

-	discovery 
-	governance 
-	trust 
-	contracts 
-	auditability 
-	execution semantics 
________________________________________
### 5. Responsibility Boundaries

Application / Provider

Responsible for:

-	exposing real capabilities 
-	maintaining accurate manifests 
-	executing approved actions 
-	returning contract-compliant outputs 
-	reporting health 

Not responsible for:

-	global orchestration 
-	external policy authority 
-	pretending to know caller intent 
________________________________________
#### Orchestrator

Responsible for:

-	discovering nodes 
-	validating manifests 
-	requesting policy decisions 
-	invoking actions 
-	composing workflows 
-	preserving operator authority
  
Not responsible for:

-	bypassing governance 
-	inventing undeclared capabilities 
-	directly modifying provider internals 
________________________________________
#### Policy Engine

Responsible for:

-	allow/deny decisions 
-	trust evaluation 
-	permission checks 
-	confirmation requirements 
-	compliance rules 

Not responsible for:

-	executing application logic 
-	generating creative plans 
-	replacing operator authority 
________________________________________
#### Operator

Responsible for:

 -	final authority 
 -	policy configuration 
 -	approval of high-risk actions 
 -	trust decisions
  
Not responsible for:

 -	manually understanding every low-level endpoint 
________________________________________
### 6. First Canonical UCI Sentence

A good one-line definition:

>UCI is a governance-aware capability contract layer that allows software nodes to declare, negotiate, and expose executable abilities to orchestrators under explicit policy and operator authority.

This should probably become the official short definition.

