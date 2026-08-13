# Add the Brainf-ck Team Template

Status: resolved

Blocked by: 04; rps-tournament multi-language-environments 12

## Parent

[Multi-language Team Templates](../PRD.md)

## What to build

Deliver an independently releasable Brainf-ck Team Template with equivalent
strategy, build, test, native-development, Docker-development, and Runner
compatibility behavior.

## Acceptance criteria

- [x] Brainf-ck uses the exact dialect, tape and cell semantics, implementation,
  and execution limits selected by the matching Language Environment, pinned
  immutably in the Catalog and Template Releases without creating a second
  interpreter contract in this repository.
- [x] The Brainf-ck starter implements the common strategy contract and includes
  deterministic tests for legal moves and seeded behavior without copying the
  Runner-owned wrapper or Seed Adapter.
- [x] One Brainf-ck-owned script validates and tests the starter with the
  compatible local implementation.
- [x] Docker invokes that identical Brainf-ck-owned script and passes the
  complete validation and test suite without a Brainf-ck implementation
  installed on the host.
- [x] Dependency resolution is deterministic and complies with the matching
  Language Environment's networkless build policy.
- [x] Advisory Validation consumes the matching Brainf-ck Language Environment
  from the exact pinned Catalog Release and passes its complete conformance
  contract, including source and execution bounds.
- [x] Brainf-ck guidance documents Team Source boundaries, the exact input and
  move encodings, native prerequisites, Docker usage, and the distinction
  between Advisory and Final Validation.
- [x] Brainf-ck can be selected, checked, and released without changing another
  Team Template's descriptor or release identity.

## Answer

Added `brainf-ck-team-template-v1` as an independently selectable Team Template
and published the annotated `brainf-ck-template-v1` release at commit
`99a64426402dca4ab5f406c6632348544a2a1987`. Its only Team Source file is
`strategy.bf`; the `,.` starter returns the Runner-provided deterministic seeded
move and does not copy the wrapper, Seed Adapter, or interpreter.

The Brainf-ck-owned `build-and-test` entrypoint loads the exact Catalog-owned
interpreter asset. The same script passed in native mode and in the pinned
Linux/ARM64 Docker toolchain with networking disabled. Participant-local
Advisory Validation passed the complete Brainf-ck conformance suite and Practice
Match, including the Catalog-owned source and execution bounds.

The repository consumes `catalog-v19` at Runner commit
`d1ccc03975c14ca6ac539896587e8fa9402d3307`, Catalog identity
`rps-language-environment-catalog-v1@sha256:5cf3fc6de60bbf5da3256fd3987440fe098f99dfcff9450787b1683338d29f69`,
and offline bundle identity
`rps-runner-offline-bundle-v1@sha256:440fe7070f3811449970a23b7c4b581c517effe146987d80f820fb261d9ed7ee`.
The Template Release records Team Source digest
`sha256:bb421af61619384243b38c070cb688c4a7342c7f3ae6f135893e70dbef3a865a`
and Team Template digest
`sha256:8d31d22eb3dbb6bdd1a1336a298e2917e8d66c9e082b56d4b66e6cca1b67119b`.
The full repository suite passed 137 tests with 15 expected opt-in/toolchain
skips.
