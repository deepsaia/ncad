"""Validate an assembly document against the assembly schema + instance-id uniqueness.

Mirrors SchemaValidator (shape/field constraints via jsonschema) and adds the semantic check
that instance ids are unique within the assembly (author-controlled reference names, so a
collision is a contract error reported by id).
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
        issues.extend(self._instance_geometry_source(document))
        issues.extend(self._duplicate_ids(document))
        issues.extend(self._duplicate_constraint_ids(document))
        issues.extend(self._duplicate_joint_ids(document))
        issues.extend(self._joint_constraint_id_collisions(document))
        issues.extend(self._duplicate_coupling_ids(document))
        issues.extend(self._coupling_id_collisions(document))
        issues.extend(self._coupling_joint_refs(document))
        return issues

    def _instance_geometry_source(self, document: dict) -> list[SchemaIssue]:
        """Each instance must name exactly one geometry source.

        A part ({file, part}), a sub-assembly (`assembly`), a `mirror`/`of` reflection, or a
        `replace` swap. A {file} without {part} (or vice versa) is a contract error, as is an
        instance naming none of the above.
        """
        out: list[SchemaIssue] = []
        for instance in document.get("assembly", {}).get("instances", []):
            iid = instance.get("id")
            has_part = "file" in instance and "part" in instance
            partial_part = ("file" in instance) != ("part" in instance)
            has_assembly = "assembly" in instance
            has_mirror = "mirror" in instance or "of" in instance
            has_replace = "replace" in instance
            if partial_part and not has_replace:
                out.append(SchemaIssue(
                    location="assembly.instances",
                    message=f"instance {iid!r} needs both 'file' and 'part'"))
            elif not (has_part or has_assembly or has_mirror or has_replace):
                out.append(SchemaIssue(
                    location="assembly.instances",
                    message=f"instance {iid!r} needs a geometry source "
                            "(file+part, assembly, mirror/of, or replace)"))
        return out

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

    def _duplicate_coupling_ids(self, document: dict) -> list[SchemaIssue]:
        """One issue per repeated coupling id."""
        seen: set[str] = set()
        out: list[SchemaIssue] = []
        for coupling in document.get("assembly", {}).get("couplings", []):
            cid = coupling.get("id")
            if cid is None:
                continue
            if cid in seen:
                out.append(SchemaIssue(location="assembly.couplings",
                                       message=f"duplicate coupling id {cid!r}"))
            seen.add(cid)
        return out

    def _coupling_id_collisions(self, document: dict) -> list[SchemaIssue]:
        """A coupling id must not collide with an instance, constraint, or joint id."""
        assembly = document.get("assembly", {})
        taken = {i.get("id") for i in assembly.get("instances", [])}
        taken |= {c.get("id") for c in assembly.get("constraints", [])}
        taken |= {j.get("id") for j in assembly.get("joints", [])}
        out: list[SchemaIssue] = []
        for coupling in assembly.get("couplings", []):
            cid = coupling.get("id")
            if cid is not None and cid in taken:
                out.append(SchemaIssue(
                    location="assembly.couplings",
                    message=f"coupling id {cid!r} collides with an instance/constraint/joint id"))
        return out

    def _coupling_joint_refs(self, document: dict) -> list[SchemaIssue]:
        """Each coupling `between` entry must reference a declared joint id."""
        assembly = document.get("assembly", {})
        joint_ids = {j.get("id") for j in assembly.get("joints", [])}
        out: list[SchemaIssue] = []
        for coupling in assembly.get("couplings", []):
            cid = coupling.get("id")
            for ref in coupling.get("between", []):
                if ref not in joint_ids:
                    out.append(SchemaIssue(
                        location="assembly.couplings",
                        message=f"coupling {cid!r} references unknown joint {ref!r}"))
        return out
