"""Parse + validate the physics ``srdf {}`` overlay block against a RobotModel.

SRDF (Semantic Robot Description Format) adds the planning semantics a URDF lacks: planning groups
(the joint chains a planner/IK operates on), end-effectors, named group states, and
disabled-collision pairs. This spec owns the AUTHORED part of that (groups / end-effectors / group
states from the optional ``srdf {}`` block in a ``.physics.hocon`` overlay), validated against the
built RobotModel so every reference resolves before anything is emitted. When the block is absent,
one default chain group spanning the base link to the deepest leaf is synthesized, so an SRDF is
always available. The derived part (adjacency disabled-collision pairs) is computed by the writer
directly from the model.

A bad reference here (a group naming a nonexistent link, an end-effector pointing at an unknown
group) is a programmer/authoring error, not validation data, so it raises SrdfSpecError. One class.
"""

import logging

from ncad.robotics.robot_model import RobotModel

logger = logging.getLogger(__name__)


class SrdfSpecError(ValueError):
    """Raised when the srdf block references a link, joint, or group the model does not have."""


class SrdfSpec:
    """The resolved, validated planning semantics for a robot's SRDF (groups, EE, group states)."""

    def __init__(self, document: dict, model: RobotModel) -> None:
        """Parse + validate ``document['physics']['srdf']`` against ``model``.

        :param document: the loaded .physics.hocon document dict.
        :param model: the built RobotModel the SRDF describes (for reference validation).
        :raises SrdfSpecError: if any group/end-effector/group-state reference does not resolve.
        """
        self._model = model
        self._link_names = {link.name for link in model.links}
        self._joint_names = {joint.name for joint in model.joints}
        srdf = (document.get("physics") or {}).get("srdf") or {}

        self._groups = self._parse_groups(srdf.get("groups"))
        self._group_names = {group["name"] for group in self._groups}
        self._end_effectors = self._parse_end_effectors(srdf.get("end_effectors"))
        self._group_states = self._parse_group_states(srdf.get("group_states"))

    @property
    def groups(self) -> list[dict]:
        """The planning groups: each a chain (``base``+``tip``) or a joint list (``joints``)."""
        return self._groups

    @property
    def end_effectors(self) -> list[dict]:
        """The end-effectors: each ``{name, parent, group}``."""
        return self._end_effectors

    @property
    def group_states(self) -> list[dict]:
        """The named group states: each ``{name, group, values}``."""
        return self._group_states

    def chain_joints(self, base_link: str, tip_link: str) -> list[str]:
        """Return the ordered tree joints from ``base_link`` to ``tip_link``.

        Walks parent->child over the spanning-tree joints. Raises SrdfSpecError if there is no such
        path (e.g. the links are reversed or unconnected in the tree).
        """
        child_to_joint = {joint.child: joint for joint in self._model.tree_joints()}
        chain: list[str] = []
        current = tip_link
        while current != base_link:
            joint = child_to_joint.get(current)
            if joint is None:
                raise SrdfSpecError(
                    f"no spanning-tree path from '{base_link}' to '{tip_link}'"
                )
            chain.append(joint.name)
            current = joint.parent
        chain.reverse()
        return chain

    def _parse_groups(self, raw: object) -> list[dict]:
        if not raw:
            return [self._default_group()]
        if not isinstance(raw, list):
            raise SrdfSpecError("srdf.groups must be a list")
        groups: list[dict] = []
        for entry in raw:
            groups.append(self._parse_group(entry))
        return groups

    def _parse_group(self, entry: dict) -> dict:
        name = entry.get("name")
        if not name:
            raise SrdfSpecError("each srdf group needs a 'name'")
        if entry.get("joints"):
            joints = [str(j) for j in entry["joints"]]
            for joint in joints:
                if joint not in self._joint_names:
                    raise SrdfSpecError(f"group '{name}' names unknown joint '{joint}'")
            return {"name": str(name), "joints": joints}
        base = entry.get("base")
        tip = entry.get("tip")
        if not base or not tip:
            raise SrdfSpecError(f"group '{name}' needs either 'joints' or both 'base' and 'tip'")
        for link in (base, tip):
            if link not in self._link_names:
                raise SrdfSpecError(f"group '{name}' names unknown link '{link}'")
        # Validate the chain resolves now, so an unreachable base/tip fails at parse time.
        self.chain_joints(str(base), str(tip))
        return {"name": str(name), "base": str(base), "tip": str(tip)}

    def _parse_end_effectors(self, raw: object) -> list[dict]:
        if not raw:
            return []
        if not isinstance(raw, list):
            raise SrdfSpecError("srdf.end_effectors must be a list")
        result: list[dict] = []
        for entry in raw:
            name = entry.get("name")
            parent = entry.get("parent")
            group = entry.get("group")
            if not name or not parent or not group:
                raise SrdfSpecError("each end_effector needs 'name', 'parent', and 'group'")
            if parent not in self._link_names:
                raise SrdfSpecError(f"end_effector '{name}' names unknown parent link '{parent}'")
            if group not in self._group_names:
                raise SrdfSpecError(f"end_effector '{name}' names unknown group '{group}'")
            result.append({"name": str(name), "parent": str(parent), "group": str(group)})
        return result

    def _parse_group_states(self, raw: object) -> list[dict]:
        if not raw:
            return []
        if not isinstance(raw, list):
            raise SrdfSpecError("srdf.group_states must be a list")
        result: list[dict] = []
        for entry in raw:
            name = entry.get("name")
            group = entry.get("group")
            values = entry.get("values") or {}
            if not name or not group:
                raise SrdfSpecError("each group_state needs 'name' and 'group'")
            if group not in self._group_names:
                raise SrdfSpecError(f"group_state '{name}' names unknown group '{group}'")
            allowed = self._group_joint_names(group)
            for joint in values:
                if joint not in allowed:
                    raise SrdfSpecError(
                        f"group_state '{name}' sets joint '{joint}' not in group '{group}'"
                    )
            result.append({"name": str(name), "group": str(group),
                           "values": {str(k): float(v) for k, v in values.items()}})
        return result

    def _group_joint_names(self, group_name: str) -> set[str]:
        """The joint names a group covers (its explicit list, or its resolved chain)."""
        group = next(g for g in self._groups if g["name"] == group_name)
        if "joints" in group:
            return set(group["joints"])
        return set(self.chain_joints(group["base"], group["tip"]))

    def _default_group(self) -> dict:
        """Synthesize one chain group from the base link to the deepest reachable leaf."""
        tip = self._deepest_leaf()
        return {"name": "arm", "base": self._model.base_link, "tip": tip}

    def _deepest_leaf(self) -> str:
        """The link farthest (most tree joints) from the base along parent->child edges."""
        children: dict[str, list[str]] = {}
        for joint in self._model.tree_joints():
            children.setdefault(joint.parent, []).append(joint.child)
        best_link = self._model.base_link
        best_depth = -1
        stack = [(self._model.base_link, 0)]
        while stack:
            link, depth = stack.pop()
            if depth > best_depth:
                best_depth, best_link = depth, link
            for child in children.get(link, []):
                stack.append((child, depth + 1))
        return best_link
