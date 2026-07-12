"""Compose an assembly document into a scene sidecar the viewer renders.

For each instance: build (or reuse, via a per-file DocumentBuilder + its feature cache) the
referenced part's glb, resolve its placement to a 4x4, and record it. An instance is placed either
explicitly (``placement``) or by a connector-to-connector snap (``connect``): the moving instance's
named connector frame is landed on an already-placed target instance's connector frame (bucket 5.1).
The result is a lightweight composition of independently-built cached parts (design section 7
large-assembly strategy), NOT a re-baked merged glTF. Bad instance refs / connects are id-attributed
issues; a bad instance is skipped or falls back to identity and the rest still compose.
"""

import json
import logging
import os
from typing import Any

from ncad.assembly.assembly_placement import AssemblyPlacement
from ncad.assembly.connector_frame import ConnectorFrame
from ncad.assembly.connector_resolver import ConnectorResolver
from ncad.assembly.dof_diagnostics import PRIMITIVE_DOF, DofDiagnostics
from ncad.assembly.frame_snap import FrameSnap
from ncad.assembly.joint_lowering import JointError, JointLowering
from ncad.assembly.mate_lowering import MateError, MateLowering
from ncad.assembly.mate_solver import MateSolver
from ncad.build.document_builder import DocumentBuilder
from ncad.spec.assembly_schema_validator import AssemblySchemaValidator
from ncad.spec.spec_loader import SpecLoader

logger = logging.getLogger(__name__)

_ASSEMBLY_SUFFIX = ".assembly.json"
# Document unit -> metres (glTF's unit). The scene sidecar's placements are baked to metres so
# they match the part glbs (which export in metres), and the viewer stays unit-agnostic.
_TO_METRES = {"mm": 0.001, "m": 1.0, "in": 0.0254}


