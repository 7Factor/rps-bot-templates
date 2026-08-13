# Submission cutoff and manual source handoff

This policy selects a Submission Candidate without turning a mutable Team branch
or an advisory image into an official Tournament input. Record every time below
in Coordinated Universal Time (UTC), and identify every commit by its full
40-character SHA.

## Cutoff rule

For each Team, the default selection is the latest completed green commit at or
before the declared deadline. A commit is eligible only when it was pushed to
that Team's assigned branch and its `Team Advisory Validation` run completed
successfully no later than the deadline. "Latest" means the eligible run with
the latest GitHub completion time; author and committer dates do not establish
cutoff eligibility.

A Team may explicitly select an earlier eligible green commit by giving the
organizer its full SHA before the deadline. The organizer may also fall back to
an earlier eligible green commit under the repair policy below. In either case,
the selection record must explain the exception instead of silently replacing
the default.

For every Team, preserve an immutable selection record containing:

- the declared deadline, Team identity, assigned branch, exact Template Release
  tag, Template repository commit, and committed `team-submission.json`;
- the selected source commit and whether it was the default or an explicitly
  chosen earlier commit;
- the GitHub run ID, URL, completion time, conclusion, and downloaded
  `team-advisory-<commit>` artifact;
- the artifact's `eligibility-evidence.json` and `validation-report.json`; and
- the person making the selection, selection time, and any exception rationale.

A run still queued or running at the deadline is not a completed green run. A
rerun completed after the deadline does not make a commit eligible. Never infer
eligibility from the current branch head, a commit date, or an image left on a
runner.

## GitHub handoff runbook

Download the evidence artifact from the selected run through the organizer's
normal authenticated GitHub session. Confirm before transport that
`eligibility-evidence.json` has `result` equal to `passed`, `authority` equal to
`github-advisory`, and `source_commit` equal to the selected full SHA. Its
`template_release` tag, commit, Team Template version and digest, and Advisory
Validation workflow identity must equal the selected annotated Template Release
manifest. Preserve that manifest with the selection record.

Use a new working directory and substitute the actual repository URL, Team
branch, and selected SHA. These are deliberate, manual organizer actions:

```sh
git clone --branch <team-branch> <repository-url> selected-team
git -C selected-team pull --ff-only origin <team-branch>
git -C selected-team fetch origin <selected-40-character-sha>
git -C selected-team checkout --detach <selected-40-character-sha>
git -C selected-team rev-parse HEAD

git -C selected-team show \
  <selected-40-character-sha>:team-submission.json \
  > selected-team-submission.json

RPS_CORE_PATH=<pinned-core-checkout> \
  <verified-template-release-checkout>/select-team-template --show \
  --declaration selected-team-submission.json \
  > resolved-team-submission.json

mkdir source-export
team_source_path=<resolved-team-submission-team-source-path>
language_environment=<resolved-team-submission-language-environment>
git -C selected-team archive --format=tar \
  --prefix=team-source/ <selected-40-character-sha>:"$team_source_path" \
  | tar -xf - -C source-export
```

The reported `HEAD` must equal the selection record's `source_commit`. The
resolved language ID, Template Release, Team Template version, Team Source path,
and Language Environment must equal the verified Advisory Validation evidence
and annotated Template Release manifest. Export only the resolved descriptor's
`team_source_path`; do not use a catalog,
wrapper, workflow, recipe, or core lock taken from a Team branch. The
organizer's verified Template Release
checkout supplies `core-tool.lock.json`; the exact materialized Runner checkout
named by that lock is the authority for the pinned Catalog Release.

Check out the exact core commit named by that lock and make it importable as the
pinned core's documentation directs. Then pass the exported local directory to
the core tool's existing boundary:

```sh
PYTHONPATH=<pinned-core-checkout> python3 -m rps_runner.source_cli \
  --catalog <pinned-core-checkout>/language_environments/catalog-v1/catalog.json \
  --environment "$language_environment" \
  --source source-export/team-source \
  --bundle validated-source-bundle
```

Read `validated-source-bundle/source-bundle.json`. Its `source_digest` must
match `source_digest` in `eligibility-evidence.json`, and its
`versions.catalog` must match `catalog` in that evidence. The evidence
`source_commit` must also match the detached checkout. Stop and investigate any
mismatch; do not build or validate an official image from it. Retain the
exported source and source bundle with the selection record.

This repository intentionally provides no automated branch discovery,
automated authentication, automated pulling, or automated cutoff enforcement.
Clone, pull, evidence download, commit selection, checkout, and export remain
manual transport. Language selection is not manual: it comes from the exact
commit's declaration and is reconciled with the verified Template Release. The
core tool begins at the validated local-directory
boundary and remains responsible for source freezing, building, and validation.

## No-GitHub delivery

When GitHub is unavailable, the organizer may accept Team Source as a manually
delivered directory or ZIP archive under a separately declared delivery
deadline. Record the Team, deadline, receipt time, delivery channel, filename,
archive SHA-256 when applicable, and the person accepting it. Preserve the
original delivery unchanged.

For a ZIP archive, inspect its file list for absolute paths and `..` traversal
before extracting it into a new isolated directory. Locate the directory whose
contents correspond to the selected descriptor's Team Source path; do not
accept organizer-owned catalog, wrapper, recipe, workflow, or dependency files
as Team Source. Pass that local
directory to the same pinned source validator command shown above, using the
Catalog Release pinned by the verified Template Release.

The resulting source bundle establishes the delivered Source Digest and frozen
catalog identity. Record `source_digest` and `versions.catalog` in place of the
unavailable GitHub evidence, together with the delivery record. A manual
delivery has no green GitHub status and receives no presumption of
compatibility; it must still complete organizer Final Validation.

## Validation authority

GitHub/AMD64 evidence is Advisory Validation only. It identifies a Submission
Candidate and provides compatibility confidence, but it cannot create or
authorize a Tournament-eligible Bot Artifact. The selected, source-validated
Team Source must be rebuilt on native Linux/ARM64 by the organizer against the
pinned Catalog Release named by the Template Release. Only a passing organizer
Final Validation of that rebuilt ARM64 image can create a Tournament-eligible
Bot Artifact.

Never import the disposable GitHub image into the official roster, and never
substitute a GitHub run, participant-local result, AMD64 build, multi-platform
image, or remote registry image for organizer Final Validation.

## Post-cutoff compatibility-only repair

A post-cutoff repair is exceptional. It is allowed only when organizer Final
Validation exposes a demonstrated ARM64 compatibility defect in the exact
selected source. The change must be the smallest compatibility-only repair and
must preserve strategy behavior. It must not add a strategy enhancement,
algorithm change, tuning change, new decision data, or other competitive
improvement. If the failure is not demonstrably compatibility-only, use an
eligible earlier green commit or reject the Submission Candidate.

Before evaluating a repaired source, preserve the original source and its
selection record unchanged. The repair record must retain:

- the original source and original Source Digest;
- the complete diff from original to replacement source;
- a plain-language explanation of the ARM64 incompatibility and why the change
  cannot enhance strategy;
- the replacement source and replacement Source Digest; and
- the replacement's organizer Final Validation identity and resulting Bot
  Artifact identity, if validation passes.

The organizer and Team representative must approve the recorded diff and
explanation. Run the replacement through the same pinned source validator,
native ARM64 rebuild, and organizer Final Validation; prior GitHub evidence does
not transfer to the replacement Source Digest. Link the original and replacement
records permanently so an audit can reconstruct exactly what changed and why.
