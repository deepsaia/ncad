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

from ncad.assembly.assembly_bom import AssemblyBom
from ncad.assembly.assembly_placement import AssemblyPlacement
from ncad.assembly.component_mirror import ComponentMirror
from ncad.assembly.component_pattern import ComponentPattern, ComponentPatternError
from ncad.assembly.component_replace import ComponentReplace
from ncad.assembly.connector_frame import ConnectorFrame
from ncad.assembly.connector_resolver import ConnectorResolver
from ncad.assembly.coupling import Coupling
from ncad.assembly.dof_diagnostics import PRIMITIVE_DOF, DofDiagnostics
from ncad.assembly.frame_snap import FrameSnap
from ncad.assembly.interference_checker import InterferenceChecker
from ncad.assembly.joint_lowering import JointError, JointLowering
from ncad.assembly.mate_lowering import MateError, MateLowering
from ncad.assembly.mate_solver import MateSolver
from ncad.assembly.mechanism_plane import MechanismPlane
from ncad.assembly.motion_driver import MotionDriver, MotionParamError
from ncad.assembly.planar_motion_solver import PlanarMotionSolver
from ncad.assembly.sub_assembly_composer import SubAssemblyComposer
from ncad.build.document_builder import DocumentBuilder
from ncad.build.mass_calculator import MassCalculator
from ncad.build.material_error import MaterialError
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
        self._pattern = ComponentPattern()
        self._mirror = ComponentMirror()
        self._replace = ComponentReplace()
        self._composer = SubAssemblyComposer()
        self._connectors = ConnectorResolver()
        self._snap = FrameSnap()
        self._lowering = MateLowering()
        self._joint_lowering = JointLowering()
        self._solver = MateSolver()
        self._diagnostics = DofDiagnostics()
        self._interference = InterferenceChecker(kernel)
        self._bom = AssemblyBom()
        self._mass = MassCalculator(kernel)

    def assemble(self, asm_path: str, out_dir: str,
                 _visited: frozenset = frozenset()) -> dict:
        """Compose the assembly at ``asm_path`` into ``out_dir``; return sidecar path + issues.

        ``_visited`` carries the ancestor .asm.hocon paths for sub-assembly cycle detection
        (bucket 5.7); callers use the default empty set.
        """
        abs_path = os.path.abspath(asm_path)
        if abs_path in _visited:
            raise ValueError(f"circular sub-assembly reference: {abs_path}")
        _visited = _visited | {abs_path}
        document = self._loader.load(asm_path)
        schema_issues = self._validator.validate(document)
        if schema_issues:
            rendered = "; ".join(f"{i.location}: {i.message}" for i in schema_issues)
            raise ValueError(f"assembly failed schema validation: {rendered}")
        os.makedirs(out_dir, exist_ok=True)
        asm_dir = os.path.dirname(os.path.abspath(asm_path))
        name = _stem(asm_path)
        # Expand component ops (pattern; mirror/replace/sub-assembly in later tasks) into a flat
        # instance list BEFORE placement/solve, so the rest of the pipeline sees plain instances.
        pre_issues: list[dict] = []
        expanded = self._expand_components(document["assembly"]["instances"], pre_issues)
        # Replace the instance list in place with the expanded one so the whole pipeline (place,
        # solve, analyze) iterates the flattened instances; the document dict stays typed.
        document["assembly"]["instances"] = expanded
        # Part glbs export in metres (build123d export_gltf scales the document unit to metres),
        # so the scene sidecar bakes placements to metres too. The viewer then consumes the scene
        # unit-agnostic, exactly as it does a single-part glb.
        to_metres = _TO_METRES.get(document.get("units", "mm"), 0.001)
        # One DocumentBuilder per part file so its feature cache composes cached parts across
        # instances; built_glbs dedups a {file, part} placed more than once.
        builders: dict[str, DocumentBuilder] = {}
        built_glbs: dict[tuple[str, str], str] = {}
        # Resolved part elements cached PER FILE (resolve_part_elements returns every part in the
        # file), so a file with N instances resolves once, not N times (the load/build was O(N)).
        resolved_files: dict[str, dict] = {}
        # Placement matrices are computed in document units (mm) so a connect snap can compose in a
        # single unit space; the translation is baked to metres only when the sidecar is written.
        placements_mm: dict[str, list[list[float]]] = {}
        local_frames: dict[str, dict[str, ConnectorFrame]] = {}
        instances: list[dict] = []
        issues: list[dict] = list(pre_issues)
        for instance in document["assembly"]["instances"]:
            if instance.get("assembly"):
                # A nested sub-assembly: build it recursively and compose its solved instances
                # under this instance's placement (bucket 5.7). It occupies a rigid-body slot in
                # placements_mm so a later mate/connect can target it as one body.
                instances.extend(self._compose_sub_assembly(
                    instance, asm_dir, out_dir, _visited, to_metres, placements_mm, issues))
                continue
            glb = self._ensure_part_glb(instance, asm_dir, out_dir, builders, built_glbs, issues)
            if glb is None:
                continue
            iid = instance["id"]
            local_frames[iid] = self._resolve_connectors(
                instance, asm_dir, builders, resolved_files, issues)
            matrix_mm = self._place(instance, placements_mm, local_frames, issues)
            placements_mm[iid] = matrix_mm
            world = [_bake_frame(cid, _world_frame(frame, matrix_mm), to_metres)
                     for cid, frame in local_frames[iid].items()]
            instances.append({"id": iid, "part_glb": glb, "part_name": instance["part"],
                              "placement": _bake_matrix(matrix_mm, to_metres),
                              "connectors": world, "lock": bool(instance.get("lock"))})
        # Solve the mate network (if any): overwrites solved instances' placements + world
        # connector frames in the sidecar list, and yields the solve status + mate records.
        solve_block, mates_out, joints_out, couplings_out = self._solve_constraints(
            document, local_frames, placements_mm, to_metres, instances, issues)
        # Motion pass (bucket 6.0): if the document declares a `motion` block, solve the driven
        # PLANAR mechanism over the driver's value sweep in a 2D workplane and write a trajectory
        # sidecar. Runs AFTER the static solve (its placements are the rest pose). Kinematic only
        # (dynamics -> Phase 14).
        motion_path = self._run_motion(document, name, out_dir, local_frames, placements_mm,
                                       to_metres, issues)
        # Analysis over the solved assembly (bucket 5.6): interference + BOM + roll-up mass +
        # structured STEP. Guarded so a failure is an id-attributed issue and the sidecar still
        # writes (without the analysis blocks) rather than aborting the whole assemble.
        interference, bom, mass = self._analyze(
            document, asm_dir, instances, placements_mm, builders, out_dir, name, issues)
        sidecar = os.path.join(out_dir, f"{name}{_ASSEMBLY_SUFFIX}")
        # Record the source .asm.hocon so the viewer can regenerate this assembly after a reload
        # (the browser's in-memory source map is lost on reload; this survives it, like the part
        # meta sidecar's `source`).
        with open(sidecar, "w", encoding="utf-8") as handle:
            json.dump({"schema_version": 1, "name": name, "source": os.path.abspath(asm_path),
                       "instances": instances, "solve": solve_block, "mates": mates_out,
                       "joints": joints_out, "couplings": couplings_out,
                       "interference": interference, "bom": bom, "mass": mass}, handle)
        return {"sidecar": sidecar, "issues": issues, "motion": motion_path,
                "instances": [i["id"] for i in instances]}

    def _expand_components(self, raw_instances: list, issues: list) -> list[dict]:
        """Expand component ops (replace, then mirror, then pattern) into a flat instance list.

        A ``mirror`` instance references an already-declared source (document order); a forward or
        unknown ``of`` reference is refused id-attributed. ``replace`` swaps the geometry ref
        first; ``pattern`` arrays last so a replaced/mirrored instance can also be patterned.
        """
        out: list[dict] = []
        by_id: dict[str, dict] = {}
        for inst in raw_instances:
            resolved = inst
            if "replace" in resolved:
                resolved = self._replace.apply(resolved, resolved["replace"])
            if "mirror" in resolved or "of" in resolved:
                source = by_id.get(resolved.get("of"))
                if source is None:
                    issues.append({"instance_id": resolved.get("id"),
                                   "message": f"mirror source {resolved.get('of')!r} is not "
                                              "declared before it"})
                    continue
                resolved = self._mirror.reflect(
                    resolved, source, (resolved.get("mirror") or {}).get("plane", "XY"))
            try:
                expanded = self._pattern.expand(resolved)
            except ComponentPatternError as exc:
                issues.append({"instance_id": resolved.get("id"), "message": str(exc)})
                continue
            for entry in expanded:
                by_id[entry["id"]] = entry
                out.append(entry)
        return out

    def _compose_sub_assembly(self, instance: dict, asm_dir: str, out_dir: str,
                              visited: frozenset, to_metres: float,
                              placements_mm: dict, issues: list) -> list[dict]:
        """Build a nested sub-assembly and compose its instances under this instance's placement.

        The child assembles into the same out_dir (its own sidecar + STEP); its solved instances
        (placements already baked to metres) are re-parented under the parent placement, also baked
        to metres, so the composed scene stays in one unit space. A circular reference raises inside
        the recursive assemble and is turned into an id-attributed issue here.
        """
        iid = instance["id"]
        child_path = os.path.join(asm_dir, instance["assembly"])
        try:
            child = self.assemble(child_path, out_dir, visited)
        except ValueError as exc:
            issues.append({"instance_id": iid, "message": f"sub-assembly {iid!r}: {exc}"})
            return []
        for child_issue in child["issues"]:
            issues.append({"instance_id": iid,
                           "message": f"{iid}/{child_issue.get('instance_id', '?')}: "
                                      f"{child_issue.get('message', '')}"})
        child_sidecar_path = os.path.join(out_dir, f"{_stem(child_path)}{_ASSEMBLY_SUFFIX}")
        with open(child_sidecar_path, encoding="utf-8") as handle:
            child_doc = json.load(handle)
        parent_metres = _bake_matrix(self._placement.matrix(instance.get("placement"), 1.0),
                                     to_metres)
        return self._composer.compose(child_doc["instances"], parent_metres, iid)

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
                           issues: list) -> tuple[dict, list, list, list]:
        """Solve the mate + joint network; overwrite placements; return solve/mates/joints/coupl."""
        constraints = document["assembly"].get("constraints") or []
        joints = document["assembly"].get("joints") or []
        # Couplings are declared-only (no primitives, no pose); build them up-front so they reach
        # the sidecar even when there is nothing to solve. Phase 6 enforces them.
        couplings_out = [
            Coupling(id=c["id"], type=c["type"], between=list(c.get("between", [])),
                     ratio=c.get("ratio"), profile=c.get("profile")).to_dict()
            for c in (document["assembly"].get("couplings") or [])]
        if not constraints and not joints:
            return ({"status": "well_constrained", "dof": 0, "explanation": "no constraints",
                     "failing_ids": [], "redundant_ids": [], "under_constrained_hint": None},
                    [], [], couplings_out)
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
        # Instances that actually PARTICIPATE in a primitive (referenced by a mate/joint) take the
        # solved pose; untouched instances keep their authored placement. The solver seeds rotation
        # as identity (a 5.3+ refinement), so overwriting a non-participating instance would drop an
        # authored rotation (e.g. a component-patterned bolt); guarding on participation preserves
        # it. Grounded instances also keep their authored placement (they never move).
        participants = {ref["instance"] for p in primitives
                        for ref in (p.get("a_ref"), p.get("b_ref")) if ref} - set(ground_ids)
        by_id = {inst["id"]: inst for inst in instances}
        for iid, matrix_mm in outcome.placements.items():
            inst = by_id.get(iid)
            if inst is None or iid not in participants:
                continue
            inst["placement"] = _bake_matrix(matrix_mm, to_metres)
            inst["connectors"] = [_bake_frame(cid, _world_frame(frame, matrix_mm), to_metres)
                                  for cid, frame in local_frames.get(iid, {}).items()]
        # Diagnostics (bucket 5.3): interpret the raw solve signals into a legible report. The
        # network summary feeds the nominal DoF-accounting explanation; the solver's dof is truth.
        network = {"bodies": len(local_frames), "grounded": len(ground_ids),
                   "removed": sum(PRIMITIVE_DOF.get(p["kind"], 0) for p in primitives),
                   "couplings": len(couplings_out)}
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
        return report.to_dict(), mates_out, joints_out, couplings_out

    def _run_motion(self, document: dict, name: str, out_dir: str, local_frames: dict,
                    placements_mm: dict, to_metres: float, issues: list) -> str | None:
        """Solve a driven PLANAR mechanism over the motion block's values; write <name>.motion.json.

        A planar mechanism (revolute axes parallel to one plane) is solved in a 2D workplane by
        PlanarMotionSolver, which closes the loops the 3D static solver cannot. Frames are taken at
        their WORLD rest pose (static placement applied); each solved in-plane delta composes back
        onto the rest placement. A bad motion block is an id-attributed issue; the static sidecar
        still writes, no motion sidecar. Kinematic only (dynamics -> Phase 14).
        """
        motion = document.get("motion")
        if not motion:
            return None
        try:
            joint_id, values = MotionDriver().parse(motion)
        except MotionParamError as exc:
            issues.append({"message": f"motion: {exc}"})
            return None
        joints = document["assembly"].get("joints") or []
        driven = next((j for j in joints if j.get("id") == joint_id), None)
        if driven is None:
            issues.append({"message": f"motion driver references unknown joint {joint_id!r}"})
            return None
        between = driven.get("between") or []
        pivot_ref = between[0] if len(between) >= 1 else None
        moving_ref = between[1] if len(between) >= 2 else None
        pivot_frame = self._frame_for(pivot_ref, local_frames)
        if pivot_ref is None or moving_ref is None or pivot_frame is None:
            issues.append({"message": f"motion joint {joint_id!r} has unresolved connectors"})
            return None
        if driven.get("type") != "revolute":
            issues.append({"message": f"motion driver joint {joint_id!r} must be a revolute"})
            return None
        # World-rest connector frames (static placement applied) + the mechanism plane (normal = the
        # driven revolute axis, through its pivot). PlanarMotionSolver returns per-body in-plane
        # deltas; compose each onto the body's rest placement.
        world_frames = self._world_frames(local_frames, placements_mm)
        pivot_world = self._frame_for(pivot_ref, world_frames)
        if pivot_world is None:
            issues.append({"message": f"motion joint {joint_id!r} pivot has no world frame"})
            return None
        plane = MechanismPlane.from_axis_point(pivot_world.origin, pivot_world.z)
        planar_joints = _planar_joints(joints)
        motion_ground = self._motion_ground_ids(document, placements_mm)
        driver = {"joint": joint_id,
                  "pivot": {"instance": pivot_ref["instance"], "connector": pivot_ref["connector"]},
                  "moving": {"instance": moving_ref["instance"],
                             "connector": moving_ref["connector"]}}
        deltas = PlanarMotionSolver().solve(world_frames, planar_joints, motion_ground, plane,
                                            driver, values)
        span = values[-1] - values[0]
        frames = []
        for value, delta in zip(values, deltas):
            placements = {iid: _bake_matrix(_compose(placements_mm[iid], delta.get(iid)),
                                            to_metres)
                          for iid in placements_mm}
            frames.append({"t": 0.0 if span == 0 else (value - values[0]) / span,
                           "driver_value": value, "status": "solved", "placements": placements})
        path = os.path.join(out_dir, f"{name}.motion.json")
        with open(path, "w", encoding="utf-8") as handle:
            json.dump({"schema_version": 1, "name": name,
                       "driver": motion["driver"], "frames": frames}, handle)
        logger.info("assembly motion: joint=%s frames=%d out=%s", joint_id, len(frames), path)
        return path

    def _world_frames(self, local_frames: dict, placements_mm: dict) -> dict:
        """Each instance's connector frames transformed into world space by its static placement."""
        world: dict[str, dict] = {}
        for iid, conns in local_frames.items():
            matrix = placements_mm.get(iid)
            if matrix is None:
                continue
            world[iid] = {cid: _world_frame(frame, matrix) for cid, frame in conns.items()}
        return world

    def _motion_ground_ids(self, document: dict, placements_mm: dict) -> set:
        """Instances that stay fixed during motion: the first placed instance + any lock:true one.

        Unlike the static ground set (which also grounds lock MATES), motion grounding is by the
        instance's own placement: a body the mechanism pivots on is a lock:true / first instance.
        """
        ground: set = set()
        placed = [i for i in document["assembly"]["instances"] if i["id"] in placements_mm]
        if placed:
            ground.add(placed[0]["id"])
        for inst in placed:
            if inst.get("lock"):
                ground.add(inst["id"])
        return ground

    def _analyze(self, document: dict, asm_dir: str, instances: list, placements_mm: dict,
                 builders: dict, out_dir: str, name: str, issues: list) -> tuple[list, dict, dict]:
        """Interference + BOM + roll-up mass + structured STEP over the solved assembly.

        Guarded: any failure is an id-attributed issue and the analysis blocks come back empty so
        the sidecar still writes (partial-result discipline). Reuses the per-file DocumentBuilder
        for each part's shape + a MaterialResolver (mass + STEP color), world-places each shape by
        its solved mm placement, and dedups the per-part build across instances.
        """
        try:
            return self._run_analysis(document, asm_dir, instances, placements_mm, builders,
                                      out_dir, name)
        except Exception as exc:  # noqa: BLE001 - analysis failure must not abort the assemble
            logger.warning("assembly analysis failed for %s: %s", name, exc)
            issues.append({"message": f"assembly analysis failed: {exc}"})
            return [], {"items": []}, {"total_mass": 0.0, "cog": [0.0, 0.0, 0.0]}

    def _run_analysis(self, document: dict, asm_dir: str, instances: list, placements_mm: dict,
                      builders: dict, out_dir: str, name: str) -> tuple[list, dict, dict]:
        # Per-file part builds (shape + resolver), cached across instances of the same file.
        file_builds: dict[str, dict] = {}
        placed: list[dict] = []          # {id, shape} world-placed, for interference
        components: list[dict] = []      # {shape, name, color, material, placement} for STEP
        part_mass: dict[tuple, dict] = {}  # (file, part) -> {mass, material, cog}
        inst_meta: list[dict] = []       # {id, file, part} for the BOM
        by_id = {i["id"]: i for i in instances}  # to stamp per-instance material onto the sidecar
        for inst in document["assembly"]["instances"]:
            iid = inst["id"]
            if iid not in placements_mm:
                continue  # a bad instance skipped upstream; not placed
            file_key = os.path.abspath(os.path.join(asm_dir, inst["file"]))
            builds = file_builds.get(file_key)
            if builds is None:
                builder = builders.setdefault(file_key, DocumentBuilder(self._kernel))
                builds = builder.resolve_part_builds(os.path.join(asm_dir, inst["file"]))
                file_builds[file_key] = builds
            shape, resolver = builds.get(inst["part"], (None, None))
            if shape is None:
                continue
            inst_meta.append({"id": iid, "file": inst["file"], "part": inst["part"]})
            world = self._kernel.place(shape, placements_mm[iid])
            placed.append({"id": iid, "shape": world})
            part_key = (inst["file"], inst["part"])
            if part_key not in part_mass:
                part_mass[part_key] = self._part_mass(shape, resolver)
            # Stamp the instance's material + appearance color onto the sidecar record so the viewer
            # can color assemblies by material (per instance) without a per-part element map.
            sidecar_inst = by_id.get(iid)
            if sidecar_inst is not None:
                sidecar_inst["material"] = part_mass[part_key].get("material")
                sidecar_inst["appearance_color"] = part_mass[part_key].get("color")
            components.append({
                "shape": world, "name": iid,
                "color": part_mass[part_key].get("color"),
                "material": part_mass[part_key].get("material"),
                "placement": placements_mm[iid]})
        interference = self._interference.check(placed)
        bom_out = self._bom.compute(inst_meta, part_mass, placements_mm)
        self._kernel.export_assembly(components, os.path.join(out_dir, f"{name}.step"))
        return interference, {"items": bom_out["items"]}, bom_out["mass"]

    def _part_mass(self, shape: Any, resolver: Any) -> dict:
        """A part's total mass + local COG + material + color; mass is None when no density."""
        material = None
        color = None
        try:
            props = self._mass.mass_properties(shape, resolver)
            total = props["total"]
            body = props["bodies"][0] if props["bodies"] else {}
            material = body.get("material")
            color = _appearance_color(resolver, shape, self._kernel)
            return {"mass": total["mass"], "material": material, "cog": tuple(total["cog"]),
                    "color": color}
        except MaterialError:
            # No density (or no material): counted in BOM quantity, omitted from the mass roll-up.
            return {"mass": None, "material": material, "cog": (0.0, 0.0, 0.0), "color": color}

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
        """Resolve a mate's refs + lower to primitives with a_ref/b_ref attached; None on error.

        A mate references up to THREE connectors (between[0..2]); symmetric/width use the third as
        the 'about' / second bounding plane. Each primitive's a/b role tag (``A.*``/``B.*``/
        ``C.*``) selects which between-entry the solver resolves, so a primitive can target any of
        the three connectors.
        """
        between = mate.get("between") or []
        a_ref = between[0] if len(between) >= 1 else None
        b_ref = between[1] if len(between) >= 2 else None
        c_ref = between[2] if len(between) >= 3 else None
        frame_a = self._frame_for(a_ref, local_frames)
        frame_b = self._frame_for(b_ref, local_frames) if b_ref else None
        frame_c = self._frame_for(c_ref, local_frames) if c_ref else None
        if frame_a is None or (b_ref is not None and frame_b is None):
            issues.append({"constraint_id": mate.get("id"),
                           "message": f"mate {mate.get('id')!r} references an unknown connector"})
            return None
        lowering_mate = dict(mate)
        if frame_c is not None:
            lowering_mate["_frame_c"] = frame_c
        try:
            prims = self._lowering.lower(lowering_mate, frame_a, frame_b)
        except MateError as exc:
            issues.append({"constraint_id": mate.get("id"), "message": str(exc)})
            return None
        by_role: dict[str, dict | None] = {"A": a_ref, "B": b_ref, "C": c_ref}
        for prim in prims:
            prim["id"] = mate["id"]
            prim["a_ref"] = by_role.get(_role(prim.get("a")) or "A", a_ref)
            prim["b_ref"] = by_role.get(_role(prim.get("b")) or "B", b_ref)
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
                            resolved_files: dict, issues: list) -> dict[str, ConnectorFrame]:
        """Resolve a part's declared connectors to local-space frames (empty on any failure)."""
        part_file = os.path.join(asm_dir, instance["file"])
        key = os.path.abspath(part_file)
        # resolve_part_elements returns EVERY part in the file, so resolve each file once and cache;
        # subsequent instances of any part in that file reuse it (no redundant load + build).
        parts = resolved_files.get(key)
        if parts is None:
            builder = builders.setdefault(key, DocumentBuilder(self._kernel))
            try:
                parts = builder.resolve_part_elements(part_file)
            except Exception as exc:  # noqa: BLE001 - a bad part becomes an id-attributed issue
                issues.append({"instance_id": instance["id"],
                               "message": f"connector resolution failed: {exc}"})
                return {}
            resolved_files[key] = parts
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


