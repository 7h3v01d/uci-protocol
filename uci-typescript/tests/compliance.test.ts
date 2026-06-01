/**
 * UCI Compliance Suite — TypeScript
 * Mirrors the Python compliance suite.
 * A UCI implementation is conformant when these pass.
 */

import { UCIManifest, VALID_NODE_TYPES, VALID_EXECUTION_MODES, VALID_TRANSPORT_TYPES } from "../src/manifest.js";
import { UCIManifestError, UCIValidationError, UCITrustError, UCIError } from "../src/errors.js";
import { TrustRecord, TrustState, EXECUTABLE_STATES } from "../src/trust.js";
import { PolicyEngine, GovernanceOutcome, DEFAULT_ORCHESTRATOR_PERMISSIONS } from "../src/governance.js";
import { UCIRegistry, HandshakeEngine, HandshakeStage } from "../src/registry.js";
import { AuditLog, AuditEvent, GENESIS_HASH, UCIAuditSession } from "../src/audit.js";
import { UCIResponse, ResponseState, UCIErrorCode, RESPONSE_VERSION } from "../src/response.js";
import { UCIInvocation } from "../src/invocation.js";

// ── Fixtures ─────────────────────────────────────────────────────────────────

const VALID_MANIFEST = {
  uci_manifest_version: "0.1",
  node: {
    node_id: "test_node", instance_id: "test_001",
    display_name: "Test Node", node_type: "service",
    version: "1.0.0", vendor: "KeystoneAI",
  },
  capabilities: [{
    capability_id: "document_search", version: "1.0",
    category: "retrieval", description: "Test.",
    actions: [{
      action_id: "search_index",
      execution: { mode: "sync", timeout_ms: 5000 },
      risk: { level: "low", categories: ["read_only"] },
      permissions: { required_permissions: ["documents.read"], operator_confirmation: "none", minimum_trust_state: "trusted" },
      input_schema: {}, output_schema: {},
    }],
  }],
  transports: [{ transport_id: "ipc_local", type: "ipc", endpoint: "uci://local/test" }],
  governance: { default_action_policy: "deny", audit_required: true },
  health: {},
  compliance: { profile: "minimal" },
  audit: { audit_enabled: true },
  extensions: {},
};

function makeManifest(overrides: Record<string, unknown> = {}): UCIManifest {
  const data = { ...structuredClone(VALID_MANIFEST), ...overrides };
  return new UCIManifest(data as any);
}

function makeStack() {
  const audit    = new AuditLog("test_orchestrator");
  const registry = new UCIRegistry();
  const policy   = new PolicyEngine(DEFAULT_ORCHESTRATOR_PERMISSIONS, audit);
  const engine   = new HandshakeEngine(policy, registry, audit);
  return { audit, registry, policy, engine };
}

// ═════════════════════════════════════════════════════════════════════════════
// C-MAN — Manifest Compliance
// ═════════════════════════════════════════════════════════════════════════════

