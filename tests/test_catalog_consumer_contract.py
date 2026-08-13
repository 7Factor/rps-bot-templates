from __future__ import annotations

import configparser
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
LOCK_PATH = PROJECT_ROOT / "core-tool.lock.json"
MATERIALIZED_RUNNER = Path(
    os.environ.get("RPS_CORE_PATH", PROJECT_ROOT / ".core" / "rps-tournament")
)
FULL_COMMIT = re.compile(r"^[0-9a-f]{40}$")
CONTENT_IDENTITY = re.compile(r"^[a-z0-9-]+@sha256:[0-9a-f]{64}$")


def load_runner_catalog_module():
    module_path = MATERIALIZED_RUNNER / "rps_runner" / "language_environment.py"
    spec = importlib.util.spec_from_file_location(
        "catalog_consumer_language_environment", module_path
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load Runner catalog module at {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class CatalogConsumerContractTests(unittest.TestCase):
    def test_repository_guidance_declares_the_authority_and_editing_boundaries(
        self,
    ) -> None:
        readme = " ".join((PROJECT_ROOT / "README.md").read_text().split())
        team_guide = " ".join(
            (PROJECT_ROOT / "templates/python/TEAM_GUIDE.md").read_text().split()
        )
        context = (PROJECT_ROOT / "CONTEXT.md").read_text()

        self.assertIn(
            "authoritative for Team Templates and participant-facing Team guidance",
            readme,
        )
        self.assertIn(
            "`rps-tournament` is authoritative for the Language Environment Catalog",
            readme,
        )
        self.assertIn(
            "`templates/python/team_source/` is the only Team-editable directory",
            team_guide,
        )
        self.assertIn(
            "Organizer-owned paths are never part of Team Source", team_guide
        )
        for term in (
            "Language Environment",
            "Team Template",
            "Template Release",
            "Catalog Release",
            "Advisory Validation",
            "Final Validation",
        ):
            with self.subTest(term=term):
                self.assertIn(f"**{term}**:", context)

    def test_lock_claims_compatibility_with_one_immutable_catalog_release(self) -> None:
        lock = json.loads(LOCK_PATH.read_text())

        self.assertEqual(lock["format_version"], "rps-catalog-compatibility-v1")
        self.assertEqual(
            set(lock),
            {"format_version", "runner", "catalog", "offline_bundle"},
        )

        runner = lock["runner"]
        self.assertEqual(set(runner), {"commit", "package_version"})
        self.assertRegex(runner["commit"], FULL_COMMIT)
        self.assertEqual(
            runner["commit"], "e31d9b88a43a0c58934b306b96015bd300b1685d"
        )
        self.assertEqual(runner["package_version"], "0.1.0")

        catalog_claim = lock["catalog"]
        self.assertEqual(
            catalog_claim["path"], "language_environments/catalog-v1/catalog.json"
        )
        self.assertRegex(catalog_claim["identity"], CONTENT_IDENTITY)
        self.assertEqual(
            catalog_claim["identity"],
            "rps-language-environment-catalog-v1@sha256:"
            "c1b2961447993653df86b8a58c4cb4662aa0bc6bfc8e2fe7ed388273968a9f53",
        )
        self.assertTrue(catalog_claim["assets"])
        for identity in catalog_claim["assets"].values():
            self.assertRegex(identity, CONTENT_IDENTITY)

        offline_bundle = lock["offline_bundle"]
        self.assertEqual(set(offline_bundle), {"identity"})
        self.assertRegex(offline_bundle["identity"], CONTENT_IDENTITY)
        self.assertEqual(
            offline_bundle["identity"],
            "rps-runner-offline-bundle-v1@sha256:"
            + hashlib.sha256(
                (PROJECT_ROOT / "core-tool.bundle").read_bytes()
            ).hexdigest(),
        )

        serialized_lock = LOCK_PATH.read_text().lower()
        for mutable_reference in ("latest", '"main"', '"master"'):
            self.assertNotIn(mutable_reference, serialized_lock)

    def test_lock_coordinates_match_the_materialized_runner_release(self) -> None:
        lock = json.loads(LOCK_PATH.read_text())
        runner = lock["runner"]
        catalog_claim = lock["catalog"]

        head = subprocess.run(
            ["git", "-C", str(MATERIALIZED_RUNNER), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        self.assertEqual(head, runner["commit"])

        package = configparser.ConfigParser()
        package.read(MATERIALIZED_RUNNER / "setup.cfg")
        self.assertEqual(package["metadata"]["version"], runner["package_version"])

        catalog_module = load_runner_catalog_module()
        catalog = catalog_module.load_catalog(
            MATERIALIZED_RUNNER / catalog_claim["path"]
        )
        self.assertEqual(catalog.identity, catalog_claim["identity"])
        self.assertEqual(
            {
                f"{environment_name}.{asset_name}": asset.identity
                for environment_name, environment in catalog.environments.items()
                for asset_name, asset in environment.assets.items()
            },
            catalog_claim["assets"],
        )

    def test_materializer_rejects_a_mismatched_checkout(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "rps-tournament"
            subprocess.run(
                [str(PROJECT_ROOT / "materialize-core-tool"), str(destination)],
                cwd=PROJECT_ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            subprocess.run(
                ["git", "-C", str(destination), "checkout", "--quiet", "--detach", "HEAD^"],
                check=True,
                capture_output=True,
                text=True,
            )
            completed = subprocess.run(
                [str(PROJECT_ROOT / "materialize-core-tool"), str(destination)],
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
            )

            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("not a clean checkout", completed.stderr)

    def test_repository_has_no_second_catalog_source_tree(self) -> None:
        self.assertFalse((PROJECT_ROOT / "language_environments").exists())
        for obsolete in (
            "freeze-tournament-catalog",
            "CATALOG_RELEASE.md",
            ".github/workflows/catalog-contract.yml",
            "tests/test_catalog_release.py",
            "tests/test_core_contract.py",
        ):
            with self.subTest(obsolete=obsolete):
                self.assertFalse((PROJECT_ROOT / obsolete).exists())

    def test_active_validation_paths_use_only_the_materialized_catalog(self) -> None:
        active_commands = (
            PROJECT_ROOT / "validate-team",
            PROJECT_ROOT / "prove-amd64-against-arm64",
            PROJECT_ROOT / "prove-cross-repository-cutover",
            PROJECT_ROOT / "tests" / "test_team_branch_template.py",
        )
        for path in active_commands:
            with self.subTest(path=path.name):
                source = path.read_text()
                self.assertIn('["catalog"]["path"]', source)
                self.assertIn("materialize-core-tool", source)

        workflow = (
            PROJECT_ROOT / ".github" / "workflows" / "team-advisory-validation.yml"
        ).read_text()
        self.assertIn(
            "CATALOG: .core/rps-tournament/language_environments/catalog-v1/catalog.json",
            workflow,
        )
        self.assertNotIn(
            "CATALOG: language_environments/catalog-v1/catalog.json", workflow
        )


if __name__ == "__main__":
    unittest.main()
