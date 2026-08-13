# Brainf-ck Team Template

## Your editing boundary

`templates/brainf-ck/team_source/` is the only **Team Source** directory. Edit
only `strategy.bf`; wrappers, interpreters, entrypoints, dependency files, and
container definitions remain organizer-owned. Team Source contains exactly one
ASCII file with a maximum size of 64 KiB.

## Strategy contract

The pinned Catalog Release defines Brainf-ck RPS dialect v1: the eight standard
commands `><+-.,[]`, with all other ASCII characters treated as comments;
standard bracket loops; 8-bit wrapping cells; and a fixed, zero-initialized,
non-wrapping tape of 30,000 cells. Each turn permits at most 1,000,000 steps,
50 ms, and one output byte. Output must be exactly ASCII `R`, `P`, or `S`.

Input is a binary Turn record in this order:

1. seeded move byte (`R`, `P`, or `S`) from the Runner-owned deterministic
   64-bit LCG stream: start with `state = seed`, repeat
   `state = state * 6364136223846793005 + 1442695040888963407 modulo 2^64`
   exactly `turn + 1` times, then select `R`, `P`, or `S` for
   `state modulo 3` values `0`, `1`, or `2`
2. opponent's last move, or `R` before any history exists
3. turn-modulo move: select `R`, `P`, or `S` for turn modulo 3 values `0`, `1`,
   or `2`
4. seed as an unsigned 8-byte little-endian integer
5. turn as an unsigned 8-byte little-endian integer
6. own history length as an unsigned 2-byte little-endian integer, then history
7. opponent history length in the same format, then history

History bytes are ASCII `R`, `P`, or `S`. Reading beyond that record is an
execution fault. The starter `,.` reads and returns the deterministic seeded
move; it does not copy the Runner-owned wrapper or Seed Adapter.

## Build and test

With Python 3 installed, the native check loads the exact Catalog-owned
interpreter asset and runs the Brainf-ck-owned starter tests:

```sh
./check-team-template --template brainf-ck --mode native
```

Docker runs the same script in the exact digest-pinned Catalog toolchain with
networking disabled; no host Brainf-ck implementation is required:

```sh
./materialize-core-tool .core/rps-tournament
./check-team-template --template brainf-ck --mode docker
```

`./validate-team --template brainf-ck --allow-pull` performs participant-local
**Advisory Validation**, including the complete Catalog conformance suite and a
Practice Match. It cannot accept a Bot Artifact. Only organizer-controlled
**Final Validation** on the official ARM64 platform can authorize a Bot Artifact
for a Tournament roster.