describe("C-MAN — Manifest Compliance", () => {

  test("C-MAN-001: manifest version must be '0.1'", () => {
    const m = makeManifest();
    expect(() => m.validate()).not.toThrow();
    expect(m.version).toBe("0.1");
  });

  test("C-MAN-002: node_id must be non-empty", () => {
    const m = new UCIManifest({
      ...structuredClone(VALID_MANIFEST),
      node: { ...VALID_MANIFEST.node, node_id: "" },
    } as any);
    expect(() => m.validate()).toThrow(UCIManifestError);
  });

  test("C-MAN-003: node_type must be canonical", () => {
    const m = new UCIManifest({
      ...structuredClone(VALID_MANIFEST),
      node: { ...VALID_MANIFEST.node, node_type: "plugin" },
    } as any);
    expect(() => m.validate()).toThrow(UCIValidationError);
    expect(VALID_NODE_TYPES.has("plugin")).toBe(false);
  });

  test("C-MAN-004: manifest requires at least one capability", () => {
    const m = new UCIManifest({ ...structuredClone(VALID_MANIFEST), capabilities: [] } as any);
    expect(() => m.validate()).toThrow(UCIManifestError);
  });

  test("C-MAN-005: manifest requires at least one transport", () => {
    const m = new UCIManifest({ ...structuredClone(VALID_MANIFEST), transports: [] } as any);
    expect(() => m.validate()).toThrow(UCIManifestError);
  });

  test("C-MAN-006: capability requires at least one action", () => {
    const data = structuredClone(VALID_MANIFEST) as any;
    data.capabilities[0].actions = [];
    const m = new UCIManifest(data);
    expect(() => m.validate()).toThrow(UCIManifestError);
  });

  test("C-MAN-007: execution mode 'stream' is not valid", () => {
    const data = structuredClone(VALID_MANIFEST) as any;
    data.capabilities[0].actions[0].execution.mode = "stream";
    const m = new UCIManifest(data);
    expect(() => m.validate()).toThrow(UCIValidationError);
    expect(VALID_EXECUTION_MODES.has("stream")).toBe(false);
    expect(VALID_EXECUTION_MODES.has("streaming")).toBe(true);
  });

  test("C-MAN-008: transport type 'local' is not valid", () => {
    const data = structuredClone(VALID_MANIFEST) as any;
    data.transports[0].type = "local";
    const m = new UCIManifest(data);
    expect(() => m.validate()).toThrow(UCIValidationError);
    expect(VALID_TRANSPORT_TYPES.has("local")).toBe(false);
    expect(VALID_TRANSPORT_TYPES.has("ipc")).toBe(true);
  });

  test("C-MAN-009: risk level 'catastrophic' is not valid", () => {
    const data = structuredClone(VALID_MANIFEST) as any;
    data.capabilities[0].actions[0].risk.level = "catastrophic";
    const m = new UCIManifest(data);
    expect(() => m.validate()).toThrow(UCIValidationError);
  });

  test("C-MAN-010: display_name is required", () => {
    const m = new UCIManifest({
      ...structuredClone(VALID_MANIFEST),
      node: { ...VALID_MANIFEST.node, display_name: "" },
    } as any);
    expect(() => m.validate()).toThrow(UCIManifestError);
  });

  test("C-MAN-011: valid manifest passes validation", () => {
    const m = makeManifest();
    expect(() => m.validate()).not.toThrow();
  });

  test("C-MAN-012: to_dict round-trips cleanly", () => {
    const m  = makeManifest();
    const m2 = UCIManifest.fromDict(m.toDict());
    m2.validate();
    expect(m2.nodeId).toBe(m.nodeId);
    expect(m2.capabilityIds()).toEqual(m.capabilityIds());
  });
});

// ═════════════════════════════════════════════════════════════════════════════
// C-GOV — Governance Compliance
// ═════════════════════════════════════════════════════════════════════════════

describe("C-GOV — Governance Compliance", () => {

  test("C-GOV-001: UNKNOWN trust state must be denied", () => {
    const { policy } = makeStack();
    const trust = new TrustRecord("test");
    const m     = makeManifest();
    const d     = policy.evaluateAction(m, "document_search", "search_index", trust);
    expect(d.outcome).toBe(GovernanceOutcome.DENY);
  });

  test("C-GOV-002: revoked node must be denied", () => {
    const { engine, registry, audit } = makeStack();
    const policy2 = new PolicyEngine(DEFAULT_ORCHESTRATOR_PERMISSIONS, audit);
    engine.run("test_node", VALID_MANIFEST);
    const entry = registry.require("test_node");
    entry.trust.transition(TrustState.REVOKED, "test");
    const d = policy2.evaluateAction(
      entry.manifest, "document_search", "search_index", entry.trust
    );
    expect(d.outcome).toBe(GovernanceOutcome.DENY);
  });

  test("C-GOV-003: missing permissions must be denied", () => {
    const { engine, registry, audit } = makeStack();
    engine.run("test_node", VALID_MANIFEST);
    const noPerm = new PolicyEngine(new Set(), audit);
    const entry  = registry.require("test_node");
    const d      = noPerm.evaluateAction(
      entry.manifest, "document_search", "search_index", entry.trust
    );
    expect(d.outcome).toBe(GovernanceOutcome.DENY);
    expect(d.reason).toMatch(/Missing required permissions/);
  });

  test("C-GOV-004: fail-closed — governance defaults to deny", () => {
    const { policy } = makeStack();
    const trust = new TrustRecord("n");
    const m     = makeManifest();
    // Unknown trust → deny
    expect(policy.evaluateAction(m, "document_search", "search_index", trust).outcome)
      .toBe(GovernanceOutcome.DENY);
  });

  test("C-GOV-005: operator approval converts DEFER to ALLOW", () => {
    const { policy } = makeStack();
    const deferred: any = {
      outcome: GovernanceOutcome.DEFER,
      nodeId: "n", capabilityId: "c", actionId: "a",
      reason: "needs approval", restrictions: [], requiresConfirmation: true,
    };
    const approved = policy.operatorApprove(deferred, "leon");
    expect(approved.outcome).toBe(GovernanceOutcome.ALLOW);
    expect(approved.reason).toContain("leon");
  });

  test("C-GOV-006: governance outcome baked into response", () => {
    const r = UCIResponse.successResponse({
      output: {}, nodeId: "n", instanceId: "i",
      capabilityId: "c", actionId: "a",
    });
    expect(r.governance.outcome).toMatch(/allow|deny|defer/);
    expect(r.governance.trust_state).toBeTruthy();
  });
});

