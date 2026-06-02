# UCI Capability Taxonomy & Semantic Naming Convention
### Draft v0.1
________________________________________
1. Purpose
 
This document defines the canonical semantic naming and taxonomy rules for the Universal Capability Interface (UCI).

It standardizes:

-	capability naming, 
-	action naming, 
-	permission naming, 
-	namespace rules, 
-	semantic stability, 
-	category taxonomy, 
-	and extension naming behavior.
  
The goal is to ensure:

-	predictable interoperability, 
-	semantic consistency, 
-	stable orchestration behavior, 
-	and long-term ecosystem compatibility. 
________________________________________
### 2. Taxonomy Philosophy

UCI naming conventions prioritize:

-	clarity, 
-	semantic stability, 
-	discoverability, 
-	interoperability, 
-	extensibility, 
-	and governance-aware consistency.
  
Names SHOULD describe:

-	meaning, 
-	behavior, 
-	and intent,
  
NOT:

-	implementation details, 
-	vendor branding, 
-	internal architecture, 
-	or framework choice. 
________________________________________
### 3. Core Naming Principles

| Principle	                  | Meaning                                       |
|:----------------------------|:----------------------------------------------|
| Meaning Over Brevity  	    | Clarity preferred over shorthand              |
| Semantic Stability	        | Names SHOULD preserve meaning over time       |
| Human Readability   	      | Names SHOULD remain understandable            |
| Machine Predictability	    | Names SHOULD support deterministic parsing    |
| Implementation Independence	| Names SHOULD avoid implementation coupling    |
| Namespace Safety	          | Extensions SHOULD avoid collisions            |
| Explicit Semantics	        | Names SHOULD clearly indicate behavior        |
________________________________________
### 4. Canonical Naming Style

Machine-readable identifiers SHOULD use:
```text
lowercase_snake_case
``
Examples:
```text
document_search
document_retrieve
speech_to_text
policy_validate
trust_evaluate
```
Human-readable labels MAY use normal title casing.
________________________________________
### 5. Identifier Rules

Identifiers MUST:

-	begin with a lowercase letter, 
-	contain only:
    -	lowercase letters, 
    -	numbers, 
    -	underscores, 
-	avoid spaces, 
-	avoid hyphens, 
-	avoid vendor-specific branding, 
-	remain stable once published. 
________________________________________
### 6. Capability Naming Rules

Capabilities describe broad functional abilities.

Capability names SHOULD:

-	describe domain semantics, 
-	avoid implementation references, 
-	remain vendor-neutral. 
________________________________________
### 6.1 Good Capability Examples
```text
document_search
text_generation
image_generation
text_to_speech
speech_to_text
policy_validate
network_monitor
file_storage
```
________________________________________
### 6.2 Bad Capability Examples
```text
gpt_search
kokoro_voice
fast_llm_query
vaultplusplus
super_search_v2
```
Reasons:

-	vendor-coupled, 
-	implementation-coupled, 
-	unstable semantics, 
-	branding leakage. 
________________________________________
### 7. Action Naming Rules

Actions describe executable operations.

Action names SHOULD:

-	begin with a verb where practical, 
-	clearly indicate operation behavior, 
-	avoid ambiguous shorthand. 
________________________________________
### 7.1 Good Action Examples
```text
search_index
retrieve_document
generate_summary
validate_policy
transcribe_audio
store_file
delete_record
```
________________________________________
### 7.2 Bad Action Examples
```text
do_search
run_it
execute
process
magic_mode
quick_query
```
Reasons:

-	ambiguous semantics, 
-	unclear operation intent, 
-	poor interoperability value. 
________________________________________
### 8. Permission Naming Rules

Permissions define authority requirements.

Permissions SHOULD follow:
```text
domain.operation
```
________________________________________
### 8.1 Good Permission Examples
```text
documents.read
documents.write
audio.transcribe
policy.evaluate
system.execute
vault.admin
network.external
```
________________________________________
### 8.2 Bad Permission Examples
```text
admin
full_access
godmode
all
execute_everything
```
Reasons:

-	ambiguous scope, 
-	excessive authority, 
-	weak governance semantics. 
________________________________________
### 9. Event Naming Rules

Events describe observable lifecycle occurrences.

Events SHOULD use:
```text
noun_past_tense
```
or
```text
noun_state_change
```
________________________________________
### 9.1 Good Event Examples
```text
node_discovered
manifest_validated
capability_mounted
execution_completed
trust_revoked
policy_denied
```
________________________________________
### 9.2 Bad Event Examples
```text
node_ok
thing_happened
stuff_changed
completed_event
```
Reasons:

-	weak semantics, 
-	poor audit clarity, 
-	low interoperability value. 
________________________________________
### 10. Error Naming Rules

Canonical error codes SHOULD:

-	use lowercase_snake_case, 
-	describe failure category, 
-	remain implementation-neutral. 
________________________________________
### 10.1 Good Error Examples
```text
validation_error
permission_denied
timeout_error
provider_unavailable
trust_failure
```
________________________________________
### 10.2 Bad Error Examples
```text
error_42
bad_stuff
oops
unknown_issue
```
Reasons:

-	non-semantic, 
-	unstable, 
-	difficult to automate against. 
________________________________________
### 11. Namespace Rules

Extensions SHOULD use explicit namespaces.

Recommended format:
```text
vendor.extension_name
```
Examples:
```text
acme.audit_profile
examplecorp.runtime_flags
acme.custom_transport
```
Namespaces SHOULD:

-	prevent collisions, 
-	preserve interoperability, 
-	isolate vendor-specific behavior. 
________________________________________
### 12. Reserved Core Prefixes

The following prefixes are reserved for UCI core semantics:
```
uci_
system_
policy_
trust_
audit_
governance_
```
Extensions SHOULD NOT redefine reserved prefixes.
________________________________________
### 13. Semantic Stability Rules

Published identifiers SHOULD preserve meaning over time.
________________________________________
### 13.1 Stable Semantics Principle

Example:
```text
document_search
```
MUST continue meaning:

-	searching documents. 

It MUST NOT later become:

-	document deletion, 
-	semantic generation, 
-	policy evaluation, 
-	unrelated functionality. 
________________________________________
### 13.2 Semantic Change Handling

If semantics fundamentally change:

Providers SHOULD:

-	create a new identifier, 
-	deprecate the old identifier, 
-	preserve compatibility where possible. 

Silent semantic mutation is strongly discouraged.
________________________________________
### 14. Category Taxonomy

Capabilities SHOULD belong to canonical categories.
________________________________________
### 14.1 Canonical Categories v0.1
```text
retrieval
storage
generation
analysis
transformation
communication
execution
governance
monitoring
vision
audio
identity
network
security
utility
other
```
________________________________________
### 14.2 Example Taxonomy
```text
retrieval/
    document_search
    document_retrieve

