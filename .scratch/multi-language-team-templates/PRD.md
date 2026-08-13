# Multi-language Team Templates

Status: ready-for-agent

Implementation status: not started

## Problem Statement

This repository publishes one Python Team Template through paths, metadata,
validation commands, workflows, tests, and release tooling that assume there is
only one supported language. Adding more templates directly to that shape would
duplicate behavior, couple releases together, and make it unclear which Team
Source, Language Environment, and toolchain a command targets.

Teams should be able to build and test a template either with a compatible
language toolchain installed on the host or with Docker when that toolchain is
not installed. Maintainers should not need every language toolchain on their
machines. The Docker path must be sufficient to implement and verify a template,
while the native path must invoke the same repository-owned build-and-test
script so that the two paths do not acquire different behavior.

## Solution

Reorganize the repository around a collection of independently identified Team
Templates. Migrate Python through an expand-and-contract sequence before adding
Go, Java, TypeScript, C#, Ruby, Clojure, JavaScript, Kotlin, Brainf-ck, and
optionally Rust. Give every template one language-owned build-and-test
entrypoint. A root command selects a Team Template and either invokes that
entrypoint on the host or invokes the exact same file inside a development
toolchain container.

Docker is the required implementation and CI verification path. Native
execution is a supported convenience for Teams with the selected toolchain
installed, but maintainers are not required to install or execute every native
toolchain. The successful Docker path verifies the shared script itself rather
than a separate Docker-only implementation.

Each Team Template adapts one matching Runner-owned Language Environment from
the exact Catalog Release pinned by this repository. This repository does not
copy or replace the Language Environment's official wrapper, Seed Adapter,
runtime, build recipe, readiness contract, entrypoint, or conformance fixtures.
The shared template script is participant-facing development tooling; official
Bot Artifact construction and Final Validation remain in `rps-tournament`.

## User Stories

1. As a Team, I want to choose a supported language, so that I can implement my strategy in a familiar toolchain.
2. As a Team, I want every Team Template to expose the same strategy concepts, so that language choice does not change the game contract.
3. As a Team, I want a working starter strategy, so that I can begin by changing behavior rather than assembling a project.
4. As a Team, I want one documented build-and-test entrypoint, so that I do not have to learn organizer internals.
5. As a Team with a local toolchain, I want to run that entrypoint natively, so that feedback is fast.
6. As a Team without a local toolchain, I want to run the template with Docker, so that language installation is optional.
7. As a Team, I want the native and Docker paths to execute the same script, so that they do not disagree about how my source is built or tested.
8. As a Team, I want a missing native toolchain to produce an actionable diagnostic, so that I know to use Docker.
9. As a Team, I want an unavailable Docker engine to produce an actionable diagnostic, so that I know how to restore validation.
10. As a Team, I want deterministic starter tests, so that repeated checks are trustworthy.
11. As a Team, I want the template check to reject an invalid move, so that protocol mistakes are found before submission.
12. As a Team, I want the template check to cover deterministic random behavior, so that seeded strategies behave consistently.
13. As a Team, I want clear Team Source boundaries, so that I do not accidentally edit organizer-owned files.
14. As a Team, I want language-specific guidance beside the starter, so that the required commands and file conventions are discoverable.
15. As a maintainer, I want a stable per-language repository layout, so that adding a Team Template does not require another reorganization.
16. As a maintainer, I want one root template index, so that tooling can discover supported Team Templates without hard-coded language lists.
17. As a maintainer, I want each Team Template to identify its matching Language Environment, so that compatibility is explicit.
18. As a maintainer, I want releases to target one Team Template, so that changing one language does not silently change another language's release identity.
19. As a maintainer, I want validation commands to require an explicit or unambiguous language selection, so that the wrong Team Source cannot be checked.
20. As a maintainer, I want the existing Python behavior preserved during migration, so that the reorganization does not regress current Teams.
21. As a maintainer, I want the old single-template shape removed only after Python uses the new shape, so that every intermediate change stays verifiable.
22. As a maintainer, I want Docker to be the required acceptance environment, so that implementation does not depend on workstation toolchains.
23. As a maintainer, I want upstream-supported runtime versions pinned in immutable releases, so that builds remain reproducible after upstream moves on.
24. As a maintainer, I want a documented runtime update policy, so that "latest LTS" does not become a mutable build input.
25. As a maintainer, I want a new language to pass the complete Runner conformance contract before being advertised as supported, so that starter availability does not overstate Tournament readiness.
26. As an organizer, I want every Team Template to consume the exact pinned Catalog Release, so that Advisory Validation and Final Validation agree on the Language Environment contract.
27. As an organizer, I want official Bot Artifact construction to remain Runner-owned, so that participant convenience tooling cannot redefine Tournament execution.
28. As an organizer, I want each language to receive equivalent build, test, deterministic RNG, and local-development affordances, so that infrastructure does not favor a language.
29. As a contributor, I want a documented checklist for adding a Team Template, so that future languages follow the same contract.
30. As a contributor, I want contract tests over the root dispatcher and template descriptors, so that repository wiring failures are caught without inspecting implementation details.

## Implementation Decisions

- The initial required Team Templates are Python, Go, Java, TypeScript, C#,
  Ruby, Clojure, JavaScript, Kotlin, and Brainf-ck. Rust is an optional follow-on
  template and must meet the same acceptance bar before being advertised as
  supported.
