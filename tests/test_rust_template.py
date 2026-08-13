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


def has_rust_toolchain() -> bool:
    rustc = shutil.which("rustc")
    if rustc is None:
        return False
    completed = subprocess.run([rustc, "--version"], capture_output=True, text=True)
    match = re.search(r"rustc (\d+)\.(\d+)", completed.stdout)
    return bool(
        completed.returncode == 0
        and match
        and (int(match.group(1)), int(match.group(2))) >= (1, 85)
    )


class RustTeamTemplateTests(unittest.TestCase):
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

    def test_collection_exposes_an_independent_rust_template(self) -> None:
        collection = load_collection(PROJECT_ROOT, self.catalog)
        template = collection.select("rust")

        self.assertEqual(template.language_environment, "rust")
        self.assertEqual(template.version, "rust-team-template-v1")
        self.assertEqual(template.release_tag, "rust-template-v1")
        self.assertEqual(
            template.team_source_path.as_posix(), "templates/rust/team_source"
        )
        self.assertNotIn(
            template.release_tag,
            {
                collection.select(name).release_tag
                for name in ("python", "go", "java", "typescript", "csharp")
            },
        )

    @unittest.skipUnless(
        has_rust_toolchain(), "Rust 1.85 or newer is required for native mode"
    )
    def test_native_entrypoint_builds_and_tests_seeded_behavior(self) -> None:
        completed = subprocess.run(
            [str(PROJECT_ROOT / "templates/rust/build-and-test")],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("Rust starter build passed", completed.stdout)
        self.assertIn("Rust starter tests passed", completed.stdout)

    @unittest.skipUnless(
        os.environ.get("RPS_RUN_DOCKER_INTEGRATION") == "1",
        "set RPS_RUN_DOCKER_INTEGRATION=1 to run pinned Docker integration",
    )
    def test_pinned_docker_toolchain_runs_the_complete_rust_suite(self) -> None:
        environment = os.environ.copy()
        environment["RPS_CORE_PATH"] = str(self.core)
        completed = subprocess.run(
            [
                str(PROJECT_ROOT / "check-team-template"),
                "--template",
                "rust",
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
        self.assertIn("Rust starter tests passed", completed.stdout)
        self.assertIn("Team Template check passed: rust (docker)", completed.stdout)

    @unittest.skipUnless(
        os.environ.get("RPS_RUN_DOCKER_INTEGRATION") == "1",
        "set RPS_RUN_DOCKER_INTEGRATION=1 to run Advisory Validation",
    )
    def test_catalog_v12_passes_participant_local_advisory_validation(self) -> None:
        environment = os.environ.copy()
        environment["RPS_CORE_PATH"] = str(self.core)
        completed = subprocess.run(
            [str(PROJECT_ROOT / "validate-team"), "--template", "rust"],
            cwd=PROJECT_ROOT,
            env=environment,
            capture_output=True,
            text=True,
            timeout=180,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("Participant-local Advisory Validation passed", completed.stdout)
        self.assertIn(
            "rps-language-environment-catalog-v1@sha256:"
            "035d1b59199897d0e852d88847b59e61d6fd14f74b84131b7f18541c8d9740ea",
            completed.stdout,
        )
        self.assertIn("Practice Match: passed", completed.stdout)

    def test_guidance_documents_boundaries_and_validation_authority(self) -> None:
        guidance = (PROJECT_ROOT / "templates/rust/TEAM_GUIDE.md").read_text()
        for phrase in (
            "Team Source",
            "Rust 1.97.1",
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

    def test_template_release_manifest_binds_current_catalog(self) -> None:
        environment = os.environ.copy()
        environment["RPS_CORE_PATH"] = str(self.core)
        completed = subprocess.run(
            [
                str(PROJECT_ROOT / "release-team-template"),
                "--template",
                "rust",
                "manifest",
                "rust-template-v1",
            ],
            cwd=PROJECT_ROOT,
            env=environment,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        manifest = json.loads(completed.stdout)
        lock = json.loads((PROJECT_ROOT / "core-tool.lock.json").read_text())
        self.assertEqual(
            manifest["team_template"]["expected_source_digest"],
            "sha256:f55486d39ac9dca3333b10f1667099e1488d5b937d5baa0e3786f6ca19b11884",
        )
        self.assertEqual(
            manifest["catalog_compatibility"]["runner"]["commit"],
            lock["runner"]["commit"],
        )

    def test_shared_checker_has_no_rust_language_switch(self) -> None:
        checker = (PROJECT_ROOT / "check-team-template").read_text()
        self.assertNotIn('language_environment == "rust"', checker)
        self.assertNotIn("RPS_RUST", checker)


if __name__ == "__main__":
    unittest.main()
