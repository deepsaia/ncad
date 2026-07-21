"""Order a RobotModel's spanning-tree joints into a parent->children nesting for MJCF/SDF.

URDF is a flat list of links + joints, but MJCF nests each child body inside its parent in the XML.
This turns the model's spanning-tree joints into ``{parent link -> [child joints]}`` plus the depth
order to emit, so a writer can recurse from the base link. Pure over its inputs; one class. Loop
closures are NOT part of the tree (a writer emits them separately, e.g. as MJCF equality
constraints).
"""

from ncad.robotics.robot_joint import RobotJoint
from ncad.robotics.robot_model import RobotModel


class BodyTree:
    """Parent->child-joint nesting of a RobotModel's spanning tree, rooted at the base link."""

    def __init__(self, model: RobotModel) -> None:
        self._model = model
        self._links = {link.name: link for link in model.links}
        self._children: dict[str, list[RobotJoint]] = {}
        for joint in model.tree_joints():
            self._children.setdefault(joint.parent, []).append(joint)

    def child_joints(self, link_name: str) -> list[RobotJoint]:
        """The tree joints whose parent is ``link_name`` (each names a child link to nest)."""
        return self._children.get(link_name, [])

    def link(self, name: str):
        """The RobotLink named ``name`` (KeyError if absent)."""
        return self._links[name]
