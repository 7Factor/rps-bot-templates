# Add the JavaScript Team Template

Status: resolved

Blocked by: 04; rps-tournament multi-language-environments 10

## Parent

[Multi-language Team Templates](../PRD.md)

## What to build

Deliver an independently releasable JavaScript Team Template with equivalent
strategy, build, test, native-development, Docker-development, and Runner
compatibility behavior.

## Acceptance criteria

- [ ] JavaScript uses the latest upstream-supported Node.js LTS at preparation
  time and is pinned immutably in the matching Catalog and Template Releases.
- [ ] The JavaScript starter implements the common strategy contract and
  includes deterministic unit tests for legal moves and seeded behavior.
- [ ] One JavaScript-owned script builds and tests the starter with a compatible
  local Node.js toolchain.
- [ ] Docker invokes that identical JavaScript-owned script and passes the
  complete build and unit-test suite without Node.js installed on the host.
- [ ] Dependency resolution is deterministic and complies with the matching
  Language Environment's networkless build policy.
- [ ] Advisory Validation consumes the matching JavaScript Language Environment
  from the exact pinned Catalog Release and passes its complete conformance
  contract.
- [ ] JavaScript guidance documents Team Source boundaries, native
  prerequisites, Docker usage, and the distinction between Advisory and Final
  Validation.
- [ ] JavaScript can be selected, checked, and released without changing another
  Team Template's descriptor or release identity.

## Answer

Added `javascript-team-template-v1` as an independently selectable Team
Template and published the immutable `javascript-template-v1` Template Release
at commit `8ce524d515ac504ae45b2239960e6e2e99cebdb8`. Its controlled Team Source
implements the common `chooseMove` contract, returns only legal moves, and has
deterministic same-seed behavior tests without copying the Runner-owned Seed
Adapter or its golden vectors.

The JavaScript-owned `build-and-test` entrypoint syntax-checks the complete
starter and runs the same tests in native and Docker modes. The exact pinned
Node.js 24.19.0 Linux/ARM64 toolchain ran that entrypoint with networking
disabled. JavaScript remains standard-library-only, with package manifests,
lock files, registry dependencies, and `node_modules` outside Team Source.

The repository now consumes `catalog-v16` at Runner commit
`87296899a88f1e1a091fc08454be45a7354a73cb`, Catalog identity
`rps-language-environment-catalog-v1@sha256:c70dac15b4c0220cb9315a92db7e3be696fd44a1f944a30a6f6c771864ebfb97`,
and offline bundle identity
`rps-runner-offline-bundle-v1@sha256:ec7db7d442a24a9bcc193ec42db1130e35bef8b2df255d5ce4828431f3ccb8b9`.
Participant-local Advisory Validation passed the exact JavaScript conformance
suite and Practice Match on Linux/ARM64. The Template Release records Team
Source digest
`sha256:86ab51869d8ed3ef8b33b6dfbb6092f1e89953f6c2b01d0a9149940955a179aa`
and Team Template digest
`sha256:70e52808df28430fec2ae69961077bce20e27308f36f5b3edd41c8e8300211d7`.
The full repository suite passed 125 tests with 12 expected integration skips;
the Docker build/test and Advisory Validation integration tests passed when
enabled.
