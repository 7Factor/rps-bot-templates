# Publishing a Template Release

A Template Release is an immutable participant-facing starting point for one
indexed Team Template. Its annotated Git tag manifest records the exact
repository commit, language ID, descriptor-derived Team Source and digest,
Advisory Validation workflow identity, and exact Catalog Release compatibility
claim.

## Create and verify one Template Release

Use a clean checkout with complete Git history. Select the stable language ID
and the unused Template Release tag named by its descriptor:

```text
git status --short
./materialize-core-tool .core/rps-tournament
./release-team-template --template <language-id> manifest <release-tag>
./release-team-template --template <language-id> create <release-tag>
./release-team-template --template <language-id> verify <release-tag>
```

For Python, the independently addressable Template Release is prepared with:

```text
./release-team-template --template python manifest python-template-v3
./release-team-template --template python create python-template-v3
./release-team-template --template python verify python-template-v3
```

Creation verifies the content-addressed Runner bundle, exact clean Runner
commit, complete Catalog Release identity map, selected Team Source and Source
Digest, supported Team Template version, and immutable workflow action references.
It rejects a dirty checkout, ambiguous or unknown template selection, mismatched
catalog lock, changed Team Template, mutable action reference, reused tag, or a
tag that differs from the selected descriptor.

Push the exact Template Release commit and annotated tag together. Published
Template Release tags are never moved, deleted, or recreated.

```text
git push origin HEAD
git push origin refs/tags/<release-tag>
```

## Verify from a clean clone

```text
git clone <template-repository> rps-bot-templates
cd rps-bot-templates
git switch --detach <release-tag>^{}
./materialize-core-tool .core/rps-tournament
RPS_CORE_PATH=.core/rps-tournament ./check-team-template --template <language-id> --mode docker
RPS_CORE_PATH=.core/rps-tournament ./validate-team --template <language-id>
RPS_CORE_PATH=.core/rps-tournament ./release-team-template --template <language-id> verify <release-tag>
```

Verification rejects a dirty tree, lightweight or malformed tag, tag aimed at
another commit, changed Team Template or workflow, changed compatibility claim,
and mismatch between the lock and materialized Runner Catalog Release.

## Create Team branches

Create every Team branch from the dereferenced Template Release commit:

```text
git switch --create team/<team-slug> <release-tag>^{}
git push --set-upstream origin team/<team-slug>
```

The Team then records the same language ID without organizer communication:

```text
./select-team-template <language-id>
git add team-submission.json
git commit -m "Select Team Template"
git push
```

The selection command refuses to replace an existing declaration. After adding
it once, the Team may change only the Team Source directory named by the
resolved descriptor and documented in its language-owned participant guide.
Template maintenance may continue to pass `--template`; Team validation reads
the committed declaration when that option is omitted.

## Corrections and replacement versions

A published Template Release is never repaired in place. A Team Template,
workflow, guidance, or Catalog Release compatibility change requires a new
supported Team Template version and Template Release tag. Release notes identify
the superseded Template Release and replacement. Historical `template-v1`
branches remain historical; the removed singular interface is not restored to
prepare or verify them.
