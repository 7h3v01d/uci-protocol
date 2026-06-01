# UCI Minimal Reference SDK Architecture
### Draft v0.1
________________________________________
### 1. Purpose

This document defines the minimal architecture for a reference UCI SDK.

The SDK should help implementers:

-	load manifests, 
-	validate manifests, 
-	inspect capabilities, 
-	validate invocations, 
-	build canonical responses, 
-	produce audit events, 
-	and test UCI compliance. 

The SDK is not a full orchestrator.
________________________________________
### 2. SDK Philosophy

The reference SDK SHOULD be:

-	small, 
-	boring, 
-	deterministic, 
-	dependency-light, 
-	implementation-neutral, 
-	testable, 
-	and MIT-friendly. 

It SHOULD model UCI semantics without forcing a runtime architecture.
________________________________________
### 3. Non-Goals

The SDK does NOT provide:

-	full orchestration runtime, 
-	AI agent logic, 
-	workflow engine, 
-	network server framework, 
-	policy engine implementation, 
-	authentication framework, 
-	registry service, 
-	distributed execution, 
-	vendor-specific governance. 
________________________________________
### 4. Proposed Package Layout

```text
uci_sdk/
    __init__.py
    manifest.py
    schema_validator.py
    semantic_validator.py
    capability.py
    invocation.py
    response.py
    audit.py
    policy.py
    handshake.py
    extensions.py
    errors.py

schemas/
    uci_manifest_0_1.schema.json

examples/
    minimal_provider_manifest.json
    standard_provider_manifest.json
    orchestrator_manifest.json
    registry_manifest.json
    policy_engine_manifest.json
    adapter_manifest.json
    non_ai_service_manifest.json

tests/
    test_manifest_loader.py
    test_schema_validator.py
    test_semantic_validator.py
    test_capability_registry.py
    test_invocation.py
    test_response_envelope.py
    test_audit_events.py
    test_handshake.py
    test_extensions.py
```
________________________________________
### 5. Core Modules

manifest.py

Responsible for:

-	loading manifest files, 
-	parsing manifest objects, 
-	exposing manifest metadata, 
-	normalizing internal representation. 

Should expose:

```python
load_manifest(path: str) -> UCIManifest
parse_manifest(data: dict) -> UCIManifest
```
________________________________________
schema_validator.py

Responsible for:

-	JSON Schema validation, 
-	required field validation, 
-	enum validation, 
-	identifier pattern validation. 

Should expose:
```python
validate_schema(manifest: dict) -> ValidationResult
```
________________________________________
semantic_validator.py

Responsible for higher-level consistency checks.

Examples:

-	critical risk without confirmation, 
-	audit required but audit disabled, 
-	destructive action declared as no side effects, 
-	required extension unsupported. 

Should expose:

```python
validate_semantics(manifest: UCIManifest) -> ValidationResult
```
________________________________________
capability.py

Responsible for:

-	listing capabilities, 
-	finding actions, 
-	checking action existence, 
-	exposing capability metadata. 

Should expose:

```python
list_capabilities(manifest: UCIManifest) -> list
get_action(manifest: UCIManifest, capability_id: str, action_id: str)
```
________________________________________
invocation.py

Responsible for:

-	creating invocation objects, 
-	validating invocation targets, 
-	validating input payload shape, 
-	preserving correlation identifiers. 

Should expose:

```python
build_invocation(...)
validate_invocation(invocation, manifest) -> ValidationResult
```
________________________________________
response.py

Responsible for:

-	canonical response envelope creation, 
-	success responses, 
-	failure responses, 
-	deferred responses, 
-	partial completion responses. 

Should expose:

```python
success_response(...)
error_response(...)
deferred_response(...)
partial_response(...)
```
________________________________________
audit.py

Responsible for:

-	canonical audit event creation, 
-	event typing, 
-	severity handling, 
-	correlation ID preservation. 

Should expose:

```python
build_audit_event(...)
```
________________________________________
policy.py

Responsible for defining policy interfaces only.

It should not implement a full policy engine.

Should expose:

```python
class PolicyDecision:
    outcome: str
    reason: str
    restrictions: dict
```
and:

```python
class PolicyEvaluatorProtocol:
    def evaluate(invocation, context) -> PolicyDecision:
        ...
```
________________________________________
handshake.py

Responsible for:

-	manifest validation sequence, 
-	compatibility evaluation, 
-	mount-readiness result generation. 

Should expose:

```python
evaluate_handshake(manifest: UCIManifest, supported_versions: list[str]) -> HandshakeResult
```
________________________________________
extensions.py

Responsible for:

-	namespace validation, 
-	unknown extension handling, 
-	reserved prefix checks. 

Should expose:

```python
validate_extensions(manifest: UCIManifest) -> ValidationResult
```
________________________________________
errors.py

Responsible for:

-	canonical error codes, 
-	validation error structures, 
-	warning structures. 
________________________________________
### 6. Core Data Structures

ValidationResult

