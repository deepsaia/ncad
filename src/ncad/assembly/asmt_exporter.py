"""Export an ncad assembly + motion driver to a pyondsel ASMT model for the multibody solver.

Bridges ncad's assembly vocabulary (instances, connector frames, joints, a motion driver) to
OndselSolver's ASMT model (parts with mass/inertia, markers, joints, a time motion) via pyondsel
(the motion-export boundary). Each instance becomes a Part at its rest placement carrying REAL
mass + principal inertia from MassCalculator (the solver needs physically consistent mass
properties, which is what makes a mechanism solve rather than crash); each connector becomes a
Marker in the part's
local frame; each joint maps to the matching ASMT joint; a grounded instance is fixed in place; the
driver becomes a rotational/translational Motion whose angle/distance ramps linearly over the sweep.
Pure translation to a pyondsel model; solving + reading back is the caller's job. One class.
"""

import logging
import math
from typing import Any

from ncad.assembly.connector_frame import ConnectorFrame

logger = logging.getLogger(__name__)

# ncad joint type -> pyondsel joint kind (which maps to an OndselSolver ASMT joint block). Every
# lower AND higher pair OndselSolver models is wired here, so a mechanism is driven by the real
# constraint, never a faked coupling law. ncad names on the left, pyondsel kinds on the right (some
# differ: ncad 'slider'/'ball'/'slot' -> pyondsel 'translational'/'spherical'/'point_in_line').
_JOINT_KIND = {
    # lower pairs
    "fixed": "fixed",
    "revolute": "revolute",
    "slider": "translational",
    "cylindrical": "cylindrical",
    "ball": "spherical",
    "universal": "universal",
    "screw": "screw",
    "planar": "planar",
    # compound lower pairs
    "cylspherical": "cylspherical",
    "revcylindrical": "revcylindrical",
    "sphspherical": "sphspherical",
    "revrevolute": "revrevolute",
    # higher pairs (point/line/plane incidence). 'slot'/'point_on_line' are ncad aliases for the
    # point-on-line (pin-in-slot) higher pair OndselSolver calls PointInLineJoint.
    "point_on_line": "point_in_line",
    "slot": "point_in_line",
    "point_in_line": "point_in_line",
    "point_in_plane": "point_in_plane",
    "in_line": "in_line",
    "line_in_plane": "line_in_plane",
    "in_plane": "in_plane",
    # relational joints
    "no_rotation": "no_rotation",
    "parallel_axes": "parallel_axes",
    "perpendicular": "perpendicular",
    "constant_velocity": "constant_velocity",
    "at_point": "at_point",
}
# Which joints a driver can prescribe, and the pyondsel motion kind for each.
_MOTION_KIND = {"revolute": "rotational", "slider": "translational"}
# The local-origin marker every part carries so a FixedJoint can ground it in place.
_ANCHOR = "_anchor"


