# Java Team Template

Except for the fixed root `team-submission.json` declaration, edit files only
under `templates/java/team_source/`. That directory is the
controlled Java **Team Source** boundary accepted by the Runner-owned Java
Language Environment. Keep `Strategy.java`, and implement its four-argument
`chooseMove` method. Java Team Source is Java SE standard-library-only; build
files, external dependencies, package declarations, wrappers, entrypoints, and
container configuration are outside the Team boundary.

The matching Catalog Release selects Java 25, the latest upstream-designated
LTS line at preparation time, and pins Temurin 25.0.3+9 toolchain images by
platform digest. For a native check, install a Java 25 or newer JDK and run:

```sh
./check-team-template --template java --mode native
```

Without a local JDK, use Docker. It runs the identical Java-owned
`templates/java/build-and-test` entrypoint inside the exact pinned Catalog
Release toolchain with networking disabled:

```sh
./materialize-core-tool .core/rps-tournament
./check-team-template --template java --mode docker
```

`./validate-team --allow-pull` performs participant-local
**Advisory Validation** against the exact pinned Java Language Environment. It provides
compatibility feedback, including a Practice Match, but cannot accept a Bot
Artifact. Only organizer-controlled **Final Validation** on the official ARM64
platform can authorize a Bot Artifact for a Tournament roster.
