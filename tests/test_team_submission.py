from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
COMMAND = PROJECT_ROOT / "select-team-template"


class TeamSubmissionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.repository = Path(self.temporary.name) / "repository"
        shutil.copytree(
            PROJECT_ROOT,
            self.repository,
            ignore=shutil.ignore_patterns(
                ".git", ".core", ".scratch", "__pycache__", "*.pyc"
            ),
        )
        index_path = self.repository / "team-templates.json"
        index = json.loads(index_path.read_text())
        index["templates"] = [
            entry
            for entry in index["templates"]
            if entry["language_id"] == "python"
        ]
        index_path.write_text(json.dumps(index, indent=2) + "\n")
        self.core = Path(self.temporary.name) / "core"
        subprocess.run(
            [str(PROJECT_ROOT / "materialize-core-tool"), str(self.core)],
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def run_command(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        environment = os.environ.copy()
        environment["RPS_CORE_PATH"] = str(self.core)
        return subprocess.run(
            [str(self.repository / COMMAND.name), *arguments],
            cwd=self.repository,
            env=environment,
            capture_output=True,
            text=True,
        )

    def test_team_records_a_machine_readable_language_selection(self) -> None:
        completed = self.run_command("python")

        self.assertEqual(completed.returncode, 0, completed.stderr)
        declaration = json.loads(
            (self.repository / "team-submission.json").read_text()
        )
        self.assertEqual(
            declaration,
            {
                "format_version": "rps-team-submission-v1",
                "language_id": "python",
            },
        )

        shown = self.run_command("--show")
        self.assertEqual(shown.returncode, 0, shown.stderr)
        resolved = json.loads(shown.stdout)
        self.assertEqual(
            resolved["format_version"], "rps-team-submission-resolution-v1"
        )
        self.assertEqual(resolved["language_id"], "python")
        self.assertEqual(resolved["language_environment"], "python")
        self.assertEqual(resolved["team_source_path"], "templates/python/team_source")
        self.assertEqual(resolved["template_release"], "python-template-v2")

    def test_existing_selection_is_not_silently_replaced(self) -> None:
        first = self.run_command("python")
        second = self.run_command("python")

        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertNotEqual(second.returncode, 0)
        self.assertIn("already exists", second.stderr)
        self.assertEqual(
            json.loads((self.repository / "team-submission.json").read_text())[
                "language_id"
            ],
            "python",
        )

    def test_unknown_or_malformed_selection_is_rejected(self) -> None:
        unknown = self.run_command("not-a-language")
        self.assertNotEqual(unknown.returncode, 0)
        self.assertIn("unknown Team Template", unknown.stderr)

        (self.repository / "team-submission.json").write_text(
            '{"format_version":"rps-team-submission-v1","language_id":"python",'
            '"environment":"go"}\n'
        )
        malformed = self.run_command("--show")
        self.assertNotEqual(malformed.returncode, 0)
        self.assertIn("exactly format_version and language_id", malformed.stderr)

    def test_symlink_selection_is_rejected(self) -> None:
        target = self.repository / "outside.json"
        target.write_text(
            '{"format_version":"rps-team-submission-v1",'
            '"language_id":"python"}\n'
        )
        (self.repository / "team-submission.json").symlink_to(target)

        completed = self.run_command("--show")

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("not a symlink", completed.stderr)

    def test_verified_checkout_can_resolve_a_preserved_declaration(self) -> None:
        declaration = Path(self.temporary.name) / "preserved-team-submission.json"
        declaration.write_text(
            '{"format_version":"rps-team-submission-v1",'
            '"language_id":"python"}\n'
        )

        completed = self.run_command(
            "--show", "--declaration", str(declaration)
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(json.loads(completed.stdout)["language_id"], "python")


if __name__ == "__main__":
    unittest.main()
