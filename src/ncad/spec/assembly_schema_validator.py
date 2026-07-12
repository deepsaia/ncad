"""Validate an assembly document against the assembly schema + instance-id uniqueness.

Mirrors SchemaValidator (shape/field constraints via jsonschema) and adds the semantic check
that instance ids are unique within the assembly (author-controlled reference names, so a
collision is a contract error reported by id, per design section 10).
"""

import logging
from pathlib import Path

from jsonschema import Draft202012Validator

from ncad.spec.schema_issue import SchemaIssue
from ncad.spec.spec_loader import SpecLoader

logger = logging.getLogger(__name__)

_SCHEMA_PATH = Path(__file__).resolve().parents[3] / "schema" / "assembly_schema.hocon"


class AssemblySchemaValidator:
    """Validates assembly document dicts against the assembly schema + id uniqueness."""

    def __init__(self, schema_path: Path = _SCHEMA_PATH) -> None:
        """Load and compile the assembly schema once."""
        schema = SpecLoader().load(str(schema_path))
        self._validator = Draft202012Validator(schema)

    def validate(self, document: dict) -> list[SchemaIssue]:
        """Return schema issues plus duplicate-instance-id issues; empty means valid."""
        issues: list[SchemaIssue] = [
            SchemaIssue(
                location=".".join(str(p) for p in error.absolute_path) or "<root>",
                message=error.message)
            for error in self._validator.iter_errors(document)
        ]
        issues.extend(self._duplicate_ids(document))
        return issues

    def _duplicate_ids(self, document: dict) -> list[SchemaIssue]:
        """One issue per repeated instance id (author-controlled reference names)."""
        seen: set[str] = set()
        out: list[SchemaIssue] = []
        instances = document.get("assembly", {}).get("instances", [])
        for instance in instances:
            instance_id = instance.get("id")
            if instance_id is None:
                continue
            if instance_id in seen:
                out.append(SchemaIssue(location="assembly.instances",
                                       message=f"duplicate instance id {instance_id!r}"))
            seen.add(instance_id)
        return out
