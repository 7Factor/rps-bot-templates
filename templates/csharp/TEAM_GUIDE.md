# C# Team Template

## Your editing boundary

Except for the fixed root `team-submission.json` declaration,
`templates/csharp/team_source/` is the only Team-editable directory. Keep
`Strategy.cs` and its four-argument `ChooseMove` method. Additional `.cs` files
may live in Team Source, and optional `.csv`, `.json`, and `.txt` data may live
below `team_source/resources/`. Project files, NuGet configuration, package
dependencies, wrappers, entrypoints, container files, and symbolic links are
outside the **Team Source** boundary. Team Source is limited to 64 files,
256 KiB per file, and 1 MiB total.

## Strategy contract

Keep the exact public method signature:

```csharp
public static string ChooseMove(
    int turn,
    string myHistory,
    string opponentHistory,
    RpsRandom rng)
```

`turn` begins at `0`; both histories contain prior moves oldest first. Return
only `"R"`, `"P"`, or `"S"`, and use the supplied deterministic `rng` for every
random choice. The Runner-owned wrapper controls protocol I/O, readiness,
seeding, environment sanitation, and process lifecycle.

## Build and test

The matching Catalog Release selects .NET 10 LTS and pins .NET SDK 10.0.302
plus runtime 10.0.10 by platform digest. C# Team Source is standard-library-only;
the build clears NuGet package sources and restores no external packages. For a
native check, install a compatible .NET SDK 10 or newer and run:

```sh
./check-team-template --template csharp --mode native
```

Without a local SDK, use Docker. It runs the identical C#-owned
`templates/csharp/build-and-test` entrypoint inside the exact pinned Catalog
Release toolchain with networking disabled:

```sh
./materialize-core-tool .core/rps-tournament
./check-team-template --template csharp --mode docker
```

`./validate-team --allow-pull` performs participant-local
**Advisory Validation**
against the exact pinned C# Language Environment. It gives
compatibility feedback, including a Practice Match, but cannot accept a Bot
Artifact. Only organizer-controlled **Final Validation** on the official ARM64
platform can authorize a Bot Artifact for a Tournament roster.
