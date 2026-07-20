"""Compute per-feature dependency sets and a topological rebuild order for a part.

Features within a part are mostly linear, but profile/target/tool references make the
dependency structure a DAG. This graph is what the cache-key chain
and the executor walk: a feature's key includes the keys of the features it depends on,
so a parameter edit dirties exactly the affected suffix. Broken-reference reporting is
bucket 0.5; here a reference to a missing id is still recorded as a dependency (so keys
change correctly) and the order is still produced.
"""

import logging

logger = logging.getLogger(__name__)

# Fields that name a dependency feature, per op (mirrors builder._REF_FIELDS).
_NAMED_DEP_FIELDS: dict[str, tuple[str, ...]] = {
    "extrude": ("profile",),
    "pocket": ("target", "profile"),
    "boolean": ("target", "tool"),
}
# Ops that produce no solid and are therefore never a working-solid predecessor.
_NON_SOLID_OPS = frozenset({"sketch", "datum_plane", "datum_axis"})


class GraphCycleError(Exception):
    """The feature dependency graph contains a cycle (a contract error)."""


class RebuildGraph:
    """Dependency sets + topological order over a part's features."""

    def __init__(self, features: list[dict]) -> None:
        self._ids = [f["id"] for f in features]
        self._deps = _compute_deps(features)

    def deps(self, feature_id: str) -> list[str]:
        """Ids of the features ``feature_id`` directly consumes."""
        return list(self._deps.get(feature_id, []))

    def order(self) -> list[str]:
        """Topological order of feature ids. Raises GraphCycleError on a cycle.

        The sort is AUTHORED-STABLE: among features that are ready (all deps satisfied), the
        one that appears earliest in the authored feature list runs first. A feature tree is a
        stateful pipeline (like a Blender modifier stack) where ops with no explicit input ref
        (pattern/transform/mirror/split) consume the authored-previous running solid; a plain
        topological sort could schedule an independent later solid before such an op, so it
        would replicate/transform the wrong shape. Dependencies force a feature EARLIER; they
        never license reordering two independent features out of authored order.
        """
        rank = {fid: i for i, fid in enumerate(self._ids)}
        known = set(self._ids)
        indegree = {fid: 0 for fid in self._ids}
        dependents: dict[str, list[str]] = {fid: [] for fid in self._ids}
        for fid in self._ids:
            for dep in self._deps.get(fid, []):
                if dep in known:
                    indegree[fid] += 1
                    dependents[dep].append(fid)
        # `ready` kept sorted by authored rank so the earliest-authored ready feature runs next.
        ready = sorted((fid for fid in self._ids if indegree[fid] == 0),
                       key=lambda fid: rank[fid])
        result: list[str] = []
        while ready:
            current = ready.pop(0)
            result.append(current)
            newly_ready = False
            for dependent in dependents[current]:
                indegree[dependent] -= 1
                if indegree[dependent] == 0:
                    ready.append(dependent)
                    newly_ready = True
            if newly_ready:
                ready.sort(key=lambda fid: rank[fid])
        if len(result) != len(self._ids):
            remaining = sorted(fid for fid in self._ids if fid not in result)
            raise GraphCycleError(remaining)
        return result


def _compute_deps(features: list[dict]) -> dict[str, list[str]]:
    """Map each feature id to the ids it depends on."""
    deps: dict[str, list[str]] = {}
    previous_solid: str | None = None
    for feature in features:
        fid = feature["id"]
        op = feature.get("op", "")
        named = _named_deps(feature, op)
        if op == "pocket" and not feature.get("target") and previous_solid is not None:
            named = [previous_solid, *named]
        # A sketch that projects prior geometry (edges/vertices) or references an intersection
        # curve depends on the working solid it draws from.
        if (op == "sketch" and previous_solid is not None
                and (feature.get("project") or feature.get("project_vertices")
                     or feature.get("intersect"))):
            named = [previous_solid, *named]
        if named:
            deps[fid] = named
        elif op in _NON_SOLID_OPS:
            deps[fid] = []
        elif previous_solid is not None:
            deps[fid] = [previous_solid]
        else:
            deps[fid] = []
        if op not in _NON_SOLID_OPS:
            previous_solid = fid
    return deps


def _named_deps(feature: dict, op: str) -> list[str]:
    """Explicit named dependencies from the op's reference fields, in order."""
    result: list[str] = []
    for field in _NAMED_DEP_FIELDS.get(op, ()):
        value = feature.get(field)
        if isinstance(value, str) and value:
            result.append(value)
    return result