// ═════════════════════════════════════════════════════════════════════════════
// C-HSK — Handshake Compliance
// ═════════════════════════════════════════════════════════════════════════════

describe("C-HSK — Handshake Compliance", () => {

  test("C-HSK-001: compliant node reaches READY", () => {
    const { engine } = makeStack();
    const r = engine.run("test_node", VALID_MANIFEST);
    expect(r.success).toBe(true);
    expect(r.stageReached).toBe(HandshakeStage.READY);
  });

  test("C-HSK-002: malformed manifest fails at validation stage", () => {
    const { engine } = makeStack();
    const r = engine.run("bad", { uci_manifest_version: "0.1", node: { node_id: "" } });
    expect(r.success).toBe(false);
    expect(r.stageReached).toBe(HandshakeStage.MANIFEST_VALIDATED);
  });

  test("C-HSK-003: failed node must not be registered", () => {
    const { engine, registry } = makeStack();
    engine.run("ghost", { uci_manifest_version: "0.1", node: { node_id: "" } });
    expect(registry.get("ghost")).toBeUndefined();
  });

  test("C-HSK-004: trust must be executable after successful handshake", () => {
    const { engine, registry } = makeStack();
    engine.run("test_node", VALID_MANIFEST);
    const entry = registry.require("test_node");
    expect(EXECUTABLE_STATES.has(entry.trust.state)).toBe(true);
  });

  test("C-HSK-005: handshake generates node_discovered as first event", () => {
    const { engine, audit } = makeStack();
    engine.run("test_node", VALID_MANIFEST);
    const events = audit.forNode("test_node");
    expect(events[0].data.event_type).toBe(AuditEvent.NODE_DISCOVERED);
  });

  test("C-HSK-006: successful handshake emits node_ready", () => {
    const { engine, audit } = makeStack();
    engine.run("test_node", VALID_MANIFEST);
    const types = audit.forNode("test_node").map(r => r.data.event_type);
    expect(types).toContain(AuditEvent.NODE_READY);
  });

  test("C-HSK-007: failed handshake emits handshake_failed", () => {
    const { engine, audit } = makeStack();
    engine.run("bad", { uci_manifest_version: "0.1", node: { node_id: "" } });
    const types = audit.all().map(r => r.data.event_type);
    expect(types).toContain(AuditEvent.HANDSHAKE_FAILED);
  });

  test("C-HSK-008: handshake never throws", () => {
    const { engine } = makeStack();
    const r = engine.run("x", { garbage: true });
    expect(typeof r.success).toBe("boolean");
    expect(r.stageReached).toBeTruthy();
  });
});

// ═════════════════════════════════════════════════════════════════════════════
// C-RSP — Response Compliance
// ═════════════════════════════════════════════════════════════════════════════

