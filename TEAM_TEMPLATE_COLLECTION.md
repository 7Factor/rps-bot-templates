# Maintaining the Team Template collection

[`team-templates.json`](team-templates.json) is the sole discovery index for
participant-facing Team Templates. Every stable language ID owns the same
repository layout:

```text
templates/<language-id>/team-template.json
templates/<language-id>/TEAM_GUIDE.md
templates/<language-id>/build-and-test
templates/<language-id>/team_source/
templates/<language-id>/tests/
```

The descriptor binds the controlled Team Source, participant guidance,
language-owned build-and-test entrypoint, independently addressable Template
Release, Advisory Validation workflow, and matching Runner-owned Language
Environment. Paths are repository-relative POSIX paths.
The [Python descriptor](templates/python/team-template.json) and
[Go descriptor](templates/go/team-template.json), and
[Java descriptor](templates/java/team-template.json), and
[TypeScript descriptor](templates/typescript/team-template.json), and
[C# descriptor](templates/csharp/team-template.json), and
[Rust descriptor](templates/rust/team-template.json), and
[Ruby descriptor](templates/ruby/team-template.json), and
[Clojure descriptor](templates/clojure/team-template.json), and
[JavaScript descriptor](templates/javascript/team-template.json), and
[Kotlin descriptor](templates/kotlin/team-template.json) are independent instances
of this layout.

Collection loading rejects duplicate language IDs, missing descriptors or bound
files, unsafe paths, symbolic-link targets, mutable runtime references, and
templates whose Language Environment is absent or contract-only in the exact
pinned Catalog Release. Commands may omit `--template` only while the collection
contains exactly one entry. An ambiguous or unknown selection fails and lists
the available language IDs.

## Check, validate, and prepare one Template Release

Use the stable language ID at every shared entrypoint:

```sh
./check-team-template --template <language-id> --mode docker
./check-team-template --template <language-id> --mode native
./validate-team --template <language-id>
./release-team-template --template <language-id> manifest <release-tag>
./release-team-template --template <language-id> create <release-tag>
./release-team-template --template <language-id> verify <release-tag>
```

Those explicit selectors are for collection maintenance. A Team branch records
its selector once with `./select-team-template <language-id>` and subsequently
runs `./validate-team`; validation and CI read `team-submission.json`.

Docker and native checks execute the identical language-owned `build-and-test`
file. Docker selects its immutable toolchain from the descriptor's matching
Language Environment in the exact pinned Catalog Release. Advisory Validation
and Template Release preparation derive Team Source, language identity,
guidance, workflow, and Template Release metadata from the same descriptor.

For the Go Template Release, a clean clone can run:

```sh
./materialize-core-tool .core/rps-tournament
RPS_CORE_PATH=.core/rps-tournament ./check-team-template --template go --mode docker
RPS_CORE_PATH=.core/rps-tournament ./validate-team --template go
RPS_CORE_PATH=.core/rps-tournament ./release-team-template --template go manifest go-template-v1
```

For the Java Template Release, use the same collection boundary with
`--template java` and the independent `java-template-v1` release tag.
TypeScript uses `--template typescript` and the independent
`typescript-template-v1` release tag.
C# uses `--template csharp` and the independent `csharp-template-v2` release
tag.
Rust uses `--template rust` and the independent `rust-template-v1` release tag.
Ruby uses `--template ruby` and the independent `ruby-template-v1` release tag.
Clojure uses `--template clojure` and the independent `clojure-template-v1` release tag.
JavaScript uses `--template javascript` and the independent
`javascript-template-v1` release tag.
Kotlin uses `--template kotlin` and the independent `kotlin-template-v1`
release tag.

## Checklist for adding a Team Template

1. Publish and pin the matching conforming Language Environment in the exact
   Runner-owned Catalog Release.
2. Add `templates/<language-id>/` with its descriptor, controlled Team Source,
   participant guide, tests, and executable `build-and-test` entrypoint.
3. Add the descriptor to `team-templates.json`; do not add a language switch or
   path constant to shared commands or workflows.
4. Prove native and Docker command resolution invoke the same entrypoint, and
   run the complete starter build and tests through Docker.
5. Exercise Advisory Validation, including practice Match conformance, against
   the pinned Language Environment.
6. Assign a new, language-specific Template Release version and tag; verify its
   Source Digest and manifest from a clean clone.
7. Update participant and maintainer documentation, then run all guard and
   repository tests.

## Migration from the singular shape

The Python Team Template moved to `templates/python/` and was replaced by
`python-team-template-v2` / `python-template-v2`. The former root-level
`team-template.json` and `team_source/`, the root participant guide, the
`template-v1` Template Release path, and their no-selection fallback behavior were
removed after the collection path passed Docker checks and complete Advisory
Validation. Existing branches created from the historical `template-v1` tag
remain historical Template Releases; new branches and Template Releases use the
indexed Python descriptor and `templates/python/TEAM_GUIDE.md`.

## Ownership boundary

This layout preserves [ADR 0001](docs/adr/0001-consume-runner-owned-catalog.md).
This repository owns Team Templates, Team guidance, collection metadata,
participant build-and-test entrypoints, Advisory Validation entrypoints, and
Template Releases. It does not copy or redefine Runner-owned Language
Environments, wrappers, Seed Adapters, runtimes, build recipes, readiness
contracts, entrypoints, or conformance fixtures.
