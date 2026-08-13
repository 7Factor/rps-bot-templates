from __future__ import annotations

import json
from pathlib import Path
import shutil
import tempfile
import unittest

from template_collection import CollectionError, load_collection


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class TemplateCollectionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)
        for relative in (
            "team-templates.json",
            "templates/go/team-template.json",
            "templates/go/team_source/strategy.go",
            "templates/go/TEAM_GUIDE.md",
            "templates/go/build-and-test",
            "templates/java/team-template.json",
            "templates/java/team_source/Strategy.java",
            "templates/java/TEAM_GUIDE.md",
            "templates/java/build-and-test",
            "templates/typescript/team-template.json",
            "templates/typescript/team_source/strategy.ts",
            "templates/typescript/TEAM_GUIDE.md",
            "templates/typescript/build-and-test",
            "templates/csharp/team-template.json",
            "templates/csharp/team_source/Strategy.cs",
            "templates/csharp/TEAM_GUIDE.md",
            "templates/csharp/build-and-test",
            "templates/rust/team-template.json",
            "templates/rust/team_source/strategy.rs",
            "templates/rust/TEAM_GUIDE.md",
            "templates/rust/build-and-test",
            "templates/ruby/team-template.json",
            "templates/ruby/team_source/strategy.rb",
            "templates/ruby/TEAM_GUIDE.md",
            "templates/ruby/build-and-test",
            "templates/python/team-template.json",
            "templates/python/team_source/strategy.py",
            "templates/python/TEAM_GUIDE.md",
            "templates/python/build-and-test",
            ".github/workflows/team-advisory-validation.yml",
        ):
            source = PROJECT_ROOT / relative
            destination = self.root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
        self.catalog = self.root / "catalog.json"
        self.write_json(
            "catalog.json",
            {
                "environments": {
                    "python": {
                        "language": "python",
                        "contract_only": False,
                    },
                    "go": {"language": "go", "contract_only": False},
                    "java": {"language": "java", "contract_only": False},
                    "typescript": {
                        "language": "typescript",
                        "contract_only": False,
                    },
                    "csharp": {"language": "csharp", "contract_only": False},
                    "rust": {"language": "rust", "contract_only": False},
                    "ruby": {"language": "ruby", "contract_only": False},
                }
            },
        )

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def read_json(self, relative: str) -> dict:
        return json.loads((self.root / relative).read_text())

    def write_json(self, relative: str, value: object) -> None:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, indent=2) + "\n")

    def test_discovers_python_and_binds_its_complete_contract(self) -> None:
        collection = load_collection(self.root, self.catalog)

        template = collection.select("python")

        self.assertEqual(
            collection.language_ids,
            ("csharp", "go", "java", "python", "ruby", "rust", "typescript"),
        )
        self.assertEqual(template.language_id, "python")
        self.assertEqual(template.language_environment, "python")
        self.assertEqual(
            template.team_source_path, Path("templates/python/team_source")
        )
        self.assertEqual(
            template.participant_guidance_path, Path("templates/python/TEAM_GUIDE.md")
        )
        self.assertEqual(
            template.build_and_test_entrypoint, Path("templates/python/build-and-test")
        )
        self.assertEqual(template.version, "python-team-template-v2")
        self.assertEqual(template.release_tag, "python-template-v2")
        self.assertRegex(template.expected_source_digest, r"^sha256:[0-9a-f]{64}$")

    def test_rejects_duplicate_ids_missing_descriptors_and_unsafe_paths(self) -> None:
        original = self.read_json("team-templates.json")
        python_entry = next(
            entry for entry in original["templates"] if entry["language_id"] == "python"
        )
        cases = {
            "duplicate language ID": [python_entry, python_entry],
            "missing descriptor": [
                {"language_id": "python", "descriptor": "templates/missing.json"}
            ],
            "safe repository-relative POSIX path": [
                {"language_id": "python", "descriptor": "../team-template.json"}
            ],
        }

        for diagnostic, entries in cases.items():
            with self.subTest(diagnostic=diagnostic):
                index = dict(original)
                index["templates"] = entries
                self.write_json("team-templates.json", index)
                with self.assertRaisesRegex(CollectionError, diagnostic):
                    load_collection(self.root, self.catalog)

    def test_rejects_unsafe_bound_paths_and_absent_language_environment(self) -> None:
        descriptor = self.read_json("templates/python/team-template.json")
        descriptor["team_source_path"] = "/tmp/team-source"
        self.write_json("templates/python/team-template.json", descriptor)

        with self.assertRaisesRegex(
            CollectionError, "safe repository-relative POSIX path"
        ):
            load_collection(self.root, self.catalog)

        descriptor["team_source_path"] = "templates/python/team_source"
        descriptor["language_environment"] = "clojure"
        self.write_json("templates/python/team-template.json", descriptor)
        with self.assertRaisesRegex(
            CollectionError, "Language Environment 'clojure'.*pinned Catalog Release"
        ):
            load_collection(self.root, self.catalog)

    def test_rejects_a_descriptor_reached_through_a_symlinked_directory(self) -> None:
        outside = self.root.parent / (self.root.name + "-outside")
        outside.mkdir()
        shutil.copytree(self.root / "templates", outside / "templates")
        shutil.rmtree(self.root / "templates")
        (self.root / "templates").symlink_to(outside / "templates", target_is_directory=True)
        self.addCleanup(shutil.rmtree, outside)

        with self.assertRaisesRegex(CollectionError, "symbolic link"):
            load_collection(self.root, self.catalog)

    def test_rejects_a_symlinked_collection_index(self) -> None:
        outside = self.root.parent / (self.root.name + "-index.json")
        shutil.copy2(self.root / "team-templates.json", outside)
        (self.root / "team-templates.json").unlink()
        (self.root / "team-templates.json").symlink_to(outside)
        self.addCleanup(outside.unlink)

        with self.assertRaisesRegex(CollectionError, "symbolic link"):
            load_collection(self.root, self.catalog)

    def test_selection_must_be_explicit_when_more_than_one_template_exists(self) -> None:
        collection = load_collection(self.root, self.catalog)

        with self.assertRaisesRegex(
            CollectionError,
            "selection is ambiguous.*csharp, go, java, python, ruby, rust, typescript",
        ):
            collection.select()
        with self.assertRaisesRegex(
            CollectionError, "available: csharp, go, java, python, ruby, rust, typescript"
        ):
            collection.select("clojure")

    def test_maintainer_guide_preserves_the_runner_ownership_boundary(self) -> None:
        guide = (PROJECT_ROOT / "TEAM_TEMPLATE_COLLECTION.md").read_text()
        normalized = " ".join(guide.split())

        for statement in (
            "team-templates.json",
            "templates/python/team-template.json",
            "templates/go/team-template.json",
            "templates/java/team-template.json",
            "templates/typescript/team-template.json",
            "templates/csharp/team-template.json",
            "templates/rust/team-template.json",
            "templates/ruby/team-template.json",
            "./validate-team --template go",
            "./release-team-template --template go manifest go-template-v1",
            "--template java",
            "--template typescript",
            "--template csharp",
            "--template rust",
            "--template ruby",
            "Team Templates",
            "Runner-owned Language Environments",
            "exact pinned Catalog Release",
            "ADR 0001",
            "does not copy",
        ):
            with self.subTest(statement=statement):
                self.assertIn(statement, normalized)


if __name__ == "__main__":
    unittest.main()
