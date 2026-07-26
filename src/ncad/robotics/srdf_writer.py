"""Write a RobotModel + SrdfSpec to an SRDF (Semantic Robot Description Format) XML string.

SRDF is the companion to a URDF: it carries the planning semantics a URDF cannot express. This
writer emits, from the validated SrdfSpec, one ``<group>`` per planning group (a ``<chain>`` for a
base->tip group, or a ``<joint>`` list), one ``<end_effector>`` and ``<group_state>`` per authored
entry, and a ``<disable_collisions reason="Adjacent">`` for every spanning-tree parent/child link
pair (those links always touch at the joint, so their collision check is safely disabled). Pure:
same model + spec -> identical XML. One class.
"""

# xml.etree is used for GENERATION only (build elements + tostring); this writer never parses
# untrusted XML, so the stdlib parser's XXE/entity-expansion risks do not apply here.
import xml.etree.ElementTree as ET

from ncad.robotics.robot_model import RobotModel
from ncad.robotics.srdf_spec import SrdfSpec


class SrdfWriter:
    """Serializes a RobotModel + SrdfSpec to an SRDF XML string."""

    def to_xml(self, model: RobotModel, spec: SrdfSpec) -> str:
        """Return the SRDF XML for ``model`` described by ``spec``."""
        robot = ET.Element("robot", {"name": model.name})
        for group in spec.groups:
            self._add_group(robot, group)
        for end_effector in spec.end_effectors:
            ET.SubElement(robot, "end_effector", {
                "name": end_effector["name"],
                "parent_link": end_effector["parent"],
                "group": end_effector["group"],
            })
        for state in spec.group_states:
            self._add_group_state(robot, state)
        self._add_disable_collisions(robot, model)
        ET.indent(robot)
        return ET.tostring(robot, encoding="unicode", xml_declaration=True)

    def _add_group(self, robot: ET.Element, group: dict) -> None:
        element = ET.SubElement(robot, "group", {"name": group["name"]})
        if "joints" in group:
            for joint in group["joints"]:
                ET.SubElement(element, "joint", {"name": joint})
        else:
            ET.SubElement(element, "chain",
                          {"base_link": group["base"], "tip_link": group["tip"]})

    def _add_group_state(self, robot: ET.Element, state: dict) -> None:
        element = ET.SubElement(robot, "group_state",
                                {"name": state["name"], "group": state["group"]})
        for joint, value in state["values"].items():
            ET.SubElement(element, "joint", {"name": joint, "value": _format_value(value)})

    def _add_disable_collisions(self, robot: ET.Element, model: RobotModel) -> None:
        seen: set[frozenset[str]] = set()
        for joint in model.tree_joints():
            pair = frozenset((joint.parent, joint.child))
            if pair in seen:
                continue
            seen.add(pair)
            ET.SubElement(robot, "disable_collisions",
                          {"link1": joint.parent, "link2": joint.child, "reason": "Adjacent"})


def _format_value(value: float) -> str:
    """Render a joint value: an integer-valued float as ``0``, otherwise the plain float."""
    if float(value).is_integer():
        return str(int(value))
    return repr(float(value))
