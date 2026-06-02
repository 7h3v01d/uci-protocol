#!/usr/bin/env python3
"""
UCI Interoperability Test Runner
=================================
Orchestrates the full cross-language interoperability proof.

Run with:
    python run_interop.py

Prerequisites:
    cd uci-typescript && npm ci && npm run build

What this does:
    1. Python produces 5 canonical UCI objects as JSON
    2. TypeScript (plain Node.js, no ts-node) validates Python output
    3. TypeScript (plain Node.js, from dist/) produces 5 canonical objects
    4. Python validates TypeScript output
    5. Prints a final interoperability verdict

No ts-node required. Steps 2 and 3 run against compiled dist/ output.
"""

import subprocess
import sys
import os

HERE   = os.path.dirname(os.path.abspath(__file__))
TS_DIR = os.path.join(HERE, "..", "uci-typescript")
PY_DIR = os.path.join(HERE, "..", "uci-python-v2")

GREEN = "\033[32m"
RED   = "\033[31m"
CYAN  = "\033[36m"
BOLD  = "\033[1m"
DIM   = "\033[2m"
RST   = "\033[0m"


def banner():
    print()
    print(f"{BOLD}{CYAN}{'═'*60}{RST}")
    print(f"{BOLD}{CYAN}  UCI Interoperability Test{RST}")
    print(f"{BOLD}{CYAN}  Python ↔ TypeScript{RST}")
    print(f"{BOLD}{CYAN}{'═'*60}{RST}")


def ensure_ts_built() -> bool:
    """Ensure TypeScript is compiled to dist/. Build if needed."""
    dist = os.path.join(TS_DIR, "dist", "index.js")
    if os.path.isfile(dist):
        return True
    print(f"\n{CYAN}  Building TypeScript...{RST}")
    result = subprocess.run(
        ["npm", "run", "build"],
        cwd=TS_DIR, capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"{RED}  TypeScript build failed:{RST}")
        print(result.stderr[:400])
        return False
    print(f"  {GREEN}✓{RST} TypeScript build complete")
    return True


def run_step(label: str, cmd: list[str], cwd: str) -> bool:
    print(f"\n{BOLD}── {label}{RST}")
    result = subprocess.run(cmd, cwd=cwd)
    return result.returncode == 0


def ts_producer_script() -> str:
    """
    Inline Node.js ESM script that produces TypeScript canonical objects.
    Imports from dist/ — no ts-node, no compilation at runtime.
    """
    exchange = os.path.join(HERE, "exchange").replace("\\", "/")
    return f"""
import {{ writeFileSync, mkdirSync }} from "fs";
import {{ join }} from "path";
import {{ randomUUID }} from "crypto";
import {{ UCIManifest }} from "./dist/manifest.js";
import {{ UCIInvocation }} from "./dist/invocation.js";
import {{ UCIResponse, UCIErrorCode, UCIErrorSeverity }} from "./dist/response.js";
import {{ AuditLog, AuditEvent }} from "./dist/audit.js";

const EXCHANGE = "{exchange}";
mkdirSync(EXCHANGE, {{ recursive: true }});
const write = (f, d) => writeFileSync(join(EXCHANGE,f), JSON.stringify(d,null,2));

console.log("\\n── TypeScript Producer ──────────────────────────────");

// 1. Manifest
console.log("\\n[1] Producing UCIManifest...");
const manifest = new UCIManifest({{
  uci_manifest_version:"0.1",
  node:{{ node_id:"typescript_voice_service", instance_id:"ts_voice_001",
         display_name:"TypeScript Voice Service", node_type:"service",
         version:"1.0.0", vendor:"Leon Priest", description:"Produced by TypeScript SDK." }},
  capabilities:[{{ capability_id:"voice_tts", version:"1.0", category:"audio",
    description:"Text-to-speech.", tags:["voice","tts"],
    actions:[{{ action_id:"synthesize", description:"Convert text to audio.",
      execution:{{mode:"sync",timeout_ms:8000,side_effects:true}},
      input_schema:{{text:"string",voice_id:"string"}},
      output_schema:{{audio_url:"string",duration_ms:"integer"}},
      risk:{{level:"low",categories:["read_only"]}},
      permissions:{{required_permissions:["voice.tts"],operator_confirmation:"none",minimum_trust_state:"trusted"}},
      errors:[] }}] }}],
  transports:[{{ transport_id:"ipc_local",type:"ipc",
    endpoint:"uci://local/typescript_voice_service",security:{{}},options:{{}} }}],
  governance:{{ default_action_policy:"deny",audit_required:true,operator_authority_required:false }},
  health:{{ expose_uptime:true,expose_metrics:false }},
  compliance:{{profile:"minimal"}}, audit:{{audit_enabled:true}}, extensions:{{}},
}});
manifest.validate();
write("typescript_manifest.json", manifest.toDict());
console.log("  wrote typescript_manifest.json");

// 2. Invocation
console.log("\\n[2] Producing UCIInvocation...");
const corrId = `interop-corr-${{randomUUID().slice(0,8)}}`;
const inv = UCIInvocation.create({{ nodeId:"typescript_voice_service", capabilityId:"voice_tts",
  actionId:"synthesize", payload:{{text:"UCI interop.",voice_id:"niles"}},
  callerNodeId:"typescript_orchestrator", sessionId:"interop-session-001", correlationId:corrId }});
write("typescript_invocation.json", inv.toDict());
console.log("  wrote typescript_invocation.json");

// 3. Response success
console.log("\\n[3] Producing UCIResponse (success)...");
const resp = UCIResponse.successResponse({{ output:{{audio_url:"uci://audio/test.wav",duration_ms:1560}},
  nodeId:"typescript_voice_service", instanceId:"ts_voice_001",
  capabilityId:"voice_tts", actionId:"synthesize",
  trustState:"trusted", governanceOutcome:"allow", correlationId:corrId }});
write("typescript_response_success.json", resp.toDict());
console.log("  wrote typescript_response_success.json");

// 4. Response failure
console.log("\\n[4] Producing UCIResponse (failure)...");
const fail = UCIResponse.failureResponse({{ error:{{ code:UCIErrorCode.PERMISSION_DENIED,
  severity:UCIErrorSeverity.HIGH, message:"Caller lacks voice.tts permission.",
  retryable:false, detail:{{missing_permissions:["voice.tts"]}} }},
  nodeId:"typescript_voice_service", instanceId:"ts_voice_001",
  capabilityId:"voice_tts", actionId:"synthesize",
  trustState:"trusted", governanceOutcome:"deny" }});
write("typescript_response_failure.json", fail.toDict());
console.log("  wrote typescript_response_failure.json");

// 5. Audit session
console.log("\\n[5] Producing UCIAuditSession...");
const audit = new AuditLog("typescript_orchestrator");
[
  [AuditEvent.NODE_DISCOVERED,"handshake_engine",{{}}],
  [AuditEvent.MANIFEST_VALIDATION_PASSED,"handshake_engine",{{}}],
  [AuditEvent.TRUST_ASSIGNED,"policy_engine",{{trust_state:"trusted"}}],
  [AuditEvent.CAPABILITY_MOUNTED,"handshake_engine",{{capability_id:"voice_tts"}}],
  [AuditEvent.NODE_READY,"handshake_engine",{{mounted_capabilities:["voice_tts"]}}],
  [AuditEvent.EXECUTION_ALLOWED,"policy_engine",{{capability_id:"voice_tts",action_id:"synthesize"}}],
  [AuditEvent.INVOCATION_REQUESTED,"typescript_orchestrator",{{}}],
  [AuditEvent.INVOCATION_COMPLETED,"typescript_orchestrator",{{outcome:"success"}}],
].forEach(([evt,actor,detail]) =>
  audit.append({{eventType:evt,nodeId:"typescript_voice_service",actor,detail}}));
const session = audit.export(true);
write("typescript_audit_session.json", session.toDict());
console.log("  wrote typescript_audit_session.json");

const integrity = audit.verifyIntegrity();
console.log("\\n[✓] TypeScript self-checks:");
console.log("    Audit integrity:    " + (integrity.valid?"PASS":"FAIL"));
console.log("    Session hash valid: " + (session.verifySessionHash()?"PASS":"FAIL"));
"""


