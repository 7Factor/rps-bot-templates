# Go Team guide

The Go Team Template is a working starter for the Tournament strategy contract.
It is compatible with the exact Runner-owned Go Language Environment pinned by
`core-tool.lock.json`, which selects Go 1.26.5.

## Your editing boundary

Except for the fixed root `team-submission.json` declaration,
`templates/go/team_source/` is the only Team-editable directory. Implement
`ChooseMove` in `team_source/strategy.go`; optional `.csv`, `.json`, and `.txt`
resources may live below `team_source/resources/`. Team Source may contain Go
strategy files and those approved resources only. Do not add `go.mod`, `go.sum`,
`vendor/`, wrappers, Dockerfiles, entrypoints, workflows, links, or other
infrastructure. The environment is standard-library-only and limits Team Source
to 64 files, 256 KiB per file, and 1 MiB total.

## Strategy contract

Keep the exact function signature:

```go
func ChooseMove(
    turn int,
    myHistory, opponentHistory string,
    rng *rand.Rand,
) string
```

`turn` begins at 0. Histories contain prior moves oldest first. Return only
`"R"`, `"P"`, or `"S"`, and use the supplied `rng` for every random choice.
The organizer-owned wrapper controls protocol I/O, readiness, seed adaptation,
environment sanitation, and process lifecycle; Team Source must not define
`main`, `init`, protocol handling, or its own seed source.

## Build and test

Docker is the supported acceptance path and needs no host Go installation. It
uses the exact Go 1.26.5 build-toolchain image from the pinned Catalog Release,
disables networking, and invokes the language-owned script:

```sh
./check-team-template --template go --mode docker
```

For faster feedback with a compatible local Go toolchain, run the identical
entrypoint natively:

```sh
./check-team-template --template go --mode native
```

The script disables toolchain and module downloads, compiles the complete Team
Source tree, and runs deterministic tests for legal moves and seeded behavior.
The organizer-owned conformance suite separately verifies the Seed Adapter.

## Advisory and Final Validation

Run the complete pinned container contract with:

```sh
./validate-team --allow-pull
```

This is Advisory Validation only: it freezes Team Source and checks build,
readiness, protocol, deterministic seeding, isolation, resources, lifecycle,
and a practice Match. Only organizer-controlled Final Validation on Linux/ARM64
can authorize a Bot Artifact for a Tournament roster.

Create Team branches from the dereferenced `go-template-v1^{}` annotated
Template Release. Python and Go releases remain independently addressable;
changing one template does not change the other's descriptor or release tag.
