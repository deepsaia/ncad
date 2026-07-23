"""Write the viewer sidecars for an exported robot: the tree (.robot.json) + per-joint sweeps.

The Physics view mode needs two things the URDF/MJCF files do not serve conveniently: a compact
tree to inspect (links with computed inertia, joints with limits) and a precomputed articulation
per actuated joint so a slider can scrub it. This builds both beside the robot artifact:

- ``<name>.robot.json``: base link + links (mesh + mass/COM/inertia) + joints (type/parent/child/
  origin/axis/limits/actuated). The inspector reads this.
- ``<name>.robot_sweeps.json``: per ACTUATED revolute/slider joint, a list of frames (per-body
  placements) produced by driving that joint across its range with the OndselSolver motion path
  (so closed-loop mechanisms move correctly). A slider scrubs its joint's frames.

The sweep range is the authored ``[lower, upper]``; a continuous (unlimited) revolute sweeps one
full turn; an unlimited prismatic sweeps an auto travel from the model size. Missing pyondsel is
handled honestly: the tree still writes, sweeps are skipped with a note. One class.
"""

import json
import logging
import math
import tempfile
from pathlib import Path
from typing import Any

from ncad.assembly.assembly_builder import AssemblyBuilder
from ncad.robotics.physics_spec import PhysicsSpec
from ncad.robotics.robot_model import RobotModel
from ncad.robotics.robot_model_builder import RobotModelBuilder
from ncad.spec.spec_loader import SpecLoader
from ncad.spec.spec_reference import SpecReference

logger = logging.getLogger(__name__)

_ROBOT_SUFFIX = ".robot.json"
_SWEEPS_SUFFIX = ".robot_sweeps.json"
_SWEEP_STEPS = 24                    # frames per joint sweep (matches a smooth slider)
_FULL_TURN = 2.0 * math.pi           # default range for an unlimited revolute (radians)
_AUTO_TRAVEL_FRACTION = 0.5          # unlimited prismatic travels this fraction of the model size
# Only these joint types can be driven by the motion solver (its prescribed-motion kinds).
_SWEEPABLE = frozenset({"revolute", "continuous", "prismatic"})