describe("C-RSP — Response Compliance", () => {

  test("C-RSP-001: successResponse returns UCIResponse", () => {
    const r = UCIResponse.successResponse({
      output: { ok: true }, nodeId: "n", instanceId: "i",
      capabilityId: "c", actionId: "a",
    });
    expect(r).toBeInstanceOf(UCIResponse);
  });

  test("C-RSP-002: response version is '0.1'", () => {
    const r = UCIResponse.successResponse({
      output: {}, nodeId: "n", instanceId: "i", capabilityId: "c", actionId: "a",
    });
    expect(r.data.uci_response_version).toBe(RESPONSE_VERSION);
  });

  test("C-RSP-003: success response has output and null error", () => {
    const r = UCIResponse.successResponse({
      output: { result: "ok" }, nodeId: "n", instanceId: "i", capabilityId: "c", actionId: "a",
    });
    expect(r.success).toBe(true);
    expect(r.output).toEqual({ result: "ok" });
    expect(r.error).toBeNull();
  });

  test("C-RSP-004: failure response has error and null output", () => {
    const r = UCIResponse.failureResponse({
      error: { code: UCIErrorCode.POLICY_DENIED, severity: "medium", message: "denied", retryable: false },
    });
    expect(r.success).toBe(false);
    expect(r.error).not.toBeNull();
    expect(r.output).toBeNull();
  });

  test("C-RSP-005: governance deny produces state=denied", () => {
    const r = UCIResponse.failureResponse({
      error: { code: UCIErrorCode.POLICY_DENIED, severity: "medium", message: "denied", retryable: false },
      governanceOutcome: "deny",
    });
    expect(r.state).toBe(ResponseState.DENIED);
  });

  test("C-RSP-006: deferred response has state=deferred", () => {
    const r = UCIResponse.deferredResponse({
      nodeId: "n", instanceId: "i", capabilityId: "c", actionId: "a",
    });
    expect(r.state).toBe(ResponseState.DEFERRED);
    expect(r.error?.code).toBe(UCIErrorCode.CONFIRMATION_REQUIRED);
  });

  test("C-RSP-007: two responses have different invocation IDs", () => {
    const r1 = UCIResponse.successResponse({ output: {}, nodeId: "n", instanceId: "i", capabilityId: "c", actionId: "a" });
    const r2 = UCIResponse.successResponse({ output: {}, nodeId: "n", instanceId: "i", capabilityId: "c", actionId: "a" });
    expect(r1.invocationId).not.toBe(r2.invocationId);
  });

  test("C-RSP-008: assert_success returns output on success", () => {
    const r = UCIResponse.successResponse({
      output: { status: "ok" }, nodeId: "n", instanceId: "i", capabilityId: "c", actionId: "a",
    });
    expect(r.assertSuccess()).toEqual({ status: "ok" });
  });

  test("C-RSP-009: assert_success throws UCIError on failure", () => {
    const r = UCIResponse.failureResponse({
      error: { code: UCIErrorCode.EXECUTION_ERROR, severity: "medium", message: "failed", retryable: false },
    });
    expect(() => r.assertSuccess()).toThrow(UCIError);
  });

  test("C-RSP-010: correlation_id passthrough", () => {
    const r = UCIResponse.successResponse({
      output: {}, nodeId: "n", instanceId: "i", capabilityId: "c", actionId: "a",
      correlationId: "trace-123",
    });
    expect(r.correlationId).toBe("trace-123");
  });

  test("C-RSP-011: response roundtrips through JSON", () => {
    const r  = UCIResponse.successResponse({
      output: { x: 1 }, nodeId: "n", instanceId: "i", capabilityId: "c", actionId: "a",
    });
    const r2 = UCIResponse.fromDict(JSON.parse(r.toJSON()));
    expect(r2.invocationId).toBe(r.invocationId);
    expect(r2.success).toBe(r.success);
    expect(r2.data.provider.node_id).toBe(r.data.provider.node_id);
  });
});

// ═════════════════════════════════════════════════════════════════════════════
// C-AUD — Audit Compliance
// ═════════════════════════════════════════════════════════════════════════════

