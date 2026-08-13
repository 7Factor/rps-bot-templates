# Python Team guide

The Python Team Template is a working starter for the four-argument Tournament
strategy contract. It is compatible with the exact Runner-owned Python Language
Environment pinned by `core-tool.lock.json`.

## Your editing boundary

Except for the fixed root `team-submission.json` declaration,
`templates/python/team_source/` is the only Team-editable directory for this
template. Start with
[`team_source/strategy.py`](team_source/strategy.py). Keep all Python modules
inside that directory and place optional `.csv`, `.json`, or `.txt` data below
`team_source/resources/`.

Do not add dependency manifests, wrappers, Dockerfiles, entrypoints, workflows,
or catalog files to Team Source. Runner-owned examples include `wrapper.py`,
`Dockerfile`, `requirements.lock`, `.github` workflows, and `catalog.json`.
Organizer-owned paths are never part of Team Source.
Python Team Source is standard-library-only and is limited to 64 files, 256 KiB
per file, and 1 MiB total.

## Strategy contract

Define `choose_move` exactly once and unconditionally with four arguments:

```python
def choose_move(turn, my_history, opponent_history, rng):
    return rng.choice(("R", "P", "S"))
```

`turn` begins at `1`; both histories contain prior moves oldest first; and
`rng` is the wrapper-provided deterministic random generator. Return only `R`,
`P`, or `S`, and use `rng` for every random choice. The organizer-owned wrapper
handles protocol I/O, readiness, seeding, and process lifecycle. Team Source
must not implement those responsibilities.

## Build and test

Docker is the supported acceptance path and requires no host Python used for
starter behavior. The pinned Python 3.14.6 toolchain image must already be
present in a running native Linux/AMD64 or Linux/ARM64 Docker engine:

```sh
./check-team-template --template python --mode docker
```

The Docker dispatcher reads the immutable build-toolchain coordinate from the
exact pinned Catalog Release and runs
`templates/python/build-and-test` inside that container with networking
disabled. It does not maintain a second Docker-only test implementation.

For faster feedback with compatible Python 3.9 or newer installed locally, run
the identical entrypoint through native mode:

```sh
./check-team-template --template python --mode native
```

Both modes compile the starter and run its unit tests for the four-argument
contract, legal moves, and deterministic seeded behavior. Missing native Python
and unavailable Docker engines have separate diagnostics.

## Advisory Validation

After the starter check passes, run the complete container contract against the
matching Python Language Environment from the exact pinned Catalog Release:

```sh
./validate-team --allow-pull
```

This freezes Team Source, builds a disposable confidence image, and exercises
readiness, protocol, deterministic seeding, isolation, resources, lifecycle,
and practice-Match conformance. It is Advisory Validation only and is
insufficient for official Tournament entry. Only organizer Final Validation can
accept a Bot Artifact.

GitHub Advisory Validation checks every commit pushed to a `team/**` branch on
native Linux/AMD64. It binds the exact source commit to the exact Template
Release, starter digest, pinned Catalog Release, and complete conformance result,
then retains that evidence for 90 days. A newer push cancels a superseded
in-progress run without removing the latest completed green Submission
Candidate. A practice Match proves compatibility, but its score or winner is
not an acceptance condition. GitHub results remain advisory and insufficient
for official Tournament entry.

Create Team branches from the dereferenced `python-template-v3^{}` annotated
Template Release. A published release is immutable; compatibility updates use a
new Python Template Release identity. Use the assigned `team/<team-slug>` name
and keep one branch per Team. Shared branch visibility does not provide
submission secrecy; do not inspect or copy another Team's strategy.

The [submission cutoff and manual handoff policy](../../SUBMISSION_CUTOFF.md)
defines how the organizer selects an eligible commit and exports the exact Team
Source for Final Validation.
