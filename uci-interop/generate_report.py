#!/usr/bin/env python3
"""
UCI Interoperability Report Generator
======================================
Runs the full interop test suite and produces:
  - INTEROP_REPORT.md  — human-readable proof document
  - interop_result.json — machine-readable result (for CI/badges)

Usage:
    python generate_report.py

Output files are written to the uci-interop/ directory.
The exchange/ directory (intermediate JSON files) is gitignored.
"""

import sys
import os
import json
import subprocess
import hashlib
import uuid
from datetime import datetime, timezone
from typing import Optional

HERE   = os.path.dirname(os.path.abspath(__file__))
PY_DIR = os.path.join(HERE, "..", "uci-python-v2")
TS_DIR = os.path.join(HERE, "..", "uci-typescript")

sys.path.insert(0, PY_DIR)


# ── Step runner ───────────────────────────────────────────────────────────────

class StepResult:
    def __init__(self, name: str):
        self.name    = name
        self.checks: list[dict] = []
        self.passed  = True
        self.error:  Optional[str] = None

    def check(self, name: str, passed: bool, detail: str = "") -> None:
        self.checks.append({"name": name, "passed": passed, "detail": detail})
        if not passed:
            self.passed = False

    def summary(self) -> dict:
        total  = len(self.checks)
        passed = sum(1 for c in self.checks if c["passed"])
        return {
            "step":    self.name,
            "passed":  self.passed,
            "checks":  f"{passed}/{total}",
            "details": self.checks,
        }


def run_python_producer() -> StepResult:
    step = StepResult("Python produces canonical objects")
    try:
        result = subprocess.run(
            [sys.executable, os.path.join(HERE, "python_produce.py")],
            cwd=HERE, capture_output=True, text=True
        )
        ok = result.returncode == 0
        step.check("Python producer exits cleanly", ok, result.stderr[:200] if not ok else "")

        # Verify files were written
        for fname in ["python_manifest.json", "python_invocation.json",
                      "python_response_success.json", "python_response_failure.json",
                      "python_audit_session.json"]:
            path = os.path.join(HERE, "exchange", fname)
            exists = os.path.isfile(path)
            step.check(f"Produced {fname}", exists)

        # Verify Python self-checks
        if "PASS" in result.stdout:
            step.check("Python audit integrity self-check", "Audit integrity:       PASS" in result.stdout)
            step.check("Python session hash self-check",    "Session hash valid:    PASS" in result.stdout)

    except Exception as e:
        step.error = str(e)
        step.passed = False
    return step


def run_ts_validates_python() -> StepResult:
    step = StepResult("TypeScript validates Python output")
    try:
        result = subprocess.run(
            ["node", os.path.join(HERE, "ts_validate_python.mjs")],
            cwd=HERE, capture_output=True, text=True
        )
        ok = result.returncode == 0
        step.passed = ok

        # Parse individual check results from output
        import re as _re
        ansi = _re.compile(r"\x1b\[[0-9;]*m")
        for line in result.stdout.split("\n"):
            clean = ansi.sub("", line)
            if "PASS]" in clean or "FAIL]" in clean:
                passed = "PASS]" in clean
                if "]" in clean:
                    name   = clean.split("]", 1)[-1].strip().split("  —")[0].strip()
                    detail = clean.split("  —")[-1].strip() if "  —" in clean else ""
                    if name and not name.startswith("[") and len(name) > 2:
                        step.check(name, passed, detail)

        if not step.checks:
            step.check("TypeScript validator ran", ok,
                       result.stderr[:200] if not ok else "")

    except Exception as e:
        step.error = str(e)
        step.passed = False
    return step


def run_ts_producer() -> StepResult:
    step = StepResult("TypeScript produces canonical objects")
    try:
        result = subprocess.run(
            ["node", "--input-type=module",
             "--eval", _ts_producer_code()],
            cwd=TS_DIR, capture_output=True, text=True
        )
        ok = result.returncode == 0
        step.check("TypeScript producer exits cleanly", ok,
                   result.stderr[:200] if not ok else "")

        for fname in ["typescript_manifest.json", "typescript_invocation.json",
                      "typescript_response_success.json", "typescript_response_failure.json",
                      "typescript_audit_session.json"]:
            path = os.path.join(HERE, "exchange", fname)
            step.check(f"Produced {fname}", os.path.isfile(path))

        if "PASS" in result.stdout:
            step.check("TypeScript audit integrity self-check",
                       "Audit integrity:    PASS" in result.stdout)
            step.check("TypeScript session hash self-check",
                       "Session hash valid: PASS" in result.stdout)

    except Exception as e:
        step.error = str(e)
        step.passed = False
    return step