```python
@dataclass
class ValidationResult:
    outcome: str
    errors: list
    warnings: list
    summary: dict
```

Allowed outcomes:

```text
pass
pass_with_warnings
fail
unsupported
```
________________________________________
ValidationIssue

```python
@dataclass
class ValidationIssue:
    code: str
    severity: str
    path: str
    message: str
```
________________________________________
UCIManifest

```python
@dataclass
class UCIManifest:
    raw: dict
    manifest_version: str
    node_id: str
    instance_id: str
```
________________________________________
Invocation

```python
@dataclass
class Invocation:
    invocation_id: str
    correlation_id: str
    caller: dict
    target: dict
    payload: dict
    context: dict
```
________________________________________
UCIResponse

```python
@dataclass
class UCIResponse:
    uci_response_version: str
    invocation_id: str
    correlation_id: str
    timestamp: str
    state: str
    success: bool
    provider: dict
    output: dict | None
    error: dict | None
    audit: dict
```
________________________________________
AuditEvent

```python
@dataclass
class AuditEvent:
    audit_event_version: str
    audit_id: str
    timestamp: str
    event_type: str
    correlation_id: str
    source: dict
    severity: str
    details: dict
```
________________________________________
### 7. Validation Pipeline

Canonical SDK validation flow:

```text
load manifest
    ↓
parse JSON
    ↓
schema validation
    ↓
semantic validation
    ↓
extension validation
    ↓
compatibility summary
    ↓
validation result
```

________________________________________
### 8. Handshake Evaluation Flow

```text
manifest loaded
    ↓
schema valid
    ↓
semantics valid
    ↓
version compatible
    ↓
capabilities inspected
    ↓
mount readiness produced
```

The SDK SHOULD NOT perform actual mounting.

It SHOULD only report readiness.
________________________________________
### 9. Policy Interface Boundary

The SDK MAY define policy decision objects.

The SDK SHOULD NOT implement real organizational policy.

Reason:

Policy is environment-specific.

The SDK may provide mock or sample policy evaluators for tests only.
________________________________________
### 10. Response Envelope Helpers

The SDK SHOULD provide helper functions to avoid malformed responses.

Example:
```python
success_response(
    invocation_id="invoke_001",
    correlation_id="corr_001",
    provider={"node_id": "minimal_provider"},
    output={"results": []},
)
```
________________________________________
### 11. Audit Event Helpers

The SDK SHOULD provide helper functions for canonical audit events.

Example:

```python
build_audit_event(
    event_type="manifest_validated",
    correlation_id="corr_001",
    source={"node_id": "uci_validator"},
    severity="info",
    details={}
)
```
________________________________________
### 12. Extension Handling

The SDK SHOULD:

-	validate namespaces, 
-	reject reserved prefix misuse, 
-	warn on unknown optional extensions, 
-	fail unknown required extensions if represented. 

The SDK SHOULD NOT execute extension logic.
________________________________________
### 13. Testing Strategy

Initial test groups:
```text
manifest loading
schema validation
semantic validation
extension validation
capability lookup
invocation validation
response envelope generation
audit event generation
handshake readiness
```
________________________________________
### 14. Minimal Test Expectations

The SDK test suite SHOULD confirm:

-	valid manifests pass, 
-	invalid manifests fail, 
-	warnings are deterministic, 
-	canonical responses are shaped correctly, 
-	audit events preserve correlation IDs, 
-	unknown extensions are handled safely, 
-	handshake evaluation fails closed. 
________________________________________
### 15. Recommended Dependencies

For Python reference SDK:

```text
jsonschema
pytest
Optional:
pydantic
```

But v0.1 SHOULD avoid over-dependence.
________________________________________
### 16. CLI Utility

A minimal CLI MAY be included:

```text
uci-validate manifest.json
```

Expected output:

```json
{
  "outcome": "pass",
  "errors": [],
  "warnings": []
}
```
________________________________________
### 17. Minimal Public API

The SDK should expose a small public API:

```python
from uci_sdk import (
    load_manifest,
    validate_schema,
    validate_semantics,
    evaluate_handshake,
    success_response,
    error_response,
    build_audit_event,
)
```
________________________________________
### 18. Implementation Boundary

The SDK validates and models UCI.

It does not own:

-	runtime orchestration, 
-	provider execution, 
-	transport serving, 
-	identity systems, 
-	policy engines, 
-	registry synchronization, 
-	AI reasoning. 
________________________________________
### 19. Minimal Safe SDK Principle

Minimum useful SDK behavior requires:

```text
manifest loading
+
schema validation
+
semantic validation
+
canonical response helpers
+
audit helper structures
```
________________________________________
### 20. Design Boundary

The UCI Minimal Reference SDK Architecture defines:

-	package structure, 
-	core modules, 
-	validation flow, 
-	helper responsibilities, 
-	and implementation boundaries. 

It does NOT define:

-	complete runtime behavior, 
-	orchestration engines, 
-	transport servers, 
-	policy engines, 
-	registry services, 
-	or provider business logic.

