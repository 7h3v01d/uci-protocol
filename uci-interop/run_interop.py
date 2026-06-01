#!/usr/bin/env python3
"""
UCI Interoperability Test Runner
=================================
Orchestrates the full cross-language interoperability proof.

Run with:
    python run_interop.py

What this does:
    1. Python produces 5 canonical UCI objects as JSON
    2. TypeScript validates all 5 Python-produced objects
    3. TypeScript produces 5 canonical UCI objects as JSON
    4. Python validates all 5 TypeScript-produced objects
    5. Prints a final interoperability verdict

Pass criteria:
    - Every object produced by Python passes TypeScript validation
    - Every object produced by TypeScript passes Python validation
    - Chain hashes verified cross-language
    - JSON schemas validated by both implementations
"""

import subprocess
import sys
import os

HERE = os.path.dirname(os.path.abspath(__file__))
TS_DIR  = os.path.join(HERE, "..", "uci-typescript")
PY_DIR  = os.path.join(HERE, "..", "uci-python-v2")

GREEN  = "\033[32m"
RED    = "\033[31m"
CYAN   = "\033[36m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
RST    = "\033[0m"


def banner():
    print()
    print(f"{BOLD}{CYAN}{'═'*60}{RST}")
    print(f"{BOLD}{CYAN}  UCI Interoperability Test{RST}")
    print(f"{BOLD}{CYAN}  Python ↔ TypeScript{RST}")
    print(f"{BOLD}{CYAN}{'═'*60}{RST}")


def run_step(label: str, cmd: list[str], cwd: str) -> bool:
    print(f"\n{BOLD}── {label}{RST}")
    result = subprocess.run(cmd, cwd=cwd, capture_output=False)
    return result.returncode == 0


def main() -> int:
    banner()
    steps_passed = []

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
    # Compile and run TypeScript validator
    ts_validate = os.path.join(HERE, "typescript_validate_python.ts")
    ok = run_step(
        "Step 2/4 — TypeScript validates Python output",
        ["node", "--loader", "ts-node/esm", ts_validate],
        cwd=TS_DIR,
    )
    if not ok:
        # Try with npx ts-node as fallback
        ok = run_step(
            "Step 2/4 — TypeScript validates Python output (npx fallback)",
            ["npx", "ts-node", "--esm", ts_validate],
            cwd=TS_DIR,
        )
    steps_passed.append(("TypeScript validates Python", ok))

    # ── Step 3: TypeScript produces ───────────────────────────
    ts_produce = os.path.join(HERE, "typescript_produce.ts")
    ok = run_step(
        "Step 3/4 — TypeScript produces canonical objects",
        ["node", "--loader", "ts-node/esm", ts_produce],
        cwd=TS_DIR,
    )
    if not ok:
        ok = run_step(
            "Step 3/4 — TypeScript produces canonical objects (npx fallback)",
            ["npx", "ts-node", "--esm", ts_produce],
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
        print(f"{BOLD}{RED}  ✗ INTEROPERABILITY INCOMPLETE{RST}")
        failed = [s for s, p in steps_passed if not p]
        print(f"{RED}  Failed: {', '.join(failed)}{RST}")
    print(f"{BOLD}{CYAN}{'═'*60}{RST}\n")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())


