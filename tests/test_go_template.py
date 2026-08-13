from __future__ import annotations

import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest

from template_collection import load_collection


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def has_go_1_26() -> bool:
    go = shutil.which("go")
    if go is None:
        return False
    completed = subprocess.run([go, "env", "GOVERSION"], capture_output=True, text=True)
    if completed.returncode != 0:
        return False
    match = re.fullmatch(r"go(\d+)\.(\d+).*", completed.stdout.strip())
    if not match:
        return False
    return (int(match.group(1)), int(match.group(2))) >= (1, 26)


class GoTeamTemplateTests(unittest.TestCase):
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

    def test_collection_exposes_an_independent_go_template(self) -> None:
        collection = load_collection(PROJECT_ROOT, self.catalog)
        template = collection.select("go")

        self.assertEqual(template.language_environment, "go")
        self.assertEqual(template.version, "go-team-template-v1")
        self.assertEqual(template.release_tag, "go-template-v1")
        self.assertEqual(template.team_source_path.as_posix(), "templates/go/team_source")
        self.assertNotEqual(template.release_tag, collection.select("python").release_tag)

    @unittest.skipUnless(has_go_1_26(), "Go 1.26 or newer is required for native mode")
    def test_native_entrypoint_builds_and_tests_seeded_behavior(self) -> None:
        completed = subprocess.run(
            [str(PROJECT_ROOT / "templates/go/build-and-test")],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("Go starter build passed", completed.stdout)
        self.assertIn("Go starter tests passed", completed.stdout)

    @unittest.skipUnless(has_go_1_26(), "Go 1.26 or newer is required for native mode")
    def test_native_entrypoint_builds_the_complete_valid_team_source(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            template = Path(directory) / "go"
            shutil.copytree(PROJECT_ROOT / "templates/go", template)
            strategy = template / "team_source/strategy.go"
            strategy.write_text(strategy.read_text().replace(
                'moves := [...]string{"R", "P", "S"}',
                "moves := teamMoves()",
            ))
            (template / "team_source/helper.go").write_text(
                'package main\n\nfunc teamMoves() [3]string { return [3]string{"R", "P", "S"} }\n'
            )
            resources = template / "team_source/resources"
            resources.mkdir()
            (resources / "notes.txt").write_text("valid Team resource\n")

            completed = subprocess.run(
                [str(template / "build-and-test")],
                capture_output=True,
                text=True,
            )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("Go starter tests passed", completed.stdout)

    @unittest.skipUnless(
        os.environ.get("RPS_RUN_DOCKER_INTEGRATION") == "1",
        "set RPS_RUN_DOCKER_INTEGRATION=1 to run pinned Docker integration",
    )
    def test_pinned_docker_toolchain_runs_the_complete_go_suite(self) -> None:
        completed = subprocess.run(
            [
                str(PROJECT_ROOT / "check-team-template"),
                "--template",
                "go",
                "--mode",
                "docker",
            ],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=120,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("Go starter tests passed", completed.stdout)
        self.assertIn("Team Template check passed: go (docker)", completed.stdout)

    def test_shared_docker_workspace_can_compile_a_go_toolchain(self) -> None:
        checker = (PROJECT_ROOT / "check-team-template").read_text()

        self.assertIn("/tmp:rw,exec,nosuid,size=512m", checker)
        self.assertNotIn("/tmp:rw,noexec", checker)

    def test_guidance_documents_boundaries_and_validation_authority(self) -> None:
        guidance = (PROJECT_ROOT / "templates/go/TEAM_GUIDE.md").read_text()

        for phrase in (
            "Team Source",
            "Go 1.26.5",
            "--mode native",
            "--mode docker",
            "Advisory Validation",
            "Final Validation",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, guidance)


if __name__ == "__main__":
    unittest.main()
