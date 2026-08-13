# Add the optional Rust Team Template

Status: resolved

Blocked by: 04; rps-tournament multi-language-environments 07

## Parent

[Multi-language Team Templates](../PRD.md)

## What to build

Deliver Rust as an optional independently releasable Team Template, without
lowering the build, test, native-development, Docker-development, or Runner
compatibility bar used by required languages.

## Acceptance criteria

- [x] The Rust toolchain is the latest upstream-supported stable release at
  preparation time and is pinned immutably in the matching Catalog and Template
  Releases.
- [x] The Rust starter implements the common strategy contract and includes
  deterministic unit tests for legal moves and seeded behavior.
- [x] One Rust-owned script builds and tests the starter with a compatible local
  Rust toolchain.
- [x] Docker invokes that identical Rust-owned script and passes the complete
  build and unit-test suite without Rust installed on the host.
- [x] Dependency resolution is deterministic and complies with the matching
  Language Environment's networkless build policy.
- [x] Advisory Validation consumes the matching Rust Language Environment from
  the exact pinned Catalog Release and passes its complete conformance contract.
- [x] Rust guidance documents Team Source boundaries, native prerequisites,
  Docker usage, and the distinction between Advisory and Final Validation.
- [x] Rust is advertised as supported only after meeting every required-language
  conformance and release criterion.

## Answer

The independently releasable `rust-template-v1` starter implements the shared
strategy contract and deterministic SplitMix64 seed behavior. Its Rust-owned
`build-and-test` entrypoint compiles and runs the same complete suite in native
and Docker modes, with an empty immutable dependency definition that satisfies
the Runner's networkless policy.

The repository consumes the exact `catalog-v12` offline bundle at Runner commit
`5e2dae30f5cc99393047ae91a59679825555e90e`. All 100 collection tests passed,
and all seven Rust-specific tests passed against the pinned Docker toolchain,
including the complete participant-local Advisory Validation and practice Match.
The collection and team guidance now advertise Rust and document Team Source
ownership, prerequisites, Docker usage, and Advisory versus Final authority.
