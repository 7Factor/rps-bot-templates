# TypeScript Team Template

## Your editing boundary

Except for the fixed root `team-submission.json` declaration,
`templates/typescript/team_source/` is the only Team-editable directory. Keep
`strategy.ts` and its four-argument `chooseMove` function. Additional `.ts`
files may live in Team Source, and optional `.csv`, `.json`, and `.txt` data may
live below `team_source/resources/`. Package manifests, lockfiles, dependencies,
wrappers, entrypoints, compiler configuration, container files, symbolic links,
and other infrastructure are outside the **Team Source** boundary. Team Source
is limited to 64 files, 256 KiB per file, and 1 MiB total.

## Strategy contract

Keep the exact exported function signature:

```typescript
export function chooseMove(
  turn: number,
  myHistory: string,
  opponentHistory: string,
  rng: { nextInt(upperExclusive: number): number }
): string
```

`turn` begins at `0`; both histories contain prior moves oldest first. Return
only `"R"`, `"P"`, or `"S"`, and use the supplied deterministic `rng` for every
random choice. The Runner-owned wrapper controls protocol I/O, readiness,
seeding, environment sanitation, and process lifecycle; Team Source must not
implement those responsibilities.

## Build and test

The matching Catalog Release selects Node.js 24.19.0 from the latest
upstream-supported LTS line and pins the compatible stable TypeScript 6.0.3
compiler package by checksum. For a native check, install Node.js 24 or newer
and exactly TypeScript 6.0.3, then run:

```sh
./check-team-template --template typescript --mode native
```

Without those local tools, use Docker. It runs the identical TypeScript-owned
`templates/typescript/build-and-test` entrypoint inside the exact pinned Catalog
Release toolchain, supplies the catalog-owned compiler archive, and disables
networking:

```sh
./materialize-core-tool .core/rps-tournament
./check-team-template --template typescript --mode docker
```

`./validate-team --allow-pull` performs participant-local
**Advisory Validation**
against the exact pinned TypeScript Language Environment. It gives
compatibility feedback, including a Practice Match, but cannot accept a Bot
Artifact. Only organizer-controlled **Final Validation** on the official ARM64
platform can authorize a Bot Artifact for a Tournament roster.
