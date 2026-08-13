# Add the Kotlin Team Template

Status: resolved

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

## Answer

Added `kotlin-team-template-v1` as an independently selectable Team Template
and published the immutable `kotlin-template-v1` Template Release at commit
`f45bf6033e02b7e608746a8750a3cfb328b1d649`. Its Team Source implements the
common `chooseMove` contract, returns only legal moves, and includes
deterministic same-seed tests without copying the Runner-owned Seed Adapter.

The Kotlin-owned `build-and-test` entrypoint compiles the complete starter and
runs the same tests in native and Docker modes. Docker passed with the exact
pinned Kotlin 2.4.10 and Java 25 LTS toolchain and networking disabled. The
vendored official compiler distribution is verified by SHA-256 before use, and
Team Source remains standard-library-only.

The repository consumes `catalog-v18` at Runner commit
`0ce3603722b04be9a617563a1f36f52c8cb7f465`, Catalog identity
`rps-language-environment-catalog-v1@sha256:47ce9003164c1fe9dfb4f1fd7c711e2fd11d45f041de1f5cb37fd7fad06f8c2d`,
and offline bundle identity
`rps-runner-offline-bundle-v1@sha256:035977c663d8c2e9613e26a75252799a802ab50e94d8a5c41cdb4c6cdfd34331`.
Participant-local Advisory Validation passed the exact Kotlin conformance suite
and Practice Match. The Template Release records Team Source digest
`sha256:bcd877bcaa724553412bc0a86583da310105f8da55846df3d2406c142f38ae2e`
and Team Template digest
`sha256:aa45a22e6d674370ac67abfb6f8e5d597b6d100488f197057b2f2246e709cda2`.
The full repository suite passed 131 tests with 15 expected opt-in skips; the
Docker build/test and Advisory Validation integration tests passed when
enabled. Both Standards and Spec review axes passed after resolving their
catalog-assertion duplication and Template Release findings.
