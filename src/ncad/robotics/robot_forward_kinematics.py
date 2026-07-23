"""Forward kinematics over a robot tree: pose (per-joint value) -> per-link placement matrix.

The Python mirror of the viewer's robot_fk.js. Given the robot tree (base link + joints with
parent/child/axis/parent-relative origin) and a pose ({joint: value}, radians for a revolute /
metres for a prismatic), it walks the tree computing each link's world transform
``T_world(child) = T_world(parent) . translate(origin) . motion(axis, q)`` and returns the NODE
placement per link (identity at rest): the transform that maps the in-place-authored link geometry
to its posed position, exactly the shape the assembly/viewer placement convention expects.

Row-major 4x4 matrices (the ncad placement convention: translation in the last row). Units follow
the tree's origins - the robot tree is metres, so poses are radians/metres and the result is metres.
One class; pure math (no kernel, no scene).
"""

import math


class RobotForwardKinematics:
    """Solves per-link placement matrices for a robot tree at a given joint pose."""

    def solve(self, tree: dict, pose: dict[str, float]) -> dict[str, list[list[float]]]:
        """Return ``{link: row-major 4x4}`` (node placement, identity at rest) for ``pose``.

        ``tree`` is the robot.json dict (base_link + joints). ``pose`` maps joint name -> value
        (radians for revolute/continuous, metres for prismatic); a missing joint defaults to 0.
        Loop-closure joints are skipped (a tree-only FK, like the URDF spanning tree).
        """
        joints = [j for j in tree.get("joints", []) if not j.get("loop_closure")]
        ordered = self._tree_order(tree.get("base_link", ""), joints)
        # Rest frame origin per link: cumulative parent-relative origins from the base (base at 0).
        rest = {tree.get("base_link", ""): (0.0, 0.0, 0.0)}
        for joint in ordered:
            origin = joint.get("origin", [0.0, 0.0, 0.0])
            parent_rest = rest.get(joint["parent"], (0.0, 0.0, 0.0))
            rest[joint["child"]] = (parent_rest[0] + origin[0], parent_rest[1] + origin[1],
                                    parent_rest[2] + origin[2])
        # World transform per link by walking the tree, in COLUMN-VECTOR convention (T . p, the
        # textbook order): T_world(child) = T_world(parent) . translate(origin) . motion(q). The
        # node placement = T_world . translate(-rest) maps the in-place geometry to the posed spot.
        # ncad placements are ROW-VECTOR (p . M), so the result is transposed on output.
        world = {tree.get("base_link", ""): _identity()}
        for joint in ordered:
            parent_world = world.get(joint["parent"], _identity())
            origin = joint.get("origin", [0.0, 0.0, 0.0])
            offset = _col_translation(origin[0], origin[1], origin[2])
            motion = self._joint_motion(joint, pose.get(joint["name"], 0.0))
            world[joint["child"]] = _matmul(_matmul(parent_world, offset), motion)
        nodes: dict[str, list[list[float]]] = {}
        for link, w in world.items():
            r = rest.get(link, (0.0, 0.0, 0.0))
            node_col = _matmul(w, _col_translation(-r[0], -r[1], -r[2]))
            nodes[link] = _transpose(node_col)   # column-vector -> ncad row-vector placement
        return nodes

    def _tree_order(self, base: str, joints: list[dict]) -> list[dict]:
        """Joints in parent-before-child order (so a parent transform is known first)."""
        ordered: list[dict] = []
        reachable: set[str] = {base}
        guard = len(joints) + 1
        while len(ordered) < len(joints) and guard > 0:
            guard -= 1
            for joint in joints:
                if joint not in ordered and joint.get("parent") in reachable:
                    ordered.append(joint)
                    reachable.add(str(joint.get("child", "")))
        return ordered

    def _joint_motion(self, joint: dict, q: float) -> list[list[float]]:
        """The joint's local motion transform for value ``q`` (column-vector convention)."""
        axis = _normalize(joint.get("axis", [0.0, 0.0, 1.0]))
        if joint.get("type") == "prismatic":
            return _col_translation(axis[0] * q, axis[1] * q, axis[2] * q)
        return _col_rotation(axis, q)


def _identity() -> list[list[float]]:
    return [[1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]]


def _col_translation(x: float, y: float, z: float) -> list[list[float]]:
    # Column-vector convention (T . p): translation in the last COLUMN.
    return [[1.0, 0.0, 0.0, x], [0.0, 1.0, 0.0, y], [0.0, 0.0, 1.0, z], [0.0, 0.0, 0.0, 1.0]]


def _col_rotation(axis: list[float], angle: float) -> list[list[float]]:
    """Column-vector Rodrigues rotation about ``axis`` by ``angle`` (radians)."""
    x, y, z = axis
    c, s, t = math.cos(angle), math.sin(angle), 1.0 - math.cos(angle)
    return [[t * x * x + c, t * x * y - s * z, t * x * z + s * y, 0.0],
            [t * x * y + s * z, t * y * y + c, t * y * z - s * x, 0.0],
            [t * x * z - s * y, t * y * z + s * x, t * z * z + c, 0.0],
            [0.0, 0.0, 0.0, 1.0]]


def _matmul(a: list[list[float]], b: list[list[float]]) -> list[list[float]]:
    return [[sum(a[i][k] * b[k][j] for k in range(4)) for j in range(4)] for i in range(4)]


def _transpose(m: list[list[float]]) -> list[list[float]]:
    return [[m[j][i] for j in range(4)] for i in range(4)]


def _normalize(v: list[float]) -> list[float]:
    n = math.sqrt(sum(c * c for c in v)) or 1.0
    return [c / n for c in v]