- The repository will expose a stable collection layout keyed by language ID.
  Each entry will contain one Team Template descriptor, participant-facing
  starter and guidance, a controlled Team Source subtree, and its build-and-test
  entrypoint.
- A root template index will enumerate templates. Commands, workflows, tests,
  and release tooling will derive supported languages and paths from descriptors
  instead of embedding a Python-specific path or language ID.
- Each descriptor will identify the matching Runner-owned Language Environment
  and the exact participant-facing commands. A Team Template cannot be released
  as supported unless that Language Environment exists in the pinned Catalog
  Release and passes its complete conformance contract.
- One language-owned build-and-test script is the parity seam. Native mode runs
  it directly with the host toolchain. Docker mode runs the identical file in a
  pinned development toolchain container. There will be no separate native and
  Docker implementations of the build or tests.
- The root command will select a language and execution mode, provide consistent
  diagnostics, and delegate language behavior to the template entrypoint. It
  will not contain language-specific build logic.
- Docker is the normative implementation and automated verification path.
  Native mode is supported by construction through the shared entrypoint, but
  CI and acceptance do not require the corresponding host toolchain.
- Development toolchain container inputs will be immutable. When possible they
  will be derived from the exact pinned Catalog Release rather than maintained
  as a second runtime catalog in this repository.
- "Latest LTS" is a selection policy applied when a Language Environment and
  Team Template release are prepared, never a mutable runtime reference. If an
  ecosystem designates LTS releases, the latest upstream-supported LTS is
  selected and then pinned exactly. If it has no LTS designation, the latest
  upstream-supported stable release is selected and pinned. TypeScript uses the
  latest supported Node.js LTS with an exactly pinned compatible TypeScript
  compiler, while JavaScript uses the latest supported Node.js LTS. Kotlin uses
  the stable compiler and compatible Java LTS selected by its Language
  Environment. Brainf-ck uses the exact dialect and implementation contract
  selected by its Language Environment. Updating a pin requires a new Catalog
  Release compatibility claim and Template Release.
- Template unit tests will cover the language-facing strategy contract,
  deterministic seeded behavior, legal moves, and starter behavior. Runner
  Advisory Validation remains the higher acceptance seam for Team Source,
  container build, readiness, protocol, isolation, resources, lifecycle, and
  practice-Match conformance.
- The current singular Python shape will migrate through expand, migrate, and
  contract tickets. The new collection-aware interface will coexist with the
  old paths until Python and its release workflow are green through the new
  interface.
- Template Releases are independently addressable by language. A release binds
  one Team Template identity and Source Digest to one exact Catalog Release;
  unrelated templates do not silently join its release identity.
- Existing domain ownership remains unchanged by ADR 0001: this repository owns
  Team Templates, Team guidance, and Advisory Validation entrypoints;
  `rps-tournament` owns every Language Environment and official execution asset.

## Testing Decisions

- The primary new test seam is the root template check command. Tests select a
  language and Docker mode, then observe build success, test success, stable
  diagnostics, and failure propagation from the template entrypoint.
- Every language ticket must execute its full starter build and unit-test suite
  through Docker. No ticket may rely on the corresponding host toolchain being
  installed for acceptance.
- Contract tests will prove that native and Docker modes resolve and invoke the
  same language-owned entrypoint. Native toolchains do not need to be installed
  in CI; command resolution and missing-tool diagnostics can be tested with
  controlled substitutes.
- The existing Team branch, Advisory Validation, Template Release, and
  cross-repository cutover tests are prior art and remain the highest seams for
  compatibility, immutable release identity, and organizer handoff behavior.
- Python migration tests must prove unchanged starter Source behavior and a
  deliberate release identity transition. Compatibility must not be inferred
  only from file movement.
- Descriptor and index tests will reject duplicate language IDs, unsafe paths,
  missing entrypoints, mutable runtime references, mismatched Language
  Environments, and templates absent from the pinned catalog.
- Each required language will run equivalent behavioral cases rather than tests
  coupled to its framework internals.
- A clean clone must be able to run the Docker check with repository-owned and
  pinned offline inputs under the same network policy promised by the matching
  Language Environment.

## Out of Scope

- Implementing or publishing new Language Environments in `rps-tournament`.
- Moving official wrappers, Seed Adapters, Docker build recipes, readiness
  contracts, entrypoints, conformance fixtures, or Final Validation into this
  repository.
- Requiring maintainers or CI hosts to install Go, Java, Node.js/TypeScript,
  .NET, Ruby, Clojure, Kotlin, a Brainf-ck implementation, or Rust locally.
- Claiming that an unexecuted host/toolchain combination has been independently
  certified. Native mode is supported through the Docker-exercised shared script
  but remains environment-dependent.
- Automatically tracking mutable upstream `latest` tags.
- Supporting languages beyond Python, Go, Java, TypeScript, C#, Ruby, Clojure,
  JavaScript, Kotlin, Brainf-ck, and optional Rust in this effort.

## Further Notes

The first new language after the Python migration should be Go. It is the
tracer bullet that proves the collection, release, local/Docker parity, and
Runner compatibility seams work for more than the migrated template. Java,
TypeScript, C#, Ruby, Clojure, JavaScript, Kotlin, Brainf-ck, and Rust remain
blocked on that proof so discoveries are folded into the shared contract once
rather than independently.

Language tickets also have an external dependency: a matching conforming
Language Environment must be published by `rps-tournament` and included in the
Catalog Release pinned here. Those cross-repository tickets should be created
before implementation begins; this repository's tickets do not assume authority
to create Runner-owned assets.
