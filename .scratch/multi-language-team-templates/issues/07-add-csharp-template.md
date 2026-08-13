# Add the C# Team Template

Status: resolved

Blocked by: 04; rps-tournament multi-language-environments 06

## Parent

[Multi-language Team Templates](../PRD.md)

## What to build

Deliver an independently releasable C# Team Template with equivalent strategy,
build, test, native-development, Docker-development, and Runner compatibility
behavior.

## Acceptance criteria

- [x] The .NET SDK is the latest upstream-supported LTS release at preparation
  time and is pinned immutably in the matching Catalog and Template Releases.
- [x] The C# starter implements the common strategy contract and includes
  deterministic unit tests for legal moves and seeded behavior.
- [x] One C#-owned script builds and tests the starter with a compatible local
  .NET SDK.
- [x] Docker invokes that identical C#-owned script and passes the complete build
  and unit-test suite without .NET installed on the host.
- [x] Dependency restoration is deterministic and complies with the matching
  Language Environment's networkless build policy.
- [x] Advisory Validation consumes the matching C# Language Environment from the
  exact pinned Catalog Release and passes its complete conformance contract.
- [x] C# guidance documents Team Source boundaries, native prerequisites, Docker
  usage, and the distinction between Advisory and Final Validation.
- [x] C# can be selected, checked, and released without changing another Team
  Template's descriptor or release identity.

## Answer

Added an independently selectable C# Team Template pinned to the exact,
independently proven `catalog-v8` Runner release. The starter implements the common `ChooseMove`
contract with legal-move and same-seed deterministic tests. Its single
C#-owned `build-and-test` entrypoint runs with a compatible native .NET 10 SDK
or inside the catalog-pinned SDK 10.0.302 Docker image.

The build clears NuGet package sources and restores no external packages, so
native and network-disabled Docker development use the same deterministic
standard-library-only project. Complete participant-local Advisory Validation
passed against the immutable C# Language Environment, including the Practice
Match. Guidance documents the Team Source boundary, native and Docker modes,
and Advisory/Final Validation authority. The template has its own descriptor,
Source Digest, `csharp-team-template-v2` identity, and `csharp-template-v2`
replacement release tag without changing any other template release identity.
The v2 release supersedes the immutable v1 release, whose offline-bundle
coordinate did not match its named Catalog Release.
