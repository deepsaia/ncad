"""Validate a spec dict against the part (feature-tree) schema, returning structured issues.

Issues are returned as data (a list of SchemaIssue); an empty list means valid. This is
the *schema* layer of validation (shape and field constraints). Post-build geometry and
reference validation lives in the build/validate layers.
"""

import logging
from functools import cache
from pathlib import Path

from jsonschema import Draft202012Validator

from ncad.spec.schema_issue import SchemaIssue
from ncad.spec.spec_loader import SpecLoader

logger = logging.getLogger(__name__)

_SCHEMA_PATH = Path(__file__).resolve().parents[3] / "schema" / "part_schema.hocon"
_ROOT_LOCATION = "<root>"


class SchemaValidator:
    """Validates spec dicts against the part (feature-tree) schema (JSON-Schema draft 2020-12)."""

    def __init__(self, schema_path: Path = _SCHEMA_PATH) -> None:
        """Compile the schema (reusing a cached compile for a path already seen this process).

        :param schema_path: Path to the HOCON schema file. Defaults to the bundled
            ``schema/part_schema.hocon``.
        """
        self._validator = _compiled_schema(str(schema_path))

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


@cache
def _compiled_schema(schema_path: str) -> Draft202012Validator:
    """Load + compile the schema at ``schema_path`` once per process.

    The bundled schema is immutable for the process's life, and a compiled Draft202012Validator is
    read-only (validation never mutates it), so a long-lived ``ncad serve`` shares one compile
    across every build instead of re-reading and re-checking the schema on each construction.
    """
    schema = SpecLoader().load(schema_path)
    Draft202012Validator.check_schema(schema)
    logger.debug("loaded + compiled part schema from %s", schema_path)
    return Draft202012Validator(schema)


def _format_location(absolute_path) -> str:
    """Render a jsonschema error path (a deque of keys/indices) as a dotted string."""
    parts = [str(part) for part in absolute_path]
    return ".".join(parts) if parts else _ROOT_LOCATION
