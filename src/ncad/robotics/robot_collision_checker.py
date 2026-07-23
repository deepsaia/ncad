"""Self-collision check for a posed robot: which NON-ADJACENT links interpenetrate at a given pose.

The live pose panel lets a robot fold into itself at some joint COMBINATIONS (real arms do too);
per-joint limits cannot prevent every combination without crippling the workspace, so instead the
viewer flags self-collision as it happens. This runs the assembly InterferenceChecker over the
FK-posed link shapes and returns the interfering pairs.

ADJACENT links (parent-child across a joint) touch BY DESIGN at the pin/eye, so they are excluded;
only non-adjacent overlaps are real self-collisions. Link shapes are built once and CACHED per
physics document (the geometry does not change with the pose - only the placement does), so a
repeated pose check is just place + pairwise distance/common-volume, no rebuild. One class.
"""

from pathlib import Path
from typing import Any

from ncad.assembly.interference_checker import InterferenceChecker
from ncad.build.document_builder import DocumentBuilder
from ncad.robotics.physics_spec import PhysicsSpec
from ncad.robotics.robot_forward_kinematics import RobotForwardKinematics
from ncad.spec.spec_loader import SpecLoader
from ncad.spec.spec_reference import SpecReference

# Metres -> millimetres: the robot tree (origins) + poses are metres; the base link shapes + the
# kernel placement/distance work in millimetres, so FK node matrices' translation is scaled up.
_M_TO_MM = 1000.0
# Overlap (mm^3) below this is the designed pin/eye fit or numerical noise, not a real collision.
_MIN_OVERLAP_MM3 = 100.0


class RobotCollisionChecker:
    """Checks a posed robot for non-adjacent self-collision, caching the per-link shapes."""

    def __init__(self, kernel: Any) -> None:
        self._kernel = kernel
        self._checker = InterferenceChecker(kernel)
        self._fk = RobotForwardKinematics()
        # Cache keyed by the physics doc's absolute path: {shapes, tree, adjacent}.
        self._cache: dict[str, dict] = {}

    def check(self, physics_path: str, tree: dict, pose: dict[str, float]) -> list[dict]:
        """Return interfering non-adjacent link pairs at ``pose`` as ``[{a, b, volume}]``.

        ``tree`` is the robot.json dict (base + joints); ``pose`` maps joint -> value (radians for
        revolute, metres for prismatic). Empty list means the pose is collision-free.
        """
        cached = self._cached(physics_path, tree)
        node_matrices = self._fk.solve(tree, pose)   # link -> row-major 4x4 (metres)
        placed = []
        for link, shape in cached["shapes"].items():
            matrix = node_matrices.get(link)
            if matrix is None:
                continue
            placed.append({"id": link, "shape": self._kernel.place(shape, _to_mm(matrix))})
        findings = []
        for finding in self._checker.check(placed):
            if finding.get("status") != "interfering":
                continue
            pair = frozenset({finding["a"], finding["b"]})
            if pair in cached["adjacent"]:
                continue   # parent-child links touch at the joint by design
            if finding.get("volume", 0.0) < _MIN_OVERLAP_MM3:
                continue
            findings.append({"a": finding["a"], "b": finding["b"],
                             "volume": round(finding["volume"], 1)})
        return findings

    def _cached(self, physics_path: str, tree: dict) -> dict:
        """The per-document cache entry (link shapes + adjacent-pair set), built once."""
        key = str(Path(physics_path).resolve())
        if key not in self._cache:
            self._cache[key] = self._build(physics_path, tree)
        return self._cache[key]

    def _build(self, physics_path: str, tree: dict) -> dict:
        """Build the per-link shapes (by instance id) + the adjacent-pair set from the tree."""
        spec = PhysicsSpec(SpecLoader().load(physics_path))
        asm_path = Path(SpecReference().for_doc(spec.assembly, physics_path))
        source = SpecLoader().load(str(asm_path))["assembly"]["instances"]
        file_by_id = {inst["id"]: inst for inst in source if "file" in inst}
        shapes: dict[str, Any] = {}
        for iid, inst in file_by_id.items():
            part_file = SpecReference().resolve(inst["file"], str(asm_path.parent))
            builds = DocumentBuilder(self._kernel).resolve_part_builds(part_file)
            if inst["part"] in builds:
                shapes[iid] = builds[inst["part"]][0]
        adjacent = {frozenset({j["parent"], j["child"]}) for j in tree.get("joints", [])}
        return {"shapes": shapes, "adjacent": adjacent}


def _to_mm(matrix: list[list[float]]) -> list[list[float]]:
    """Copy a row-major placement (metres) with its translation row scaled to millimetres."""
    out = [row[:] for row in matrix]
    out[3][0] *= _M_TO_MM
    out[3][1] *= _M_TO_MM
    out[3][2] *= _M_TO_MM
    return out
