"""Derive the format-neutral RobotModel from a built assembly + a .physics overlay.

The integration heart of the robotics export: it turns ncad's assembly (instances, solved
placements, connector frames, joints) plus the physics overlay (base link, actuation, limits) into
the neutral RobotModel that any format writer consumes. Everything geometric is DERIVED:

- one link per instance, with the inertial from MassCalculator (mass kg, COM m, tensor kg*m^2) and a
  per-link mesh exported from the instance's shape (Stage-0 STL);
- one joint per assembly joint, oriented into a base-rooted spanning tree (JointTreeSpanner), with
  parent/child from the joint's two instances, origin from the child link's connector frame, axis
  from the joint's motion signature, and limits/dynamics from the physics overlay;
- loop-closure joints are kept but flagged (a tree-only writer reports them).

One class. It orchestrates existing units (AssemblyBuilder, MassCalculator, the kernel STL export)
rather than re-deriving geometry.
"""

import json
from pathlib import Path
from typing import Any

from ncad.assembly.assembly_builder import AssemblyBuilder
from ncad.build.document_builder import DocumentBuilder
from ncad.build.mass_calculator import MassCalculator
from ncad.build.material_error import MaterialError
from ncad.robotics.joint_tree_spanner import JointTreeSpanner
from ncad.robotics.physics_spec import PhysicsSpec
from ncad.robotics.robot_joint import RobotJoint
from ncad.robotics.robot_link import RobotLink
from ncad.robotics.robot_model import RobotModel

# mm^2 -> m^2 for the inertia tensor (MassCalculator reports kg*mm^2; URDF/SI want kg*m^2).
_MM2_TO_M2 = 1e-6
_MM_TO_M = 1e-3
# ncad joint type -> neutral robot joint type. A revolute becomes 'revolute' when the overlay gives
# limits, else 'continuous' (unbounded); a slider is prismatic; ball/free -> floating.
_NEUTRAL_TYPE = {
    "revolute": "revolute", "slider": "prismatic", "fixed": "fixed",
    "ball": "floating", "cylindrical": "floating", "planar": "floating",
    "universal": "floating", "screw": "revolute",
}
_AXIS_VECTORS = {"X": (1.0, 0.0, 0.0), "Y": (0.0, 1.0, 0.0), "Z": (0.0, 0.0, 1.0)}


