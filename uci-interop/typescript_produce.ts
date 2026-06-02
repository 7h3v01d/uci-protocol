/**
 * UCI Interoperability Test — TypeScript Producer
 * ================================================
 * Produces the four canonical UCI objects as JSON files.
 * These are then consumed and validated by the Python implementation.
 *
 * This script does NOT know anything about Python.
 * It only knows the UCI spec and its own implementation.
 * The exchange format is plain JSON — the protocol surface.
 */

import { writeFileSync, mkdirSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";
import { randomUUID } from "crypto";

// Import from TypeScript src directly
import { UCIManifest }  from "../uci-typescript/src/manifest.js";
import { UCIInvocation } from "../uci-typescript/src/invocation.js";
import { UCIResponse, UCIErrorCode, UCIErrorSeverity } from "../uci-typescript/src/response.js";
import { AuditLog, AuditEvent } from "../uci-typescript/src/audit.js";

const __dir = dirname(fileURLToPath(import.meta.url));
const EXCHANGE_DIR = join(__dir, "exchange");
mkdirSync(EXCHANGE_DIR, { recursive: true });

function write(filename: string, data: unknown): void {
  writeFileSync(join(EXCHANGE_DIR, filename), JSON.stringify(data, null, 2));
  console.log(`  wrote ${filename}`);
}

async function main() {
  console.log("\n── TypeScript Producer ──────────────────────────────");

  // ── 1. UCIManifest ─────────────────────────────────────────
  console.log("\n[1] Producing UCIManifest...");
  const manifest = new UCIManifest({
    uci_manifest_version: "0.1",
    node: {
      node_id:      "typescript_voice_service",
      instance_id:  "ts_voice_001",
      display_name: "TypeScript Voice Service",
      node_type:    "service",
      version:      "1.0.0",
      vendor:       "Leon Priest",
      description:  "Produced by TypeScript SDK implementation.",
    },
    capabilities: [{
      capability_id: "voice_tts",
      version:       "1.0",
      category:      "audio",
      description:   "Text-to-speech synthesis.",
      tags:          ["voice", "tts", "audio"],
      actions: [{
        action_id:    "synthesize",
        description:  "Convert text to audio.",
        execution:    { mode: "sync", timeout_ms: 8000, side_effects: true },
        input_schema: { text: "string", voice_id: "string" },
        output_schema:{ audio_url: "string", duration_ms: "integer" },
        risk:         { level: "low", categories: ["read_only"] },
        permissions:  {
          required_permissions:  ["voice.tts"],
          operator_confirmation: "none",
          minimum_trust_state:   "trusted",
        },
        errors: [],
      }],
    }],
    transports: [{
      transport_id: "ipc_local",
      type:         "ipc",
      endpoint:     "uci://local/typescript_voice_service",
      security:     {},
      options:      {},
    }],
    governance: {
      default_action_policy:       "deny",
      audit_required:              true,
      operator_authority_required: false,
    },
    health:      { expose_uptime: true, expose_metrics: false },
    compliance:  { profile: "minimal" },
    audit:       { audit_enabled: true },
    extensions:  {},
  });
  manifest.validate();
  write("typescript_manifest.json", manifest.toDict());

  // ── 2. UCIInvocation ───────────────────────────────────────
  console.log("\n[2] Producing UCIInvocation...");
  const correlationId = `interop-corr-${randomUUID().slice(0, 8)}`;
  const inv = UCIInvocation.create({
    nodeId:        "typescript_voice_service",
    capabilityId:  "voice_tts",
    actionId:      "synthesize",
    payload:       { text: "UCI interoperability test.", voice_id: "niles" },
    callerNodeId:  "typescript_orchestrator",
    sessionId:     "interop-session-001",
    correlationId,
  });
  write("typescript_invocation.json", inv.toDict());

  // ── 3. UCIResponse (success) ───────────────────────────────
  console.log("\n[3] Producing UCIResponse (success)...");
  const response = UCIResponse.successResponse({
    output: {
      audio_url:   "uci://audio/interop_test_001.wav",
      duration_ms: 1560,
      voice_id:    "niles",
    },
    nodeId:            "typescript_voice_service",
    instanceId:        "ts_voice_001",
    capabilityId:      "voice_tts",
    actionId:          "synthesize",
    trustState:        "trusted",
    governanceOutcome: "allow",
    correlationId,
    actor:             "typescript_orchestrator",
  });
  write("typescript_response_success.json", response.toDict());

  // ── 4. UCIResponse (failure) ───────────────────────────────
  console.log("\n[4] Producing UCIResponse (failure)...");
  const failure = UCIResponse.failureResponse({
    error: {
      code:      UCIErrorCode.PERMISSION_DENIED,
      severity:  UCIErrorSeverity.HIGH,
      message:   "Caller lacks voice.tts permission.",
      retryable: false,
      detail:    { missing_permissions: ["voice.tts"] },
    },
    nodeId:            "typescript_voice_service",
    instanceId:        "ts_voice_001",
    capabilityId:      "voice_tts",
    actionId:          "synthesize",
    trustState:        "trusted",
    governanceOutcome: "deny",
  });
  write("typescript_response_failure.json", failure.toDict());

  // ── 5. UCIAuditSession ─────────────────────────────────────
  console.log("\n[5] Producing UCIAuditSession...");
  const audit = new AuditLog("typescript_orchestrator");

  audit.append({ eventType: AuditEvent.NODE_DISCOVERED,            nodeId: "typescript_voice_service", actor: "handshake_engine" });
  audit.append({ eventType: AuditEvent.MANIFEST_VALIDATION_PASSED, nodeId: "typescript_voice_service", actor: "handshake_engine" });
  audit.append({ eventType: AuditEvent.TRUST_ASSIGNED,             nodeId: "typescript_voice_service", actor: "policy_engine",
                 detail: { trust_state: "trusted" } });
  audit.append({ eventType: AuditEvent.CAPABILITY_MOUNTED,         nodeId: "typescript_voice_service", actor: "handshake_engine",
                 detail: { capability_id: "voice_tts" } });
  audit.append({ eventType: AuditEvent.NODE_READY,                 nodeId: "typescript_voice_service", actor: "handshake_engine",
                 detail: { mounted_capabilities: ["voice_tts"] } });
  audit.append({ eventType: AuditEvent.EXECUTION_ALLOWED,          nodeId: "typescript_voice_service", actor: "policy_engine",
                 outcome: "allow", detail: { capability_id: "voice_tts", action_id: "synthesize" } });
  audit.append({ eventType: AuditEvent.INVOCATION_REQUESTED,       nodeId: "typescript_voice_service", actor: "typescript_orchestrator",
                 detail: { capability_id: "voice_tts", action_id: "synthesize" } });
  audit.append({ eventType: AuditEvent.INVOCATION_COMPLETED,       nodeId: "typescript_voice_service", actor: "typescript_orchestrator",
                 outcome: "success" });

  const session = audit.export(true);
  write("typescript_audit_session.json", session.toDict());

  // ── Self-checks ────────────────────────────────────────────
  console.log("\n[✓] TypeScript self-checks:");
  const integrity = audit.verifyIntegrity();
  console.log(`    Audit integrity:    ${integrity.valid ? "PASS" : "FAIL"}`);
  console.log(`    Session hash valid: ${session.verifySessionHash() ? "PASS" : "FAIL"}`);

  console.log(`\n── Exchange files written to: ${EXCHANGE_DIR}`);
  console.log(`   typescript_manifest.json`);
  console.log(`   typescript_invocation.json`);
  console.log(`   typescript_response_success.json`);
  console.log(`   typescript_response_failure.json`);
  console.log(`   typescript_audit_session.json\n`);
}

main().catch(console.error);
