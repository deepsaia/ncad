"""Static reference checks for an assembly document (bucket: validation & diagnostics).

Catches the cross-document errors an agent trips on that today only surface as a mid-solve crash: an
instance referencing a part that does not exist, a joint/mate `between` naming an unknown instance
or a connector the part does not declare, and an unknown joint type. Returns Diagnostics; never
raises. Connector resolution is supplied by the caller as connectors_by_part (a part absent from the
map = its file/part could not be read -> MISSING_INSTANCE_PART). One class.
"""

from ncad.diagnostics import codes
from ncad.diagnostics.diagnostic import Diagnostic

_KNOWN_JOINT_TYPES = frozenset({
    "fixed", "revolute", "slider", "cylindrical", "planar", "ball", "point_on_line", "slot",
    "screw",
    "point_in_line", "point_in_plane", "in_line", "line_in_plane", "in_plane",
    "cylspherical", "revcylindrical", "sphspherical", "revrevolute",
    "no_rotation", "parallel_axes", "perpendicular", "constant_velocity", "at_point"})


class AssemblyReferenceCheck:
    """Validates instance/connector/joint references in an assembly document."""

    def check(self, document: dict, connectors_by_part: dict) -> list[Diagnostic]:
        """Return reference Diagnostics for the assembly (empty when all references resolve)."""
        assembly = document.get("assembly") or {}
        instances = assembly.get("instances") or []
        part_of = {i.get("id"): i.get("part") for i in instances}
        out: list[Diagnostic] = []
        for idx, inst in enumerate(instances):
            part = inst.get("part")
            if part is not None and part not in connectors_by_part:
                out.append(Diagnostic(
                    severity="error", code=codes.MISSING_INSTANCE_PART,
                    location=f"assembly.instances.{idx}",
                    message=f"instance {inst.get('id')!r} references part {part!r} not found in "
                            f"{inst.get('file')!r}",
                    hint="check the instance 'file' + 'part' name", stage="semantic"))
        for jidx, joint in enumerate(assembly.get("joints") or []):
            jtype = joint.get("type")
            if jtype is not None and jtype not in _KNOWN_JOINT_TYPES:
                out.append(Diagnostic(
                    severity="error", code=codes.UNKNOWN_JOINT_TYPE,
                    location=f"assembly.joints.{jidx}.type",
                    message=f"joint {joint.get('id')!r} has unknown type {jtype!r}",
                    hint=f"use one of {sorted(_KNOWN_JOINT_TYPES)}", stage="semantic"))
            out.extend(self._between(joint.get("between") or [], part_of, connectors_by_part,
                                     f"assembly.joints.{jidx}.between"))
        for midx, mate in enumerate(assembly.get("mates") or []):
            out.extend(self._between(mate.get("between") or [], part_of, connectors_by_part,
                                     f"assembly.mates.{midx}.between"))
        return out

    def _between(self, between: list, part_of: dict, connectors_by_part: dict,
                 base_location: str) -> list[Diagnostic]:
        """Diagnostics for one joint/mate's connector refs (unknown instance or connector)."""
        out: list[Diagnostic] = []
        for ridx, ref in enumerate(between):
            if not isinstance(ref, dict):
                continue
            iid, conn = ref.get("instance"), ref.get("connector")
            location = f"{base_location}.{ridx}"
            if iid not in part_of:
                out.append(Diagnostic(
                    severity="error", code=codes.UNRESOLVED_CONNECTOR, location=location,
                    message=f"references unknown instance {iid!r}",
                    hint="reference a declared instance id", stage="semantic"))
                continue
            declared = connectors_by_part.get(part_of[iid], set())
            if conn is not None and conn not in declared:
                out.append(Diagnostic(
                    severity="error", code=codes.UNRESOLVED_CONNECTOR, location=location,
                    message=f"instance {iid!r} (part {part_of[iid]!r}) has no connector {conn!r}",
                    hint=f"declare connector {conn!r} on part {part_of[iid]!r}, or fix the name",
                    stage="semantic"))
        return out
