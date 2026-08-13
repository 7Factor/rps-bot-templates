from __future__ import annotations

import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import textwrap
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
COMMAND = PROJECT_ROOT / "check-team-template"
DESCRIPTOR = json.loads(
    (PROJECT_ROOT / "templates/python/team-template.json").read_text()
)
LOCK = json.loads((PROJECT_ROOT / "core-tool.lock.json").read_text())


class PythonTemplateMigrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.bin = self.root / "bin"
        self.bin.mkdir()
        self.log = self.root / "docker.jsonl"
        self.core = self.root / "core"
        subprocess.run(
            [str(PROJECT_ROOT / "materialize-core-tool"), str(self.core)],
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def write_executable(self, name: str, source: str) -> None:
        path = self.bin / name
        path.write_text(textwrap.dedent(source).lstrip())
        path.chmod(path.stat().st_mode | stat.S_IXUSR)

    def run_command(
        self, *arguments: str, path: str | None = None
    ) -> subprocess.CompletedProcess[str]:
        environment = os.environ.copy()
        environment.update(
            {
                "PATH": path or environment["PATH"],
                "RPS_CORE_PATH": str(self.core),
                "RPS_TEST_DOCKER_LOG": str(self.log),
            }
        )
        return subprocess.run(
            [sys.executable, str(COMMAND), *arguments],
            cwd=PROJECT_ROOT,
            env=environment,
            capture_output=True,
            text=True,
            timeout=30,
        )

    def test_native_mode_runs_the_python_owned_build_and_test_entrypoint(self) -> None:
        completed = self.run_command("--template", "python", "--mode", "native")

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("Python starter build passed", completed.stdout)
        self.assertIn("Python starter tests passed", completed.stdout)
        self.assertIn(
            "Entrypoint: templates/python/build-and-test", completed.stdout
        )

    def test_root_command_reports_available_language_ids_for_a_bad_selection(self) -> None:
        completed = self.run_command("--template", "swift", "--mode", "native")

        self.assertEqual(completed.returncode, 2)
        self.assertIn("unknown Team Template 'swift'", completed.stderr)
        self.assertIn(
            "available: brainf-ck, clojure, csharp, go, java, javascript, kotlin, python, ruby, rust, typescript",
            completed.stderr,
        )

    def test_docker_mode_runs_the_identical_entrypoint_in_the_pinned_toolchain(self) -> None:
        self.write_executable(
            "docker",
            """
            #!/bin/sh
            if [ "$1" = version ]; then
              printf '%s\n' 'linux/arm64'
              exit 0
            fi
            printf '%s\n' "$@" > "$RPS_TEST_DOCKER_LOG"
            printf '%s\n' 'Python starter build passed'
            printf '%s\n' 'Python starter tests passed'
            exit "${RPS_TEST_DOCKER_EXIT:-0}"
            """,
        )
        completed = self.run_command(
            "--template",
            "python",
            "--mode",
            "docker",
            path=str(self.bin) + os.pathsep + os.environ["PATH"],
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        arguments = self.log.read_text().splitlines()
        catalog = json.loads(
            (self.core / LOCK["catalog"]["path"]).read_text()
        )
        runtime_path = catalog["environments"]["python"]["assets"][
            "build_toolchain"
        ]["path"]
        runtimes = json.loads(
            (self.core / Path(LOCK["catalog"]["path"]).parent / runtime_path).read_text()
        )
        expected_image = runtimes["platforms"]["linux/arm64"][
            "build_toolchain"
        ]["image"]
        self.assertIn("--pull=never", arguments)
        self.assertIn("--network=none", arguments)
        self.assertIn("linux/arm64", arguments)
        self.assertIn(expected_image, arguments)
        self.assertEqual(arguments[-1], "./templates/python/build-and-test")
        self.assertIn("Python starter build passed", completed.stdout)
        self.assertIn("Python starter tests passed", completed.stdout)
        self.assertIn(
            "Entrypoint: templates/python/build-and-test", completed.stdout
        )

        environment = os.environ.copy()
        environment.update(
            {
                "PATH": str(self.bin) + os.pathsep + environment["PATH"],
                "RPS_CORE_PATH": str(self.core),
                "RPS_TEST_DOCKER_LOG": str(self.log),
                "RPS_TEST_DOCKER_EXIT": "7",
            }
        )
        failed = subprocess.run(
            [
                sys.executable,
                str(COMMAND),
                "--template",
                "python",
                "--mode",
                "docker",
            ],
            cwd=PROJECT_ROOT,
            env=environment,
            capture_output=True,
            text=True,
            timeout=30,
        )
        self.assertEqual(failed.returncode, 7)
        self.assertIn("Python starter build passed", failed.stdout)
        self.assertIn("Docker execution failure", failed.stderr)

    def test_native_missing_tool_and_docker_host_failures_are_distinct(self) -> None:
        self.write_executable(
            "git",
            """
            #!/bin/sh
            exec /usr/bin/git "$@"
            """,
        )
        native = self.run_command(
            "--template", "python", "--mode", "native", path=str(self.bin)
        )
        self.assertNotEqual(native.returncode, 0)
        self.assertIn("Native toolchain failure", native.stderr)
        self.assertIn("--mode docker", native.stderr)

        self.write_executable(
            "docker",
            """
            #!/bin/sh
            printf '%s\n' 'Cannot connect to the Docker daemon' >&2
            exit 1
            """,
        )
        docker = self.run_command(
            "--template",
            "python",
            "--mode",
            "docker",
            path=str(self.bin) + os.pathsep + os.environ["PATH"],
        )
        self.assertNotEqual(docker.returncode, 0)
        self.assertIn("Docker-host failure", docker.stderr)
        self.assertIn("Cannot connect to the Docker daemon", docker.stderr)

    def test_contraction_keeps_only_the_migrated_release_identity(self) -> None:
        legacy = PROJECT_ROOT / "team_source/strategy.py"
        migrated = PROJECT_ROOT / "templates/python/team_source/strategy.py"

        self.assertTrue(migrated.is_file())
        self.assertFalse(legacy.exists())
        self.assertEqual(
            DESCRIPTOR["expected_source_digest"],
            "sha256:e2890c1587c6c98acb62121e5524d8f75a53925ed738f333f63beee81e60fd1a",
        )
        self.assertEqual(DESCRIPTOR["version"], "python-team-template-v3")
        self.assertEqual(DESCRIPTOR["release_tag"], "python-template-v3")
        self.assertEqual(
            DESCRIPTOR["team_source_path"], "templates/python/team_source"
        )
        self.assertFalse((PROJECT_ROOT / "team-template.json").exists())


if __name__ == "__main__":
    unittest.main()
