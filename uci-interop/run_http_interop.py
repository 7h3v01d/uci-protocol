#!/usr/bin/env python3
"""
UCI HTTP Interoperability Test
================================
Proves UCI works over a real HTTP transport:
  - Starts the Python UCI provider on localhost
  - Runs the TypeScript client against it
  - Verifies all protocol semantics survived the wire trip

Run with:
    python run_http_interop.py

Prerequisites:
    cd uci-typescript && npm ci && npm run build
    cd examples/http_client_typescript && npm install && npm run build
"""

import subprocess
import sys
import os
import time
import signal
import json
import urllib.request
import urllib.error

HERE   = os.path.dirname(os.path.abspath(__file__))
ROOT   = os.path.join(HERE, "..")
TS_DIR = os.path.join(ROOT, "uci-typescript")
PY_DIR = os.path.join(ROOT, "uci-python-v2")
CLIENT = os.path.join(ROOT, "examples", "http_client_typescript")

PORT     = 8765    # use a non-standard port to avoid conflicts
BASE_URL = f"http://localhost:{PORT}"

GREEN = "\033[32m"; RED = "\033[31m"; CYAN = "\033[36m"
BOLD  = "\033[1m";  DIM = "\033[2m";  RST  = "\033[0m"

sys.path.insert(0, PY_DIR)


