/**
 * UCI Interoperability Test — TypeScript Validator
 * =================================================
 * Validates JSON produced by the Python implementation.
 * Uses TypeScript's UCI stack — ajv schema validation,
 * manifest parser, response parser, audit chain verifier.
 *
 * Pass criteria:
 *   - All objects pass JSON Schema (uci-spec.org)
 *   - All objects deserialise without error
 *   - Manifest passes semantic validation
 *   - Audit session chain hash is intact
 *   - Audit session session hash is valid
 *   - Response objects have correct structure
 */

import { readFileSync, existsSync } from "fs";
import { join, dirname }            from "path";
import { fileURLToPath }            from "url";
import Ajv2020                      from "ajv/dist/2020";

import { UCIManifest }              from "../uci-typescript/src/manifest.js";
import { UCIResponse }              from "../uci-typescript/src/response.js";
import { UCIAuditSession, GENESIS_HASH } from "../uci-typescript/src/audit.js";

const __dir       = dirname(fileURLToPath(import.meta.url));
const EXCHANGE    = join(__dir, "exchange");
const SCHEMAS_DIR = join(__dir, "..", "uci-typescript", "schemas");

// ── Schema setup ───────────────────────────────────────────

const ajv             = new Ajv2020({ strict: false });
const manifestSchema  = JSON.parse(readFileSync(join(SCHEMAS_DIR, "uci_manifest_v0_1.json"),      "utf-8"));
const responseSchema  = JSON.parse(readFileSync(join(SCHEMAS_DIR, "uci_response_v0_1.json"),      "utf-8"));
const auditSchema     = JSON.parse(readFileSync(join(SCHEMAS_DIR, "uci_audit_session_v0_1.json"), "utf-8"));

const validateManifest  = ajv.compile(manifestSchema);
const validateResponse  = ajv.compile(responseSchema);
const validateAudit     = ajv.compile(auditSchema);

// ── Result tracking ────────────────────────────────────────

interface CheckResult { name: string; passed: boolean; detail: string; }
const results: CheckResult[] = [];

const GREEN = "\x1b[32m";
const RED   = "\x1b[31m";
const CYAN  = "\x1b[36m";
const RST   = "\x1b[0m";

function check(name: string, passed: boolean, detail = ""): void {
  results.push({ name, passed, detail });
  const tag = passed ? `${GREEN} PASS ${RST}` : `${RED} FAIL ${RST}`;
  console.log(`  [${tag}] ${name}${!passed && detail ? `  — ${detail}` : ""}`);
}

function load(filename: string): unknown {
  const path = join(EXCHANGE, filename);
  if (!existsSync(path)) return null;
  return JSON.parse(readFileSync(path, "utf-8"));
}

// ── Main ───────────────────────────────────────────────────