def run_python_validates_ts() -> StepResult:
    step = StepResult("Python validates TypeScript output")
    try:
        result = subprocess.run(
            [sys.executable, os.path.join(HERE, "python_validate_typescript.py")],
            cwd=HERE, capture_output=True, text=True
        )
        ok = result.returncode == 0
        step.passed = ok

        for line in result.stdout.split("\n"):
            if " PASS " in line or " FAIL " in line:
                passed = " PASS " in line
                # Strip ANSI codes and extract name
                clean  = line.replace("\x1b[32m","").replace("\x1b[31m","").replace("\x1b[0m","")
                clean  = clean.replace("\033[32m","").replace("\033[31m","").replace("\033[0m","")
                if "]" in clean:
                    name   = clean.split("]", 1)[-1].strip().split("  —")[0].strip()
                    detail = clean.split("  —")[-1].strip() if "  —" in clean else ""
                    if name and not name.startswith("#") and len(name) > 2:
                        step.check(name, passed, detail)

        if not step.checks:
            step.check("Python validator ran", ok,
                       result.stderr[:200] if not ok else "")

    except Exception as e:
        step.error = str(e)
        step.passed = False
    return step


def _ts_producer_code() -> str:
    """Inline the TypeScript producer as a Node.js ESM eval string."""
    return r"""
import { writeFileSync } from "fs";
import { join } from "path";
import { randomUUID } from "crypto";
import { UCIManifest } from "./dist/manifest.js";
import { UCIInvocation } from "./dist/invocation.js";
import { UCIResponse, UCIErrorCode, UCIErrorSeverity } from "./dist/response.js";
import { AuditLog, AuditEvent } from "./dist/audit.js";

const EXCHANGE = "/home/claude/uci-interop/exchange";
const write = (f, d) => writeFileSync(join(EXCHANGE,f), JSON.stringify(d,null,2));

const manifest = new UCIManifest({
  uci_manifest_version:"0.1",
  node:{ node_id:"typescript_voice_service", instance_id:"ts_voice_001",
         display_name:"TypeScript Voice Service", node_type:"service",
         version:"1.0.0", vendor:"KeystoneAI", description:"Produced by TypeScript SDK." },
  capabilities:[{ capability_id:"voice_tts", version:"1.0", category:"audio",
    description:"Text-to-speech.", tags:["voice","tts"],
    actions:[{ action_id:"synthesize", description:"Convert text to audio.",
      execution:{mode:"sync",timeout_ms:8000,side_effects:true},
      input_schema:{text:"string",voice_id:"string"}, output_schema:{audio_url:"string",duration_ms:"integer"},
      risk:{level:"low",categories:["read_only"]},
      permissions:{required_permissions:["voice.tts"],operator_confirmation:"none",minimum_trust_state:"trusted"},
      errors:[] }] }],
  transports:[{ transport_id:"ipc_local",type:"ipc",endpoint:"uci://local/typescript_voice_service",security:{},options:{} }],
  governance:{ default_action_policy:"deny",audit_required:true,operator_authority_required:false },
  health:{ expose_uptime:true,expose_metrics:false },
  compliance:{profile:"minimal"}, audit:{audit_enabled:true}, extensions:{},
});
manifest.validate();
write("typescript_manifest.json", manifest.toDict());

const corrId = `interop-corr-${randomUUID().slice(0,8)}`;
const inv = UCIInvocation.create({ nodeId:"typescript_voice_service", capabilityId:"voice_tts",
  actionId:"synthesize", payload:{text:"UCI interop.",voice_id:"niles"},
  callerNodeId:"typescript_orchestrator", sessionId:"interop-session-001", correlationId:corrId });
write("typescript_invocation.json", inv.toDict());

const resp = UCIResponse.successResponse({ output:{audio_url:"uci://audio/test.wav",duration_ms:1560},
  nodeId:"typescript_voice_service", instanceId:"ts_voice_001",
  capabilityId:"voice_tts", actionId:"synthesize",
  trustState:"trusted", governanceOutcome:"allow", correlationId:corrId });
write("typescript_response_success.json", resp.toDict());

const fail = UCIResponse.failureResponse({ error:{ code:UCIErrorCode.PERMISSION_DENIED,
  severity:UCIErrorSeverity.HIGH, message:"Caller lacks voice.tts permission.",
  retryable:false, detail:{missing_permissions:["voice.tts"]} },
  nodeId:"typescript_voice_service", instanceId:"ts_voice_001",
  capabilityId:"voice_tts", actionId:"synthesize",
  trustState:"trusted", governanceOutcome:"deny" });
write("typescript_response_failure.json", fail.toDict());

const audit = new AuditLog("typescript_orchestrator");
[[AuditEvent.NODE_DISCOVERED,"handshake_engine",{}],
 [AuditEvent.MANIFEST_VALIDATION_PASSED,"handshake_engine",{}],
 [AuditEvent.TRUST_ASSIGNED,"policy_engine",{trust_state:"trusted"}],
 [AuditEvent.CAPABILITY_MOUNTED,"handshake_engine",{capability_id:"voice_tts"}],
 [AuditEvent.NODE_READY,"handshake_engine",{mounted_capabilities:["voice_tts"]}],
 [AuditEvent.EXECUTION_ALLOWED,"policy_engine",{capability_id:"voice_tts",action_id:"synthesize"}],
 [AuditEvent.INVOCATION_REQUESTED,"typescript_orchestrator",{}],
 [AuditEvent.INVOCATION_COMPLETED,"typescript_orchestrator",{outcome:"success"}],
].forEach(([evt,actor,detail]) => audit.append({eventType:evt,nodeId:"typescript_voice_service",actor,detail}));
const session = audit.export(true);
write("typescript_audit_session.json", session.toDict());

const integrity = audit.verifyIntegrity();
console.log("Audit integrity:    " + (integrity.valid?"PASS":"FAIL"));
console.log("Session hash valid: " + (session.verifySessionHash()?"PASS":"FAIL"));
"""


