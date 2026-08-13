from __future__ import annotations

import importlib.machinery
import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
COMMAND = PROJECT_ROOT / "prove-amd64-against-arm64"
RUNBOOK = PROJECT_ROOT / "CROSS_PLATFORM_PROOF.md"


def load_command_module():
    loader = importlib.machinery.SourceFileLoader("cross_platform_proof", str(COMMAND))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    if spec is None:
        raise RuntimeError("cannot load cross-platform proof command")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    loader.exec_module(module)
    return module


def identities(*, source: str, image: str, platform: str) -> dict[str, str]:
    return {
        "source": source,
        "image": image,
        "runtime": "python-runtime-v1@sha256:" + platform[-1] * 64,
        "wrapper": "python-wrapper-v3@sha256:" + "1" * 64,
        "recipe": "python-build-recipe-v1@sha256:" + "2" * 64,
        "entrypoint": "python-entrypoint-v1@sha256:" + "3" * 64,
        "catalog": "rps-language-environment-catalog-v1@sha256:" + "4" * 64,
        "suite": "python-certification-suite-v1@sha256:" + "5" * 64,
        "platform": "oci-platforms-v1@sha256:" + "6" * 64,
        "profile": "docker-execution-v1@sha256:" + "7" * 64,
        "core_tool": "rps-runner-v1@sha256:" + "8" * 64,
        "builder_core_tool": "rps-runner-v1@sha256:" + "8" * 64,
    }


CHECKS = {
    "source_validation": "passed-by-frozen-bundle",
    "networkless_build": "passed-by-verified-current-builder-record",
    "image_identity": "passed",
    "readiness": "passed",
    "clean_shutdown": "passed",
    "protocol_transcripts": "passed",
    "same_seed_behavior": "passed",
    "timing_and_stream_limits": "passed",
    "resource_enforcement": "passed-through-profile",
    "isolation": "passed-through-profile",
    "diagnostics": "passed",
    "complete_smoke_match": "passed",
    "practice_match_result_gate": "not-applicable",
}