class AsmtExporter:
    """Builds a pyondsel AsmtModel from an ncad assembly + motion driver."""

    def build_model(self, name: str, instances: list[dict], local_frames: dict,
                    placements_mm: dict, mass_props: dict, joints: list[dict],
                    ground_ids: set, driver: dict, to_metres: float,
                    secondaries: list[dict] | None = None) -> Any:
        """Return a pyondsel.AsmtModel for the assembly (metres); raise if pyondsel is unavailable.

        ``mass_props`` maps instance id -> mass/cog(mm)/inertia; ``driver`` is
        {"joint_id", "joint_type", "pivot", "moving", "values"}. ``secondaries`` (bucket 6.2) are
        extra prescribed motions {joint_id, joint_type, expression} from enforced couplings / cam
        laws, driven ALONGSIDE the primary (the solver co-solves multiple prescribed motions).
        Lengths convert to metres via ``to_metres``.
        """
        # pyondsel's top-level package is intentionally empty (no re-exports), so import the leaf
        # symbols and bundle them into a namespace the helpers below use as ``po.AsmtModel`` etc.
        # Kept as a lazy in-method import: pyondsel is an optional dependency (motion only), so ncad
        # imports fine without it and only a motion build touches it.
        from types import SimpleNamespace

        from pyondsel.model.asmt_model import AsmtModel
        from pyondsel.model.joint import Joint
        from pyondsel.model.marker import Marker
        from pyondsel.model.motion import Motion
        from pyondsel.model.part import Part
        from pyondsel.model.simulation import Simulation

        po = SimpleNamespace(AsmtModel=AsmtModel, Joint=Joint, Marker=Marker,
                             Motion=Motion, Part=Part, Simulation=Simulation)

        model = po.AsmtModel(name=name)
        for inst in instances:
            iid = inst["id"]
            if iid not in placements_mm:
                continue
            model.add_part(self._part(po, iid, placements_mm[iid], mass_props.get(iid),
                                      local_frames.get(iid, {}), to_metres))
        self._add_grounds(po, model, ground_ids, instances, placements_mm, to_metres)
        self._add_joints(po, model, joints)
        self._add_driver(po, model, driver)
        self._add_secondaries(po, model, secondaries or [])
        model.simulation = po.Simulation(t_start=0.0, t_end=1.0,
                                         frames=max(len(driver["values"]) - 1, 1))
        return model

    def _part(self, po: Any, iid: str, placement_mm: list, mass: dict | None,
              frames: dict, to_metres: float) -> Any:
        """One Part: rest pose (metres) + real mass/inertia + a marker per connector + an anchor.

        A dedicated ``_anchor`` marker at the part's local origin lets a FixedJoint ground the part
        in place without reusing (and thus over-pinning) one of its joint connectors.
        """
        pos, rot = _pose_to_metres(placement_mm, to_metres)
        mass_kg, inertia, cog = _mass_terms(mass, to_metres)
        part = po.Part(name=iid, position=pos, rotation=rot, mass=mass_kg,
                       moments_of_inertia=inertia, mass_center=cog, density=1.0)
        part.add_marker(po.Marker(_ANCHOR))
        for cid, frame in frames.items():
            part.add_marker(self._marker(po, cid, frame, to_metres))
        return part

    def _marker(self, po: Any, cid: str, frame: ConnectorFrame, to_metres: float) -> Any:
        """A Marker at the connector origin (metres) oriented by the connector triad."""
        origin = tuple(c * to_metres for c in frame.origin)
        rotation = _triad_matrix(frame.x, frame.y, frame.z)
        return po.Marker(name=cid, position=origin, rotation=rotation)

    def _add_grounds(self, po: Any, model: Any, ground_ids: set, instances: list[dict],
                     placements_mm: dict, to_metres: float) -> None:
        """Fix each grounded instance IN PLACE: a world marker at its rest pose + a FixedJoint.

        The world (assembly) marker is placed at the part's rest position/orientation and pinned to
        the part's local ``_anchor`` (0,0,0), so the FixedJoint holds the body exactly where it was
        assembled without dragging it to the origin (the earlier bug) or reusing a joint connector.
        """
        for inst in instances:
            iid = inst["id"]
            if iid not in ground_ids or iid not in placements_mm:
                continue
            pos, rot = _pose_to_metres(placements_mm[iid], to_metres)
            ground_name = f"world_{iid}"
            model.add_ground_marker(po.Marker(ground_name, position=pos, rotation=rot))
            model.add_joint(po.Joint(f"ground_{iid}", "fixed",
                                     model.ground_path(ground_name),
                                     model.part_path(iid, _ANCHOR)))

    def _add_joints(self, po: Any, model: Any, joints: list[dict]) -> None:
        """Add every declared joint (revolute/slider/etc.) between its two connector markers."""
        for joint in joints:
            kind = _JOINT_KIND.get(joint.get("type") or "")
            between = joint.get("between") or []
            if kind is None or len(between) < 2:
                logger.debug("asmt export: skipping joint %r (type %r)", joint.get("id"),
                             joint.get("type"))
                continue
            a, b = between[0], between[1]
            # Extra scalars for the joints that carry them (screw pitch, in_plane offset); pyondsel
            # writes them after the markers. Absent keys stay None and are simply not emitted.
            extra = {}
            if joint.get("pitch") is not None:
                extra["pitch"] = float(joint["pitch"])
            if joint.get("offset") is not None:
                extra["offset"] = float(joint["offset"])
            model.add_joint(po.Joint(
                joint["id"], kind,
                model.part_path(a["instance"], a["connector"]),
                model.part_path(b["instance"], b["connector"]), **extra))

    def _add_driver(self, po: Any, model: Any, driver: dict) -> None:
        """Add the driver's time motion: angle (rad) or distance (m) ramped linearly over t 0..1."""
        motion_kind = _MOTION_KIND.get(driver["joint_type"])
        if motion_kind is None:
            raise ValueError(f"joint type {driver['joint_type']!r} is not drivable")
        values = driver["values"]
        start, end = values[0], values[-1]
        if motion_kind == "rotational":
            # ncad driver values are degrees; ASMT rotation is radians. Ramp: start + span*t.
            span = math.radians(end - start)
            expr = f"{math.radians(start)} + {span}*time"
        else:
            # slider values are mm displacement; scale to the model's metre space (*0.001).
            span = (end - start) * 0.001
            expr = f"{start * 0.001} + {span}*time"
        model.add_motion(po.Motion(name=f"drive_{driver['joint_id']}", joint=driver["joint_id"],
                                   expression=expr, kind=motion_kind))

    def _add_secondaries(self, po: Any, model: Any, secondaries: list[dict]) -> None:
        """Add a prescribed motion per secondary (coupled / cam) joint (bucket 6.2).

        Each secondary is {joint_id, joint_type, expression}; the expression is already in the ASMT
        motion's units (radians for a revolute rotation, metres for a slider translation) as a
        function of ``time``, so this is a thin emitter (CouplingDriver / CamProfile own the math).
        """
        for sec in secondaries:
            motion_kind = _MOTION_KIND.get(sec["joint_type"])
            if motion_kind is None:
                logger.debug("asmt export: skipping secondary on non-drivable joint %r (type %r)",
                             sec.get("joint_id"), sec.get("joint_type"))
                continue
            model.add_motion(po.Motion(name=f"couple_{sec['joint_id']}", joint=sec["joint_id"],
                                       expression=sec["expression"], kind=motion_kind))


