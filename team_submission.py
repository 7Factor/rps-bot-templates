"""Team-owned, commit-resident Team Template selection."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

from template_collection import TeamTemplate, TemplateCollection


FORMAT_VERSION = "rps-team-submission-v1"
RESOLUTION_FORMAT_VERSION = "rps-team-submission-resolution-v1"
FILENAME = "team-submission.json"


class TeamSubmissionError(RuntimeError):
    """A Team submission declaration is absent, malformed, or inconsistent."""


def load_team_submission(path: Path) -> str:
    if path.is_symlink() or not path.is_file():
        raise TeamSubmissionError(
            str(path) + " must be a repository-owned regular file, not a symlink"
        )
    try:
        value = json.loads(path.read_text())
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise TeamSubmissionError(str(path) + " is unreadable: " + str(error)) from error
    return validate_team_submission(value, str(path))


def validate_team_submission(value: object, label: str) -> str:
    if not isinstance(value, dict):
        raise TeamSubmissionError(label + " must contain a JSON object")
    if set(value) != {"format_version", "language_id"}:
        raise TeamSubmissionError(
            label + " must contain exactly format_version and language_id"
        )
    if value["format_version"] != FORMAT_VERSION:
        raise TeamSubmissionError(
            label + " has unsupported format_version "
            + repr(value["format_version"])
        )
    language_id = value["language_id"]
    if not isinstance(language_id, str) or not language_id:
        raise TeamSubmissionError(label + " language_id must be a non-empty string")
    return language_id


def resolve_team_submission(
    root: Path,
    collection: TemplateCollection,
    explicit_language_id: Optional[str] = None,
) -> TeamTemplate:
    path = root / FILENAME
    if explicit_language_id is None:
        language_id = load_team_submission(path)
    elif path.exists() or path.is_symlink():
        language_id = load_team_submission(path)
        if language_id != explicit_language_id:
            raise TeamSubmissionError(
                str(path)
                + " selects "
                + repr(language_id)
                + ", not explicit Team Template "
                + repr(explicit_language_id)
            )
    else:
        language_id = explicit_language_id
    return collection.select(language_id)


def write_team_submission(path: Path, language_id: str) -> None:
    declaration: Dict[str, Any] = {
        "format_version": FORMAT_VERSION,
        "language_id": language_id,
    }
    try:
        with path.open("x") as stream:
            json.dump(declaration, stream, indent=2, sort_keys=True)
            stream.write("\n")
    except FileExistsError as error:
        raise TeamSubmissionError(
            str(path) + " already exists; it was not replaced"
        ) from error


def resolved_manifest(template: TeamTemplate) -> Dict[str, str]:
    return {
        "format_version": RESOLUTION_FORMAT_VERSION,
        "language_id": template.language_id,
        "language_environment": template.language_environment,
        "team_source_path": template.team_source_path.as_posix(),
        "template_release": template.release_tag,
        "template_version": template.version,
    }
