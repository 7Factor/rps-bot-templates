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


def has_csharp_toolchain() -> bool:
    dotnet = shutil.which("dotnet")
    if dotnet is None:
        return False
    completed = subprocess.run(
        [dotnet, "--version"], capture_output=True, text=True
    )
    try:
        return completed.returncode == 0 and int(completed.stdout.split(".", 1)[0]) >= 10
    except (ValueError, IndexError):
        return False


class CSharpTeamTemplateTests(unittest.TestCase):
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

    def test_collection_exposes_an_independent_csharp_template(self) -> None:
        collection = load_collection(PROJECT_ROOT, self.catalog)
        template = collection.select("csharp")

        self.assertEqual(template.language_environment, "csharp")
        self.assertEqual(template.version, "csharp-team-template-v2")
        self.assertEqual(template.release_tag, "csharp-template-v2")
        self.assertEqual(
            template.team_source_path.as_posix(), "templates/csharp/team_source"
        )
        self.assertNotIn(
            template.release_tag,
            {
                collection.select(name).release_tag
                for name in ("python", "go", "java", "typescript")
            },
        )

    @unittest.skipUnless(
        has_csharp_toolchain(), ".NET SDK 10 or newer is required for native mode"
    )
    def test_native_entrypoint_builds_and_tests_seeded_behavior(self) -> None:
        completed = subprocess.run(
            [str(PROJECT_ROOT / "templates/csharp/build-and-test")],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("C# starter build passed", completed.stdout)
        self.assertIn("C# starter tests passed", completed.stdout)

    @unittest.skipUnless(
        os.environ.get("RPS_RUN_DOCKER_INTEGRATION") == "1",
        "set RPS_RUN_DOCKER_INTEGRATION=1 to run pinned Docker integration",
    )
    def test_pinned_docker_toolchain_runs_the_complete_csharp_suite(self) -> None:
        environment = os.environ.copy()
        environment["RPS_CORE_PATH"] = str(self.core)
        completed = subprocess.run(
            [
                str(PROJECT_ROOT / "check-team-template"),
                "--template",
                "csharp",
                "--mode",
                "docker",
            ],
            cwd=PROJECT_ROOT,
            env=environment,
            capture_output=True,
            text=True,
            timeout=120,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("C# starter tests passed", completed.stdout)
        self.assertIn("Team Template check passed: csharp (docker)", completed.stdout)

    def test_guidance_documents_boundaries_and_validation_authority(self) -> None:
        guidance = (PROJECT_ROOT / "templates/csharp/TEAM_GUIDE.md").read_text()
        for phrase in (
            "Team Source",
            ".NET SDK 10.0.302",
            "64 files",
            "256 KiB per file",
            "1 MiB total",
            "supplied deterministic `rng`",
            "--mode native",
            "--mode docker",
            "Advisory Validation",
            "Final Validation",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, guidance)

    def test_shared_checker_has_no_csharp_language_switch(self) -> None:
        checker = (PROJECT_ROOT / "check-team-template").read_text()
        self.assertNotIn('language_environment == "csharp"', checker)
        self.assertNotIn("RPS_CSHARP", checker)


if __name__ == "__main__":
    unittest.main()