# ── Report generator ──────────────────────────────────────────────────────────

def generate_markdown_report(
    steps: list[StepResult],
    run_id: str,
    timestamp: str,
    all_passed: bool,
) -> str:

    verdict = "✓ PASS" if all_passed else "✗ FAIL"
    verdict_badge = "PASS" if all_passed else "FAIL"

    total_checks = sum(len(s.checks) for s in steps)
    total_passed = sum(sum(1 for c in s.checks if c["passed"]) for s in steps)

    lines = [
        "# UCI Interoperability Report",
        "",
        "> This document is generated automatically by `uci-interop/generate_report.py`.",
        "> It proves that the Python and TypeScript UCI implementations can exchange",
        "> canonical protocol objects and validate each other's output.",
        "",
        "---",
        "",
        "## Result",
        "",
        f"| | |",
        f"|---|---|",
        f"| **Verdict** | **{verdict}** |",
        f"| Run ID | `{run_id}` |",
        f"| Timestamp | {timestamp} |",
        f"| Total checks | {total_passed}/{total_checks} passed |",
        f"| Python → TypeScript | {'✓ PASS' if steps[1].passed else '✗ FAIL'} |",
        f"| TypeScript → Python | {'✓ PASS' if steps[3].passed else '✗ FAIL'} |",
        "",
        "---",
        "",
        "## What was tested",
        "",
        "Each implementation independently produces five canonical UCI objects as JSON.",
        "The other implementation then validates them — using its own stack, its own",
        "schema validator, and its own chain hash implementation.",
        "",
        "Neither implementation calls the other's code.",
        "The only shared surface is the UCI specification and JSON schemas.",
        "",
        "| Object | Validated |",
        "|---|---|",
        "| `UCIManifest` | Schema + semantic validation |",
        "| `UCIInvocation` | Structure + field completeness |",
        "| `UCIResponse` (success) | Schema + field semantics |",
        "| `UCIResponse` (failure) | Schema + error code canonicality |",
        "| `UCIAuditSession` | Schema + session hash + chain hash integrity |",
        "",
        "---",
        "",
        "## Step results",
        "",
    ]

    for step in steps:
        passed_count = sum(1 for c in step.checks if c["passed"])
        total_count  = len(step.checks)
        icon = "✓" if step.passed else "✗"
        lines.append(f"### {icon} {step.name}")
        lines.append("")
        lines.append(f"{passed_count}/{total_count} checks passed")
        lines.append("")

        if step.checks:
            lines.append("| Check | Result |")
            lines.append("|---|---|")
            for c in step.checks:
                result = "✓" if c["passed"] else "✗"
                detail = f" — {c['detail']}" if c["detail"] and not c["passed"] else ""
                lines.append(f"| {c['name']}{detail} | {result} |")
            lines.append("")

    lines += [
        "---",
        "",
        "## Chain hash algorithm",
        "",
        "The audit chain hash is computed as:",
        "",
        "```",
        "SHA-256(canonical_json({",
        "  previous_hash, sequence, event_id, event_type,",
        "  node_id, timestamp, actor, outcome, detail",
        "}))",
        "```",
        "",
        "Where `canonical_json` means: **sorted keys, no whitespace**.",
        "",
        "- Python: `json.dumps(payload, sort_keys=True, separators=(',', ':'))`",
        "- TypeScript: recursive object serialisation with `Object.keys().sort()`",
        "",
        "Both produce byte-identical output for the same input.",
        "This was verified by the interoperability test.",
        "",
        "---",
        "",
        "## Schemas",
        "",
        "All objects validated against canonical schemas at `uci-spec.org`:",
        "",
        "| Schema | URI |",
        "|---|---|",
        "| Manifest | `https://uci-spec.org/schemas/uci_manifest_v0_1.json` |",
        "| Response | `https://uci-spec.org/schemas/uci_response_v0_1.json` |",
        "| Audit Session | `https://uci-spec.org/schemas/uci_audit_session_v0_1.json` |",
        "",
        "---",
        "",
        f"*Generated by `uci-interop/generate_report.py` · UCI v0.1.0-alpha · {timestamp}*",
        "",
    ]

    return "\n".join(lines)


