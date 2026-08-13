from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from template_collection import load_collection

ROOT = Path(__file__).resolve().parents[1]


class RubyTeamTemplateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temporary = tempfile.TemporaryDirectory()
        cls.core = Path(cls.temporary.name) / "rps-tournament"
        subprocess.run([str(ROOT / "materialize-core-tool"), str(cls.core)], cwd=ROOT, check=True, capture_output=True, text=True)
        lock = json.loads((ROOT / "core-tool.lock.json").read_text())
        cls.catalog = cls.core / lock["catalog"]["path"]

    @classmethod
    def tearDownClass(cls) -> None:
        cls.temporary.cleanup()

    def test_collection_exposes_independent_ruby_template(self) -> None:
        template = load_collection(ROOT, self.catalog).select("ruby")
        self.assertEqual(template.language_environment, "ruby")
        self.assertEqual(template.version, "ruby-team-template-v1")
        self.assertEqual(template.release_tag, "ruby-template-v1")

    @unittest.skipUnless(shutil.which("ruby") and subprocess.run([shutil.which("ruby"), "-e", "exit RUBY_VERSION.split('.').first.to_i >= 4 ? 0 : 1"]).returncode == 0, "Ruby 4 or newer is required")
    def test_native_entrypoint_builds_and_tests_seeded_behavior(self) -> None:
        completed = subprocess.run([str(ROOT / "templates/ruby/build-and-test")], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("Ruby starter tests passed", completed.stdout)

    def test_guidance_documents_boundaries_and_authority(self) -> None:
        guidance = (ROOT / "templates/ruby/TEAM_GUIDE.md").read_text()
        for phrase in ("Team Source", "Ruby 4.0.6", "--mode native", "--mode docker", "Advisory Validation", "Final Validation"):
            self.assertIn(phrase, guidance)

    def test_shared_checker_has_no_ruby_language_switch(self) -> None:
        checker = (ROOT / "check-team-template").read_text()
        self.assertNotIn('language_environment == "ruby"', checker)
        self.assertNotIn("RPS_RUBY", checker)


if __name__ == "__main__":
    unittest.main()
