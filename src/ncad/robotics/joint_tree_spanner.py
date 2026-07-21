"""Span an assembly's joint graph into a kinematic tree rooted at the base link.

An assembly is a GRAPH of links connected by joints (it may contain closed loops, e.g. a four-bar).
URDF is a TREE: one parent per link. This walks the joint graph breadth-first from the base link,
orienting each first-reached joint as parent->child; a joint whose child is already reached closes a
loop and is flagged (a tree-only writer reports it; MJCF/SDF keep it as an equality constraint). The
walk fixes each joint's direction so the tree is consistent regardless of how ``between`` was
authored. Pure over its inputs; one class.
"""


class JointTreeSpanner:
    """Orients joints into a spanning tree from a base link, flagging loop-closure joints."""

    def span(self, base_link: str, joints: list[dict]) -> dict:
        """Return ``{oriented: [{joint, parent, child}], loop_closures: [joint_id], reached: set}``.

        ``joints`` are assembly joints (``id``, ``type``, ``between``: two ends). Each
        joint connects two instances; the walk orients it away from the base. A joint reaching an
        already-reached link is a loop closure. Joints in a disconnected component (never reached
        from the base) are also returned as loop_closures with a note via ``reached``.
        """
        adjacency = self._adjacency(joints)
        reached = {base_link}
        oriented: list[dict] = []
        loop_closures: list[str] = []
        used: set[str] = set()
        frontier = [base_link]
        while frontier:
            parent = frontier.pop(0)
            for joint_id, child in adjacency.get(parent, []):
                if joint_id in used:
                    continue
                used.add(joint_id)
                if child in reached:
                    loop_closures.append(joint_id)
                    continue
                reached.add(child)
                oriented.append({"joint": joint_id, "parent": parent, "child": child})
                frontier.append(child)
        # Any joint never traversed sits in a component disconnected from the base: a loop closure
        # for tree purposes (the writer reports it; it is not part of the base-rooted tree).
        for joint in joints:
            if joint.get("id") not in used:
                loop_closures.append(joint["id"])
        return {"oriented": oriented, "loop_closures": loop_closures, "reached": reached}

    def _adjacency(self, joints: list[dict]) -> dict[str, list[tuple[str, str]]]:
        """Undirected adjacency: link id -> [(joint id, other link id)] for each joint's ends."""
        adjacency: dict[str, list[tuple[str, str]]] = {}
        for joint in joints:
            between = joint.get("between") or []
            if len(between) < 2:
                continue
            a, b = between[0].get("instance"), between[1].get("instance")
            joint_id = joint.get("id")
            if a is None or b is None or joint_id is None:
                continue
            adjacency.setdefault(a, []).append((joint_id, b))
            adjacency.setdefault(b, []).append((joint_id, a))
        return adjacency
