# Kotlin Team Template

## Your editing boundary

`templates/kotlin/team_source/` is the only Team-editable directory. Keep
`Strategy.kt`, its `Strategy` object, and its four-argument `chooseMove`
function. Additional `.kt` files may live in Team Source, and optional `.csv`,
`.json`, and `.txt` data may live below `team_source/resources/`. Build files,
external libraries, wrappers, entrypoints, package declarations, and container
files are outside the **Team Source** boundary. Team Source is limited to 64
files, 256 KiB per file, and 1 MiB total.

## Strategy contract

Keep the exact function signature:

```kotlin
fun chooseMove(
    turn: Int,
    myHistory: String,
    opponentHistory: String,
    rng: RandomGenerator
): String
```

`turn` begins at `0`; both histories contain prior moves oldest first. Return
only `"R"`, `"P"`, or `"S"`, and use `rng.nextInt(limit)` for every random
choice. The Runner-owned wrapper controls protocol I/O, lifecycle, readiness,
and the deterministic Seed Adapter.

## Build and test

The matching Catalog Release selects Kotlin 2.4.10 and Java 25 LTS (Temurin
25.0.3+9). Team Source is standard-library-only and cannot add dependencies;
the networkless build verifies the vendored Kotlin compiler distribution from
the Catalog lock. With exactly Kotlin 2.4.10 and a Java 25 JDK installed, run:

```sh
./check-team-template --template kotlin --mode native
```

Without local Kotlin and Java, Docker runs the identical Kotlin-owned script in
the exact pinned Catalog Release toolchain with networking disabled:

```sh
./materialize-core-tool .core/rps-tournament
./check-team-template --template kotlin --mode docker
```

`./validate-team --template kotlin --allow-pull` performs participant-local
**Advisory Validation** and a Practice Match. It cannot accept a Bot Artifact;
only organizer-controlled **Final Validation** on the official ARM64 platform
can authorize one for a Tournament roster.