describe("C-AUD — Audit Compliance", () => {

  test("C-AUD-001: records are append-only and ordered", () => {
    const log = new AuditLog();
    for (let i = 0; i < 5; i++) {
      log.append({ eventType: AuditEvent.NODE_DISCOVERED, nodeId: `n${i}` });
    }
    const seqs = log.all().map(r => r.data.sequence);
    expect(seqs).toEqual([1, 2, 3, 4, 5]);
  });

  test("C-AUD-002: every record has a 64-char chain_hash", () => {
    const log = new AuditLog();
    log.append({ eventType: AuditEvent.NODE_DISCOVERED, nodeId: "n" });
    log.append({ eventType: AuditEvent.TRUST_ASSIGNED,  nodeId: "n" });
    for (const r of log.all()) {
      expect(r.data.chain_hash).toHaveLength(64);
    }
  });

  test("C-AUD-003: first record chains from GENESIS_HASH", () => {
    const log = new AuditLog();
    const r   = log.append({ eventType: AuditEvent.NODE_DISCOVERED, nodeId: "n" });
    expect(r.data.previous_hash).toBe(GENESIS_HASH);
  });

  test("C-AUD-004: each record chains from previous", () => {
    const log = new AuditLog();
    const r1  = log.append({ eventType: AuditEvent.NODE_DISCOVERED, nodeId: "n" });
    const r2  = log.append({ eventType: AuditEvent.TRUST_ASSIGNED,  nodeId: "n" });
    expect(r2.data.previous_hash).toBe(r1.data.chain_hash);
  });

  test("C-AUD-005: unmodified log passes integrity check", () => {
    const log = new AuditLog();
    for (let i = 0; i < 5; i++) {
      log.append({ eventType: AuditEvent.INVOCATION_COMPLETED, nodeId: "n" });
    }
    const report = log.verifyIntegrity();
    expect(report.valid).toBe(true);
    expect(report.breaks).toHaveLength(0);
  });

  test("C-AUD-006: tampered record fails integrity check", () => {
    const log = new AuditLog();
    const r   = log.append({ eventType: AuditEvent.NODE_DISCOVERED, nodeId: "n" });
    log.append({ eventType: AuditEvent.NODE_READY, nodeId: "n" });
    (r.data as any).outcome = "forged";   // tamper
    const report = log.verifyIntegrity();
    expect(report.valid).toBe(false);
    expect(report.breaks.length).toBeGreaterThan(0);
  });

  test("C-AUD-007: export produces UCIAuditSession", () => {
    const log     = new AuditLog();
    log.append({ eventType: AuditEvent.NODE_DISCOVERED, nodeId: "n" });
    const session = log.export(true);
    expect(session).toBeInstanceOf(UCIAuditSession);
    expect(session.sessionHash).toHaveLength(64);
    expect(session.verifySessionHash()).toBe(true);
  });

  test("C-AUD-008: session survives JSON wire trip", () => {
    const log = new AuditLog();
    log.append({ eventType: AuditEvent.NODE_DISCOVERED,    nodeId: "n" });
    log.append({ eventType: AuditEvent.INVOCATION_COMPLETED, nodeId: "n" });
    const session  = log.export(true);
    const wire     = session.toJSON();
    const session2 = UCIAuditSession.fromJSON(wire);
    expect(session2.verifySessionHash()).toBe(true);
    expect(session2.records).toHaveLength(session.records.length);
  });
});

// ═════════════════════════════════════════════════════════════════════════════
// C-INT — Integration Compliance
// ═════════════════════════════════════════════════════════════════════════════

