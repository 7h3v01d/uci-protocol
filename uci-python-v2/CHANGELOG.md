# Changelog

All notable changes to the UCI Python reference implementation.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [0.1.0-alpha] — 2026-06

First public release of the UCI Python reference implementation.

### Protocol objects
- `UCIManifest` — identity and capability contract, with full serialisation, JSON Schema validation, and semantic validation pipeline
- `UCIInvocation` — first-class canonical request object with caller identity, target, payload, execution context, and correlation ID
- `UCIResponse` — canonical answer envelope with all 10 spec-defined states, canonical `lowercase_snake_case` error codes, `severity` and `retryable` fields
- `UCIAuditSession` — tamper-evident, chain-hashed audit session with `verify_integrity()` and portable JSON export

### Core engine
- `HandshakeEngine` — 9-stage fail-closed handshake lifecycle
- `PolicyEngine` — governance evaluation with allow / allow_with_restrictions / defer / deny outcomes
- `TrustRecord` — enforced trust state machine (unknown → discovered → verified → trusted / restricted → suspended / revoked)
- `UCIRegistry` — in-memory node registry

### Schemas
- Three canonical JSON Schemas (`uci-spec.org`) for manifest, response, and audit session
- `schema_validator.py` — language-agnostic schema validation layer with structured issue reporting

### CLI
- `uci_validate.py` — 8-stage manifest validator with `--strict`, `--json`, `--quiet`, `--no-colour` flags
- Exit codes: `0` valid · `1` invalid · `2` usage error

### Test coverage
- 331 tests · 0 failures
- Formal compliance suite: 63 rules across C-MAN / C-GOV / C-HSK / C-RSP / C-AUD / C-SCH / C-INT
- Spec alignment tests verifying implementation matches all 23 specification documents

### Specification
- 23 specification documents in `docs/`
- `SPEC.md` index at root
- Canonical test vectors in `test_vectors/`

---

## Roadmap

### [0.2.0] — planned
- HTTP transport layer — real over-the-wire UCI between processes
- First production integration (Niles/NYALS orchestrator)

### [0.3.0] — planned
- UCI Registry service
- Interoperability validation against external implementations

### [1.0.0] — planned
- After external review and interoperability testing
- Stable protocol surface

---

*See `patches/` for detailed development patch notes.*
