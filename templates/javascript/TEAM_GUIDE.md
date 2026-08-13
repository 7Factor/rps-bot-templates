# JavaScript Team Template

## Your editing boundary

`templates/javascript/team_source/` is the only Team-editable directory. Keep
`strategy.js` and its four-argument `chooseMove` export. Additional `.js` files
may live in Team Source, and optional `.csv`, `.json`, and `.txt` data may live
below `team_source/resources/`. Package manifests, external libraries,
wrappers, entrypoints, and container files are outside the **Team Source**
boundary. Team Source is limited to 64 files, 256 KiB per file, and 1 MiB total.

## Strategy contract

Keep the exact function signature and CommonJS export:

```javascript
function chooseMove(turn, myHistory, opponentHistory, rng) {
  return "R";
}

module.exports = { chooseMove };
```

`turn` begins at `0`; `myHistory` and `opponentHistory` contain prior moves
oldest first. Return only `"R"`, `"P"`, or `"S"`, and use
`rng.nextInt(limit)` for every random choice. The Runner-owned wrapper controls
protocol I/O, lifecycle, readiness, and the deterministic Seed Adapter.

## Build and test

The matching Catalog Release selects Node.js 24.19.0. Team Source is
standard-library-only: do not add registry dependencies, `package.json`, lock
files, or `node_modules`. With Node.js 24 or newer installed, run:

```sh
./check-team-template --template javascript --mode native
```

Without local Node.js, Docker runs the identical JavaScript-owned script in the
exact pinned Catalog Release toolchain with networking disabled:

```sh
./materialize-core-tool .core/rps-tournament
./check-team-template --template javascript --mode docker
```

`./validate-team --template javascript --allow-pull` performs participant-local
**Advisory Validation** and a Practice Match. It cannot accept a Bot Artifact;
only organizer-controlled **Final Validation** on the official ARM64 platform
can authorize one for a Tournament roster.
