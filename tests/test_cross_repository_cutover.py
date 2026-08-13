from __future__ import annotations

import importlib.machinery
import importlib.util
import json
from pathlib import Path
import sys
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
COMMAND = PROJECT_ROOT / "prove-cross-repository-cutover"
RUNBOOK = PROJECT_ROOT / "CROSS_REPOSITORY_CUTOVER.md"
EXPECTED_SOURCE = "sha256:" + "a" * 64
CATALOG = "rps-language-environment-catalog-v1@sha256:" + "b" * 64
ARTIFACT = "sha256:" + "c" * 64
INDEX = "artifact-set-index-v1@sha256:" + "d" * 64


def load_command_module():
    loader = importlib.machinery.SourceFileLoader("catalog_cutover", str(COMMAND))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    if spec is None:
        raise RuntimeError("cannot load cutover proof command")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    loader.exec_module(module)
    return module


def compatibility() -> dict[str, object]:
    return {
        "format_version": "rps-catalog-compatibility-v1",
        "runner": {"commit": "1" * 40, "package_version": "0.1.0"},
        "catalog": {
            "path": "language_environments/catalog-v1/catalog.json",
            "identity": CATALOG,
            "assets": {
                "python.wrapper": "python-wrapper-v1@sha256:" + "2" * 64
            },
        },
        "offline_bundle": {"identity": "rps-runner-offline-bundle-v1@sha256:" + "3" * 64},
    }


def template_release() -> dict[str, object]:
    return {
        "release_format_version": "template-release-v1",
        "template_repository": {"commit": "4" * 40, "tag": "python-template-v2"},
        "team_template": {
            "version": "python-team-template-v2",
            "path": "templates/python/team_source",
            "digest": "sha256:" + "5" * 64,
            "files": {"strategy.py": "sha256:" + "6" * 64},
            "expected_source_digest": EXPECTED_SOURCE,
            "language_id": "python",
            "language_environment": "python",
            "participant_guidance_path": "templates/python/TEAM_GUIDE.md",
            "build_and_test_entrypoint": "templates/python/build-and-test",
        },
        "catalog_compatibility": compatibility(),
        "advisory_validation": {
            "workflow_path": ".github/workflows/team-advisory-validation.yml",
            "workflow_identity": "team-advisory-validation-v1@sha256:" + "7" * 64,
            "supported_template_version": "python-team-template-v2",
        },
    }


def runner_evidence() -> dict[str, object]:
    coordinates = compatibility()
    return {
        "evidence_format_version": "runner-catalog-independence-v1",
        "status": "passed",
        "compatibility_coordinates": coordinates,
        "catalog_release": {
            "manifest": {
                "compatibility_coordinates": coordinates,
                "platform_runtimes": {
                    "linux/amd64": {"digest": "sha256:" + "8" * 64},
                    "linux/arm64": {"digest": "sha256:" + "b" * 64},
                },
            },
            "participant_template_asset_paths": [],
            "participant_template_digest_fields": [],
            "participant_template_paths": [],
            "unowned_catalog_paths": [],
        },
        "repository_scan": {
            "companion_repository": "absent",
            "dependency_matches": [],
            "participant_template_paths": [],
        },
        "organizer_workflows": {"status": "passed"},
    }


def advisory_eligibility() -> dict[str, object]:
    release = template_release()
    return {
        "result": "passed",
        "authority": "github-advisory",
        "team_submission": {
            "format_version": "rps-team-submission-v1",
            "language_id": "python",
        },
        "source_digest": EXPECTED_SOURCE,
        "catalog": CATALOG,
        "core_tool_commit": "1" * 40,
        "platform": "linux/amd64",
        "template_release": {
            "tag": "python-template-v2",
            "commit": "4" * 40,
            "team_template_version": "python-team-template-v2",
            "team_template_digest": "sha256:" + "5" * 64,
            "starter_source_digest": EXPECTED_SOURCE,
            "advisory_validation_workflow": release["advisory_validation"]["workflow_identity"],
        },
    }


def cross_platform_proof() -> dict[str, object]:
    return {
        "cross_platform_proof_format_version": "cross-platform-proof-v1",
        "result": "passed",
        "source_digest": EXPECTED_SOURCE,
        "shared_contract": {"identities": {"source": EXPECTED_SOURCE, "catalog": CATALOG}},
        "architecture_specific": {
            "linux/amd64": {
                "authority": "advisory",
                "image_role": "disposable-confidence-image",
                "runtime_digest": "sha256:" + "8" * 64,
                "image_digest": "sha256:" + "9" * 64,
                "validation_identity": "validation-report-v1@sha256:" + "a" * 64,
            },
            "linux/arm64": {
                "authority": "canonical",
                "image_role": "bot-artifact",
                "runtime_digest": "sha256:" + "b" * 64,
                "image_digest": ARTIFACT,
                "validation_identity": "validation-report-v1@sha256:" + "c" * 64,
            },
        },
        "official_roster_source": "organizer-final-linux-arm64-only",
    }