def main() -> int:
    banner()
    steps_passed = []

    # Ensure TypeScript is compiled
    if not ensure_ts_built():
        print(f"\n{RED}  Cannot run interop without TypeScript build.{RST}")
        print(f"  Run: cd uci-typescript && npm ci && npm run build\n")
        return 1

    # ── Step 1: Python produces ───────────────────────────────
    ok = run_step(
        "Step 1/4 — Python produces canonical objects",
        [sys.executable, os.path.join(HERE, "python_produce.py")],
        cwd=HERE,
    )
    steps_passed.append(("Python producer", ok))
    if not ok:
        print(f"\n{RED}  Python producer failed — cannot continue.{RST}")
        return 1

    # ── Step 2: TypeScript validates Python output ─────────────
    # ts_validate_python.mjs uses plain Node.js — no ts-node needed
    ok = run_step(
        "Step 2/4 — TypeScript validates Python output",
        ["node", os.path.join(HERE, "ts_validate_python.mjs")],
        cwd=HERE,
    )
    steps_passed.append(("TypeScript validates Python", ok))

    # ── Step 3: TypeScript produces (from dist/, no ts-node) ───
    ok = run_step(
        "Step 3/4 — TypeScript produces canonical objects",
        ["node", "--input-type=module", "--eval", ts_producer_script()],
        cwd=TS_DIR,
    )
    steps_passed.append(("TypeScript producer", ok))

    # ── Step 4: Python validates TypeScript output ─────────────
    ok = run_step(
        "Step 4/4 — Python validates TypeScript output",
        [sys.executable, os.path.join(HERE, "python_validate_typescript.py")],
        cwd=HERE,
    )
    steps_passed.append(("Python validates TypeScript", ok))

    # ── Final verdict ──────────────────────────────────────────
    all_passed = all(p for _, p in steps_passed)
    print(f"\n{BOLD}{CYAN}{'═'*60}{RST}")
    print(f"{BOLD}  Interoperability Results{RST}")
    print(f"{BOLD}{CYAN}{'═'*60}{RST}")
    for step, passed in steps_passed:
        tag = f"{GREEN}✓ PASS{RST}" if passed else f"{RED}✗ FAIL{RST}"
        print(f"  {tag}  {step}")

    print(f"\n{BOLD}{CYAN}{'═'*60}{RST}")
    if all_passed:
        print(f"{BOLD}{GREEN}  ✓ INTEROPERABILITY PROOF: Python ↔ TypeScript{RST}")
        print(f"{DIM}  All canonical objects cross-validated successfully.{RST}")
        print(f"{DIM}  UCI is demonstrably language-neutral.{RST}")
    else:
        failed = [s for s, p in steps_passed if not p]
        print(f"{BOLD}{RED}  ✗ INTEROPERABILITY INCOMPLETE{RST}")
        print(f"{RED}  Failed: {', '.join(failed)}{RST}")
    print(f"{BOLD}{CYAN}{'═'*60}{RST}\n")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