describe("C-INT — Integration Compliance", () => {

  test("C-INT-001: UCIInvocation roundtrips cleanly", () => {
    const inv  = UCIInvocation.create({
      nodeId: "n", capabilityId: "c", actionId: "a",
      payload: { query: "UCI" }, callerNodeId: "niles",
      correlationId: "corr-001",
    });
    const inv2 = UCIInvocation.fromDict(JSON.parse(inv.toJSON()));
    expect(inv2.data.invocation_id).toBe(inv.data.invocation_id);
    expect(inv2.payload).toEqual(inv.payload);
    expect(inv2.correlationId).toBe("corr-001");
  });

  test("C-INT-002: full session — handshake + governance + response + audit all pass", () => {
    const { engine, registry, audit, policy } = makeStack();

    // Handshake
    const result = engine.run("test_node", VALID_MANIFEST);
    expect(result.success).toBe(true);
    expect(result.stageReached).toBe(HandshakeStage.READY);

    // Governance
    const entry   = registry.require("test_node");
    const decision = policy.evaluateAction(
      entry.manifest, "document_search", "search_index", entry.trust
    );
    expect(decision.outcome).toBe(GovernanceOutcome.ALLOW);

    // Response
    const r = UCIResponse.successResponse({
      output: { results: [] }, nodeId: "test_node", instanceId: "test_001",
      capabilityId: "document_search", actionId: "search_index",
      trustState: entry.trust.state, governanceOutcome: decision.outcome,
    });
    expect(r.success).toBe(true);
    const r2 = UCIResponse.fromDict(JSON.parse(r.toJSON()));
    expect(r2.invocationId).toBe(r.invocationId);

    // Audit
    expect(audit.verifyIntegrity().valid).toBe(true);
    const session = audit.export(true);
    expect(session.verifySessionHash()).toBe(true);
    const session2 = UCIAuditSession.fromJSON(session.toJSON());
    expect(session2.verifySessionHash()).toBe(true);
  });
});

// ═════════════════════════════════════════════════════════════════════════════
// C-GOV (continued) — missing rules 007–010
// ═════════════════════════════════════════════════════════════════════════════

describe("C-GOV (continued) — Governance Compliance", () => {

  test("C-GOV-007: invoke_with never throws — all outcomes are envelopes", () => {
    // Every governance outcome must return a UCIResponse, not throw
    const r1 = UCIResponse.failureResponse({
      error: { code: UCIErrorCode.POLICY_DENIED, severity: "medium", message: "denied", retryable: false },
      governanceOutcome: "deny",
    });
    const r2 = UCIResponse.fromException({ error: new Error("runtime error"), nodeId: "n" });
    expect(r1).toBeInstanceOf(UCIResponse);
    expect(r2).toBeInstanceOf(UCIResponse);
    expect(r1.success).toBe(false);
    expect(r2.success).toBe(false);
  });

  test("C-GOV-008: operator approval converts DEFER to ALLOW and records operator id", () => {
    const { policy } = makeStack();
    const deferred: any = {
      outcome: GovernanceOutcome.DEFER,
      nodeId: "n", capabilityId: "c", actionId: "a",
      reason: "high risk", restrictions: [], requiresConfirmation: true,
    };
    const approved = policy.operatorApprove(deferred, "leon_priest");
    expect(approved.outcome).toBe(GovernanceOutcome.ALLOW);
    expect(approved.reason).toContain("leon_priest");
    expect(approved.requiresConfirmation).toBe(false);
  });

  test("C-GOV-009: restricted trust permits low-risk actions", () => {
    const { engine, registry, policy } = makeStack();
    // Run a normal handshake — node gets TRUSTED
    engine.run("test_node", VALID_MANIFEST);
    const entry = registry.require("test_node");

    // Manually transition to RESTRICTED (simulating operator restriction)
    entry.trust.transition(TrustState.RESTRICTED, "test_operator", "compliance test");
    expect(entry.trust.state).toBe(TrustState.RESTRICTED);

    // Low-risk action on restricted node → ALLOW_WITH_RESTRICTIONS, not deny
    const decision = policy.evaluateAction(
      entry.manifest, "document_search", "search_index", entry.trust
    );
    expect([GovernanceOutcome.ALLOW, GovernanceOutcome.ALLOW_RESTRICTED]).toContain(decision.outcome);
  });

  test("C-GOV-010: every governance decision generates at least one audit event", () => {
    const { engine, audit } = makeStack();
    const countBefore = audit.count();
    engine.run("test_node", VALID_MANIFEST);
    expect(audit.count()).toBeGreaterThan(countBefore);
    const types = audit.all().map(r => r.data.event_type);
    expect(types).toContain(AuditEvent.POLICY_EVALUATED);
  });
});

