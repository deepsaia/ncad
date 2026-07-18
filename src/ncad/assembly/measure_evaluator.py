"""Evaluate measures over time (a scalar sampled per motion frame) from a solved trajectory.

Pure post-processing over the trajectory (no re-solve, no kernel): each measure resolves its point
reference(s) per frame (via motion_point_sampler, in mm) and reduces them to a scalar. Kinds:

- coordinate:   one point's chosen world axis component (mm).
- distance:     ||p_b - p_a|| (mm).
- angle:        the angle a-vertex-b (degrees).
- swept_volume: references a coordinate measure by id; the plunger travel (max-min of that series,
                mm) times a circular bore area, converted to mL (mm^3 / 1000). Emits a scalar
                ``value`` (full swept volume) plus a per-frame swept-so-far series.

Each result is {id, kind, unit, series, min, max [, value, of]}, the series aligned 1:1 with frames.
Velocity / acceleration are deferred (the driver sweep is normalized, not real seconds). One class.
"""

import math

from ncad.assembly.motion_point_sampler import sample_world_points

_AXIS_INDEX = {"x": 0, "y": 1, "z": 2}


class MeasureEvaluator:
    """Turns normalized measure specs + a trajectory into per-measure time series."""

    def evaluate(self, measure_specs: list[dict], frames: list[dict], local_frames: dict,
                 to_metres: float) -> list[dict]:
        """Return [{id, kind, unit, series, min, max [, value, of]}] for each measure."""
        results: list[dict] = []
        by_id: dict[str, dict] = {}
        for spec in measure_specs:
            result = self._one(spec, frames, local_frames, to_metres, by_id)
            by_id[spec["id"]] = result
            results.append(result)
        return results

    def _one(self, spec: dict, frames: list[dict], local_frames: dict, to_metres: float,
             by_id: dict) -> dict:
        kind = spec["kind"]
        if kind == "coordinate":
            return self._coordinate(spec, frames, local_frames, to_metres)
        if kind == "distance":
            return self._distance(spec, frames, local_frames, to_metres)
        if kind == "angle":
            return self._angle(spec, frames, local_frames, to_metres)
        return self._swept_volume(spec, by_id)

    def _coordinate(self, spec: dict, frames: list, local_frames: dict, to_metres: float) -> dict:
        idx = _AXIS_INDEX[spec["axis"]]
        pts = sample_world_points(spec["a"], frames, local_frames, to_metres)
        series = [p[idx] if p is not None else None for p in pts]
        return _finish(spec, "mm", series)

    def _distance(self, spec: dict, frames: list, local_frames: dict, to_metres: float) -> dict:
        a = sample_world_points(spec["a"], frames, local_frames, to_metres)
        b = sample_world_points(spec["b"], frames, local_frames, to_metres)
        series = [math.dist(pa, pb) if (pa is not None and pb is not None) else None
                  for pa, pb in zip(a, b)]
        return _finish(spec, "mm", series)

    def _angle(self, spec: dict, frames: list, local_frames: dict, to_metres: float) -> dict:
        v = sample_world_points(spec["vertex"], frames, local_frames, to_metres)
        a = sample_world_points(spec["a"], frames, local_frames, to_metres)
        b = sample_world_points(spec["b"], frames, local_frames, to_metres)
        series = [_angle_deg(vv, pa, pb) if None not in (vv, pa, pb) else None
                  for vv, pa, pb in zip(v, a, b)]
        return _finish(spec, "deg", series)

    def _swept_volume(self, spec: dict, by_id: dict) -> dict:
        source = by_id[spec["of"]]                # validated to exist + be a coordinate upstream
        values = [s for s in source["series"] if s is not None]
        lo = min(values) if values else 0.0
        area = math.pi / 4.0 * spec["bore_d"] ** 2       # mm^2
        # swept-so-far each frame: travel from the low point x area, mm^3 -> mL.
        series = [(abs(s - lo) * area / 1000.0) if s is not None else None
                  for s in source["series"]]
        travel = (max(values) - lo) if values else 0.0
        value = travel * area / 1000.0
        result = _finish(spec, "mL", series)
        result["value"] = value
        result["of"] = spec["of"]
        return result


def _angle_deg(vertex, a, b) -> float:
    """The angle a-vertex-b in degrees (0..180); 0.0 if a leg is degenerate."""
    u = (a[0] - vertex[0], a[1] - vertex[1], a[2] - vertex[2])
    w = (b[0] - vertex[0], b[1] - vertex[1], b[2] - vertex[2])
    nu = math.sqrt(sum(c * c for c in u))
    nw = math.sqrt(sum(c * c for c in w))
    if nu == 0.0 or nw == 0.0:
        return 0.0
    dot = sum(uc * wc for uc, wc in zip(u, w))
    cos = max(-1.0, min(1.0, dot / (nu * nw)))
    return math.degrees(math.acos(cos))


def _finish(spec: dict, unit: str, series: list) -> dict:
    """Package a series into a result with min/max over its non-None values."""
    present = [s for s in series if s is not None]
    return {"id": spec["id"], "kind": spec["kind"], "unit": unit, "series": series,
            "min": min(present) if present else 0.0, "max": max(present) if present else 0.0}