class AssemblyBuilder:
    """Builds/reuses each instance's part glb and writes the assembly scene sidecar."""

    def __init__(self, kernel: Any) -> None:
        self._kernel = kernel
        self._loader = SpecLoader()
        self._validator = AssemblySchemaValidator()
        self._placement = AssemblyPlacement()
        self._connectors = ConnectorResolver()
        self._snap = FrameSnap()
        self._lowering = MateLowering()
        self._joint_lowering = JointLowering()
        self._solver = MateSolver()
        self._diagnostics = DofDiagnostics()

    def assemble(self, asm_path: str, out_dir: str) -> dict:
        """Compose the assembly at ``asm_path`` into ``out_dir``; return sidecar path + issues."""
        document = self._loader.load(asm_path)
        schema_issues = self._validator.validate(document)
        if schema_issues:
            rendered = "; ".join(f"{i.location}: {i.message}" for i in schema_issues)
            raise ValueError(f"assembly failed schema validation: {rendered}")
        os.makedirs(out_dir, exist_ok=True)
        asm_dir = os.path.dirname(os.path.abspath(asm_path))
        name = _stem(asm_path)
        # Part glbs export in metres (build123d export_gltf scales the document unit to metres),
        # so the scene sidecar bakes placements to metres too. The viewer then consumes the scene
        # unit-agnostic, exactly as it does a single-part glb.
        to_metres = _TO_METRES.get(document.get("units", "mm"), 0.001)
        # One DocumentBuilder per part file so its feature cache composes cached parts across
        # instances; built_glbs dedups a {file, part} placed more than once.
        builders: dict[str, DocumentBuilder] = {}
        built_glbs: dict[tuple[str, str], str] = {}
        # Placement matrices are computed in document units (mm) so a connect snap can compose in a
        # single unit space; the translation is baked to metres only when the sidecar is written.
        placements_mm: dict[str, list[list[float]]] = {}
        local_frames: dict[str, dict[str, ConnectorFrame]] = {}
        instances: list[dict] = []
        issues: list[dict] = []
        for instance in document["assembly"]["instances"]:
            glb = self._ensure_part_glb(instance, asm_dir, out_dir, builders, built_glbs, issues)
            if glb is None:
                continue
            iid = instance["id"]
            local_frames[iid] = self._resolve_connectors(instance, asm_dir, builders, issues)
            matrix_mm = self._place(instance, placements_mm, local_frames, issues)
            placements_mm[iid] = matrix_mm
            world = [_bake_frame(cid, _world_frame(frame, matrix_mm), to_metres)
                     for cid, frame in local_frames[iid].items()]
            instances.append({"id": iid, "part_glb": glb, "part_name": instance["part"],
                              "placement": _bake_matrix(matrix_mm, to_metres),
                              "connectors": world, "lock": bool(instance.get("lock"))})
        # Solve the mate network (if any): overwrites solved instances' placements + world
        # connector frames in the sidecar list, and yields the solve status + mate records.
        solve_block, mates_out, joints_out = self._solve_constraints(
            document, local_frames, placements_mm, to_metres, instances, issues)
        sidecar = os.path.join(out_dir, f"{name}{_ASSEMBLY_SUFFIX}")
        # Record the source .asm.hocon so the viewer can regenerate this assembly after a reload
        # (the browser's in-memory source map is lost on reload; this survives it, like the part
        # meta sidecar's `source`).
        with open(sidecar, "w", encoding="utf-8") as handle:
            json.dump({"schema_version": 1, "name": name, "source": os.path.abspath(asm_path),
                       "instances": instances, "solve": solve_block, "mates": mates_out,
                       "joints": joints_out}, handle)
        return {"sidecar": sidecar, "issues": issues, "instances": [i["id"] for i in instances]}

    def _place(self, instance: dict, placements_mm: dict,
               local_frames: dict, issues: list) -> list[list[float]]:
        """Placement matrix (mm) for an instance: connect snap, explicit placement, or identity."""
        connect = instance.get("connect")
        if connect:
            return self._connect_matrix(instance, connect, placements_mm, local_frames, issues)
        return self._placement.matrix(instance.get("placement"), 1.0)

    def _connect_matrix(self, instance: dict, connect: dict, placements_mm: dict,
                        local_frames: dict, issues: list) -> list[list[float]]:
        """Snap ``my`` connector onto an already-placed target connector; identity on any gap."""
        iid = instance["id"]
        target = connect.get("to", {})
        tinst, tconn = target.get("instance"), target.get("connector")
        # The target must be an already-placed earlier instance (single-pass, document order); a
        # forward/unknown reference cannot be resolved here and falls back to identity.
        if tinst not in placements_mm:
            issues.append({"instance_id": iid,
                           "message": f"connect target {tinst!r} not placed before {iid!r}"})
            return self._placement.matrix(None, 1.0)
        moving = local_frames.get(iid, {}).get(connect.get("my"))
        target_local = local_frames.get(tinst, {}).get(tconn)
        if moving is None or target_local is None:
            mine = connect.get("my")
            issues.append({"instance_id": iid,
                           "message": f"connect connector missing ({mine!r}/{tconn!r})"})
            return self._placement.matrix(None, 1.0)
        target_world = _world_frame(target_local, placements_mm[tinst])
        return self._snap.transform(moving, target_world,
                                    float(connect.get("offset", 0.0)), bool(connect.get("flip")))

    def _solve_constraints(self, document: dict, local_frames: dict, placements_mm: dict,
                           to_metres: float, instances: list,
                           issues: list) -> tuple[dict, list, list]:
        """Solve the mate + joint network; overwrite placements; return (solve, mates, joints)."""
        constraints = document["assembly"].get("constraints") or []
        joints = document["assembly"].get("joints") or []
        if not constraints and not joints:
            return ({"status": "well_constrained", "dof": 0, "explanation": "no constraints",
                     "failing_ids": [], "redundant_ids": [], "under_constrained_hint": None},
                    [], [])
        primitives: list[dict] = []
        mates_out: list[dict] = []
        for mate in constraints:
            prims = self._lower_mate(mate, local_frames, issues)
            if prims is None:
                continue
            primitives.extend(prims)
            mates_out.append({"id": mate["id"], "type": mate["type"],
                              "between": mate.get("between", []), "value": mate.get("value"),
                              "ok": True})
        joints_out: list[dict] = []
        for joint in joints:
            prims_sig = self._lower_joint(joint, local_frames, issues)
            if prims_sig is None:
                continue
            prims, signature = prims_sig
            primitives.extend(prims)
            joints_out.append({"id": joint["id"], "type": joint["type"],
                               "between": joint.get("between", []), "value": joint.get("value"),
                               "limits": joint.get("limits"),
                               "signature": [a.to_dict() for a in signature], "ok": True})
        ground_ids = self._ground_ids(document, constraints, instances)
        outcome = self._solver.solve(local_frames, primitives, ground_ids, placements_mm)
        # Overwrite each solved instance's placement + world connector frames (baked to metres).
        by_id = {inst["id"]: inst for inst in instances}
        for iid, matrix_mm in outcome.placements.items():
            inst = by_id.get(iid)
            if inst is None:
                continue
            inst["placement"] = _bake_matrix(matrix_mm, to_metres)
            inst["connectors"] = [_bake_frame(cid, _world_frame(frame, matrix_mm), to_metres)
                                  for cid, frame in local_frames.get(iid, {}).items()]
        # Diagnostics (bucket 5.3): interpret the raw solve signals into a legible report. The
        # network summary feeds the nominal DoF-accounting explanation; the solver's dof is truth.
        network = {"bodies": len(local_frames), "grounded": len(ground_ids),
                   "removed": sum(PRIMITIVE_DOF.get(p["kind"], 0) for p in primitives)}
        report = self._diagnostics.analyze(outcome, network)
        failing = set(report.failing_ids)
        redundant = set(report.redundant_ids)
        for record in (*mates_out, *joints_out):
            record["ok"] = record["id"] not in failing
            record["role"] = ("failing" if record["id"] in failing
                              else "redundant" if record["id"] in redundant else "active")
        logger.info("assembly solve: status=%s dof=%d failing=%s redundant=%s joints=%d (%s)",
                    report.status, report.dof, report.failing_ids, report.redundant_ids,
                    len(joints_out), report.explanation)
        return report.to_dict(), mates_out, joints_out

    def _lower_joint(self, joint: dict, local_frames: dict, issues: list):
        """Resolve a joint's refs + lower to primitives + signature; None on error."""
        between = joint.get("between") or []
        a_ref = between[0] if len(between) >= 1 else None
        b_ref = between[1] if len(between) >= 2 else None
        frame_a = self._frame_for(a_ref, local_frames)
        frame_b = self._frame_for(b_ref, local_frames)
        if frame_a is None or frame_b is None:
            issues.append({"joint_id": joint.get("id"),
                           "message": f"joint {joint.get('id')!r} references an unknown connector"})
            return None
        try:
            prims, signature = self._joint_lowering.lower(joint, frame_a, frame_b)
        except JointError as exc:
            issues.append({"joint_id": joint.get("id"), "message": str(exc)})
            return None
        for prim in prims:
            prim["id"] = joint["id"]
            prim["a_ref"] = a_ref
            prim["b_ref"] = b_ref
        return prims, signature

    def _lower_mate(self, mate: dict, local_frames: dict, issues: list) -> list[dict] | None:
        """Resolve a mate's refs + lower to primitives with a_ref/b_ref attached; None on error."""
        between = mate.get("between") or []
        a_ref = between[0] if len(between) >= 1 else None
        b_ref = between[1] if len(between) >= 2 else None
        frame_a = self._frame_for(a_ref, local_frames)
        frame_b = self._frame_for(b_ref, local_frames) if b_ref else None
        if frame_a is None or (b_ref is not None and frame_b is None):
            issues.append({"constraint_id": mate.get("id"),
                           "message": f"mate {mate.get('id')!r} references an unknown connector"})
            return None
        try:
            prims = self._lowering.lower(mate, frame_a, frame_b)
        except MateError as exc:
            issues.append({"constraint_id": mate.get("id"), "message": str(exc)})
            return None
        for prim in prims:
            prim["id"] = mate["id"]
            prim["a_ref"] = a_ref
            prim["b_ref"] = b_ref
        return prims

    def _frame_for(self, ref: dict | None,
                   local_frames: dict) -> ConnectorFrame | None:
        """The local ConnectorFrame a {instance, connector} ref names, or None."""
        if not ref:
            return None
        return local_frames.get(ref.get("instance"), {}).get(ref.get("connector"))

    def _ground_ids(self, document: dict, constraints: list, instances: list) -> set:
        """First instance + any lock:true instance + any instance targeted by a lock mate."""
        ground: set = set()
        if instances:
            ground.add(instances[0]["id"])
        for inst in document["assembly"]["instances"]:
            if inst.get("lock"):
                ground.add(inst["id"])
        for mate in constraints:
            if mate.get("type") == "lock":
                between = mate.get("between") or []
                if between:
                    ground.add(between[0]["instance"])
        return ground

    def _resolve_connectors(self, instance: dict, asm_dir: str, builders: dict,
                            issues: list) -> dict[str, ConnectorFrame]:
        """Resolve a part's declared connectors to local-space frames (empty on any failure)."""
        part_file = os.path.join(asm_dir, instance["file"])
        key = os.path.abspath(part_file)
        builder = builders.setdefault(key, DocumentBuilder(self._kernel))
        try:
            parts = builder.resolve_part_elements(part_file)
        except Exception as exc:  # noqa: BLE001 - a bad part becomes an id-attributed issue
            issues.append({"instance_id": instance["id"],
                           "message": f"connector resolution failed: {exc}"})
            return {}
        part = parts.get(instance["part"])
        if part is None:
            return {}
        part_dict, elements = part
        connectors = part_dict.get("connectors") or []
        if not connectors:
            return {}
        frames, conn_issues = self._connectors.resolve(connectors, elements)
        for issue in conn_issues:
            issues.append({"instance_id": instance["id"], "message": issue["message"]})
        return frames

    def _ensure_part_glb(self, instance: dict, asm_dir: str, out_dir: str,
                         builders: dict, built_glbs: dict, issues: list) -> str | None:
        """Build or reuse the glb for one instance's {file, part}; return its glb basename."""
        instance_id = instance["id"]
        part_file = os.path.join(asm_dir, instance["file"])
        part_name = instance["part"]
        key = (os.path.abspath(part_file), part_name)
        if key in built_glbs:
            return built_glbs[key]  # this {file, part} already built: reuse the glb (dedup)
        if not os.path.exists(part_file):
            issues.append({"instance_id": instance_id,
                           "message": f"part file not found: {instance['file']!r}"})
            return None
        builder = builders.setdefault(key[0], DocumentBuilder(self._kernel))
        try:
            artifacts = builder.build_file(part_file, out_dir, formats=("glb",))
        except Exception as exc:  # noqa: BLE001 - a bad part becomes an id-attributed issue
            issues.append({"instance_id": instance_id, "message": f"part build failed: {exc}"})
            return None
        if part_name not in artifacts:
            issues.append({"instance_id": instance_id,
                           "message": f"part {part_name!r} not in {instance['file']!r}"})
            return None
        glb = os.path.basename(artifacts[part_name])
        built_glbs[key] = glb
        return glb


