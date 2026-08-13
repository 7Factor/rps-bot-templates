from __future__ import annotations

from pathlib import Path
import re
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = PROJECT_ROOT / ".github" / "workflows" / "team-advisory-validation.yml"
TEAM_GUIDE = PROJECT_ROOT / "templates/python/TEAM_GUIDE.md"


class GithubAdvisoryWorkflowTests(unittest.TestCase):
    workflow = WORKFLOW.read_text()

    def test_every_team_commit_uses_exact_source_and_core_commits_on_native_amd64(self) -> None:
        workflow = self.workflow

        self.assertIn("branches: [\"team/**\"]", workflow)
        self.assertIn("ref: ${{ github.sha }}", workflow)
        self.assertIn("fetch-depth: 0", workflow)
        self.assertIn("persist-credentials: false", workflow)
        self.assertIn('runs-on: ubuntu-24.04', workflow)
        self.assertIn('PLATFORM: linux/amd64', workflow)
        self.assertIn('lock["runner"]["commit"]', workflow)
        self.assertIn("./materialize-core-tool .core/rps-tournament", workflow)
        self.assertNotIn("repository: ${{", workflow)
        self.assertNotIn("qemu", workflow.lower())
        self.assertNotIn("buildx", workflow.lower())
        self.assertNotIn("--push", workflow)

    def test_branch_is_bound_to_one_verified_template_release(self) -> None:
        workflow = self.workflow

        self.assertIn("from template_collection import load_collection", workflow)
        self.assertIn("from team_submission import resolve_team_submission", workflow)
        self.assertIn('collection = load_collection(Path("."), catalog_path)', workflow)
        self.assertIn('resolve_team_submission(Path("."), collection)', workflow)
        self.assertNotIn("candidates = []", workflow)
        self.assertIn('git rev-parse "${TEAM_TEMPLATE_RELEASE}^{}"', workflow)
        self.assertIn(
            '--template "$TEAM_TEMPLATE_ID" verify "$TEAM_TEMPLATE_RELEASE"',
            workflow,
        )
        self.assertIn('\":(exclude)${TEAM_SOURCE_PATH}/**\"', workflow)
        self.assertIn('\":(exclude)team-submission.json\"', workflow)
        self.assertIn('"template_release"', workflow)
        for field in (
            '"team_template_version"',
            '"team_template_digest"',
            '"starter_source_digest"',
            '"advisory_validation_workflow"',
        ):
            with self.subTest(field=field):
                self.assertIn(field, workflow)

    def test_pinned_core_owns_the_frozen_catalog_build_and_advisory_conformance(self) -> None:
        workflow = self.workflow

        catalog = ".core/rps-tournament/language_environments/catalog-v1/catalog.json"
        self.assertIn("PYTHONPATH: .core/rps-tournament", workflow)
        self.assertIn("python3 -m rps_runner.source_cli", workflow)
        self.assertIn('--source "$TEAM_SOURCE_PATH"', workflow)
        self.assertIn('--environment "$TEAM_LANGUAGE_ENVIRONMENT"', workflow)
        self.assertIn("--catalog \"$CATALOG\"", workflow)
        self.assertEqual(workflow.count("python3 -m rps_runner.artifact_cli"), 1)
        self.assertIn("python3 -m rps_runner.certification_cli", workflow)
        self.assertIn("--mode github-advisory", workflow)
        self.assertIn("--platform \"$PLATFORM\"", workflow)
        self.assertIn("--profile docker-execution-v1", workflow)
        self.assertIn("CATALOG: " + catalog, workflow)
        self.assertNotIn(
            "CATALOG: language_environments/catalog-v1/catalog.json", workflow
        )

    def test_ephemeral_runner_fetches_all_catalog_pinned_language_images(self) -> None:
        workflow = self.workflow

        self.assertIn(
            'from rps_runner.language_environment import load_catalog', workflow
        )
        self.assertEqual(
            workflow.count('load_catalog(Path(os.environ["CATALOG"]))'), 2
        )
        self.assertIn('assets["base_runtime"].content', workflow)
        self.assertIn('selected["build_toolchain"]["image"]', workflow)
        self.assertIn('selected["execution_runtime"]["image"]', workflow)
        self.assertIn(
            'docker pull --platform "$PLATFORM" "$image_reference"', workflow
        )
        self.assertIn(
            'for image_reference in "${language_image_references[@]}"', workflow
        )
        self.assertNotIn(
            'with open("language_environments/catalog-v1/python/runtimes.json")',
            workflow,
        )
        self.assertNotIn("docker push", workflow.lower())
        self.assertIn(
            './check-team-template --template "$TEAM_TEMPLATE_ID" --mode docker',
            workflow,
        )

    def test_job_has_read_only_authority_and_cancels_only_superseded_branch_work(self) -> None:
        workflow = self.workflow

        self.assertIn("permissions:\n  contents: read", workflow)
        self.assertIn("group: team-advisory-${{ github.ref }}", workflow)
        self.assertIn("cancel-in-progress: true", workflow)
        self.assertNotIn("secrets.", workflow)
        self.assertNotIn("docker login", workflow.lower())
        self.assertNotIn("pull_request_target", workflow)

    def test_commit_specific_evidence_is_retained_for_pass_and_failure(self) -> None:
        workflow = self.workflow

        for field in (
            '"source_commit"',
            '"team_submission"',
            '"template_release"',
            '"source_digest"',
            '"catalog"',
            '"core_tool"',
            '"suite"',
            '"recipe"',
            '"wrapper"',
            '"runtime_digest"',
            '"platform"',
            '"disposable_image_identity"',
            '"execution_profile"',
            '"result"',
        ):
            with self.subTest(field=field):
                self.assertIn(field, workflow)
        self.assertIn("if: always()", workflow)
        self.assertIn("name: team-advisory-${{ github.sha }}", workflow)
        self.assertRegex(
            workflow,
            r"uses: actions/upload-artifact@[0-9a-f]{40}",
        )
        self.assertIn("retention-days: 90", workflow)
        self.assertIn('destination / "team-submission.json"', workflow)
        self.assertIn("practice_match_result_gate", workflow)
        self.assertIn("id: evidence", workflow)
        self.assertIn("steps.evidence.outputs.result != 'passed'", workflow)
        self.assertNotRegex(workflow, r"(?i)(smoke_match|practice_match).*(winner|score)")
        self.assertNotIn("bot-artifact-manifest.json\n", workflow)

    def test_team_guide_explains_github_evidence_and_authority(self) -> None:
        guide = " ".join(TEAM_GUIDE.read_text().split())

        for statement in (
            "every commit pushed to a `team/**` branch",
            "native Linux/AMD64",
            "exact source commit",
            "90 days",
            "superseded in-progress run",
            "latest completed green Submission Candidate",
            "score or winner",
            "exact Template Release",
            "starter digest",
            "insufficient for official Tournament entry",
        ):
            with self.subTest(statement=statement):
                self.assertIn(statement, guide)


if __name__ == "__main__":
    unittest.main()