async function main(): Promise<number> {
  console.log(`\n${CYAN}── TypeScript validates Python output ──────────────────${RST}`);

  // ── Manifest ───────────────────────────────────────────────
  console.log(`\n${CYAN}[1] UCIManifest (python_manifest.json)${RST}`);
  const manifestData = load("python_manifest.json") as any;
  if (manifestData) {
    check("Schema validation passes", validateManifest(manifestData),
          ajv.errorsText(validateManifest.errors ?? []));

    try {
      const manifest = UCIManifest.fromDict(manifestData);
      manifest.validate();
      check("Semantic validation passes",  true);
      check("node_id is non-empty",        !!manifest.nodeId);
      check("display_name is non-empty",   !!manifest.displayName);
      check("Has capabilities",            manifest.data.capabilities.length > 0);
      check("Has transports",              manifest.data.transports.length > 0);
      check("health block present",        "health" in manifestData);
      const VALID_TYPES = new Set(["application","service","agent","daemon","adapter",
                                   "hardware_bridge","orchestrator","policy_engine","registry"]);
      check("node_type is canonical",      VALID_TYPES.has(manifest.data.node.node_type));
    } catch (e) {
      check("Semantic validation passes",  false, String(e));
    }
  } else {
    console.log("  [SKIP] python_manifest.json not found — run Python producer first");
  }

  // ── Invocation ─────────────────────────────────────────────
  console.log(`\n${CYAN}[2] UCIInvocation (python_invocation.json)${RST}`);
  const invData = load("python_invocation.json") as any;
  if (invData) {
    check("Has uci_invocation_version", !!invData.uci_invocation_version);
    check("Has invocation_id",          !!invData.invocation_id);
    check("Has correlation_id",         !!invData.correlation_id);
    check("Has timestamp",              !!invData.timestamp);
    check("Has caller block",           !!invData.caller?.node_id);
    check("Has target block",           !!invData.target?.node_id);
    check("Has payload",                "payload" in invData);
    check("version is '0.1'",          invData.uci_invocation_version === "0.1");
  } else {
    console.log("  [SKIP] python_invocation.json not found");
  }

  // ── Response (success) ─────────────────────────────────────
  console.log(`\n${CYAN}[3] UCIResponse success (python_response_success.json)${RST}`);
  const respSuccessData = load("python_response_success.json") as any;
  if (respSuccessData) {
    check("Schema validation passes", validateResponse(respSuccessData),
          ajv.errorsText(validateResponse.errors ?? []));

    const r = UCIResponse.fromDict(respSuccessData);
    check("success == true",           r.success === true);
    check("state == 'completed'",      r.state   === "completed");
    check("output is present",         r.output  !== null && r.output !== undefined);
    check("error is null",             r.error   === null);
    check("Has invocation_id",         !!r.invocationId);
    check("Has correlation_id",        !!r.correlationId);
    check("provider.node_id non-empty",!!r.provider.node_id);
    check("governance.outcome present",!!r.governance.outcome);
    check("audit snapshot present",    !!r.audit.invocation_id);
  } else {
    console.log("  [SKIP] python_response_success.json not found");
  }

  // ── Response (failure) ─────────────────────────────────────
  console.log(`\n${CYAN}[4] UCIResponse failure (python_response_failure.json)${RST}`);
  const respFailData = load("python_response_failure.json") as any;
  if (respFailData) {
    check("Schema validation passes", validateResponse(respFailData),
          ajv.errorsText(validateResponse.errors ?? []));

    const r = UCIResponse.fromDict(respFailData);
    check("success == false",          r.success === false);
    check("state == 'denied'",         r.state   === "denied");
    check("error is present",          r.error   !== null);
    check("error.code is lowercase",   r.error!.code === r.error!.code.toLowerCase());
    check("error.code is canonical",   r.error!.code === "permission_denied");
    check("error.retryable is bool",   typeof r.error!.retryable === "boolean");
    check("error.severity is present", !!r.error!.severity);
    check("output is null",            r.output  === null);
  } else {
    console.log("  [SKIP] python_response_failure.json not found");
  }

  // ── Audit session ───────────────────────────────────────────
  console.log(`\n${CYAN}[5] UCIAuditSession (python_audit_session.json)${RST}`);
  const auditData = load("python_audit_session.json") as any;
  if (auditData) {
    check("Schema validation passes", validateAudit(auditData),
          ajv.errorsText(validateAudit.errors ?? []));

    const session = UCIAuditSession.fromDict(auditData);
    check("Has records",               session.records.length > 0);
    check("Session hash present",      !!session.sessionHash);
    check("Session hash verifies",     session.verifySessionHash());

    // Walk the chain
    let prevHash = GENESIS_HASH;
    let chainOk  = true;
    for (const record of session.records) {
      if (!record.verify(prevHash)) { chainOk = false; break; }
      prevHash = record.data.chain_hash;
    }
    check("Chain integrity intact",    chainOk);

    const eventTypes = new Set(session.records.map(r => r.data.event_type));
    check("Contains node_discovered",  eventTypes.has("node_discovered"));
    check("Contains trust_assigned",   eventTypes.has("trust_assigned"));
    check("Contains node_ready",       eventTypes.has("node_ready"));
    check("Contains invocation records",
          eventTypes.has("invocation_requested") || eventTypes.has("invocation_completed"));
  } else {
    console.log("  [SKIP] python_audit_session.json not found");
  }

  // ── Summary ─────────────────────────────────────────────────
  const total  = results.length;
  const passed = results.filter(r => r.passed).length;
  const failed = total - passed;

  console.log(`\n${"─".repeat(56)}`);
  if (failed === 0) {
    console.log(`${GREEN}  ✓ TypeScript validates Python: ${passed}/${total} checks passed${RST}`);
  } else {
    console.log(`${RED}  ✗ TypeScript validates Python: ${passed}/${total} passed, ${failed} failed${RST}`);
  }
  console.log(`${"─".repeat(56)}\n`);

  return failed === 0 ? 0 : 1;
}

main().then(process.exit).catch(console.error);
