from __future__ import annotations

import json
import os
from pathlib import Path
import stat
import subprocess
import tempfile
import textwrap
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
COMMAND = PROJECT_ROOT / "validate-team"
LOCK = json.loads((PROJECT_ROOT / "core-tool.lock.json").read_text())


class TeamValidationCommandTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.bin = self.root / "bin"
        self.bin.mkdir()
        self.core = self.root / "core"
        subprocess.run(
            [str(PROJECT_ROOT / "materialize-core-tool"), str(self.core)],
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        package = self.core / "rps_runner"
        (package / "__init__.py").write_text("")
        self.log = self.root / "calls.jsonl"
        self.docker_log = self.root / "docker-calls.txt"
        self.pulled_images = self.root / "pulled-images.txt"
        self._write_executable(
            "git",
            """
            #!/bin/sh
            if [ "$3" = rev-parse ]; then
              printf '%s\\n' "$RPS_TEST_CORE_COMMIT"
            elif [ "${RPS_TEST_CORE_DIRTY:-}" ]; then
              printf '%s\\n' ' M rps_runner/source_cli.py'
            fi
            """,
        )
        self._write_executable(
            "docker",
            """
            #!/bin/sh
            if [ "${RPS_TEST_DOCKER_FAILURE:-}" ]; then
              printf '%s\\n' "$RPS_TEST_DOCKER_FAILURE" >&2
              exit 1
            fi
            if [ "$1" = version ]; then
              printf '%s\\n' "${RPS_TEST_PLATFORM:-linux/arm64}"
              exit 0
            fi
            printf '%s\\n' "$*" >> "$RPS_TEST_DOCKER_LOG"
            if [ "$1 $2" = "image inspect" ] && [ "${RPS_TEST_MISSING_IMAGES:-}" ]; then
              if [ -f "$RPS_TEST_PULLED_IMAGES" ] && grep -Fqx "$3" "$RPS_TEST_PULLED_IMAGES"; then
                exit 0
              fi
              printf '%s\\n' "No such image: $3" >&2
              exit 1
            fi
            if [ "$1" = pull ]; then
              printf '%s\\n' "$4" >> "$RPS_TEST_PULLED_IMAGES"
            fi
            exit 0
            """,
        )
        helper = textwrap.dedent(
            """
            import json
            import os
            from pathlib import Path
            import sys

            def option(name):
                return Path(sys.argv[sys.argv.index(name) + 1])

            def record(stage):
                with Path(os.environ["RPS_TEST_LOG"]).open("a") as stream:
                    stream.write(json.dumps({"stage": stage, "arguments": sys.argv[1:]}) + "\\n")
                if os.environ.get("RPS_TEST_FAIL_STAGE") == stage:
                    print(os.environ["RPS_TEST_FAILURE"], file=sys.stderr)
                    raise SystemExit(2)
            """
        )
        (package / "fake.py").write_text(helper)
        (package / "source_cli.py").write_text(
            textwrap.dedent(
                """
                import json
                from .fake import option, record

                record("source")
                bundle = option("--bundle")
                bundle.mkdir()
                result = {"source_digest": "sha256:" + "1" * 64}
                (bundle / "source-bundle.json").write_text(json.dumps(result))
                print(json.dumps(result))
                """
            )
        )
        (package / "artifact_cli.py").write_text(
            textwrap.dedent(
                """
                import json
                from .fake import option, record

                record("build")
                candidate = option("--candidate")
                candidate.mkdir()
                result = {
                    "artifact_digest": "sha256:" + "2" * 64,
                    "runtime": {"identity": "python-runtime-v1@sha256:" + "3" * 64},
                    "retention": {
                        "local_image_id": "sha256:" + "4" * 64,
                        "local_image_reference": "rps-tournament-candidate:test",
                    },
                    "identities": {
                        "catalog": "catalog-v1@sha256:" + "5" * 64,
                        "core_tool": "rps-core-tool-v1@sha256:" + "6" * 64,
                        "recipe": "python-build-recipe-v1@sha256:" + "7" * 64,
                        "wrapper": "python-wrapper-v3@sha256:" + "8" * 64,
                    },
                }
                (candidate / "artifact-candidate.json").write_text(json.dumps(result))
                print(json.dumps(result))
                """
            )
        )
        (package / "certification_cli.py").write_text(
            textwrap.dedent(
                """
                import json
                from .fake import option, record

                record("certification")
                output = option("--output")
                output.mkdir()
                result = {
                    "status": "passed",
                    "advisory": True,
                    "canonical_tournament_eligible": False,
                    "platform": "linux/arm64",
                    "identities": {
                        "source": "sha256:" + "1" * 64,
                        "image": "sha256:" + "2" * 64,
                        "runtime": "python-runtime-v1@sha256:" + "3" * 64,
                        "wrapper": "python-wrapper-v3@sha256:" + "8" * 64,
                        "recipe": "python-build-recipe-v1@sha256:" + "7" * 64,
                        "catalog": "catalog-v1@sha256:" + "5" * 64,
                        "suite": "python-artifact-conformance-v1@sha256:" + "9" * 64,
                        "core_tool": "rps-core-tool-v1@sha256:" + "6" * 64,
                    },
                    "checks": {"complete_smoke_match": "passed"},
                    "notice": "participant-local results are advisory",
                }
                (output / "validation-report.json").write_text(json.dumps(result))
                print(json.dumps(result))
                """
            )
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _write_executable(self, name: str, source: str) -> None:
        path = self.bin / name
        path.write_text(textwrap.dedent(source).lstrip())
        path.chmod(path.stat().st_mode | stat.S_IXUSR)

    def run_command(
        self, *arguments: str, **environment: str
    ) -> subprocess.CompletedProcess[str]:
        if "--template" not in arguments:
            arguments = ("--template", "python", *arguments)
        process_environment = os.environ.copy()
        process_environment.update(
            {
                "PATH": str(self.bin) + os.pathsep + process_environment["PATH"],
                "RPS_CORE_PATH": str(self.core),
                "RPS_TEST_CORE_COMMIT": LOCK["runner"]["commit"],
                "RPS_TEST_LOG": str(self.log),
                "RPS_TEST_DOCKER_LOG": str(self.docker_log),
                "RPS_TEST_PULLED_IMAGES": str(self.pulled_images),
            }
        )
        process_environment.update(environment)
        return subprocess.run(
            [str(COMMAND), *arguments],
            cwd=PROJECT_ROOT,
            env=process_environment,
            capture_output=True,
            text=True,
            timeout=10,
        )

    def run_command_without_template(
        self, **environment: str
    ) -> subprocess.CompletedProcess[str]:
        process_environment = os.environ.copy()
        process_environment.update(
            {
                "PATH": str(self.bin) + os.pathsep + process_environment["PATH"],
                "RPS_CORE_PATH": str(self.core),
                "RPS_TEST_CORE_COMMIT": LOCK["runner"]["commit"],
                "RPS_TEST_LOG": str(self.log),
                "RPS_TEST_DOCKER_LOG": str(self.docker_log),
                "RPS_TEST_PULLED_IMAGES": str(self.pulled_images),
            }
        )
        process_environment.update(environment)
        return subprocess.run(
            [str(COMMAND)],
            cwd=PROJECT_ROOT,
            env=process_environment,
            capture_output=True,
            text=True,
            timeout=10,
        )

    def run_declared_command(
        self, language_id: str, **environment: str
    ) -> subprocess.CompletedProcess[str]:
        declaration = PROJECT_ROOT / "team-submission.json"
        declaration.write_text(
            json.dumps(
                {
                    "format_version": "rps-team-submission-v1",
                    "language_id": language_id,
                }
            )
            + "\n"
        )
        try:
            return self.run_command_without_template(**environment)
        finally:
            declaration.unlink()

    def calls(self) -> list[dict[str, object]]:
        return [json.loads(line) for line in self.log.read_text().splitlines()]

    def docker_calls(self) -> list[str]:
        return self.docker_log.read_text().splitlines()

    def test_one_command_delegates_the_native_advisory_workflow_to_pinned_core(self) -> None:
        completed = self.run_command(RPS_TEST_PLATFORM="linux/arm64")

        self.assertEqual(completed.returncode, 0, completed.stderr)
        calls = self.calls()
        self.assertEqual([call["stage"] for call in calls], ["source", "build", "certification"])
        catalog = str(self.core.resolve() / LOCK["catalog"]["path"])
        self.assertIn(catalog, calls[0]["arguments"])
        self.assertIn(
            str(PROJECT_ROOT / "templates/python/team_source"),
            calls[0]["arguments"],
        )
        self.assertEqual(
            calls[1]["arguments"][calls[1]["arguments"].index("--platform") + 1],
            "linux/arm64",
        )
        self.assertNotIn("--push", calls[1]["arguments"])
        self.assertEqual(
            calls[2]["arguments"][calls[2]["arguments"].index("--mode") + 1],
            "participant-local",
        )
        self.assertEqual(
            calls[2]["arguments"][calls[2]["arguments"].index("--platform") + 1],
            "linux/arm64",
        )

        for label in (
            "Template Release: python-template-v2",
            "Supported Team Template: python-team-template-v2",
            "Team Source digest:",
            "Catalog:",
            "Core tool:",
            "Conformance suite:",
            "Build recipe:",
            "Wrapper:",
            "Runtime:",
            "Native platform: linux/arm64",
            "Disposable image:",
            "Advisory Validation: passed",
            "Practice Match: passed",
        ):
            with self.subTest(label=label):
                self.assertIn(label, completed.stdout)
        self.assertIn("insufficient for official Tournament entry", completed.stdout)

        for call in calls:
            self.assertIn(catalog, call["arguments"])
        self.assertNotIn(
            str(PROJECT_ROOT / "language_environments"),
            json.dumps(calls),
        )

    def test_selected_template_derives_source_and_environment_from_descriptor(self) -> None:
        completed = self.run_declared_command("python")

        self.assertEqual(completed.returncode, 0, completed.stderr)
        source_call = self.calls()[0]["arguments"]
        self.assertEqual(
            source_call[source_call.index("--source") + 1],
            str(PROJECT_ROOT / "templates/python/team_source"),
        )
        self.assertEqual(
            source_call[source_call.index("--environment") + 1], "python"
        )

    def test_missing_team_submission_requires_an_explicit_maintenance_selection(self) -> None:
        completed = self.run_command_without_template()

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("team-submission.json", completed.stderr)

    def test_allow_pull_acquires_both_pinned_images_before_java_validation(self) -> None:
        completed = self.run_command(
            "--template",
            "java",
            "--allow-pull",
            RPS_TEST_MISSING_IMAGES="1",
            RPS_TEST_PLATFORM="linux/arm64",
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        runtime_definition = json.loads(
            (
                self.core
                / "language_environments/catalog-v1/java/runtimes.json"
            ).read_text()
        )["platforms"]["linux/arm64"]
        expected = {
            runtime_definition["build_toolchain"]["image"],
            runtime_definition["execution_runtime"]["image"],
        }
        pulls = {
            call.removeprefix("pull --platform linux/arm64 ")
            for call in self.docker_calls()
            if call.startswith("pull ")
        }
        self.assertEqual(pulls, expected)

    def test_allow_pull_acquires_a_shared_toolchain_runtime_only_once(self) -> None:
        completed = self.run_command(
            "--allow-pull",
            RPS_TEST_MISSING_IMAGES="1",
            RPS_TEST_PLATFORM="linux/arm64",
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        pulls = [call for call in self.docker_calls() if call.startswith("pull ")]
        self.assertEqual(len(pulls), 1)

    def test_team_facing_diagnostics_name_each_failure_area(self) -> None:
        cases = (
            ("source", "invalid strategy signature", "Team Source failure"),
            ("build", "Docker build failed", "Build failure"),
            (
                "certification",
                "launch/readiness/lifecycle conformance failed: wrapper readiness marker was not observed",
                "Readiness failure",
            ),
            (
                "certification",
                "protocol/timing/stream/resource conformance failed: invalid protocol move at Turn 4",
                "Protocol failure",
            ),
            ("certification", "same-seed behavior was nondeterministic", "Determinism failure"),
            ("certification", "candidate produced security evidence", "Isolation failure"),
            (
                "certification",
                "protocol/timing/stream/resource conformance failed: container OOM resource fault",
                "Resource failure",
            ),
            (
                "certification",
                "launch/readiness/lifecycle conformance failed: candidate exited before clean shutdown",
                "Lifecycle failure",
            ),
        )
        for stage, message, label in cases:
            with self.subTest(stage=stage, label=label):
                if self.log.exists():
                    self.log.unlink()
                completed = self.run_command(
                    RPS_TEST_FAIL_STAGE=stage,
                    RPS_TEST_FAILURE=message,
                )
                self.assertNotEqual(completed.returncode, 0)
                self.assertIn(label, completed.stderr)
                self.assertIn(message, completed.stderr)

        completed = self.run_command(
            RPS_TEST_DOCKER_FAILURE="Cannot connect to the Docker daemon"
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("Docker-host failure", completed.stderr)
        self.assertIn("GitHub Advisory Validation", completed.stderr)

    def test_wrong_core_checkout_is_rejected_before_team_source_is_touched(self) -> None:
        completed = self.run_command(RPS_TEST_CORE_COMMIT="f" * 40)

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("Pinned core tool failure", completed.stderr)
        self.assertIn(LOCK["runner"]["commit"], completed.stderr)
        self.assertFalse(self.log.exists())

    def test_modified_core_checkout_is_rejected_before_team_source_is_touched(self) -> None:
        completed = self.run_command(RPS_TEST_CORE_DIRTY="1")

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("Pinned core tool failure", completed.stderr)
        self.assertIn("tracked modifications", completed.stderr)
        self.assertFalse(self.log.exists())

    def test_team_guide_documents_the_one_command_and_advisory_limit(self) -> None:
        guide = (PROJECT_ROOT / "templates/python/TEAM_GUIDE.md").read_text()
        normalized_guide = " ".join(guide.split())
        readme = " ".join((PROJECT_ROOT / "README.md").read_text().split())

        self.assertIn("./validate-team", guide)
        self.assertIn("--allow-pull", guide)
        self.assertIn("GitHub Advisory Validation", normalized_guide)
        self.assertIn("insufficient for official Tournament entry", normalized_guide)
        self.assertIn("Bot Artifact execution remain networkless", readme)


if __name__ == "__main__":
    unittest.main()