def _mass_terms(mass: dict | None, to_metres: float) -> tuple:
    """(mass_kg, principal_inertia, cog_metres) from a mass-props record, with safe fallbacks.

    A part with no material density has no mass; give it a small unit mass + inertia so the solver
    stays well-posed (kinematic motion is geometry-driven, so the exact value does not change the
    trajectory, but zero mass/inertia makes the solver singular).
    """
    if not mass or mass.get("mass") in (None, 0):
        return 1.0, (1.0, 1.0, 1.0), (0.0, 0.0, 0.0)
    mass_kg = float(mass["mass"])
    principal = mass.get("inertia", {}).get("principal") or [1.0, 1.0, 1.0]
    inertia = tuple(float(p) for p in principal[:3])
    cog = tuple(c * to_metres for c in mass.get("cog", (0.0, 0.0, 0.0)))
    return mass_kg, inertia, cog


def _pose_to_metres(placement_mm: list, to_metres: float) -> tuple:
    """Split a row-major 4x4 (mm) into (position metres, 3x3 rotation) for an ASMT part.

    ncad placements are row-major with the rotation in rows 0..2 (row i = image of basis e_i, the
    BodyPose convention) + the translation in row 3. ASMT's RotationMatrix is the body orientation;
    we pass the rotation columns (the basis images as columns) so the marker/part axes align.
    """
    r = placement_mm
    position = (r[3][0] * to_metres, r[3][1] * to_metres, r[3][2] * to_metres)
    # Transpose rows->columns: ncad row i is the image of e_i; ASMT wants columns = basis images.
    rotation = ((r[0][0], r[1][0], r[2][0]),
                (r[0][1], r[1][1], r[2][1]),
                (r[0][2], r[1][2], r[2][2]))
    return position, rotation


def _triad_matrix(x: tuple, y: tuple, z: tuple) -> tuple:
    """A 3x3 rotation with columns x, y, z (the connector axes) for a marker's orientation."""
    return ((x[0], y[0], z[0]),
            (x[1], y[1], z[1]),
            (x[2], y[2], z[2]))
