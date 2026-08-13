# Add the Kotlin Team Template

Status: ready-for-agent

Blocked by: 04; rps-tournament multi-language-environments 11

## Parent

[Multi-language Team Templates](../PRD.md)

## What to build

Deliver an independently releasable Kotlin Team Template with equivalent
strategy, build, test, native-development, Docker-development, and Runner
compatibility behavior.

## Acceptance criteria

- [ ] Kotlin uses the stable compiler and compatible upstream-supported Java
  LTS selected by the matching Language Environment, pinned immutably in the
  Catalog and Template Releases.
- [ ] The Kotlin starter implements the common strategy contract and includes
  deterministic unit tests for legal moves and seeded behavior without copying
  the Runner-owned Seed Adapter.
- [ ] One Kotlin-owned script builds and tests the starter with compatible local
  Kotlin and Java toolchains.
- [ ] Docker invokes that identical Kotlin-owned script and passes the complete
  build and unit-test suite without Kotlin or Java installed on the host.
- [ ] Dependency resolution is deterministic and complies with the matching
  Language Environment's networkless build policy.
- [ ] Advisory Validation consumes the matching Kotlin Language Environment
  from the exact pinned Catalog Release and passes its complete conformance
  contract.
- [ ] Kotlin guidance documents Team Source boundaries, native prerequisites,
  Docker usage, and the distinction between Advisory and Final Validation.
- [ ] Kotlin can be selected, checked, and released without changing another
  Team Template's descriptor or release identity.