class RobotModelBuilder:
    """Builds a RobotModel from a .physics document (an assembly + robot/sim overlay)."""

    def __init__(self, kernel: Any) -> None:
        self._kernel = kernel
        self._mass = MassCalculator(kernel)

    def build(self, physics_path: str, out_dir: str) -> tuple[RobotModel, list[str]]:
        """Build the RobotModel for the physics doc at ``physics_path``; write per-link meshes.

        Returns ``(model, warnings)``. Warnings collect non-fatal issues (a loop-closure joint a
        tree-only export drops, a link with no density). Per-link meshes are written into
        ``out_dir/meshes`` and referenced (relative) by each link.
        """
        from ncad.spec.spec_loader import SpecLoader

        document = SpecLoader().load(physics_path)
        spec = PhysicsSpec(document)
        asm_path = Path(physics_path).resolve().parent / spec.assembly
        out_path = Path(out_dir)

        out_path.mkdir(parents=True, exist_ok=True)
        result = AssemblyBuilder(self._kernel).assemble(str(asm_path), str(out_path))
        scene = json.loads(Path(result["sidecar"]).read_text(encoding="utf-8"))
        warnings = [i["message"] for i in result.get("issues", [])]

        # The scene sidecar bakes instances without their source `file`; the ORIGINAL assembly
        # document keeps `file` + `part`, needed to rebuild each part for mass + mesh. Map by id.
        source = SpecLoader().load(str(asm_path))["assembly"]["instances"]
        file_by_id = {inst["id"]: inst for inst in source if "file" in inst}
        mass_props = self._mass_props(asm_path, file_by_id)
        meshes = self._export_meshes(asm_path, file_by_id, out_path, spec.mesh_format)
        links = [self._link(inst, mass_props.get(inst["id"]), meshes.get(inst["id"]))
                 for inst in scene["instances"]]

        base = spec.base_link or self._default_base(scene, links)
        spanned = JointTreeSpanner().span(base, scene.get("joints") or [])
        joints = self._joints(scene.get("joints") or [], scene["instances"], spanned, spec)
        for closure in spanned["loop_closures"]:
            warnings.append(
                f"joint {closure!r} closes a kinematic loop; it is outside the base-rooted tree "
                "(a tree-only URDF drops it; MJCF keeps it as an equality, SDF as a joint)")
        return RobotModel(name=scene["name"], base_link=base, links=links, joints=joints), warnings

    def _mass_props(self, asm_path: Path, file_by_id: dict[str, dict]) -> dict[str, dict]:
        """Per-instance mass properties (mass/cog/inertia) via the per-file part build."""
        props: dict[str, dict] = {}
        for iid, shape_resolver in self._part_builds(asm_path, file_by_id).items():
            shape, resolver = shape_resolver
            try:
                mp = self._mass.mass_properties(shape, resolver)
                props[iid] = mp["bodies"][0] if mp.get("bodies") else {}
            except MaterialError:
                continue  # no density; the link falls back to a unit mass
        return props

    def _export_meshes(self, asm_path: Path, file_by_id: dict[str, dict], out_path: Path,
                       mesh_format: str) -> dict[str, str]:
        """Export each instance's shape to ``meshes/<id>.<fmt>``; return id -> relative path."""
        (out_path / "meshes").mkdir(parents=True, exist_ok=True)
        out: dict[str, str] = {}
        for iid, (shape, _) in self._part_builds(asm_path, file_by_id).items():
            rel = Path("meshes") / f"{iid}.{mesh_format}"
            self._kernel.export(shape, str(out_path / rel))
            out[iid] = str(rel)
        return out

    def _part_builds(self, asm_path: Path,
                     file_by_id: dict[str, dict]) -> dict[str, tuple]:
        """Map instance id -> (shape, resolver) by building each instance's referenced part file."""
        asm_dir = asm_path.parent
        builds_by_file: dict[str, dict] = {}
        out: dict[str, tuple] = {}
        for iid, inst in file_by_id.items():
            file_path = asm_dir / inst["file"]
            file_key = str(file_path.resolve())
            builds = builds_by_file.get(file_key)
            if builds is None:
                builds = DocumentBuilder(self._kernel).resolve_part_builds(str(file_path))
                builds_by_file[file_key] = builds
            shape, resolver = builds.get(inst["part"], (None, None))
            if shape is not None:
                out[iid] = (shape, resolver)
        return out

    def _link(self, instance: dict, mass: dict | None, mesh: str | None) -> RobotLink:
        """One RobotLink from an instance + its mass props (SI) + its mesh path."""
        if not mass or not mass.get("mass"):
            return RobotLink(name=instance["id"], mass=1.0,
                             inertia={"ixx": 1.0, "iyy": 1.0, "izz": 1.0}, mesh=mesh)
        matrix = mass.get("inertia", {}).get("matrix") or [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
        cog = mass.get("cog", (0.0, 0.0, 0.0))
        return RobotLink(
            name=instance["id"], mass=float(mass["mass"]),
            inertia={
                "ixx": matrix[0][0] * _MM2_TO_M2, "iyy": matrix[1][1] * _MM2_TO_M2,
                "izz": matrix[2][2] * _MM2_TO_M2, "ixy": matrix[0][1] * _MM2_TO_M2,
                "ixz": matrix[0][2] * _MM2_TO_M2, "iyz": matrix[1][2] * _MM2_TO_M2},
            center_of_mass=tuple(c * _MM_TO_M for c in cog), mesh=mesh)

    def _joints(self, joints: list[dict], instances: list[dict], spanned: dict,
                spec: PhysicsSpec) -> list[RobotJoint]:
        """One RobotJoint per assembly joint, oriented by the spanning tree + overlay semantics."""
        orient = {o["joint"]: o for o in spanned["oriented"]}
        loop = set(spanned["loop_closures"])
        connectors = self._connector_origins(instances)
        out: list[RobotJoint] = []
        for joint in joints:
            jid = joint.get("id")
            oriented = orient.get(jid)
            parent, child = self._parent_child(joint, oriented)
            out.append(self._joint(joint, parent, child, connectors, spec, jid in loop))
        return out

    def _joint(self, joint: dict, parent: str, child: str, connectors: dict,
               spec: PhysicsSpec, is_loop: bool) -> RobotJoint:
        """Assemble one RobotJoint: derived kinematics + overlay limits/dynamics."""
        overlay = spec.joint_overlay(joint.get("id", ""))
        limit = overlay.get("limit") or [None, None]
        ncad_type = joint.get("type", "fixed")
        neutral = _NEUTRAL_TYPE.get(ncad_type, "fixed")
        if neutral == "revolute" and limit[0] is None and limit[1] is None:
            neutral = "continuous"   # an unbounded revolute is a URDF continuous joint
        origin = connectors.get((child, self._child_connector(joint)), (0.0, 0.0, 0.0))
        return RobotJoint(
            name=joint.get("id", "joint"), joint_type=neutral, parent=parent, child=child,
            origin_xyz=tuple(o * _MM_TO_M for o in origin), axis=self._axis(joint),
            limit_lower=limit[0], limit_upper=limit[1],
            effort=overlay.get("effort"), velocity=overlay.get("velocity"),
            damping=overlay.get("damping"), friction=overlay.get("friction"),
            is_loop_closure=is_loop)

    def _parent_child(self, joint: dict, oriented: dict | None) -> tuple[str, str]:
        """Parent/child links: the tree orientation if present, else the joint's authored order."""
        if oriented is not None:
            return oriented["parent"], oriented["child"]
        between = joint.get("between") or [{}, {}]
        return between[0].get("instance", ""), between[1].get("instance", "")

    def _child_connector(self, joint: dict) -> str:
        """The connector id on the child side (second entry of ``between``)."""
        between = joint.get("between") or [{}, {}]
        return between[1].get("connector", "")

    def _axis(self, joint: dict) -> tuple[float, float, float]:
        """The joint axis from its motion signature (falls back to +Z)."""
        signature = joint.get("signature") or []
        if signature and signature[0].get("axis") in _AXIS_VECTORS:
            return _AXIS_VECTORS[signature[0]["axis"]]
        return (0.0, 0.0, 1.0)

    def _connector_origins(self, instances: list[dict]) -> dict[tuple[str, str], tuple]:
        """Map (instance id, connector id) -> the connector's local origin (mm)."""
        origins: dict[tuple[str, str], tuple] = {}
        for inst in instances:
            for connector in inst.get("connectors", []):
                origins[(inst["id"], connector["id"])] = tuple(connector.get("origin", (0, 0, 0)))
        return origins

    def _default_base(self, scene: dict, links: list[RobotLink]) -> str:
        """The base link: the first locked/grounded instance, else the first link."""
        for inst in scene["instances"]:
            if inst.get("lock"):
                return inst["id"]
        return links[0].name if links else scene["instances"][0]["id"]
