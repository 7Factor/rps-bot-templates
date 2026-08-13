# Add the Ruby Team Template

Status: resolved

Blocked by: 04; rps-tournament multi-language-environments 08

## Parent

[Multi-language Team Templates](../PRD.md)

## What to build

Deliver an independently releasable Ruby Team Template with equivalent
strategy, build, test, native-development, Docker-development, and Runner
compatibility behavior.

## Acceptance criteria

- [x] Ruby uses the latest upstream-supported stable release at preparation time
  and is pinned immutably in the matching Catalog and Template Releases.
- [x] The Ruby starter implements the common strategy contract and includes
  deterministic unit tests for legal moves and seeded behavior.
- [x] One Ruby-owned script builds and tests the starter with a compatible local
  Ruby toolchain.
- [x] Docker invokes that identical Ruby-owned script and passes the complete
  build and unit-test suite without Ruby installed on the host.
- [x] Dependency resolution is deterministic and complies with the matching
  Language Environment's networkless build policy.
- [x] Advisory Validation consumes the matching Ruby Language Environment from
  the exact pinned Catalog Release and passes its complete conformance contract.
- [x] Ruby guidance documents Team Source boundaries, native prerequisites,
  Docker usage, and the distinction between Advisory and Final Validation.
- [x] Ruby can be selected, checked, and released without changing another Team
  Template's descriptor or release identity.

## Answer

The independently releasable `ruby-template-v1` starter implements the shared
strategy contract and deterministic SplitMix64 behavior. Its Ruby-owned
`build-and-test` entrypoint runs the same complete suite in native and Docker
modes under the catalog's standard-library-only dependency policy.

The repository consumes exact `catalog-v13` coordinates at Runner commit
`9952cf795b3f5ffb26b9d3de9c886c5669eb6464`. The pinned Docker suite and full
participant-local Advisory Validation passed, including the Practice Match.
The collection and Team guide expose Ruby independently and document Team
Source ownership, prerequisites, Docker use, and Advisory versus Final
Validation authority.
