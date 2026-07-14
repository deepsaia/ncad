"""Reflect an existing assembly instance across a plane into a new instance (bucket 5.7).

A ``mirror`` instance references an already-declared source instance (``of``) and reflects its
placement across a base plane (XY/XZ/YZ) or a ``{point, normal}`` plane. The new instance shares
the source's file/part (or sub-assembly); its placement translation is mirrored. Position mirror
(the common bolt-symmetry case); a full handed-orientation mirror is a documented follow-up. Pure
math.
"""

_BASE_NORMAL = {"XY": (0.0, 0.0, 1.0), "XZ": (0.0, 1.0, 0.0), "YZ": (1.0, 0.0, 0.0)}


class ComponentMirror:
    """Reflects a source instance's placement across a plane into a new instance."""

    def reflect(self, instance: dict, source: dict, plane) -> dict:
        """Return a new instance: the source's geometry at the mirrored placement."""
        normal = self._normal(plane)
        position = (source.get("placement") or {}).get("position") or [0.0, 0.0, 0.0]
        reflected = _reflect_point(tuple(float(c) for c in position), normal)
        out = {key: value for key, value in instance.items() if key not in ("mirror", "of")}
        if "file" in source:
            out["file"] = source["file"]
        if "part" in source:
            out["part"] = source["part"]
        if "assembly" in source:
            out["assembly"] = source["assembly"]
        out["placement"] = {"position": list(reflected)}
        return out

    def _normal(self, plane) -> tuple:
        if isinstance(plane, str):
            return _BASE_NORMAL[plane]
        return tuple(float(c) for c in plane["normal"])


def _reflect_point(point: tuple, normal: tuple) -> tuple:
    """Reflect ``point`` across the plane through the origin with unit ``normal``."""
    length = (normal[0] ** 2 + normal[1] ** 2 + normal[2] ** 2) ** 0.5
    if length < 1e-12:
        return point
    unit = (normal[0] / length, normal[1] / length, normal[2] / length)
    dot = point[0] * unit[0] + point[1] * unit[1] + point[2] * unit[2]
    return (point[0] - 2.0 * dot * unit[0],
            point[1] - 2.0 * dot * unit[1],
            point[2] - 2.0 * dot * unit[2])
