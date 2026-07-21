"""The format-neutral robot IR: a named base link + links + joints, shared by every format writer.

The intermediate representation between an ncad assembly and a robot/physics description. It is
produced once (by RobotModelBuilder, from an assembly + a .physics overlay) and consumed by each
format writer (UrdfWriter now; MjcfWriter / SdfWriter later) so the derivation logic is written
once and the writers stay thin. Holds only neutral data; a writer decides how (or whether) to
express each piece in its target format. One class.
"""

from dataclasses import dataclass, field

from ncad.robotics.robot_joint import RobotJoint
from ncad.robotics.robot_link import RobotLink


@dataclass(frozen=True)
class RobotModel:
    """A robot: a name, the base (root) link name, and the link + joint lists (SI units)."""

    name: str
    base_link: str
    links: list[RobotLink] = field(default_factory=list)
    joints: list[RobotJoint] = field(default_factory=list)

    def tree_joints(self) -> list[RobotJoint]:
        """The spanning-tree joints (excludes loop closures a tree-only format cannot hold)."""
        return [j for j in self.joints if not j.is_loop_closure]

    def loop_closures(self) -> list[RobotJoint]:
        """The joints that close a kinematic loop (reported by a tree-only writer, kept by MJCF)."""
        return [j for j in self.joints if j.is_loop_closure]
