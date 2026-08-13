# Ruby Team Template

## Your editing boundary

`templates/ruby/team_source/` is the only Team-editable directory. Keep
`strategy.rb` and its four-argument `choose_move` method. Additional `.rb`
files may live in Team Source, and optional `.csv`, `.json`, and `.txt` data may
live below `team_source/resources/`. Gemfiles, lock files, external gems,
wrappers, entrypoints, and container files are outside the **Team Source**
boundary. Team Source is limited to 64 files, 256 KiB per file, and 1 MiB total.

## Strategy contract

Keep the exact method signature:

```ruby
def choose_move(turn, my_history, opponent_history, rng)
```

`turn` begins at `0`; both histories contain prior moves oldest first. Return
only `"R"`, `"P"`, or `"S"`, and use the supplied deterministic `rng` for every
random choice. The Runner-owned wrapper controls protocol I/O and lifecycle.

## Build and test

The matching Catalog Release selects Ruby 4.0.6 and pins its build toolchain
and execution runtime by platform digest. Ruby Team Source is standard-library-only.
Install Ruby 4.0 or newer and run:

```sh
./check-team-template --template ruby --mode native
```

Without local Ruby, Docker runs the identical Ruby-owned script in the exact
pinned Catalog Release toolchain with networking disabled:

```sh
./materialize-core-tool .core/rps-tournament
./check-team-template --template ruby --mode docker
```

`./validate-team --template ruby --allow-pull` performs participant-local
**Advisory Validation** and a Practice Match. It cannot accept a Bot Artifact;
only organizer-controlled **Final Validation** on the official ARM64 platform
can authorize one for a Tournament roster.
