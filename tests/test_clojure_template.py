from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from template_collection import load_collection


ROOT = Path(__file__).resolve().parents[1]


class ClojureTeamTemplateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temporary = tempfile.TemporaryDirectory()
        cls.core = Path(cls.temporary.name) / "rps-tournament"
        subprocess.run(
            [str(ROOT / "materialize-core-tool"), str(cls.core)],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        lock = json.loads((ROOT / "core-tool.lock.json").read_text())
        cls.catalog = cls.core / lock["catalog"]["path"]

    @classmethod
    def tearDownClass(cls) -> None:
        cls.temporary.cleanup()

    def test_collection_exposes_independent_clojure_template(self) -> None:
        template = load_collection(ROOT, self.catalog).select("clojure")
        self.assertEqual(template.language_environment, "clojure")
        self.assertEqual(template.version, "clojure-team-template-v1")
        self.assertEqual(template.release_tag, "clojure-template-v1")

    @unittest.skipUnless(
        shutil.which("clojure") and shutil.which("java"),
        "Clojure and Java are required",
    )
    def test_native_entrypoint_builds_and_tests_seeded_behavior(self) -> None:
        completed = subprocess.run(
            [str(ROOT / "templates/clojure/build-and-test")],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("Clojure starter tests passed", completed.stdout)

    @unittest.skipUnless(
        os.environ.get("RPS_RUN_DOCKER_INTEGRATION") == "1",
        "set RPS_RUN_DOCKER_INTEGRATION=1 to run pinned Docker integration",
    )
    def test_pinned_docker_toolchain_runs_the_complete_clojure_suite(self) -> None:
        environment = os.environ.copy()
        environment["RPS_CORE_PATH"] = str(self.core)
        completed = subprocess.run(
            [
                str(ROOT / "check-team-template"),
                "--template",
                "clojure",
                "--mode",
                "docker",
            ],
            cwd=ROOT,
            env=environment,
            capture_output=True,
            text=True,
            timeout=120,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("Clojure starter tests passed", completed.stdout)
        self.assertIn("Team Template check passed: clojure (docker)", completed.stdout)

    def test_guidance_documents_boundaries_and_authority(self) -> None:
        guidance = (ROOT / "templates/clojure/TEAM_GUIDE.md").read_text()
        for phrase in (
            "Team Source",
            "Clojure 1.12.5",
            "Java 25",
            "--mode native",
            "--mode docker",
            "Advisory Validation",
            "Final Validation",
        ):
            self.assertIn(phrase, guidance)

    def test_shared_checker_has_no_clojure_language_switch(self) -> None:
        checker = (ROOT / "check-team-template").read_text()
        self.assertNotIn('language_environment == "clojure"', checker)
        self.assertNotIn("RPS_CLOJURE", checker)


if __name__ == "__main__":
    unittest.main()
