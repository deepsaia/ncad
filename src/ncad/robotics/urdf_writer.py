"""Write a RobotModel to a URDF (Unified Robot Description Format) XML string.

URDF is the most widely consumed robot description (ROS, MoveIt, PyBullet, Isaac, Drake). It is a
KINEMATIC TREE: exactly one path from the base to each link, no closed loops. This writer emits one
``<link>`` per RobotLink (with the derived inertial + a mesh visual/collision) and one ``<joint>``
per spanning-tree RobotJoint; loop-closure joints cannot be expressed and are reported by the caller
(they are kept for the MJCF/SDF writers, which support equality constraints). Pure: same model ->
identical XML. One class; XML is built with xml.etree so the output is well-formed and escaped.
"""

# xml.etree is used for GENERATION only (build elements + tostring); this writer never parses
# untrusted XML, so the stdlib parser's XXE/entity-expansion risks do not apply here.
import xml.etree.ElementTree as ET
from typing import Any

from ncad.robotics.robot_joint import RobotJoint
from ncad.robotics.robot_link import RobotLink
from ncad.robotics.robot_model import RobotModel

# ncad neutral joint type -> URDF joint type. A revolute with no limits is a 'continuous' joint in
# URDF (unbounded rotation); a limited revolute stays 'revolute'. Ball/free have no direct URDF
# single-joint form, so they map to 'floating' (6-DOF), the closest URDF concept.
_URDF_TYPE = {
    "revolute": "revolute",
    "continuous": "continuous",
    "prismatic": "prismatic",
    "fixed": "fixed",
    "floating": "floating",
}


class UrdfWriter:
    """Serializes a RobotModel to a URDF XML string (spanning-tree joints only)."""

    def to_xml(self, model: RobotModel) -> str:
        """Return the URDF XML for ``model`` (its links + spanning-tree joints)."""
        robot = ET.Element("robot", {"name": model.name})
        for link in model.links:
            self._add_link(robot, link)
        for joint in model.tree_joints():
            self._add_joint(robot, joint)
        ET.indent(robot)
        return ET.tostring(robot, encoding="unicode", xml_declaration=True)

    def _add_link(self, robot: Any, link: RobotLink) -> None:
        """Append a ``<link>`` with the derived inertial and (if any) a mesh visual+collision."""
        element = ET.SubElement(robot, "link", {"name": link.name})
        inertial = ET.SubElement(element, "inertial")
        ET.SubElement(inertial, "origin", {"xyz": _triple(link.center_of_mass), "rpy": "0 0 0"})
        ET.SubElement(inertial, "mass", {"value": _num(link.mass)})
        i = link.inertia
        ET.SubElement(inertial, "inertia", {
            "ixx": _num(i.get("ixx", 0.0)), "iyy": _num(i.get("iyy", 0.0)),
            "izz": _num(i.get("izz", 0.0)), "ixy": _num(i.get("ixy", 0.0)),
            "ixz": _num(i.get("ixz", 0.0)), "iyz": _num(i.get("iyz", 0.0))})
        if link.mesh is not None:
            for tag in ("visual", "collision"):
                container = ET.SubElement(element, tag)
                geometry = ET.SubElement(container, "geometry")
                ET.SubElement(geometry, "mesh", {"filename": link.mesh})

    def _add_joint(self, robot: Any, joint: RobotJoint) -> None:
        """Append a ``<joint>`` (type-mapped) with its parent/child, origin, axis, and limits."""
        urdf_type = _URDF_TYPE.get(joint.joint_type, "fixed")
        element = ET.SubElement(robot, "joint", {"name": joint.name, "type": urdf_type})
        ET.SubElement(element, "parent", {"link": joint.parent})
        ET.SubElement(element, "child", {"link": joint.child})
        ET.SubElement(element, "origin",
                      {"xyz": _triple(joint.origin_xyz), "rpy": _triple(joint.origin_rpy)})
        if urdf_type in ("revolute", "continuous", "prismatic"):
            ET.SubElement(element, "axis", {"xyz": _triple(joint.axis)})
        self._add_limit(element, joint, urdf_type)
        self._add_dynamics(element, joint)

    def _add_limit(self, element: Any, joint: RobotJoint, urdf_type: str) -> None:
        """A ``<limit>``. URDF REQUIRES it on revolute/prismatic; continuous omits the bounds."""
        needs_limit = urdf_type in ("revolute", "prismatic")
        if not needs_limit and joint.effort is None and joint.velocity is None:
            return
        attrs: dict[str, str] = {}
        if joint.limit_lower is not None:
            attrs["lower"] = _num(joint.limit_lower)
        if joint.limit_upper is not None:
            attrs["upper"] = _num(joint.limit_upper)
        # effort + velocity are REQUIRED attributes of <limit>; default to 0 (unspecified) so the
        # URDF stays schema-valid when the physics overlay did not set them.
        attrs["effort"] = _num(joint.effort if joint.effort is not None else 0.0)
        attrs["velocity"] = _num(joint.velocity if joint.velocity is not None else 0.0)
        ET.SubElement(element, "limit", attrs)

    def _add_dynamics(self, element: Any, joint: RobotJoint) -> None:
        """A ``<dynamics>`` element when damping/friction were authored."""
        if joint.damping is None and joint.friction is None:
            return
        attrs: dict[str, str] = {}
        if joint.damping is not None:
            attrs["damping"] = _num(joint.damping)
        if joint.friction is not None:
            attrs["friction"] = _num(joint.friction)
        ET.SubElement(element, "dynamics", attrs)


def _num(value: float) -> str:
    """A compact, deterministic string for a float (trailing zeros trimmed)."""
    return f"{float(value):.9g}"


def _triple(vec: tuple[float, float, float]) -> str:
    """A space-separated 3-vector string (URDF xyz/rpy attribute value)."""
    return " ".join(_num(c) for c in vec)
