# Contributing to UCI

UCI is an open protocol. Contributions to the specification and reference implementation are welcome.

## What needs the most help right now

- **External implementations** — a Go or TypeScript implementation using only the JSON schemas and compliance suite as a guide. This is the single most valuable contribution possible.
- **Interoperability testing** — running the compliance suite against an external implementation.
- **Spec review** — reading the documents in `docs/` and filing issues where the spec is ambiguous or incorrect.

## Contribution process

1. Open an issue describing the proposed change before writing code or spec text.
2. For spec changes, reference the relevant document and section.
3. For implementation changes, all existing tests must pass and new behaviour must have tests.
4. Run `python -m pytest test_rig/` before submitting.

## Design principles

Changes MUST NOT:
- Weaken the fail-closed governance guarantee
- Remove canonical enum values without a deprecation path
- Break the three-object model (Manifest / Invocation / Response)

## Contact

Leon Priest · KeystoneAI
