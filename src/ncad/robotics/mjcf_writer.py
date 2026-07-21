"""Write a RobotModel to a MuJoCo MJCF (MJCF XML) string.

MJCF is MuJoCo's native format and the best SIMULATION target: unlike URDF it nests each child body
inside its parent, keeps closed loops (as ``<equality>`` constraints), and models actuators/contact.
This writer:

- emits one ``<asset><mesh>`` per link mesh, referenced by the body's ``<geom>``;
- recurses the spanning tree (BodyTree) so each child ``<body>`` nests in its parent, with the joint
  declared INSIDE the child (MJCF joints connect a body to its parent);
- writes the full inertia tensor via ``fullinertia`` (ncad computes it, so no diagonalization);
- keeps every loop-closure joint as an ``<equality><connect>`` between its two bodies (the thing a
  tree-only URDF must drop);
- adds a ``<position>`` actuator for each authored ``actuated`` joint.

Pure: same model -> identical XML. Uses xml.etree for GENERATION only (never parses untrusted XML,
so the stdlib parser's XXE risks do not apply). One class.
"""

import xml.etree.ElementTree as ET
from typing import Any

from ncad.robotics.body_tree import BodyTree
from ncad.robotics.robot_joint import RobotJoint
from ncad.robotics.robot_link import RobotLink
from ncad.robotics.robot_model import RobotModel

# neutral joint type -> MJCF joint type. fixed = no joint element (the body is rigidly nested);
# floating -> a free joint (6 DOF).
_MJCF_TYPE = {
    "revolute": "hinge", "continuous": "hinge", "prismatic": "slide", "floating": "free",
}


class MjcfWriter:
    """Serializes a RobotModel to a MuJoCo MJCF XML string (nested bodies + loop equalities)."""

    def __init__(self) -> None:
        self._actuated: list[RobotJoint] = []

    def to_xml(self, model: RobotModel) -> str:
        """Return the MJCF XML for ``model`` (nested bodies + mesh assets + loop equalities)."""
        self._actuated = []
        mujoco = ET.Element("mujoco", {"model": model.name})
        ET.SubElement(mujoco, "compiler", {"meshdir": ".", "angle": "radian"})
        self._add_assets(mujoco, model)
        worldbody = ET.SubElement(mujoco, "worldbody")
        tree = BodyTree(model)
        self._add_body(worldbody, tree, model.base_link, None)
        self._add_equalities(mujoco, model)
        self._add_actuators(mujoco)
        ET.indent(mujoco)
        return ET.tostring(mujoco, encoding="unicode", xml_declaration=True)

    def _add_assets(self, mujoco: Any, model: RobotModel) -> None:
        """One ``<mesh>`` asset per link that has a mesh (named ``<link>_mesh``)."""
        meshed = [link for link in model.links if link.mesh is not None]
        if not meshed:
            return
        asset = ET.SubElement(mujoco, "asset")
        for link in meshed:
            mesh = link.mesh or ""   # the filter above guarantees non-None; narrow for the checker
            ET.SubElement(asset, "mesh", {"name": f"{link.name}_mesh", "file": mesh})

    def _add_body(self, parent_xml: Any, tree: BodyTree, link_name: str,
                  joint: RobotJoint | None) -> None:
        """Emit ``<body>`` for ``link_name`` nested in ``parent_xml``; recurse into its children.

        ``joint`` is the tree joint connecting this body to its parent (None for the base). The body
        is positioned at the joint origin; the joint element is declared inside the body.
        """
        link = tree.link(link_name)
        attrs = {"name": link_name}
        if joint is not None:
            attrs["pos"] = _triple(joint.origin_xyz)
        body = ET.SubElement(parent_xml, "body", attrs)
        if joint is not None:
            self._add_joint(body, joint)
        self._add_inertial(body, link)
        if link.mesh is not None:
            ET.SubElement(body, "geom", {"type": "mesh", "mesh": f"{link_name}_mesh"})
        for child_joint in tree.child_joints(link_name):
            self._add_body(body, tree, child_joint.child, child_joint)

    def _add_joint(self, body: Any, joint: RobotJoint) -> None:
        """The ``<joint>`` inside a child body (MJCF joints connect the body to its parent)."""
        mjcf_type = _MJCF_TYPE.get(joint.joint_type)
        if mjcf_type is None:
            return  # fixed: rigidly nested, no joint element
        if joint.joint_type == "free":
            ET.SubElement(body, "joint", {"name": joint.name, "type": "free"})
            return
        attrs = {"name": joint.name, "type": mjcf_type, "axis": _triple(joint.axis)}
        if joint.limit_lower is not None and joint.limit_upper is not None:
            attrs["range"] = f"{_num(joint.limit_lower)} {_num(joint.limit_upper)}"
            attrs["limited"] = "true"
        if joint.damping is not None:
            attrs["damping"] = _num(joint.damping)
        if joint.friction is not None:
            attrs["frictionloss"] = _num(joint.friction)
        ET.SubElement(body, "joint", attrs)
        if joint.effort is not None or joint.velocity is not None:
            self._actuated.append(joint)

    def _add_inertial(self, body: Any, link: RobotLink) -> None:
        """The ``<inertial>`` with mass + the full inertia tensor (fullinertia) at the COM."""
        i = link.inertia
        ET.SubElement(body, "inertial", {
            "pos": _triple(link.center_of_mass), "mass": _num(link.mass),
            "fullinertia": " ".join(_num(i.get(k, 0.0)) for k in
                                    ("ixx", "iyy", "izz", "ixy", "ixz", "iyz"))})

    def _add_equalities(self, mujoco: Any, model: RobotModel) -> None:
        """Each loop-closure joint becomes an ``<equality><connect>`` between its two bodies."""
        closures = model.loop_closures()
        if not closures:
            return
        equality = ET.SubElement(mujoco, "equality")
        for joint in closures:
            ET.SubElement(equality, "connect", {
                "body1": joint.child, "body2": joint.parent, "anchor": _triple(joint.origin_xyz)})

    def _add_actuators(self, mujoco: Any) -> None:
        """A ``<position>`` actuator per actuated joint (those with an authored effort/velocity)."""
        if not self._actuated:
            return
        actuator = ET.SubElement(mujoco, "actuator")
        for joint in self._actuated:
            attrs = {"name": f"{joint.name}_act", "joint": joint.name}
            if joint.effort is not None:
                attrs["forcerange"] = f"{_num(-joint.effort)} {_num(joint.effort)}"
                attrs["forcelimited"] = "true"
            ET.SubElement(actuator, "position", attrs)


def _num(value: float) -> str:
    """A compact, deterministic string for a float."""
    return f"{float(value):.9g}"


def _triple(vec: tuple[float, float, float]) -> str:
    """A space-separated 3-vector string."""
    return " ".join(_num(c) for c in vec)