def _apply_point(matrix: list[list[float]], p: tuple) -> tuple:
    """Map a point through a row-major 4x4 (p' = p . R + t; translation in the last row)."""
    return tuple(sum(p[k] * matrix[k][i] for k in range(3)) + matrix[3][i] for i in range(3))


def _apply_dir(matrix: list[list[float]], d: tuple) -> tuple:
    """Map a direction through a row-major 4x4 (rotation only, no translation)."""
    return tuple(sum(d[k] * matrix[k][i] for k in range(3)) for i in range(3))


def _world_frame(frame: ConnectorFrame, matrix: list[list[float]]) -> ConnectorFrame:
    """Transform a connector frame by a placement matrix into that placement's space."""
    return ConnectorFrame(_apply_point(matrix, frame.origin), _apply_dir(matrix, frame.x),
                          _apply_dir(matrix, frame.y), _apply_dir(matrix, frame.z))


def _bake_matrix(matrix: list[list[float]], to_metres: float) -> list[list[float]]:
    """Copy a placement matrix with its translation row scaled to metres (rotation unit-free)."""
    out = [row[:] for row in matrix]
    out[3][0] *= to_metres
    out[3][1] *= to_metres
    out[3][2] *= to_metres
    return out


def _bake_frame(cid: str, frame: ConnectorFrame, to_metres: float) -> dict:
    """Serialize a world-space connector frame with its origin baked to metres (axes unit-free)."""
    return {"id": cid,
            "origin": [c * to_metres for c in frame.origin],
            "x": list(frame.x), "y": list(frame.y), "z": list(frame.z)}


def _stem(path: str) -> str:
    """The assembly name: the basename without the .asm.hocon (or .hocon) extension."""
    base = os.path.basename(path)
    for suffix in (".asm.hocon", ".hocon"):
        if base.lower().endswith(suffix):
            return base[: -len(suffix)]
    return base
