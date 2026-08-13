from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from template_collection import load_collection


ROOT = Path(__file__).resolve().parents[1]


class BrainfCkTeamTemplateTests(unittest.TestCase):
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
        cls.interpreter = (
            cls.catalog.parent / "brainf-ck" / "interpreter.py"
        )

    @classmethod
    def tearDownClass(cls) -> None:
        cls.temporary.cleanup()

    def test_collection_exposes_independent_brainf_ck_template(self) -> None:
        template = load_collection(ROOT, self.catalog).select("brainf-ck")
        self.assertEqual(template.language_environment, "brainf-ck")
        self.assertEqual(template.version, "brainf-ck-team-template-v3")
        self.assertEqual(template.release_tag, "brainf-ck-template-v3")

    def test_owned_script_uses_the_catalog_interpreter_for_seeded_moves(self) -> None:
        environment = os.environ.copy()
        environment["RPS_DEPENDENCY_DEFINITION"] = str(self.interpreter)
        completed = subprocess.run(
            [str(ROOT / "templates/brainf-ck/build-and-test")],
            cwd=ROOT,
            env=environment,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("Brainf-ck starter tests passed", completed.stdout)

    def test_native_checker_supplies_the_catalog_interpreter(self) -> None:
        environment = os.environ.copy()
        environment["RPS_CORE_PATH"] = str(self.core)
        completed = subprocess.run(
            [
                str(ROOT / "check-team-template"),
                "--template",
                "brainf-ck",
                "--mode",
                "native",
            ],
            cwd=ROOT,
            env=environment,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("Brainf-ck starter tests passed", completed.stdout)

    def test_starter_is_only_strategy_source_and_does_not_copy_runner_infrastructure(self) -> None:
        source = ROOT / "templates/brainf-ck/team_source"
        self.assertEqual(
            [path.relative_to(source).as_posix() for path in source.rglob("*") if path.is_file()],
            ["strategy.bf"],
        )
        template_files = {
            path.name for path in (ROOT / "templates/brainf-ck").rglob("*") if path.is_file()
        }
        self.assertNotIn("wrapper.py", template_files)
        self.assertNotIn("interpreter.py", template_files)

    def test_guidance_documents_dialect_limits_input_and_authority(self) -> None:
        guidance = (ROOT / "templates/brainf-ck/TEAM_GUIDE.md").read_text()
        for phrase in (
            "8-bit wrapping cells",
            "30,000",
            "1,000,000",
            "50 ms",
            "one output byte",
            "64-bit LCG",
            "6364136223846793005",
            "1442695040888963407",
            "turn modulo 3",
            "seed",
            "history",
            "--mode native",
            "--mode docker",
            "Advisory Validation",
            "Final Validation",
        ):
            self.assertIn(phrase, guidance)

    def test_shared_checker_has_no_brainf_ck_language_switch(self) -> None:
        checker = (ROOT / "check-team-template").read_text()
        self.assertNotIn('language_environment == "brainf-ck"', checker)
        self.assertNotIn("RPS_BRAINF", checker)


if __name__ == "__main__":
    unittest.main()