generation/
    text_generation
    image_generation

audio/
    speech_to_text
    text_to_speech

governance/
    policy_validate
    trust_evaluate
```
________________________________________
### 15. Alias Handling

Providers MAY expose aliases for compatibility.

Aliases MUST:

-	map deterministically, 
-	preserve semantics, 
-	avoid ambiguity. 

Canonical identifiers remain authoritative.
________________________________________
### 15.1 Alias Example
```json
{
  "capability_id": "document_search",
  "aliases": [
    "search_documents",
    "query_documents"
  ]
}
```
________________________________________
### 16. Deprecation Rules

Deprecated identifiers SHOULD:

-	remain temporarily resolvable, 
-	emit compatibility warnings, 
-	include migration guidance where possible. 

Deprecation SHOULD NOT silently remove semantics.
________________________________________
### 17. Versioning Implications

Identifier meaning SHOULD remain stable across:

-	patch versions, 
-	minor versions. 

Major semantic changes SHOULD:

-	increment major version, 
-	or create new identifiers. 
________________________________________
### 18. Discovery Considerations

Naming consistency directly impacts:

-	capability discovery, 
-	orchestration compatibility, 
-	registry indexing, 
-	semantic search, 
-	workflow composition, 
-	and interoperability reliability. 

Semantic ambiguity SHOULD be minimized.
________________________________________
### 19. Anti-Patterns

The following are strongly discouraged:
________________________________________
### 19.1 Vendor-Coupled Names
Bad:
```text
openai_query
anthropic_reasoning
kokoro_tts
```
________________________________________
### 19.2 Version-Coupled Names
Bad:
```text
document_search_v2
voice_engine_2026
```
________________________________________
### 19.3 Ambiguous Shorthand

Bad:
```text
proc
exec
mgr
qry
```
________________________________________
### 19.4 Emotional or Marketing Terms

Bad:
```text
super_mode
ultimate_ai
hyper_reasoning
magic_execute
```
________________________________________
### 20. Human Readability Principle

UCI identifiers SHOULD remain understandable by humans without external tooling.

Example:

Good:
```text
generate_summary
```
Bad:
```text
gen_sum_v4x
```
________________________________________
### 21. Machine Predictability Principle

Identifiers SHOULD support:

-	deterministic parsing, 
-	stable indexing, 
-	orchestration matching, 
-	semantic grouping. 

Naming SHOULD favor consistency over stylistic variation.
________________________________________
### 22. Minimal Naming Principle
Minimum safe naming requires:
```text
stable semantics
+
human readability
+
machine predictability
+
vendor neutrality
```
________________________________________
### 23. Transport Independence

Naming semantics are independent from:

-	transport implementation, 
-	serialization format, 
-	runtime framework, 
-	programming language. 
________________________________________
### 24. Design Boundary

The UCI Capability Taxonomy & Semantic Naming Convention specification defines:

-	naming semantics, 
-	taxonomy structure, 
-	namespace behavior, 
-	semantic stability rules, 
-	and identifier conventions. 

It does NOT define:

-	transport protocols, 
-	orchestration logic, 
-	provider implementation, 
-	workflow semantics, 
-	registry architecture, 
-	or execution behavior. 

Those belong to separate specifications or implementations.

