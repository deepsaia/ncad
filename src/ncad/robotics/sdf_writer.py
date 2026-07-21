"""Write a RobotModel to an SDF (Simulation Description Format, Gazebo) string.

SDF is the middle ground between URDF and MJCF: like URDF it is a FLAT list of links + joints (not
nested), but like MJCF a joint may connect any two links, so closed loops need no special handling
(every joint, including loop closures, is emitted normally). This writer emits one ``<link>`` per
RobotLink (inertial with the full tensor + a mesh visual/collision) and one ``<joint>`` per joint
(tree AND loop closures), using SDF's ``<pose>`` + ``<axis>`` vocabulary.

Pure: same model -> identical XML. Uses xml.etree for GENERATION only (never parses untrusted XML).
One class.
"""

import xml.etree.ElementTree as ET
from typing import Any

from ncad.robotics.robot_joint import RobotJoint
from ncad.robotics.robot_link import RobotLink
from ncad.robotics.robot_model import RobotModel

# neutral joint type -> SDF joint type. SDF 'revolute' takes limits; 'ball'/'fixed' are direct.
_SDF_TYPE = {
    "revolute": "revolute", "continuous": "revolute", "prismatic": "prismatic",
    "fixed": "fixed", "floating": "ball",
}


class SdfWriter:
    """Serializes a RobotModel to an SDF XML string (flat links + joints, loops kept)."""

    def to_xml(self, model: RobotModel) -> str:
        """Return the SDF XML for ``model`` (all links + all joints, including loop closures)."""
        sdf = ET.Element("sdf", {"version": "1.9"})
        model_el = ET.SubElement(sdf, "model", {"name": model.name})
        for link in model.links:
            self._add_link(model_el, link)
        for joint in model.joints:   # SDF is not tree-limited: emit every joint
            self._add_joint(model_el, joint)
        ET.indent(sdf)
        return ET.tostring(sdf, encoding="unicode", xml_declaration=True)

    def _add_link(self, model_el: Any, link: RobotLink) -> None:
        """A ``<link>`` with an inertial (mass + full tensor at the COM) and, if any, a mesh."""
        element = ET.SubElement(model_el, "link", {"name": link.name})
        inertial = ET.SubElement(element, "inertial")
        ET.SubElement(inertial, "pose").text = f"{_triple(link.center_of_mass)} 0 0 0"
        ET.SubElement(inertial, "mass").text = _num(link.mass)
        inertia = ET.SubElement(inertial, "inertia")
        i = link.inertia
        for tag in ("ixx", "ixy", "ixz", "iyy", "iyz", "izz"):
            ET.SubElement(inertia, tag).text = _num(i.get(tag, 0.0))
        if link.mesh is not None:
            for tag in ("visual", "collision"):
                container = ET.SubElement(element, tag, {"name": f"{link.name}_{tag}"})
                geometry = ET.SubElement(container, "geometry")
                mesh = ET.SubElement(geometry, "mesh")
                ET.SubElement(mesh, "uri").text = link.mesh

    def _add_joint(self, model_el: Any, joint: RobotJoint) -> None:
        """A ``<joint>`` with parent/child, pose, and an axis (with limits) for movable types."""
        sdf_type = _SDF_TYPE.get(joint.joint_type, "fixed")
        element = ET.SubElement(model_el, "joint",
                                {"name": joint.name, "type": sdf_type})
        ET.SubElement(element, "parent").text = joint.parent
        ET.SubElement(element, "child").text = joint.child
        pose = f"{_triple(joint.origin_xyz)} {_triple(joint.origin_rpy)}"
        ET.SubElement(element, "pose").text = pose
        if sdf_type in ("revolute", "prismatic"):
            self._add_axis(element, joint)

    def _add_axis(self, element: Any, joint: RobotJoint) -> None:
        """An ``<axis>`` with the joint xyz + a ``<limit>`` (lower/upper/effort/velocity)."""
        axis = ET.SubElement(element, "axis")
        ET.SubElement(axis, "xyz").text = _triple(joint.axis)
        if all(v is None for v in
               (joint.limit_lower, joint.limit_upper, joint.effort, joint.velocity)):
            return
        limit = ET.SubElement(axis, "limit")
        if joint.limit_lower is not None:
            ET.SubElement(limit, "lower").text = _num(joint.limit_lower)
        if joint.limit_upper is not None:
            ET.SubElement(limit, "upper").text = _num(joint.limit_upper)
        if joint.effort is not None:
            ET.SubElement(limit, "effort").text = _num(joint.effort)
        if joint.velocity is not None:
            ET.SubElement(limit, "velocity").text = _num(joint.velocity)


def _num(value: float) -> str:
    """A compact, deterministic string for a float."""
    return f"{float(value):.9g}"


def _triple(vec: tuple[float, float, float]) -> str:
    """A space-separated 3-vector string."""
    return " ".join(_num(c) for c in vec)
