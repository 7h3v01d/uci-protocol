# UCI TypeScript SDK
### Universal Capability Interface · v0.1.0-alpha

TypeScript implementation of the UCI protocol.
Validates against the same JSON schemas and passes the same compliance suite as the Python reference implementation.

---

## Install

```bash
npm install uci-sdk        # when published
# or clone and build:
git clone <repo>
cd uci-typescript
npm install
npm run build
```

## Quick start

```typescript
import {
  UCIManifest, UCIInvocation, UCIResponse,
  AuditLog, UCIRegistry, PolicyEngine,
  HandshakeEngine, TrustState,
} from "uci-sdk";

// Build the engine stack
const audit    = new AuditLog("my_orchestrator");
const registry = new UCIRegistry();
const policy   = new PolicyEngine(undefined, audit);
const engine   = new HandshakeEngine(policy, registry, audit);

// Run a handshake
const result = engine.run("my_service", myManifestData);
console.log(result.trustState);          // "trusted"
console.log(result.mountedCapabilities); // ["document_search"]

// Create a canonical invocation
const inv = UCIInvocation.create({
  nodeId:        "my_service",
  capabilityId:  "document_search",
  actionId:      "search_index",
  payload:       { query: "UCI protocol" },
  callerNodeId:  "my_orchestrator",
  correlationId: "trace-abc-123",
});

// Evaluate governance
const entry    = registry.require("my_service");
const decision = policy.evaluateAction(
  entry.manifest, inv.capabilityId, inv.actionId, entry.trust
);

// Build a response
const response = UCIResponse.successResponse({
  output:            { results: [], count: 0 },
  nodeId:            "my_service",
  instanceId:        "my_service_001",
  capabilityId:      inv.capabilityId,
  actionId:          inv.actionId,
  governanceOutcome: decision.outcome,
  trustState:        entry.trust.state,
  correlationId:     inv.correlationId,
});

console.log(response.success);           // true
console.log(response.governance.outcome); // "allow"

// Export a verifiable audit session
const session = audit.export(true);
console.log(session.verifySessionHash()); // true
const wire     = session.toJSON();        // send over the wire
```

## The browser demo

Open `demo/index.html` in any browser — no server required.

Paste any UCI manifest JSON and get instant validation with precise error locations, warnings, and metadata. All three example manifests are built in.

## Tests

```bash
npm test
```

47 compliance tests · 0 failures — same rules as the Python compliance suite.

## The four protocol objects

| Object | Class | Role |
|---|---|---|
| Identity | `UCIManifest` | Who am I? What can I do? |
| Request | `UCIInvocation` | Do this, for this caller |
| Answer | `UCIResponse` | What happened? |
| Record | `UCIAuditSession` | Verifiable session history |

## Canonical error codes

All error codes are `lowercase_snake_case`:

```typescript
import { UCIErrorCode } from "uci-sdk";

UCIErrorCode.PERMISSION_DENIED      // "permission_denied"
UCIErrorCode.TRUST_FAILURE          // "trust_failure"
UCIErrorCode.CONFIRMATION_REQUIRED  // "confirmation_required"
UCIErrorCode.EXECUTION_ERROR        // "execution_error"
UCIErrorCode.VERSION_MISMATCH       // "version_mismatch"
```

## Spec

Full specification: [`docs/`](../docs/) in the Python reference implementation.
JSON Schemas: [`schemas/`](schemas/)

---

*UCI TypeScript SDK · v0.1.0-alpha · © Leon Priest · MIT*