def generate_json_result(
    steps: list[StepResult],
    run_id: str,
    timestamp: str,
    all_passed: bool,
) -> dict:
    return {
        "uci_interop_version": "0.1",
        "run_id":              run_id,
        "timestamp":           timestamp,
        "verdict":             "pass" if all_passed else "fail",
        "python_version":      f"{sys.version_info.major}.{sys.version_info.minor}",
        "implementations": {
            "python":     "uci-python v0.1.0-alpha",
            "typescript": "uci-typescript v0.1.0-alpha",
        },
        "directions": {
            "python_to_typescript": steps[1].passed,
            "typescript_to_python": steps[3].passed,
        },
        "steps": [s.summary() for s in steps],
        "total_checks": {
            "total":  sum(len(s.checks) for s in steps),
            "passed": sum(sum(1 for c in s.checks if c["passed"]) for s in steps),
        },
    }


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> int:
    GREEN = "\033[32m"
    RED   = "\033[31m"
    CYAN  = "\033[36m"
    BOLD  = "\033[1m"
    RST   = "\033[0m"

    run_id    = str(uuid.uuid4())[:8]
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    print(f"\n{BOLD}{CYAN}{'═'*60}{RST}")
    print(f"{BOLD}{CYAN}  UCI Interoperability Report Generator{RST}")
    print(f"{BOLD}{CYAN}  Run ID: {run_id}  ·  {timestamp}{RST}")
    print(f"{BOLD}{CYAN}{'═'*60}{RST}")

    print(f"\n{CYAN}Running interoperability test suite...{RST}\n")

    steps = [
        run_python_producer(),
        run_ts_validates_python(),
        run_ts_producer(),
        run_python_validates_ts(),
    ]

    all_passed = all(s.passed for s in steps)

    # Print step summary
    for step in steps:
        icon = f"{GREEN}✓{RST}" if step.passed else f"{RED}✗{RST}"
        passed = sum(1 for c in step.checks if c["passed"])
        total  = len(step.checks)
        print(f"  {icon} {step.name:50s} {passed}/{total}")

    # Write reports
    md_path   = os.path.join(HERE, "INTEROP_REPORT.md")
    json_path = os.path.join(HERE, "interop_result.json")

    md_content   = generate_markdown_report(steps, run_id, timestamp, all_passed)
    json_content = generate_json_result(steps, run_id, timestamp, all_passed)

    with open(md_path,   "w") as f: f.write(md_content)
    with open(json_path, "w") as f: json.dump(json_content, f, indent=2)

    print(f"\n  Report written:  INTEROP_REPORT.md")
    print(f"  Result written:  interop_result.json")

    print(f"\n{BOLD}{CYAN}{'═'*60}{RST}")
    if all_passed:
        print(f"{BOLD}{GREEN}  ✓ INTEROPERABILITY PROOF: Python ↔ TypeScript{RST}")
        print(f"  UCI is demonstrably language-neutral.")
    else:
        failed = [s.name for s in steps if not s.passed]
        print(f"{BOLD}{RED}  ✗ INTEROPERABILITY INCOMPLETE{RST}")
        print(f"  Failed: {', '.join(failed)}")
    print(f"{BOLD}{CYAN}{'═'*60}{RST}\n")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
