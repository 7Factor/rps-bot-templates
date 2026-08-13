# Add the Brainfuck Team Template

Status: ready-for-agent

Blocked by: 04; rps-tournament multi-language-environments 12

## Parent

[Multi-language Team Templates](../PRD.md)

## What to build

Deliver an independently releasable Brainfuck Team Template with equivalent
strategy, build, test, native-development, Docker-development, and Runner
compatibility behavior.

## Acceptance criteria

- [ ] Brainfuck uses the exact dialect, tape and cell semantics, implementation,
  and execution limits selected by the matching Language Environment, pinned
  immutably in the Catalog and Template Releases without creating a second
  interpreter contract in this repository.
- [ ] The Brainfuck starter implements the common strategy contract and includes
  deterministic tests for legal moves and seeded behavior without copying the
  Runner-owned wrapper or Seed Adapter.
- [ ] One Brainfuck-owned script validates and tests the starter with the
  compatible local implementation.
- [ ] Docker invokes that identical Brainfuck-owned script and passes the
  complete validation and test suite without a Brainfuck implementation
  installed on the host.
- [ ] Dependency resolution is deterministic and complies with the matching
  Language Environment's networkless build policy.
- [ ] Advisory Validation consumes the matching Brainfuck Language Environment
  from the exact pinned Catalog Release and passes its complete conformance
  contract, including source and execution bounds.
- [ ] Brainfuck guidance documents Team Source boundaries, the exact input and
  move encodings, native prerequisites, Docker usage, and the distinction
  between Advisory and Final Validation.
- [ ] Brainfuck can be selected, checked, and released without changing another
  Team Template's descriptor or release identity.
