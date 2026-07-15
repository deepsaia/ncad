"""Parse and validate a ``primitive`` base-body feature into make_primitive kwargs.

The feature dict names a ``kind`` (box/cylinder/sphere/cone/torus/wedge) plus that kind's
dimensions (diameters or radii), an optional base ``plane`` (default XY) and ``at`` origin offset.
This resolves the authored vocabulary (d -> radius, major_d -> major_radius, ...) into the resolved
numeric ``dims`` dict ``Kernel.make_primitive`` consumes. A contract violation raises
PrimitiveParamError (the op wraps it into a BuildIssue).
"""

_KINDS = frozenset({"box", "cylinder", "sphere", "cone", "torus", "wedge"})


class PrimitiveParamError(Exception):
    """A primitive kind is unknown or a required dimension is missing."""


def primitive_kwargs(params: dict) -> dict:
    """Return ``{kind, dims, plane, at}`` for a primitive feature."""
    kind = params.get("kind")
    if not isinstance(kind, str) or kind not in _KINDS:
        raise PrimitiveParamError(
            f"unknown primitive kind {kind!r}; expected one of {sorted(_KINDS)}")
    dims = _dims_for(kind, params)
    plane = params.get("plane", "XY")
    at = params.get("at", [0.0, 0.0])
    plane_offset = float(params.get("plane_offset", 0.0))
    return {"kind": kind, "dims": dims, "plane": plane,
            "at": (float(at[0]), float(at[1])), "plane_offset": plane_offset}


def _radius(params: dict, kind: str, d_key: str, r_key: str) -> float:
    if d_key in params:
        return float(params[d_key]) / 2.0
    if r_key in params:
        return float(params[r_key])
    raise PrimitiveParamError(f"{kind} needs {d_key!r} (diameter) or {r_key!r} (radius)")


def _num(params: dict, kind: str, key: str) -> float:
    if key not in params:
        raise PrimitiveParamError(f"{kind} needs a {key!r} dimension")
    return float(params[key])


def _dims_for(kind: str, params: dict) -> dict:
    if kind == "box":
        return {"w": _num(params, kind, "w"), "d": _num(params, kind, "d"),
                "h": _num(params, kind, "h")}
    if kind == "cylinder":
        return {"radius": _radius(params, kind, "d", "r"), "h": _num(params, kind, "h")}
    if kind == "sphere":
        return {"radius": _radius(params, kind, "d", "r")}
    if kind == "cone":
        return {"bottom_radius": _radius(params, kind, "bottom_d", "bottom_r"),
                "top_radius": _radius(params, kind, "top_d", "top_r"),
                "h": _num(params, kind, "h")}
    if kind == "torus":
        return {"major_radius": _radius(params, kind, "major_d", "major_r"),
                "minor_radius": _radius(params, kind, "minor_d", "minor_r")}
    return {"dx": _num(params, kind, "dx"), "dy": _num(params, kind, "dy"),
            "dz": _num(params, kind, "dz")}
