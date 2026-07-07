"""Parse and validate a sweep feature's vocabulary into a sweep description.

A sweep names a ``profile`` (or ``sections``) and exactly one path source: a ``path`` (an
open sketch wire, resolved by the op) or a generated ``helix`` (pitch/height/radius +
axis). Options: ``anchor`` (which profile point lands on the path start: origin/centroid/
[x,y]), ``is_frenet`` (keep-orientation vs Frenet), ``transition``, and ``guides``. This
turns the authored vocabulary into a validated description; the op resolves refs and calls
the kernel. A contract violation raises SweepParamError (the op wraps it into a BuildIssue).
"""

import logging

from ncad.ops.revolve_params import RevolveParamError, resolve_axis

logger = logging.getLogger(__name__)

_TRANSITIONS = frozenset({"transformed", "round", "right"})


class SweepParamError(Exception):
    """A sweep path source, section count, anchor, transition, or helix is invalid."""


def sweep_kwargs(params: dict, refs: dict) -> dict:
    """Return the validated sweep description for a sweep feature."""
    has_path = "path" in params
    has_helix = "helix" in params
    if has_path == has_helix:
        raise SweepParamError(
            "sweep needs exactly one of 'path' (a wire) or 'helix' (generated)")
    transition = str(params.get("transition", "transformed"))
    if transition not in _TRANSITIONS:
        raise SweepParamError(
            f"unknown sweep transition {transition!r}; expected {sorted(_TRANSITIONS)}")
    kwargs: dict = {"is_frenet": bool(params.get("is_frenet", False)),
                    "transition": transition, "anchor": _resolve_anchor(params)}
    if "sections" in params:
        sections = params["sections"]
        if len(sections) < 2:
            raise SweepParamError("sweep 'sections' needs at least 2 profiles")
        kwargs["sections"] = list(sections)
    if has_helix:
        kwargs["helix"] = _resolve_helix(params["helix"])
    return kwargs


def _resolve_anchor(params: dict):
    """The anchor spec: 'origin' (default), 'centroid', or an [x, y] profile point."""
    anchor = params.get("anchor", "origin")
    if anchor in ("origin", "centroid"):
        return anchor
    if isinstance(anchor, (list, tuple)) and len(anchor) == 2:
        return (float(anchor[0]), float(anchor[1]))
    raise SweepParamError(
        f"unknown anchor {anchor!r}; expected 'origin', 'centroid', or [x, y]")


def _resolve_helix(spec: dict) -> dict:
    """Resolve a helix spec to concrete params; require positive pitch/height/radius."""
    for key in ("pitch", "height", "radius"):
        if key not in spec:
            raise SweepParamError(f"helix needs a '{key}'")
        if float(spec[key]) <= 0.0:
            raise SweepParamError(f"helix '{key}' must be positive; got {spec[key]}")
    try:
        axis_point, axis_dir = resolve_axis(spec.get("axis", "Z"))
    except RevolveParamError as exc:
        raise SweepParamError(f"helix axis: {exc}") from exc
    return {"pitch": float(spec["pitch"]), "height": float(spec["height"]),
            "radius": float(spec["radius"]), "axis_point": axis_point,
            "axis_dir": axis_dir, "lefthand": bool(spec.get("lefthand", False)),
            "cone_angle": float(spec.get("cone_angle", 0.0))}