def wait_for_server(url: str, timeout: int = 10) -> bool:
    """Poll until the server responds or timeout."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            urllib.request.urlopen(f"{url}/uci/health", timeout=1)
            return True
        except Exception:
            time.sleep(0.3)
    return False


def run_python_checks(base_url: str) -> list[tuple[str, bool, str]]:
    """Python directly validates the live HTTP provider."""
    results = []

    def check(name, passed, detail=""):
        results.append((name, passed, detail))
        tag = f"{GREEN}PASS{RST}" if passed else f"{RED}FAIL{RST}"
        print(f"    [{tag}] {name}" + (f"  — {detail}" if detail and not passed else ""))

    import json, urllib.request
    from uci.core.schema_validator import (
        validate_manifest_schema, validate_response_schema, validate_audit_session_schema
    )
    from uci.core.manifest  import UCIManifest
    from uci.core.invocation import UCIInvocation
    from uci.core.audit     import UCIAuditSession, GENESIS_HASH

    # GET /uci/manifest
    print(f"\n  {CYAN}[1] GET /uci/manifest{RST}")
    try:
        data = json.loads(urllib.request.urlopen(f"{base_url}/uci/manifest").read())
        schema_result = validate_manifest_schema(data)
        check("Schema valid",             schema_result.valid)
        manifest = UCIManifest.from_dict(data)
        manifest.validate()
        check("Semantic validation",      True)
        check("node_id non-empty",        bool(manifest.node.node_id))
        check("transport type = http",    any(t.type == "http" for t in manifest.transports))
        check("health block present",     bool(manifest.health))
    except Exception as e:
        check("Manifest fetch", False, str(e))

    # POST /uci/invoke
    print(f"\n  {CYAN}[2] POST /uci/invoke (search){RST}")
    try:
        inv = UCIInvocation.create(
            node_id="uci_doc_service", capability_id="document_search",
            action_id="search_index", payload={"query": "UCI", "limit": 3},
            caller_node_id="python_http_test", correlation_id="http-test-001"
        )
        req = urllib.request.Request(
            f"{base_url}/uci/invoke",
            data=json.dumps(inv.to_dict()).encode(),
            headers={"Content-Type": "application/json"},
        )
        resp_data = json.loads(urllib.request.urlopen(req).read())
        schema_result = validate_response_schema(resp_data)
        check("Response schema valid",    schema_result.valid)
        check("success == True",          resp_data.get("success") is True)
        check("state == completed",       resp_data.get("state") == "completed")
        check("output has results",       isinstance(resp_data.get("output", {}).get("results"), list))
        check("correlation_id preserved", resp_data.get("correlation_id") == "http-test-001")
        check("governance.outcome allow", resp_data.get("governance", {}).get("outcome", "").startswith("allow"))
    except Exception as e:
        check("Invocation", False, str(e))

    # GET /uci/audit/session
    print(f"\n  {CYAN}[3] GET /uci/audit/session{RST}")
    try:
        data = json.loads(urllib.request.urlopen(f"{base_url}/uci/audit/session").read())
        schema_result = validate_audit_session_schema(data)
        check("Audit schema valid",       schema_result.valid)
        session = UCIAuditSession.from_dict(data)
        check("Session hash verifies",    session.verify_session_hash())

        # Walk chain
        import hashlib
        prev = GENESIS_HASH
        ok = True
        for r in session.records:
            if not r.verify(prev):
                ok = False; break
            prev = r.chain_hash
        check("Chain integrity intact",   ok)
        check("Has invocation records",   any(
            r.event_type in ("invocation_requested", "invocation_completed")
            for r in session.records
        ))
    except Exception as e:
        check("Audit session", False, str(e))

    return results


def main() -> int:
    print(f"\n{BOLD}{CYAN}{'═'*60}{RST}")
    print(f"{BOLD}{CYAN}  UCI HTTP Interoperability Test{RST}")
    print(f"{BOLD}{CYAN}  Python provider ↔ TypeScript client over localhost{RST}")
    print(f"{BOLD}{CYAN}{'═'*60}{RST}")

    # ── Step 1: Start Python provider ────────────────────────────
    print(f"\n{BOLD}── Step 1/4 — Starting Python provider on port {PORT}{RST}")
    provider_proc = subprocess.Popen(
        [sys.executable,
         os.path.join(ROOT, "examples", "http_provider_python", "provider.py"),
         "--port", str(PORT), "--log-level", "warning"],
        cwd=PY_DIR,
    )

    print(f"  Waiting for provider...")
    if not wait_for_server(BASE_URL, timeout=15):
        provider_proc.terminate()
        print(f"  {RED}Provider failed to start{RST}")
        return 1
    print(f"  {GREEN}✓{RST} Provider ready at {BASE_URL}")

    steps_passed = []

    try:
        # ── Step 2: Python validates live HTTP provider ───────────
        print(f"\n{BOLD}── Step 2/4 — Python validates live HTTP endpoints{RST}")
        py_results = run_python_checks(BASE_URL)
        py_passed  = sum(1 for _, p, _ in py_results if p)
        py_ok      = py_passed == len(py_results)
        steps_passed.append((f"Python HTTP checks ({py_passed}/{len(py_results)})", py_ok))

        # ── Step 3: Build TypeScript client if needed ─────────────
        print(f"\n{BOLD}── Step 3/4 — Building TypeScript client{RST}")
        build_result = subprocess.run(
            ["npm", "run", "build"],
            cwd=CLIENT, capture_output=True, text=True
        )
        build_ok = build_result.returncode == 0
        steps_passed.append(("TypeScript client build", build_ok))
        if build_ok:
            print(f"  {GREEN}✓{RST} TypeScript build complete")
        else:
            print(f"  {RED}✗{RST} Build failed: {build_result.stderr[:200]}")

        # ── Step 4: TypeScript client runs against live provider ───
        if build_ok:
            print(f"\n{BOLD}── Step 4/4 — TypeScript client ↔ Python provider{RST}")
            ts_result = subprocess.run(
                ["node", "dist/demo.js"],
                cwd=CLIENT,
                env={**os.environ, "UCI_PROVIDER_URL": BASE_URL},
            )
            ts_ok = ts_result.returncode == 0
            steps_passed.append(("TypeScript client demo", ts_ok))
        else:
            steps_passed.append(("TypeScript client demo", False))

    finally:
        provider_proc.terminate()
        try: provider_proc.wait(timeout=3)
        except: provider_proc.kill()

    # ── Verdict ───────────────────────────────────────────────────
    all_passed = all(p for _, p in steps_passed)
    print(f"\n{BOLD}{CYAN}{'═'*60}{RST}")
    print(f"{BOLD}  HTTP Interoperability Results{RST}")
    print(f"{BOLD}{CYAN}{'═'*60}{RST}")
    for step, passed in steps_passed:
        tag = f"{GREEN}✓ PASS{RST}" if passed else f"{RED}✗ FAIL{RST}"
        print(f"  {tag}  {step}")
    print(f"\n{BOLD}{CYAN}{'═'*60}{RST}")
    if all_passed:
        print(f"{BOLD}{GREEN}  ✓ HTTP TRANSPORT PROOF: Python ↔ TypeScript over HTTP{RST}")
        print(f"{DIM}  UCI works beyond shared JSON files.{RST}")
        print(f"{DIM}  Cross-process transport: PASS{RST}")
    else:
        failed = [s for s, p in steps_passed if not p]
        print(f"{BOLD}{RED}  ✗ HTTP interop incomplete: {', '.join(failed)}{RST}")
    print(f"{BOLD}{CYAN}{'═'*60}{RST}\n")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
