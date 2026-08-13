# Rust Team Template

## Your editing boundary

Except for the fixed root `team-submission.json` declaration,
`templates/rust/team_source/` is the only Team-editable directory. Keep
`strategy.rs` and its four-argument `choose_move` function. Additional `.rs`
files may live in Team Source, and optional `.csv`, `.json`, and `.txt` data may
live below `team_source/resources/`. Cargo manifests, lock files, external
crates, wrappers, entrypoints, container files, toolchain selectors, and
symbolic links are outside the **Team Source** boundary. Team Source is limited
to 64 files, 256 KiB per file, and 1 MiB total.

## Strategy contract

Keep the exact public function signature:

```rust
pub fn choose_move(
    turn: usize,
    my_history: &str,
    opponent_history: &str,
    rng: &mut RpsRandom
) -> &'static str
```

`turn` begins at `0`; both histories contain prior moves oldest first. Return
only `"R"`, `"P"`, or `"S"`, and use the supplied deterministic `rng` for every
random choice. The Runner-owned wrapper controls protocol I/O, readiness,
seeding, environment sanitation, and process lifecycle.

## Build and test

The matching Catalog Release selects Rust 1.97.1 and pins its build toolchain
and execution runtime by platform digest. Rust Team Source is
standard-library-only, so the build invokes `rustc` directly and never resolves
crates.io or another mutable dependency source. For a native check, install a
Rust toolchain compatible with edition 2024 (Rust 1.85 or newer) and run:

```sh
./check-team-template --template rust --mode native
```

Without a local toolchain, use Docker. It runs the identical Rust-owned
`templates/rust/build-and-test` entrypoint inside the exact pinned Catalog
Release toolchain with networking disabled:

```sh
./materialize-core-tool .core/rps-tournament
./check-team-template --template rust --mode docker
```

`./validate-team --allow-pull` performs participant-local
**Advisory Validation**
against the exact pinned Rust Language Environment. It gives
compatibility feedback, including a Practice Match, but cannot accept a Bot
Artifact. Only organizer-controlled **Final Validation** on the official ARM64
platform can authorize a Bot Artifact for a Tournament roster.