def plan() -> dict[str, object]:
    teams = []
    for suffix in "abcd":
        teams.append(
            {
                "team_id": "cutover-" + suffix,
                "roster_ready": True,
                "selected_source": {"source_digest": EXPECTED_SOURCE},
                "bot_artifact_manifest": {
                    "status": "validated",
                    "authority": "canonical",
                    "platform": "linux/arm64",
                    "source_digest": EXPECTED_SOURCE,
                    "artifact_digest": ARTIFACT,
                    "identities": {"catalog": CATALOG},
                },
                "artifact_store_reference": {
                    "index_identity": INDEX,
                    "artifact_digest": ARTIFACT,
                    "platform": "linux/arm64",
                },
            }
        )
    return {
        "tournament_plan_format_version": "tournament-plan-v1",
        "status": "draft",
        "catalog": {"identity": CATALOG},
        "artifact_store": {"index_identity": INDEX},
        "teams": teams,
    }


def competition_record() -> dict[str, object]:
    return {
        "record": {
            "type": "match_terminal",
            "team_ids": ["cutover-a", "cutover-b"],
            "artifact_digests": {
                "cutover-a": ARTIFACT,
                "cutover-b": ARTIFACT,
            },
        }
    }


class CrossRepositoryCutoverTests(unittest.TestCase):
    def test_combines_release_native_and_organizer_evidence(self) -> None:
        module = load_command_module()

        proof = module.build_cutover_proof(
            template_release=template_release(),
            runner_evidence=runner_evidence(),
            starter_source_bundle={
                "source_digest": EXPECTED_SOURCE,
                "versions": {"catalog": CATALOG},
            },
            advisory_eligibility=advisory_eligibility(),
            cross_platform=cross_platform_proof(),
            batch_report={
                "batch_report_format_version": "artifact-batch-report-v1",
                "status": "passed",
                "teams": [
                    {"team_id": "cutover-" + suffix, "status": "validated"}
                    for suffix in "abcd"
                ],
            },
            tournament_plan=plan(),
            competition_record=competition_record(),
        )

        self.assertEqual(proof["result"], "passed")
        self.assertEqual(proof["catalog_identity"], CATALOG)
        self.assertEqual(proof["source_digest"], EXPECTED_SOURCE)
        self.assertEqual(
            proof["starter_source_digest"],
            {
                "expected": EXPECTED_SOURCE,
                "observed": EXPECTED_SOURCE,
                "migration_difference": "none",
            },
        )
        self.assertEqual(
            set(proof["native_platform_evidence"]),
            {"linux/amd64", "linux/arm64"},
        )
        self.assertEqual(proof["organizer_workflow"]["artifact_store_identity"], INDEX)
        self.assertEqual(
            proof["organizer_workflow"]["executed_record_type"], "match_terminal"
        )

    def test_rejects_release_source_catalog_or_authority_drift(self) -> None:
        module = load_command_module()
        evidence = runner_evidence()
        evidence["repository_scan"]["dependency_matches"] = ["workflow.yml"]

        with self.assertRaisesRegex(ValueError, "reverse Runner dependency"):
            module.build_cutover_proof(
                template_release=template_release(),
                runner_evidence=evidence,
                starter_source_bundle={
                    "source_digest": EXPECTED_SOURCE,
                    "versions": {"catalog": CATALOG},
                },
                advisory_eligibility=advisory_eligibility(),
                cross_platform=cross_platform_proof(),
                batch_report={
                    "batch_report_format_version": "artifact-batch-report-v1",
                    "status": "passed",
                    "teams": [],
                },
                tournament_plan=plan(),
                competition_record=competition_record(),
                )

    def test_rejects_team_submission_language_drift(self) -> None:
        module = load_command_module()
        eligibility = advisory_eligibility()
        eligibility["team_submission"]["language_id"] = "go"

        with self.assertRaisesRegex(ValueError, "declared Team Template language"):
            module.build_cutover_proof(
                template_release=template_release(),
                runner_evidence=runner_evidence(),
                starter_source_bundle={
                    "source_digest": EXPECTED_SOURCE,
                    "versions": {"catalog": CATALOG},
                },
                advisory_eligibility=eligibility,
                cross_platform=cross_platform_proof(),
                batch_report={
                    "batch_report_format_version": "artifact-batch-report-v1",
                    "status": "passed",
                    "teams": [],
                },
                tournament_plan=plan(),
                competition_record=competition_record(),
            )

    def test_rejects_missing_native_platform_identity(self) -> None:
        module = load_command_module()
        native_proof = cross_platform_proof()
        del native_proof["architecture_specific"]["linux/amd64"]["runtime_digest"]
        evidence = runner_evidence()
        del evidence["catalog_release"]["manifest"]["platform_runtimes"][
            "linux/amd64"
        ]["digest"]

        with self.assertRaisesRegex(ValueError, "AMD64 .*runtime digest"):
            module.build_cutover_proof(
                template_release=template_release(),
                runner_evidence=evidence,
                starter_source_bundle={
                    "source_digest": EXPECTED_SOURCE,
                    "versions": {"catalog": CATALOG},
                },
                advisory_eligibility=advisory_eligibility(),
                cross_platform=native_proof,
                batch_report={
                    "batch_report_format_version": "artifact-batch-report-v1",
                    "status": "passed",
                    "teams": [
                        {"team_id": "cutover-" + suffix, "status": "validated"}
                        for suffix in "abcd"
                    ],
                },
                tournament_plan=plan(),
                competition_record=competition_record(),
            )

    def test_rejects_malformed_native_platform_identity(self) -> None:
        module = load_command_module()
        native_proof = cross_platform_proof()
        native_proof["architecture_specific"]["linux/amd64"][
            "validation_identity"
        ] = "not-an-identity"

        with self.assertRaisesRegex(ValueError, "AMD64 validation identity"):
            module.build_cutover_proof(
                template_release=template_release(),
                runner_evidence=runner_evidence(),
                starter_source_bundle={
                    "source_digest": EXPECTED_SOURCE,
                    "versions": {"catalog": CATALOG},
                },
                advisory_eligibility=advisory_eligibility(),
                cross_platform=native_proof,
                batch_report={
                    "batch_report_format_version": "artifact-batch-report-v1",
                    "status": "passed",
                    "teams": [
                        {"team_id": "cutover-" + suffix, "status": "validated"}
                        for suffix in "abcd"
                    ],
                },
                tournament_plan=plan(),
                competition_record=competition_record(),
            )

    def test_rejects_execution_record_for_unplanned_artifact(self) -> None:
        module = load_command_module()
        record = competition_record()
        record["record"]["artifact_digests"]["cutover-a"] = "sha256:" + "f" * 64

        with self.assertRaisesRegex(ValueError, "executed Bot Artifact digests"):
            module.build_cutover_proof(
                template_release=template_release(),
                runner_evidence=runner_evidence(),
                starter_source_bundle={
                    "source_digest": EXPECTED_SOURCE,
                    "versions": {"catalog": CATALOG},
                },
                advisory_eligibility=advisory_eligibility(),
                cross_platform=cross_platform_proof(),
                batch_report={
                    "batch_report_format_version": "artifact-batch-report-v1",
                    "status": "passed",
                    "teams": [
                        {"team_id": "cutover-" + suffix, "status": "validated"}
                        for suffix in "abcd"
                    ],
                },
                tournament_plan=plan(),
                competition_record=record,
            )

    def test_command_verifies_all_offline_inputs_before_selected_source(self) -> None:
        source = COMMAND.read_text()
        run_body = source.split("def _run(", 1)[1]

        for statement in (
            "materialize-core-tool",
            "release-team-template",
            "runner-catalog-independence-v1",
            "rps_runner.source_cli",
            "prove-amd64-against-arm64",
            "rps_runner.batch_plan_cli",
            "rps_runner.tournament_cli",
            "template-release.bundle",
            "cutover-proof.json",
        ):
            with self.subTest(statement=statement):
                self.assertIn(statement, source)
        self.assertLess(
            run_body.index("release-team-template"),
            run_body.index("prove-amd64-against-arm64"),
        )
        self.assertLess(
            run_body.index("runner-catalog-independence-v1"),
            run_body.index("prove-amd64-against-arm64"),
        )
        self.assertIn('catalog = core / lock["catalog"]["path"]', source)
        self.assertIn('offline_template = options.output / "offline-template"', source)
        self.assertIn('offline_core = options.output / "offline-runner"', source)
        self.assertIn('"clone", "--quiet", str(template_bundle)', source)
        self.assertLess(
            run_body.index('"clone", "--quiet", str(template_bundle)'),
            run_body.index("prove-amd64-against-arm64"),
        )
        self.assertNotIn('PROJECT_ROOT / "language_environments"', source)
        for forbidden in (
            "curl",
            "wget",
            "git clone http",
            "docker pull",
            "docker push",
            "qemu",
            "buildx",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, source.lower())

    def test_runbook_records_cutover_and_archives_old_authority(self) -> None:
        normalized = " ".join(RUNBOOK.read_text().split())

        for statement in (
            "clean Template Release checkout",
            "offline Runner bundle",
            "native Linux/AMD64 Advisory Validation",
            "native Linux/ARM64 Final Validation",
            "sha256:e2890c1587c6c98acb62121e5524d8f75a53925ed738f333f63beee81e60fd1a",
            "no Source Digest migration difference",
            "builds, Final Validates, preserves, plans, and executes",
            "never reads a catalog from the Template repository",
            "superseded catalog release procedure",
        ):
            with self.subTest(statement=statement):
                self.assertIn(statement, normalized)


if __name__ == "__main__":
    unittest.main()
