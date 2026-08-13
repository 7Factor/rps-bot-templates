from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from template_collection import load_collection


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def has_javascript_toolchain() -> bool:
    node = shutil.which("node")
    if node is None:
        return False
    completed = subprocess.run([node, "--version"], capture_output=True, text=True)
    try:
        return (
            completed.returncode == 0
            and int(completed.stdout.strip().lstrip("v").split(".", 1)[0]) >= 24
        )
    except (ValueError, IndexError):
        return False


class JavaScriptTeamTemplateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temporary = tempfile.TemporaryDirectory()
        cls.core = Path(cls.temporary.name) / "rps-tournament"
        subprocess.run(
            [str(PROJECT_ROOT / "materialize-core-tool"), str(cls.core)],
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        lock = json.loads((PROJECT_ROOT / "core-tool.lock.json").read_text())
        cls.catalog = cls.core / lock["catalog"]["path"]

    @classmethod
    def tearDownClass(cls) -> None:
        cls.temporary.cleanup()

    def test_collection_exposes_an_independent_javascript_template(self) -> None:
        collection = load_collection(PROJECT_ROOT, self.catalog)
        template = collection.select("javascript")

        self.assertEqual(template.language_environment, "javascript")
        self.assertEqual(template.version, "javascript-team-template-v1")
        self.assertEqual(template.release_tag, "javascript-template-v1")
        self.assertEqual(
            template.team_source_path.as_posix(),
            "templates/javascript/team_source",
        )
        self.assertNotIn(
            template.release_tag,
            {
                collection.select(name).release_tag
                for name in ("python", "typescript", "clojure")
            },
        )

    @unittest.skipUnless(
        has_javascript_toolchain(), "Node.js 24 or newer is required for native mode"
    )
    def test_native_entrypoint_builds_and_tests_seeded_behavior(self) -> None:
        completed = subprocess.run(
            [str(PROJECT_ROOT / "templates/javascript/build-and-test")],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("JavaScript starter build passed", completed.stdout)
        self.assertIn("JavaScript starter tests passed", completed.stdout)

    @unittest.skipUnless(
        os.environ.get("RPS_RUN_DOCKER_INTEGRATION") == "1",
        "set RPS_RUN_DOCKER_INTEGRATION=1 to run pinned Docker integration",
    )
    def test_pinned_docker_toolchain_runs_the_complete_javascript_suite(self) -> None:
        environment = os.environ.copy()
        environment["RPS_CORE_PATH"] = str(self.core)
        completed = subprocess.run(
            [
                str(PROJECT_ROOT / "check-team-template"),
                "--template", "javascript", "--mode", "docker",
            ],
            cwd=PROJECT_ROOT,
            env=environment,
            capture_output=True,
            text=True,
            timeout=120,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("JavaScript starter tests passed", completed.stdout)
        self.assertIn(
            "Team Template check passed: javascript (docker)", completed.stdout
        )

    @unittest.skipUnless(
        os.environ.get("RPS_RUN_DOCKER_INTEGRATION") == "1",
        "set RPS_RUN_DOCKER_INTEGRATION=1 to run Advisory Validation",
    )
    def test_current_catalog_passes_participant_local_advisory_validation(self) -> None:
        environment = os.environ.copy()
        environment["RPS_CORE_PATH"] = str(self.core)
        lock = json.loads((PROJECT_ROOT / "core-tool.lock.json").read_text())
        completed = subprocess.run(
            [str(PROJECT_ROOT / "validate-team"), "--template", "javascript"],
            cwd=PROJECT_ROOT,
            env=environment,
            capture_output=True,
            text=True,
            timeout=180,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("Participant-local Advisory Validation passed", completed.stdout)
        self.assertIn(lock["catalog"]["identity"], completed.stdout)
        self.assertIn(
            "javascript-artifact-conformance-v1@sha256:"
            "7c8de8485a6d643f0e93112f3bd319df03a6d93cd4472da7a9bfc3652941c91c",
            completed.stdout,
        )
        self.assertIn("Practice Match: passed", completed.stdout)
        self.assertIn("Advisory Validation: passed", completed.stdout)

    def test_guidance_documents_boundaries_and_validation_authority(self) -> None:
        guidance = (PROJECT_ROOT / "templates/javascript/TEAM_GUIDE.md").read_text()

        for phrase in (
            "Team Source", "Node.js 24.19.0", "64 files", "256 KiB per file",
            "1 MiB total", "turn", "myHistory", "opponentHistory", "rng.nextInt",
            "standard-library-only", "Docker", "Advisory Validation",
            "Final Validation",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, guidance)

    def test_pinned_catalog_owns_the_javascript_seed_adapter(self) -> None:
        environment = json.loads(self.catalog.read_text())["environments"][
            "javascript"
        ]
        conformance_path = self.catalog.parent / environment["assets"][
            "conformance"
        ]["path"]
        seed_adapter = json.loads(conformance_path.read_text())["seed_adapter"]

        self.assertEqual(
            seed_adapter["version"], "javascript-splitmix64-seed-adapter-v1"
        )
        self.assertFalse(seed_adapter["system_randomness"])
        self.assertEqual(len(seed_adapter["golden_vectors"]), 4)
        test_source = (
            PROJECT_ROOT / "templates/javascript/tests/strategy.test.js"
        ).read_text()
        self.assertNotIn("first_uint64", test_source)


if __name__ == "__main__":
    unittest.main()