class CrossPlatformProofTests(unittest.TestCase):
    def setUp(self) -> None:
        self.source_digest = "sha256:" + "a" * 64
        self.commit = "b" * 40
        self.advisory_identities = identities(
            source=self.source_digest,
            image="sha256:" + "c" * 64,
            platform="amd64",
        )
        self.final_identities = identities(
            source=self.source_digest,
            image="sha256:" + "d" * 64,
            platform="arm64",
        )
        self.eligibility = {
            "result": "passed",
            "authority": "github-advisory",
            "source_commit": self.commit,
            "source_digest": self.source_digest,
            "platform": "linux/amd64",
            "runtime_digest": "sha256:" + "5" * 64,
            "disposable_image_identity": "sha256:" + "c" * 64,
            "validation_identity": "validation-report-v1@sha256:" + "9" * 64,
            "catalog": self.advisory_identities["catalog"],
            "core_tool": self.advisory_identities["core_tool"],
            "suite": self.advisory_identities["suite"],
            "recipe": self.advisory_identities["recipe"],
            "wrapper": self.advisory_identities["wrapper"],
            "execution_profile": self.advisory_identities["profile"],
            "team_submission": {
                "format_version": "rps-team-submission-v1",
                "language_id": "python",
            },
        }
        self.advisory = {
            "status": "passed",
            "mode": "github-advisory",
            "authority": "advisory",
            "advisory": True,
            "canonical_tournament_eligible": False,
            "platform": "linux/amd64",
            "profile": "docker-execution-v1",
            "validation_identity": self.eligibility["validation_identity"],
            "identities": self.advisory_identities,
            "checks": dict(CHECKS),
            "smoke_match": {"random": {"moves": ["R", "P"]}},
        }
        self.source_bundle = {
            "source_digest": self.source_digest,
            "environment": "python",
            "versions": {"catalog": self.advisory_identities["catalog"]},
        }
        self.candidate = {
            "source_digest": self.source_digest,
            "language": "python",
            "runtime_digest": "sha256:" + "6" * 64,
            "artifact_digest": "sha256:" + "d" * 64,
            "platform": "linux/arm64",
            "identities": {
                "catalog": self.final_identities["catalog"],
                "wrapper": self.final_identities["wrapper"],
                "recipe": self.final_identities["recipe"],
            },
        }
        self.manifest = {
            "status": "validated",
            "authority": "canonical",
            "source_digest": self.source_digest,
            "language": "python",
            "runtime_digest": self.candidate["runtime_digest"],
            "artifact_digest": self.candidate["artifact_digest"],
            "platform": "linux/arm64",
            "validation_identity": "validation-report-v1@sha256:" + "e" * 64,
            "identities": self.final_identities,
        }
        self.final = {
            "status": "passed",
            "mode": "organizer-final",
            "authority": "canonical",
            "advisory": False,
            "canonical_tournament_eligible": True,
            "platform": "linux/arm64",
            "profile": "docker-execution-v1",
            "validation_identity": self.manifest["validation_identity"],
            "identities": self.final_identities,
            "checks": dict(CHECKS),
            "smoke_match": {"random": {"moves": ["S", "S"]}},
        }

    def test_comparison_proves_shared_contract_without_equating_platform_outputs(self) -> None:
        module = load_command_module()

        proof = module.build_cross_platform_proof(
            selected_commit=self.commit,
            eligibility=self.eligibility,
            advisory_report=self.advisory,
            source_bundle=self.source_bundle,
            arm64_candidate=self.candidate,
            bot_artifact_manifest=self.manifest,
            final_report=self.final,
            language_id="python",
            language_environment="python",
        )

        self.assertEqual(proof["result"], "passed")
        self.assertEqual(proof["shared_contract"]["checks"], CHECKS)
        self.assertEqual(
            proof["architecture_specific"]["linux/amd64"]["runtime_digest"],
            self.eligibility["runtime_digest"],
        )
        self.assertEqual(
            proof["architecture_specific"]["linux/arm64"]["runtime_digest"],
            self.candidate["runtime_digest"],
        )
        self.assertEqual(
            proof["language_native_random_stream_comparison"], "not-required"
        )

    def test_comparison_rejects_source_or_contract_drift(self) -> None:
        module = load_command_module()
        self.final["checks"]["readiness"] = "failed"

        with self.assertRaisesRegex(ValueError, "readiness"):
            module.build_cross_platform_proof(
                selected_commit=self.commit,
                eligibility=self.eligibility,
                advisory_report=self.advisory,
                source_bundle=self.source_bundle,
                arm64_candidate=self.candidate,
                bot_artifact_manifest=self.manifest,
                final_report=self.final,
                language_id="python",
                language_environment="python",
            )

    def test_comparison_rejects_declared_language_drift(self) -> None:
        module = load_command_module()
        self.eligibility["team_submission"]["language_id"] = "go"

        with self.assertRaisesRegex(ValueError, "declared Team Template language"):
            module.build_cross_platform_proof(
                selected_commit=self.commit,
                eligibility=self.eligibility,
                advisory_report=self.advisory,
                source_bundle=self.source_bundle,
                arm64_candidate=self.candidate,
                bot_artifact_manifest=self.manifest,
                final_report=self.final,
                language_id="python",
                language_environment="python",
            )

    def test_advisory_evidence_is_rejected_before_an_arm64_run(self) -> None:
        module = load_command_module()
        self.eligibility["source_commit"] = "0" * 40

        with self.assertRaisesRegex(ValueError, "source_commit"):
            module.validate_advisory_evidence(
                selected_commit=self.commit,
                eligibility=self.eligibility,
                advisory_report=self.advisory,
            )

        command = COMMAND.read_text()
        run_body = command.split("def _run(", 1)[1]
        self.assertLess(
            run_body.index("validate_advisory_evidence("),
            run_body.index('"build-arm64-candidate"'),
        )

    def test_comparison_failure_is_retained_as_a_failed_stage(self) -> None:
        module = load_command_module()
        with tempfile.TemporaryDirectory() as directory:
            run = module.ProofRun(Path(directory))
            run.record_failure("compare-native-platforms", ValueError("suite drift"))

            progress = (Path(directory) / "proof-progress.json").read_text()
            diagnostic = (
                Path(directory) / "compare-native-platforms.error.log"
            ).read_text()

        self.assertIn('"result": "failed"', progress)
        self.assertIn('"compare-native-platforms": "failed"', progress)
        self.assertEqual(diagnostic, "suite drift\n")

    def test_command_uses_native_arm64_and_the_pinned_core_contract(self) -> None:
        command = COMMAND.read_text()

        for statement in (
            '"linux/arm64"',
            '"organizer-final"',
            'rps_runner.source_cli',
            'rps_runner.artifact_cli',
            'rps_runner.certification_cli',
            '"docker-execution-v1"',
            'core-tool.lock.json',
            'materialize-core-tool',
            'eligibility-evidence.json',
            'validation-report.json',
            'cross-platform-proof.json',
        ):
            with self.subTest(statement=statement):
                self.assertIn(statement, command)
        for forbidden in ("qemu", "buildx", "docker pull", "docker push", "docker load"):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, command.lower())
        self.assertIn('catalog = options.core_path / lock["catalog"]["path"]', command)
        self.assertNotIn(
            'PROJECT_ROOT / "language_environments" / "catalog-v1" / "catalog.json"',
            command,
        )

    def test_runbook_preserves_diagnostic_and_repair_evidence(self) -> None:
        normalized = " ".join(RUNBOOK.read_text().split())

        for statement in (
            "same selected Team Source",
            "native Linux/AMD64",
            "native Linux/ARM64",
            "protocol version 1",
            "disposable confidence image",
            "canonical Bot Artifact",
            "no QEMU",
            "no multi-platform build",
            "no combined OCI index",
            "pinned base runtime",
            "Bot Artifact images",
            "never pushed to or pulled from a registry",
            "language-native random streams",
            "compatibility-only repair",
            "complete diff",
        ):
            with self.subTest(statement=statement):
                self.assertIn(statement, normalized)


if __name__ == "__main__":
    unittest.main()