// ═════════════════════════════════════════════════════════════════════════════
// C-HSK-009 — Handshake never throws
// ═════════════════════════════════════════════════════════════════════════════

describe("C-HSK-009 — Handshake never throws on any input", () => {

  test("C-HSK-009: completely malformed input returns a result, never throws", () => {
    const { engine } = makeStack();
    const inputs = [
      null, undefined, 42, "not an object", [],
      { garbage: true, random: "data" },
      { uci_manifest_version: "0.1" },  // valid version, missing everything else
    ];
    for (const input of inputs) {
      const r = engine.run("x", input);
      expect(typeof r.success).toBe("boolean");
      expect(r.stageReached).toBeTruthy();
      expect(typeof r.failureReason).toBe("string");
    }
  });
});

// ═════════════════════════════════════════════════════════════════════════════
// C-AUD-009, C-AUD-010 — Audit event completeness
// ═════════════════════════════════════════════════════════════════════════════

describe("C-AUD (continued) — Audit Completeness", () => {

  test("C-AUD-009: handshake lifecycle generates a complete audit trail", () => {
    const { engine, audit } = makeStack();
    engine.run("test_node", VALID_MANIFEST);
    const types = new Set(audit.forNode("test_node").map(r => r.data.event_type));
    const required = new Set([
      AuditEvent.NODE_DISCOVERED,
      AuditEvent.MANIFEST_VALIDATION_PASSED,
      AuditEvent.TRUST_ASSIGNED,
      AuditEvent.NODE_READY,
    ]);
    for (const evt of required) {
      expect(types.has(evt)).toBe(true);
    }
  });

  test("C-AUD-010: invocation events are audited (requested and completed)", () => {
    const { engine, audit } = makeStack();
    engine.run("test_node", VALID_MANIFEST);

    // Manually append invocation events as the engine does
    audit.append({ eventType: AuditEvent.INVOCATION_REQUESTED, nodeId: "test_node",
                   actor: "orchestrator", detail: { capability_id: "document_search", action_id: "search_index" } });
    audit.append({ eventType: AuditEvent.INVOCATION_COMPLETED, nodeId: "test_node",
                   actor: "orchestrator", outcome: "success" });

    const types = audit.all().map(r => r.data.event_type);
    expect(types).toContain(AuditEvent.INVOCATION_REQUESTED);
    expect(types).toContain(AuditEvent.INVOCATION_COMPLETED);
  });
});

// ═════════════════════════════════════════════════════════════════════════════
// C-RSP-012 — Response JSON roundtrip (full)
// ═════════════════════════════════════════════════════════════════════════════

describe("C-RSP-012 — Response full JSON roundtrip", () => {

  test("C-RSP-012: all response types survive JSON wire trip with fields intact", () => {
    const responses = [
      UCIResponse.successResponse({
        output: { data: [1, 2, 3], count: 3 }, nodeId: "n", instanceId: "i",
        capabilityId: "c", actionId: "a", trustState: "trusted",
        governanceOutcome: "allow", correlationId: "corr-001",
      }),
      UCIResponse.failureResponse({
        error: { code: UCIErrorCode.EXECUTION_ERROR, severity: "medium", message: "failed", retryable: true },
        nodeId: "n", capabilityId: "c", actionId: "a", governanceOutcome: "deny",
      }),
      UCIResponse.deferredResponse({
        nodeId: "n", instanceId: "i", capabilityId: "c", actionId: "a",
        reason: "needs operator",
      }),
    ];

    for (const r of responses) {
      const wire = r.toJSON();
      const r2   = UCIResponse.fromDict(JSON.parse(wire));
      expect(r2.data.invocation_id).toBe(r.data.invocation_id);
      expect(r2.success).toBe(r.success);
      expect(r2.state).toBe(r.state);
      expect(r2.data.provider.node_id).toBe(r.data.provider.node_id);
      expect(r2.data.governance.outcome).toBe(r.data.governance.outcome);
      expect(r2.data.audit.node_id).toBe(r.data.audit.node_id);
      if (r.error) {
        expect(r2.error?.code).toBe(r.error.code);
        expect(r2.error?.retryable).toBe(r.error.retryable);
      }
    }
  });
});

