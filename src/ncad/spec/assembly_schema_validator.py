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
        issues.extend(self._duplicate_constraint_ids(document))
        issues.extend(self._duplicate_joint_ids(document))
        issues.extend(self._joint_constraint_id_collisions(document))
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

    def _duplicate_constraint_ids(self, document: dict) -> list[SchemaIssue]:
        """One issue per repeated constraint id (author-controlled reference names)."""
        seen: set[str] = set()
        out: list[SchemaIssue] = []
        constraints = document.get("assembly", {}).get("constraints", [])
        for constraint in constraints:
            constraint_id = constraint.get("id")
            if constraint_id is None:
                continue
            if constraint_id in seen:
                out.append(SchemaIssue(location="assembly.constraints",
                                       message=f"duplicate constraint id {constraint_id!r}"))
            seen.add(constraint_id)
        return out

    def _duplicate_joint_ids(self, document: dict) -> list[SchemaIssue]:
        """One issue per repeated joint id (author-controlled reference names)."""
        seen: set[str] = set()
        out: list[SchemaIssue] = []
        joints = document.get("assembly", {}).get("joints", [])
        for joint in joints:
            joint_id = joint.get("id")
            if joint_id is None:
                continue
            if joint_id in seen:
                out.append(SchemaIssue(location="assembly.joints",
                                       message=f"duplicate joint id {joint_id!r}"))
            seen.add(joint_id)
        return out

    def _joint_constraint_id_collisions(self, document: dict) -> list[SchemaIssue]:
        """A joint id must not collide with a constraint id (they share one solve id space)."""
        assembly = document.get("assembly", {})
        constraint_ids = {c.get("id") for c in assembly.get("constraints", [])}
        out: list[SchemaIssue] = []
        for joint in assembly.get("joints", []):
            joint_id = joint.get("id")
            if joint_id is not None and joint_id in constraint_ids:
                out.append(SchemaIssue(
                    location="assembly.joints",
                    message=f"joint id {joint_id!r} collides with a constraint id"))
        return out
