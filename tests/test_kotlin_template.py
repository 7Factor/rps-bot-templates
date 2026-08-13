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


def has_kotlin_2_4_10_and_java_25() -> bool:
    kotlinc = shutil.which("kotlinc")
    java = shutil.which("java")
    if kotlinc is None or java is None:
        return False
    kotlin = subprocess.run(
        [kotlinc, "-version"], capture_output=True, text=True
    )
    java_version = subprocess.run(
        [java, "-version"], capture_output=True, text=True
    )
    return (
        kotlin.returncode == 0
        and "2.4.10" in (kotlin.stdout + kotlin.stderr)
        and java_version.returncode == 0
        and 'version "25' in java_version.stderr
    )


class KotlinTeamTemplateTests(unittest.TestCase):
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

    def test_collection_exposes_an_independent_kotlin_template(self) -> None:
        collection = load_collection(PROJECT_ROOT, self.catalog)
        template = collection.select("kotlin")

        self.assertEqual(template.language_environment, "kotlin")
        self.assertEqual(template.version, "kotlin-team-template-v1")
        self.assertEqual(template.release_tag, "kotlin-template-v1")
        self.assertEqual(
            template.team_source_path.as_posix(), "templates/kotlin/team_source"
        )
        self.assertNotIn(
            template.release_tag,
            {collection.select(name).release_tag for name in ("java", "clojure")},
        )

    @unittest.skipUnless(
        has_kotlin_2_4_10_and_java_25(),
        "Kotlin 2.4.10 and Java 25 are required for native mode",
    )
    def test_native_entrypoint_builds_and_tests_seeded_behavior(self) -> None:
        completed = subprocess.run(
            [str(PROJECT_ROOT / "templates/kotlin/build-and-test")],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("Kotlin starter build passed", completed.stdout)
        self.assertIn("Kotlin starter tests passed", completed.stdout)

    @unittest.skipUnless(
        os.environ.get("RPS_RUN_DOCKER_INTEGRATION") == "1",
        "set RPS_RUN_DOCKER_INTEGRATION=1 to run pinned Docker integration",
    )
    def test_pinned_docker_toolchain_runs_the_complete_kotlin_suite(self) -> None:
        environment = os.environ.copy()
        environment["RPS_CORE_PATH"] = str(self.core)
        completed = subprocess.run(
            [
                str(PROJECT_ROOT / "check-team-template"),
                "--template",
                "kotlin",
                "--mode",
                "docker",
            ],
            cwd=PROJECT_ROOT,
            env=environment,
            capture_output=True,
            text=True,
            timeout=180,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("Kotlin starter tests passed", completed.stdout)
        self.assertIn("Team Template check passed: kotlin (docker)", completed.stdout)

    @unittest.skipUnless(
        os.environ.get("RPS_RUN_DOCKER_INTEGRATION") == "1",
        "set RPS_RUN_DOCKER_INTEGRATION=1 to run Advisory Validation",
    )
    def test_catalog_v18_passes_participant_local_advisory_validation(self) -> None:
        environment = os.environ.copy()
        environment["RPS_CORE_PATH"] = str(self.core)
        lock = json.loads((PROJECT_ROOT / "core-tool.lock.json").read_text())
        completed = subprocess.run(
            [str(PROJECT_ROOT / "validate-team"), "--template", "kotlin"],
            cwd=PROJECT_ROOT,
            env=environment,
            capture_output=True,
            text=True,
            timeout=240,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("Participant-local Advisory Validation passed", completed.stdout)
        self.assertIn(lock["catalog"]["identity"], completed.stdout)
        self.assertIn(lock["catalog"]["assets"]["kotlin.conformance"], completed.stdout)
        self.assertIn("Practice Match: passed", completed.stdout)
        self.assertIn("Advisory Validation: passed", completed.stdout)

    def test_guidance_documents_boundaries_and_validation_authority(self) -> None:
        guidance = (PROJECT_ROOT / "templates/kotlin/TEAM_GUIDE.md").read_text()
        for phrase in (
            "Team Source",
            "Kotlin 2.4.10",
            "Java 25",
            "--mode native",
            "--mode docker",
            "Advisory Validation",
            "Final Validation",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, guidance)

    def test_template_does_not_copy_the_runner_owned_seed_adapter(self) -> None:
        test_source = (PROJECT_ROOT / "templates/kotlin/tests/StrategyTest.kt").read_text()
        self.assertNotIn("parseUnsignedLong", test_source)
        self.assertNotIn("RPS_SEED", test_source)


if __name__ == "__main__":
    unittest.main()
