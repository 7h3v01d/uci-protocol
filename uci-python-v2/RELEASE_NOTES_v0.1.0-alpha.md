# UCI v0.1.0-alpha — Release Notes

**Universal Capability Interface · Python Reference Implementation**
**Release date:** June 2026
**Status:** Alpha — feature-frozen pending interoperability review

---

## What is UCI?

UCI is an open protocol for capability-based interoperability between software
nodes — programs, AI agents, services, hardware bridges, and orchestrators.

It defines how nodes discover each other, negotiate trust, invoke capabilities
through a governance layer, and produce verifiable audit records — regardless
of language, platform, or vendor.

> *"What USB did for peripheral connectivity, UCI does for programs, AI agents,
> and services."*

---

## Release highlights

### Protocol specification
- 23 specification documents covering all aspects of the protocol
- Canonical ontology, taxonomy, governance model, trust model, audit model
- Formal compliance profiles and conformance expectations
- Versioning and compatibility rules

### Four canonical protocol objects
| Object | Role |
|---|---|
| `UCIManifest` | Identity — who I am, what I can do, what my rules are |
| `UCIInvocation` | Request — do this, for this caller, with this payload |
| `UCIResponse` | Answer — what happened, what was the output, what did governance decide |
| `UCIAuditSession` | Record — tamper-evident, chain-hashed proof of everything that happened |

### Python reference implementation
- Full implementation of all four protocol objects
- 9-stage fail-closed handshake engine
- Governance policy engine (allow / allow_with_restrictions / defer / deny)
- Trust state machine with enforced transitions
- Chain-hashed append-only audit log with session export and integrity verification
- Three canonical JSON schemas (`uci-spec.org`)
- CLI manifest validator (`uci_validate.py`) with `--strict`, `--json`, `--quiet` flags
- **331 tests · 0 failures**

### Formal compliance suite
63 compliance rules across seven groups:

| Group | Rules | Verifies |
|---|---|---|
| C-MAN | 001–012 | Manifest structure and canonical enums |
| C-GOV | 001–010 | Governance fail-closed behaviour |
| C-HSK | 001–009 | Handshake stages and ordering |
| C-RSP | 001–012 | Response envelope and never-raises contract |
| C-AUD | 001–010 | Audit append-only and chain integrity |
| C-SCH | 001–008 | All objects pass JSON Schema |
| C-INT | 001–002 | Full session compliance end-to-end |

### TypeScript SDK
- Independent implementation of all four protocol objects
- Same compliance rules as Python — 63 tests, same rule IDs
- Same JSON schemas — validated via ajv Draft 2020-12
- Browser-based manifest validator (`demo/index.html`) — no install required

### Cross-language interoperability proof

```
Python  → TypeScript:  29/29 checks  PASS
TypeScript → Python:   42/42 checks  PASS
Total:                 87/87 checks  PASS
Verdict:               PASS
```

Neither implementation calls the other's code.
The only shared surface is the UCI specification and JSON schemas.

See `INTEROP_REPORT.md` in the `uci-interop` package for the full proof.

---

## Canonical error codes

All error codes are `lowercase_snake_case` as defined in the spec taxonomy:
`permission_denied` · `trust_failure` · `confirmation_required` ·
`execution_error` · `validation_error` · `version_mismatch` · and more.

---

## Known limitations

These gaps are known and documented. They do not block the alpha release
but must be resolved before v0.1.0 stable.

| Limitation | Target |
|---|---|
| No HTTP transport — interop is in-process and via JSON file exchange | v0.2 |
| No UCI Registry service — node discovery is manual | v0.2 |
| No production integration (Niles/NYALS or similar) | v0.2 |
| No Go or Rust implementation | v0.3 |
| `uci-spec.org` not yet live — schemas reference the domain but it is not hosted | Before v0.1.0 stable |
| Chain hash algorithm not yet formally written into spec documents | Next patch |
| No stable API or wire format guarantees — breaking changes may occur | By design for alpha |

---

## Interop status

| Direction | Status | Checks |
|---|---|---|
| Python → TypeScript | ✓ PASS | 29/29 |
| TypeScript → Python | ✓ PASS | 42/42 |
| Schema compatibility | ✓ PASS | Byte-identical across both implementations |
| Chain hash cross-language | ✓ PASS | SHA-256 of canonical JSON (sorted keys, no whitespace) |

---

## Repositories

| Repo | Description |
|---|---|
| `uci-protocol/uci-python` | Python reference implementation (this package) |
| `uci-protocol/uci-typescript` | TypeScript SDK |
| `uci-protocol/uci-interop` | Cross-language interoperability harness |

---

## What comes next

**v0.2 target: HTTP transport proof**

One Python UCI provider exposing capabilities over HTTP.
One TypeScript UCI client discovering and invoking it.
Full protocol conversation — manifest, invocation, response, audit — over `localhost`.

That becomes the next proof point:
```
Cross-language objects:    PASS  ← done
Cross-process transport:   next
```

---

## Author

**Leon Priest** 

UCI is an open protocol. The specification, schemas, and reference implementations
are freely available for adoption under the Apache 2.0 licence.

If you build something with UCI, or implement UCI in another language,
please get in touch.

---

*UCI v0.1.0-alpha · © Leon Priest · Apache License 2.0*