def _planar_joints(joints: list[dict]) -> list[dict]:
    """The joints in PlanarMotionSolver form ({id, type, a/b {instance, connector}}), skipping any
    that lack two between-refs (a planar joint always couples two connectors)."""
    out: list[dict] = []
    for joint in joints:
        between = joint.get("between") or []
        if len(between) < 2:
            continue
        out.append({"id": joint.get("id"), "type": joint.get("type"),
                    "a": {"instance": between[0]["instance"],
                          "connector": between[0]["connector"]},
                    "b": {"instance": between[1]["instance"],
                          "connector": between[1]["connector"]}})
    return out


def _compose(rest: list[list[float]],
             delta: list[list[float]] | None) -> list[list[float]]:
    """Row-major compose rest THEN world delta: final = rest . delta (None delta -> rest)."""
    if delta is None:
        return [row[:] for row in rest]
    return [[sum(rest[i][k] * delta[k][j] for k in range(4)) for j in range(4)] for i in range(4)]


def _role(tag: str | None) -> str | None:
    """The connector role letter (A/B/C) from a primitive role tag like 'A.origin' or 'C.plane'."""
    if not tag:
        return None
    return tag.split(".", 1)[0]


def _appearance_color(resolver: Any, shape: Any, kernel: Any) -> tuple | None:
    """The first body's material appearance color (mat_data.appearance.color) as (r,g,b), or None.

    Best-effort for the STEP part color; never raises (display-only, like the viewer material path).
    """
    try:
        bodies = kernel.bodies(shape)
        if not bodies:
            return None
        mat = resolver.for_body(bodies[0])
        color = (mat or {}).get("appearance", {}).get("color")
        return tuple(color) if color is not None else None
    except Exception:  # noqa: BLE001 - color is optional; a failure just means no STEP color
        return None


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
