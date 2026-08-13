from __future__ import annotations

import importlib.util
import inspect
import json
import os
from pathlib import Path
import random
import shutil
import subprocess
import sys
import tempfile
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
TEAM_SOURCE = PROJECT_ROOT / "templates/python/team_source"
TEAM_GUIDE = PROJECT_ROOT / "templates/python/TEAM_GUIDE.md"
CORE_PATH = Path(
    os.environ.get("RPS_CORE_PATH", PROJECT_ROOT / ".core" / "rps-tournament")
).resolve()
LOCK = json.loads((PROJECT_ROOT / "core-tool.lock.json").read_text())
CATALOG_PATH = CORE_PATH / LOCK["catalog"]["path"]


def load_module(name: str, path: Path, *, register: bool = False):
    # Loading straight from `path` would otherwise have CPython write a
    # `.pyc` into a `__pycache__` sibling of the loaded file. For paths under
    # `TEAM_SOURCE`, that leaves a stray file behind in the real Team Source
    # directory, which a later source-validation test then rejects.
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module at {path}")
    module = importlib.util.module_from_spec(spec)
    if register:
        sys.modules[spec.name] = module
    previous = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = previous
    return module


class TeamBranchTemplateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        subprocess.run(
            [str(PROJECT_ROOT / "materialize-core-tool"), str(CORE_PATH)],
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )

    def test_fresh_branch_strategy_implements_the_team_contract(self) -> None:
        strategy = load_module("team_strategy", TEAM_SOURCE / "strategy.py")
        self.assertEqual(
            list(inspect.signature(strategy.choose_move).parameters),
            ["turn", "my_history", "opponent_history", "rng"],
        )
        first_rng = random.Random(8675309)
        second_rng = random.Random(8675309)
        first_moves = [strategy.choose_move(1, "", "", first_rng) for _ in range(12)]
        second_moves = [
            strategy.choose_move(1, "", "", second_rng) for _ in range(12)
        ]
        self.assertEqual(first_moves, second_moves)
        self.assertLessEqual(set(first_moves), {"R", "P", "S"})

    def test_fresh_branch_strategy_runs_through_the_organizer_wrapper(self) -> None:
        seed = "8675309"
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "team-source"
            shutil.copytree(TEAM_SOURCE, source)
            completed = subprocess.run(
                [
                    sys.executable,
                    str(CATALOG_PATH.parent / "python" / "wrapper.py"),
                ],
                cwd=source,
                env={
                    "RPS_PROTOCOL_VERSION": "rps-jsonl-v1",
                    "RPS_ROUNDS": "1",
                    "RPS_SEED": seed,
                },
                input="1\n-\n-\n",
                capture_output=True,
                text=True,
                timeout=5,
                check=True,
            )

        self.assertEqual(completed.stderr, "RPS_READY_V1\n")
        self.assertEqual(
            completed.stdout,
            random.Random(int(seed)).choice(("R", "P", "S")) + "\n",
        )

    def test_team_source_accepts_approved_modules_and_resources(self) -> None:
        core = load_module(
            "team_branch_language_environment",
            CORE_PATH / "rps_runner" / "language_environment.py",
            register=True,
        )
        catalog = core.load_catalog(CATALOG_PATH)
        environment = catalog.environment("python")

        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "team-source"
            shutil.copytree(TEAM_SOURCE, source)
            (source / "helpers").mkdir()
            (source / "helpers" / "counter.py").write_text("MOVE = 'P'\n")
            (source / "resources").mkdir()
            (source / "resources" / "openings.csv").write_text("turn,move\n1,R\n")
            (source / "resources" / "policy.json").write_text('{"fallback":"S"}\n')
            (source / "resources" / "notes.txt").write_text("Team data\n")

            frozen = core.freeze_source_bundle(
                source,
                Path(directory) / "bundle",
                catalog,
                environment,
            )

        self.assertEqual(
            set(frozen["files"]),
            {
                "helpers/counter.py",
                "resources/notes.txt",
                "resources/openings.csv",
                "resources/policy.json",
                "strategy.py",
            },
        )

    def test_team_guide_defines_the_shared_branch_and_ownership_policy(self) -> None:
        guide = TEAM_GUIDE.read_text()
        normalized_guide = " ".join(guide.split())

        required_statements = (
            "`templates/python/team_source/` is the only Team-editable directory",
            "`R`, `P`, or `S`",
            "protocol I/O, readiness, seeding, and process lifecycle",
            "`team/<team-slug>`",
            "one branch per Team",
            "does not provide submission secrecy",
            "64 files",
            "256 KiB",
            "1 MiB",
        )
        for statement in required_statements:
            with self.subTest(statement=statement):
                self.assertIn(statement, normalized_guide)

        catalog = json.loads(CATALOG_PATH.read_text())
        schema = catalog["environments"]["python"]["source_schema"]
        for path in (
            "wrapper.py",
            "Dockerfile",
            "requirements.lock",
            ".github",
            "catalog.json",
        ):
            with self.subTest(organizer_owned=path):
                self.assertIn(path, guide)
        self.assertEqual(schema["max_file_count"], 64)
        self.assertEqual(schema["max_file_bytes"], 256 * 1024)
        self.assertEqual(schema["max_total_bytes"], 1024 * 1024)


if __name__ == "__main__":
    unittest.main()