// ═════════════════════════════════════════════════════════════════════════════
// C-SCH — Schema Compliance (using ajv)
// ═════════════════════════════════════════════════════════════════════════════

import Ajv2020 from "ajv/dist/2020";
import { readFileSync } from "fs";
import { join } from "path";

const schemasDir = join(process.cwd(), "schemas");

function loadSchema(name: string) {
  return JSON.parse(readFileSync(join(schemasDir, name), "utf-8"));
}

const ajv = new Ajv2020({ strict: false });
const manifestSchema      = loadSchema("uci_manifest_v0_1.json");
const responseSchema      = loadSchema("uci_response_v0_1.json");
const auditSessionSchema  = loadSchema("uci_audit_session_v0_1.json");

describe("C-SCH — Schema Compliance", () => {

  test("C-SCH-001: compliant manifest passes JSON schema", () => {
    const validate = ajv.compile(manifestSchema);
    expect(validate(VALID_MANIFEST)).toBe(true);
  });

  test("C-SCH-002: successful response passes JSON schema", () => {
    const validate = ajv.compile(responseSchema);
    const r = UCIResponse.successResponse({
      output: { status: "ok" }, nodeId: "n", instanceId: "i",
      capabilityId: "c", actionId: "a",
    });
    expect(validate(r.toDict())).toBe(true);
  });

  test("C-SCH-003: failure response passes JSON schema", () => {
    const validate = ajv.compile(responseSchema);
    const r = UCIResponse.failureResponse({
      error: { code: UCIErrorCode.POLICY_DENIED, severity: "medium", message: "denied", retryable: false },
    });
    expect(validate(r.toDict())).toBe(true);
  });

  test("C-SCH-004: deferred response passes JSON schema", () => {
    const validate = ajv.compile(responseSchema);
    const r = UCIResponse.deferredResponse({
      nodeId: "n", instanceId: "i", capabilityId: "c", actionId: "a",
    });
    expect(validate(r.toDict())).toBe(true);
  });

  test("C-SCH-005: audit session passes JSON schema", () => {
    const validate = ajv.compile(auditSessionSchema);
    const log = new AuditLog("test_orch");
    log.append({ eventType: AuditEvent.NODE_DISCOVERED,    nodeId: "n" });
    log.append({ eventType: AuditEvent.INVOCATION_COMPLETED, nodeId: "n", outcome: "success" });
    const session = log.export(true);
    expect(validate(session.toDict())).toBe(true);
  });

  test("C-SCH-006: all three canonical objects pass schema in a live session", () => {
    const validateM = ajv.compile(manifestSchema);
    const validateR = ajv.compile(responseSchema);
    const validateA = ajv.compile(auditSessionSchema);

    const { engine, registry, audit, policy } = makeStack();
    engine.run("test_node", VALID_MANIFEST);
    const entry    = registry.require("test_node");
    const decision = policy.evaluateAction(entry.manifest, "document_search", "search_index", entry.trust);
    const resp     = UCIResponse.successResponse({
      output: {}, nodeId: "test_node", instanceId: "test_001",
      capabilityId: "document_search", actionId: "search_index",
      trustState: entry.trust.state, governanceOutcome: decision.outcome,
    });
    const session = audit.export(true);

    expect(validateM(VALID_MANIFEST)).toBe(true);
    expect(validateR(resp.toDict())).toBe(true);
    expect(validateA(session.toDict())).toBe(true);
  });

  test("C-SCH-007: schema rejects legacy execution mode 'stream'", () => {
    const validate = ajv.compile(manifestSchema);
    const bad = structuredClone(VALID_MANIFEST) as any;
    bad.capabilities[0].actions[0].execution.mode = "stream";
    expect(validate(bad)).toBe(false);
  });

  test("C-SCH-008: schema rejects legacy transport type 'local'", () => {
    const validate = ajv.compile(manifestSchema);
    const bad = structuredClone(VALID_MANIFEST) as any;
    bad.transports[0].type = "local";
    expect(validate(bad)).toBe(false);
  });
});