class RobotSidecarBuilder:
    """Writes the .robot.json tree + per-actuated-joint sweep sidecars for the Physics viewer."""

    def __init__(self, kernel: Any) -> None:
        self._kernel = kernel
        self._model_builder = RobotModelBuilder(kernel)
        self._assembler = AssemblyBuilder(kernel)

    def build(self, physics_path: str, out_dir: str, with_sweeps: bool = True) -> dict:
        """Build the model then write the sidecars; return ``{robot, sweeps, warnings}`` paths.

        ``with_sweeps`` defaults to True here (the standalone builder's job is the full sidecar
        set); the CLI passes its own flag. Set False for just the cheap ``.robot.json`` tree.
        """
        model, warnings = self._model_builder.build(physics_path, out_dir)
        result = self.write(model, physics_path, out_dir, with_sweeps=with_sweeps)
        result["warnings"] = warnings + result["warnings"]
        return result

    def write(self, model: RobotModel, physics_path: str, out_dir: str,
              with_sweeps: bool = False) -> dict:
        """Write the tree sidecar for an ALREADY-BUILT ``model`` (so a caller does not rebuild it).

        Always writes ``.robot.json`` (cheap: no solve). The per-joint ``.robot_sweeps.json`` is
        written ONLY when ``with_sweeps`` is set, because each sweep is a motion solve per actuated
        joint (expensive) and is only needed for slider articulation. Returns
        ``{robot, sweeps, warnings}``; ``sweeps`` is None when not generated.
        """
        spec = PhysicsSpec(SpecLoader().load(physics_path))
        out = Path(out_dir)
        actuated = self._actuated_names(spec, model)

        robot_path = out / f"{model.name}{_ROBOT_SUFFIX}"
        # Record the .physics.hocon source so the viewer can re-export the robot after a reload
        # (mirrors the .assembly.json / .motion.json source field).
        tree = {**self._tree(model, actuated), "source": str(Path(physics_path).resolve())}
        robot_path.write_text(json.dumps(tree, indent=2), encoding="utf-8")
        if not with_sweeps:
            return {"robot": str(robot_path), "sweeps": None, "warnings": []}

        sweeps, sweep_warnings = self._sweeps(physics_path, model, actuated, out_dir)
        sweeps_path = out / f"{model.name}{_SWEEPS_SUFFIX}"
        sweeps_path.write_text(json.dumps(sweeps), encoding="utf-8")
        return {"robot": str(robot_path), "sweeps": str(sweeps_path), "warnings": sweep_warnings}

    def _actuated_names(self, spec: PhysicsSpec, model: RobotModel) -> set[str]:
        """The joint names the overlay marks ``actuated``."""
        return {j.name for j in model.joints if spec.joint_overlay(j.name).get("actuated")}

    def _tree(self, model: RobotModel, actuated: set[str]) -> dict:
        """The .robot.json tree: base + links (inertia) + joints (limits + actuated flag)."""
        return {
            "schema_version": 1,
            "name": model.name,
            "base_link": model.base_link,
            "links": [{"name": link.name, "mesh": link.mesh, "mass": link.mass,
                       "center_of_mass": list(link.center_of_mass), "inertia": link.inertia}
                      for link in model.links],
            "joints": [{"name": j.name, "type": j.joint_type, "parent": j.parent, "child": j.child,
                        "axis": list(j.axis), "origin": list(j.origin_xyz),
                        "limit": [j.limit_lower, j.limit_upper],
                        "actuated": j.name in actuated,
                        "loop_closure": j.is_loop_closure}
                       for j in model.joints],
        }

    def _sweeps(self, physics_path: str, model: RobotModel, actuated: set[str],
                out_dir: str) -> tuple[dict, list[str]]:
        """Per actuated sweepable joint, the frames from driving it across its range.

        Each sweep is solved in a THROWAWAY temp dir, not ``out_dir``: the motion solve rewrites the
        assembly + motion sidecars, so isolating it keeps ``out_dir`` to only the two robot sidecars
        (no per-joint sidecar churn, no stray last-joint .motion.json).
        """
        spec = PhysicsSpec(SpecLoader().load(physics_path))
        assembly_path = SpecReference().for_doc(spec.assembly, physics_path)
        model_size = self._model_size(model)
        sweeps: dict[str, dict] = {}
        warnings: list[str] = []
        with tempfile.TemporaryDirectory(prefix="ncad-robot-sweep-") as scratch:
            for joint in model.joints:
                if joint.name not in actuated:
                    continue
                if joint.joint_type not in _SWEEPABLE:
                    warnings.append(
                        f"joint {joint.name!r} is actuated but type {joint.joint_type!r} is not "
                        "sweepable (only revolute/prismatic); no slider")
                    continue
                low, high = self._range(joint, model_size)
                frames, note = self._sweep_joint(
                    assembly_path, joint.name, joint.joint_type, low, high, scratch)
                if note:
                    warnings.append(note)
                if frames is not None:
                    sweeps[joint.name] = {"from": low, "to": high, "frames": frames}
        return sweeps, warnings

    def _sweep_joint(self, assembly_path: str, joint_name: str, joint_type: str,
                     low: float, high: float, scratch: str) -> tuple[list | None, str | None]:
        """Drive one joint across [low, high] via the motion path (in ``scratch``).

        ``low``/``high`` are the joint's URDF-native units (radians for a revolute, metres for a
        prismatic), but the motion driver takes a revolute angle in DEGREES and a slider travel in
        MILLIMETRES (see AsmtExporter). Convert here so a full-turn limit actually sweeps a full
        turn (a radian range fed as degrees would rotate the mechanism by only a few degrees).
        """
        if joint_type == "prismatic":
            drive_from, drive_to = low * 1000.0, high * 1000.0    # metres -> mm
        else:
            drive_from, drive_to = math.degrees(low), math.degrees(high)   # radians -> degrees
        motion_spec = {"driver": {"joint": joint_name, "from": drive_from, "to": drive_to,
                                  "steps": _SWEEP_STEPS}}
        try:
            result = self._assembler.assemble(assembly_path, scratch, motion_spec=motion_spec)
        except Exception as exc:  # noqa: BLE001 - a solve failure is a skipped sweep, not a crash
            return None, f"joint {joint_name!r} sweep failed: {exc}"
        trajectory = result.get("motion")
        if not trajectory or not Path(trajectory).is_file():
            return None, (f"joint {joint_name!r} sweep produced no trajectory "
                          "(pyondsel missing or the solve did not converge); no slider")
        data = json.loads(Path(trajectory).read_text(encoding="utf-8"))
        return data.get("frames", []), None

    def _range(self, joint: Any, model_size: float) -> tuple[float, float]:
        """The sweep range: authored limits, else full turn (revolute) / auto travel (prismatic)."""
        if joint.limit_lower is not None and joint.limit_upper is not None:
            return joint.limit_lower, joint.limit_upper
        if joint.joint_type == "prismatic":
            return 0.0, _AUTO_TRAVEL_FRACTION * model_size
        return 0.0, _FULL_TURN

    def _model_size(self, model: RobotModel) -> float:
        """A rough model size (m) for the auto prismatic travel: max |COM| span, min 0.1."""
        extents = [abs(c) for link in model.links for c in link.center_of_mass]
        return max(2.0 * max(extents, default=0.0), 0.1)


def robot_sidecar_suffixes() -> tuple[str, str]:
    """The (.robot.json, .robot_sweeps.json) suffixes (for the catalog + delete cleanup)."""
    return _ROBOT_SUFFIX, _SWEEPS_SUFFIX
