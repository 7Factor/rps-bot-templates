# RPS Bot Templates

This context describes the shared repository in which Teams develop source for
Bot Artifacts that play in a Rock–Paper–Scissors Tournament.

## Language

**Tournament**:
The complete competition for one accepted roster, comprising qualification and
playoffs and, unless no eligible Team remains, one Tournament Champion.
_Avoid_: Event, competition run

**Team**:
The competitive identity that owns one Tournament entry, appears in standings,
and may become Tournament Champion.
_Avoid_: Bot, participant, player, entrant

**Team Source**:
The Team-editable files accepted as build input under a Language Environment's
controlled source schema. Team Source is not itself a Bot Artifact.
_Avoid_: Bot Artifact, participant Docker image

**Submission Candidate**:
A specific Team Source commit that passed advisory validation and is eligible
for organizer selection under the cutoff policy. It is not an official Bot
Artifact.
_Avoid_: Bot Artifact, winning submission

**Team Submission Declaration**:
The commit-resident `team-submission.json` through which a Team selects one
stable Team Template language ID. Tooling resolves it against the verified Team
Template collection; it cannot define a Language Environment or override a
Template Release.
_Avoid_: Bot Artifact Manifest, organizer selection record, build configuration

**Language Environment**:
A versioned organizer-owned adapter package in the Language Environment Catalog
that defines the Team Source schema, wrapper, Seed Adapter, pinned runtimes,
networkless build recipe, readiness contract, entrypoint, and conformance
fixtures for one supported language.
_Avoid_: Team Template, participant repository, runtime image

**Language Environment Catalog**:
The Runner-owned collection of supported Language Environments.
_Avoid_: Dependency registry, mutable latest catalog

**Team Template**:
A participant-facing starter project maintained in this repository that adapts
one Language Environment for Team coding and claims compatibility with one exact
Catalog Release.
_Avoid_: Language Environment, catalog fixture, official wrapper

**Template Release**:
An immutable publication of a Team Template that records its own identity and
an exact Catalog Release compatibility claim.
_Avoid_: Catalog Release, mutable branch, latest template

**Catalog Release**:
An immutable publication of the Runner-owned Language Environment Catalog and
its assets, identified by an exact Runner commit, package version, catalog path
and content identity, and offline bundle identity.
_Avoid_: Template Release, catalog branch, latest catalog

**Bot Artifact**:
The immutable, single-platform container image built and accepted by the
organizer for a Team in one Tournament. Team-built and GitHub-built images are
confidence artifacts only.
_Avoid_: Team Source, submission, Team

**Advisory Validation**:
A compatibility check performed before organizer acceptance, such as Team-local
or CI validation, that provides feedback but cannot authorize a Bot Artifact for
a Tournament.
_Avoid_: Final Validation, official certification, roster acceptance

**Final Validation**:
The organizer-controlled, authoritative validation of selected Team Source
against the exact Catalog Release and official target platform; only its result
can authorize the resulting Bot Artifact for a Tournament roster.
_Avoid_: Advisory Validation, CI check, Team-built image

**Source Digest**:
The deterministic identity of validated Team Source contents, independent of a
branch name, repository URL, or mutable working directory.
_Avoid_: Git commit, Bot Artifact digest

**Seed Adapter**:
The versioned part of an organizer-owned language wrapper that deterministically
maps a bot-visible 64-bit seed into that language's random-number generator.
_Avoid_: Seed derivation, system randomness

**Bot-visible Seed**:
The deterministic per-Team seed supplied to a Bot Artifact's Seed Adapter for
one Match.
_Avoid_: Tournament Seed, shared seed
