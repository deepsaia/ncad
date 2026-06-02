"""Validate a spec dict against the building schema, returning structured issues.

Issues are returned as data (a list of SchemaIssue); an empty list means valid. This is
the *schema* layer of validation (shape and field constraints). Semantic/topological
validation (openings fit their walls, rooms reachable, etc.) lives in the separate
`validate` unit — see design.md §5.
"""

import logging
from pathlib import Path

from jsonschema import Draft202012Validator

from ncad.spec.schema_issue import SchemaIssue
from ncad.spec.spec_loader import SpecLoader

logger = logging.getLogger(__name__)

_SCHEMA_PATH = Path(__file__).resolve().parents[3] / "schema" / "building_schema.hocon"
_ROOT_LOCATION = "<root>"


class SchemaValidator:
    """Validates spec dicts against the building schema (JSON-Schema draft 2020-12)."""

    def __init__(self, schema_path: Path = _SCHEMA_PATH) -> None:
        """Load and compile the schema once.

        :param schema_path: Path to the HOCON schema file. Defaults to the bundled
            ``schema/building_schema.hocon``.
        """
        schema = SpecLoader().load(str(schema_path))
        Draft202012Validator.check_schema(schema)
        self._validator = Draft202012Validator(schema)
        logger.debug("loaded building schema from %s", schema_path)

    def validate(self, spec: dict) -> list[SchemaIssue]:
        """Validate ``spec`` against the schema.

        :param spec: A loaded spec dict.
        :return: A list of issues; empty if the spec is schema-valid.
        """
        issues = [
            SchemaIssue(location=_format_location(error.absolute_path), message=error.message)
            for error in self._validator.iter_errors(spec)
        ]
        if issues:
            logger.debug("spec failed schema validation with %d issue(s)", len(issues))
        return issues


def _format_location(absolute_path) -> str:
    """Render a jsonschema error path (a deque of keys/indices) as a dotted string."""
    parts = [str(part) for part in absolute_path]
    return ".".join(parts) if parts else _ROOT_LOCATION
