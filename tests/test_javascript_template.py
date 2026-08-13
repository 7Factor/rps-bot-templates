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

    def test_template_seed_vectors_match_the_runner_owned_adapter(self) -> None:
        test_source = (
            PROJECT_ROOT / "templates/javascript/tests/strategy.test.js"
        ).read_text()
        environment = json.loads(self.catalog.read_text())["environments"][
            "javascript"
        ]
        conformance_path = self.catalog.parent / environment["assets"][
            "conformance"
        ]["path"]
        vectors = json.loads(conformance_path.read_text())["seed_adapter"][
            "golden_vectors"
        ]

        for vector in vectors:
            self.assertIn(vector["seed"], test_source)
            for value in vector["first_uint64"]:
                self.assertIn(value, test_source)


if __name__ == "__main__":
    unittest.main()
