"""A robot joint in the format-neutral robot IR: a parent->child connection with axis + limits.

One articulation between two links. The kinematic facts (``parent``, ``child``, ``origin``,
``axis``) are DERIVED from the assembly's joint + connector frames; the robot/sim semantics
(``joint_type`` mapped from the ncad joint, and the authored ``limit``/``effort``/``velocity``/
``damping``/``friction`` from the .physics overlay) ride alongside. A format writer turns this into
that format's joint element. ``is_loop_closure`` marks a joint that closes a kinematic loop (not
part of the spanning tree); a tree-only format (URDF) reports these instead of emitting them.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class RobotJoint:
    """A robot joint: type + parent/child links + origin/axis (derived) + authored limits."""

    name: str
    joint_type: str                 # neutral: revolute | continuous | prismatic | fixed | floating
    parent: str
    child: str
    # Joint origin in the parent link frame: translation (m) + rpy rotation (rad).
    origin_xyz: tuple[float, float, float] = (0.0, 0.0, 0.0)
    origin_rpy: tuple[float, float, float] = (0.0, 0.0, 0.0)
    axis: tuple[float, float, float] = (0.0, 0.0, 1.0)
    # Authored (physics overlay) limits/dynamics; None means unspecified (writer omits or defaults).
    limit_lower: float | None = None
    limit_upper: float | None = None
    effort: float | None = None
    velocity: float | None = None
    damping: float | None = None
    friction: float | None = None
    # True when this joint closes a loop and is excluded from the URDF spanning tree.
    is_loop_closure: bool = False
