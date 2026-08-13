# Clojure Team Template

## Your editing boundary

`templates/clojure/team_source/` is the only Team-editable directory. Keep
`strategy.clj`, its `strategy` namespace, and its four-argument `choose-move`
function. Additional `.clj` files may live in Team Source, and optional `.csv`,
`.json`, and `.txt` data may live below `team_source/resources/`. Dependency
manifests, external libraries, wrappers, entrypoints, and container files are
outside the **Team Source** boundary. Team Source is limited to 64 files,
256 KiB per file, and 1 MiB total.

## Strategy contract

Keep the exact function signature:

```clojure
(defn choose-move [turn my-history opponent-history rng])
```

`turn` begins at `0`; both histories contain prior moves oldest first. Return
only `"R"`, `"P"`, or `"S"`, and use `(.nextInt rng limit)` for every random
choice. The Runner-owned wrapper controls protocol I/O, lifecycle, readiness,
and the deterministic Seed Adapter.

## Build and test

The matching Catalog Release selects Clojure 1.12.5, Clojure CLI 1.12.5.1664,
and Java 25 (Temurin 25.0.3+9). Team Source cannot add dependencies; the
networkless build verifies the three approved Clojure runtime jars from the
Catalog lock. With the exact Clojure and Java toolchain installed, run:

```sh
./check-team-template --template clojure --mode native
```

Without local Clojure and Java, Docker runs the identical Clojure-owned script
in the exact pinned Catalog Release toolchain with networking disabled:

```sh
./materialize-core-tool .core/rps-tournament
./check-team-template --template clojure --mode docker
```

`./validate-team --template clojure --allow-pull` performs participant-local
**Advisory Validation** and a Practice Match. It cannot accept a Bot Artifact;
only organizer-controlled **Final Validation** on the official ARM64 platform
can authorize one for a Tournament roster.
