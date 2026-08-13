# Add the Clojure Team Template

Status: resolved

Blocked by: 04; rps-tournament multi-language-environments 09

## Parent

[Multi-language Team Templates](../PRD.md)

## What to build

Deliver an independently releasable Clojure Team Template with equivalent
strategy, build, test, native-development, Docker-development, and Runner
compatibility behavior.

## Acceptance criteria

- [x] Clojure uses the latest upstream-supported stable release and a compatible
  upstream-supported Java LTS at preparation time, pinned immutably in the
  matching Catalog and Template Releases.
- [x] The Clojure starter implements the common strategy contract and includes
  deterministic unit tests for legal moves and seeded behavior.
- [x] One Clojure-owned script builds and tests the starter with a compatible
  local Clojure and Java toolchain.
- [x] Docker invokes that identical Clojure-owned script and passes the complete
  build and unit-test suite without Clojure or Java installed on the host.
- [x] Dependency resolution is deterministic and complies with the matching
  Language Environment's networkless build policy.
- [x] Advisory Validation consumes the matching Clojure Language Environment
  from the exact pinned Catalog Release and passes its complete conformance
  contract.
- [x] Clojure guidance documents Team Source boundaries, native prerequisites,
  Docker usage, and the distinction between Advisory and Final Validation.
- [x] Clojure can be selected, checked, and released without changing another
  Team Template's descriptor or release identity.

## Answer

The independently releasable `clojure-template-v1` starter implements the
shared four-argument strategy contract and deterministic seeded behavior. Its
Clojure-owned `build-and-test` entrypoint runs the same two-test, 200-assertion
suite natively or inside the catalog-pinned Clojure 1.12.5 / Java 25 Docker
toolchain with networking disabled and the approved runtime jars hash-verified.

The repository consumes exact `catalog-v15` coordinates at Runner commit
`e31d9b88a43a0c58934b306b96015bd300b1685d`. The pinned Docker suite and full
participant-local Advisory Validation passed, including the Practice Match.
Collection and Team guidance expose Clojure independently and document Team
Source ownership, exact native prerequisites, Docker usage, and Advisory versus
Final Validation authority without changing another Template Release identity.
