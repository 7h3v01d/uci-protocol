# UCI — Universal Capability Interface

> *"What USB did for peripheral connectivity, UCI does for programs, AI agents, and services."*

UCI is an open protocol for capability-based interoperability between software nodes —
programs, AI agents, services, hardware bridges, and orchestrators — with governance,
trust, and accountability built in from the start.

---

## Cross-language interoperability

| Direction | Status | Checks |
|---|---|---|
| Python → TypeScript | ✓ PASS | 29/29 |
| TypeScript → Python | ✓ PASS | 42/42 |
| **Total** | **✓ PASS** | **87/87** |

Neither implementation calls the other's code.
The only shared surface is the UCI specification and JSON schemas.

→ **[Full Interoperability Report](uci-interop/INTEROP_REPORT.md)**

---

## The four protocol objects

| Object | Role |
|---|---|
| `UCIManifest` | Identity — who I am, what I can do, what my rules are |
| `UCIInvocation` | Request — do this, for this caller, with this payload |
| `UCIResponse` | Answer — what happened, what was the output, what did governance decide |
| `UCIAuditSession` | Record — tamper-evident, chain-hashed proof of everything that happened |

---

## Repositories

| Repo | Description | Tests |
|---|---|---|
| [`uci-python-v2/`](uci-python-v2/) | Python reference implementation | 331 passing |
| [`uci-typescript/`](uci-typescript/) | TypeScript SDK | 63 passing |
| [`uci-interop/`](uci-interop/) | Cross-language interoperability harness | 87/87 checks |

---

## Quick start

**Python:**
```bash
cd uci-python-v2
pip install pytest jsonschema
python run_rig.py          # live demo
python -m pytest test_rig/ # test suite
python uci_validate.py example_manifests/valid_document_service.json
```

**TypeScript:**
```bash
cd uci-typescript
npm install
npm test                   # compliance suite
open demo/index.html       # browser validator — no server needed
```

**Interoperability:**
```bash
cd uci-interop
python generate_report.py  # runs full cross-language proof, writes INTEROP_REPORT.md
```

---

## Specification

The full protocol specification lives in [`uci-python-v2/docs/`](uci-python-v2/docs/) —
23 documents covering every aspect of UCI.

Start here: **[`uci-python-v2/SPEC.md`](uci-python-v2/SPEC.md)**

---

## JSON Schemas

Three canonical schemas define the protocol's wire format,
validated by both implementations independently:

| Schema | URI |
|---|---|
| Manifest | `https://uci-spec.org/schemas/uci_manifest_v0_1.json` |
| Response | `https://uci-spec.org/schemas/uci_response_v0_1.json` |
| Audit Session | `https://uci-spec.org/schemas/uci_audit_session_v0_1.json` |

Schemas live in both [`uci-python-v2/uci/schemas/`](uci-python-v2/uci/schemas/)
and [`uci-typescript/schemas/`](uci-typescript/schemas/) — byte-for-byte identical.

---

## Release

**Current:** `v0.1.0-alpha` — feature-frozen pending interoperability review

→ [Release Notes](uci-python-v2/RELEASE_NOTES_v0.1.0-alpha.md)
→ [Release Checklist](uci-python-v2/RELEASE_CHECKLIST.md)
→ [Changelog](uci-python-v2/CHANGELOG.md)

---

## Contributing

The single most valuable contribution is an **external implementation** —
build a UCI node or orchestrator in Go, Rust, or any other language using
only the JSON schemas and compliance suite as your guide.

→ [Contributing Guide](uci-python-v2/CONTRIBUTING.md)
→ [Security Policy](uci-python-v2/SECURITY.md)

---

## Author

**Leon Priest**

UCI is an open protocol. The specification, schemas, and implementations
are freely available for adoption under the MIT licence.

---

*UCI v0.1.0-alpha · © Leon Priest · MIT License*
