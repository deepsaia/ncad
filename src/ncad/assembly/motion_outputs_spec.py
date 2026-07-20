"""Parse and validate a motion study's ``outputs`` block into typed trace + measure records.

A motion study can declare OUTPUTS: trace curves (the path a point sweeps) and
measures over time (a scalar sampled per frame). This unit turns the raw ``outputs { traces = [...],
measures = [...] }`` block into normalized, validated records the TraceExtractor / MeasureEvaluator
consume; a malformed entry raises MotionOutputsError (the builder wraps it into an id-attributed
issue). Pure parsing, no geometry: point references stay symbolic ({instance, point|connector}) and
are resolved to coordinates later against the trajectory. One class.
"""

_AXES = frozenset({"x", "y", "z"})
_MEASURE_KINDS = frozenset({"coordinate", "distance", "angle", "swept_volume"})


class MotionOutputsError(Exception):
    """A motion ``outputs`` block is malformed; the builder reports it as an id-attributed issue."""


class MotionOutputsSpec:
    """Turns an ``outputs`` block into (traces, measures) as normalized, validated records."""

    def parse(self, outputs: dict) -> tuple[list[dict], list[dict]]:
        """Return (traces, measures); raise MotionOutputsError on any malformed entry.

        Traces: [{id, instance, point|connector}]. Measures: [{id, kind, ...}] where a point ref is
        normalized to {instance, point (tuple|None), connector (str|None)} under keys a/b/vertex.
        """
        traces = [self._trace(t) for t in (outputs.get("traces") or [])]
        _reject_duplicate_ids(traces, "trace")
        measures = [self._measure(m) for m in (outputs.get("measures") or [])]
        _reject_duplicate_ids(measures, "measure")
        self._validate_swept_refs(measures)
        return traces, measures

    def _trace(self, spec: dict) -> dict:
        """One trace: an id + a point ref (a point on a moving instance to follow)."""
        tid = _require_id(spec, "trace")
        ref = _point_ref(spec, f"trace {tid!r}")
        return {"id": tid, "instance": ref["instance"], "point": ref["point"],
                "connector": ref["connector"]}

    def _measure(self, spec: dict) -> dict:
        """One measure, normalized by kind (point refs under a/b/vertex)."""
        mid = _require_id(spec, "measure")
        kind = spec.get("kind")
        if kind not in _MEASURE_KINDS:
            raise MotionOutputsError(
                f"measure {mid!r} has unknown kind {kind!r}; expected {sorted(_MEASURE_KINDS)}")
        if kind == "coordinate":
            axis = spec.get("axis")
            if axis not in _AXES:
                raise MotionOutputsError(
                    f"coordinate measure {mid!r} needs axis in {sorted(_AXES)}")
            return {"id": mid, "kind": kind, "axis": axis,
                    "a": _point_ref(spec, f"measure {mid!r}")}
        if kind == "distance":
            return {"id": mid, "kind": kind,
                    "a": _side_ref(spec, "a", mid), "b": _side_ref(spec, "b", mid)}
        if kind == "angle":
            return {"id": mid, "kind": kind, "vertex": _side_ref(spec, "vertex", mid),
                    "a": _side_ref(spec, "a", mid), "b": _side_ref(spec, "b", mid)}
        # swept_volume: references a coordinate measure by id + a bore diameter.
        of = spec.get("of")
        if not isinstance(of, str) or not of:
            raise MotionOutputsError(f"swept_volume measure {mid!r} needs an 'of' measure id")
        bore_d = spec.get("bore_d")
        if not isinstance(bore_d, (int, float)) or bore_d <= 0:
            raise MotionOutputsError(f"swept_volume measure {mid!r} needs a positive 'bore_d'")
        return {"id": mid, "kind": kind, "of": of, "bore_d": float(bore_d)}

    def _validate_swept_refs(self, measures: list[dict]) -> None:
        """Every swept_volume 'of' must reference a coordinate measure declared earlier."""
        by_id: dict[str, dict] = {}
        for m in measures:
            if m["kind"] == "swept_volume":
                target = by_id.get(m["of"])
                if target is None:
                    raise MotionOutputsError(
                        f"swept_volume {m['id']!r} references unknown measure 'of'={m['of']!r}")
                if target["kind"] != "coordinate":
                    raise MotionOutputsError(
                        f"swept_volume {m['id']!r} 'of'={m['of']!r} must be a coordinate measure")
            by_id[m["id"]] = m


def _require_id(spec: dict, what: str) -> str:
    """The entry's non-empty string id, or raise."""
    mid = spec.get("id")
    if not isinstance(mid, str) or not mid:
        raise MotionOutputsError(f"a {what} needs a non-empty 'id'")
    return mid


def _point_ref(spec: dict, where: str) -> dict:
    """A point ref taken from a spec's own instance + point/connector (traces + coordinate)."""
    return _normalize_ref(spec.get("instance"), spec.get("point"), spec.get("connector"), where)


def _side_ref(spec: dict, key: str, mid: str) -> dict:
    """A point ref under ``key`` (a/b/vertex) of a measure spec."""
    side = spec.get(key)
    if not isinstance(side, dict):
        raise MotionOutputsError(f"measure {mid!r} needs a {key!r} point reference")
    return _normalize_ref(side.get("instance"), side.get("point"), side.get("connector"),
                          f"measure {mid!r} {key}")


def _normalize_ref(instance, point, connector, where: str) -> dict:
    """{instance, point (tuple|None), connector (str|None)}; exactly one of point/connector."""
    if not isinstance(instance, str) or not instance:
        raise MotionOutputsError(f"{where} needs an 'instance'")
    if point is not None and connector is not None:
        raise MotionOutputsError(f"{where} has both 'point' and 'connector'; use one")
    if point is not None:
        if len(point) != 3:
            raise MotionOutputsError(f"{where} 'point' must be [x, y, z]")
        return {"instance": instance,
                "point": (float(point[0]), float(point[1]), float(point[2])), "connector": None}
    if isinstance(connector, str) and connector:
        return {"instance": instance, "point": None, "connector": connector}
    raise MotionOutputsError(f"{where} needs a 'point' [x,y,z] or a 'connector' id")


def _reject_duplicate_ids(records: list[dict], what: str) -> None:
    """Raise if any two records share an id."""
    seen: set[str] = set()
    for r in records:
        if r["id"] in seen:
            raise MotionOutputsError(f"duplicate {what} id {r['id']!r}")
        seen.add(r["id"])
