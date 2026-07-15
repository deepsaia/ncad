"""Lower a user-facing assembly mate to normal-form primitive constraint records.

The user vocabulary (coincident/flush/concentric/parallel/perpendicular/angle/distance/lock) is
sugar over a closed set of ~9 primitive kinds (the 21-primitive normal form from
docs/research/assembly-constraints-3d.md, restricted to the pairs 5.2 ships). MateLowering owns
the vocabulary; MateSolver maps each primitive to a concrete py-slvs call. Pure data: a primitive
is a dict {kind, a, b, value} whose a/b are symbolic connector-role tags ("A.origin", "B.axis",
"A.plane", ...) the solver resolves to transformed entities. Keeping lowering solver-independent
makes the core small, closed, and unit-testable without py-slvs.
"""

import logging

from ncad.assembly.connector_frame import ConnectorFrame

logger = logging.getLogger(__name__)


class MateError(Exception):
    """A mate cannot be lowered (unknown type or missing data); reported by mate id."""


class MateLowering:
    """Maps a user mate to its normal-form primitive records."""

    def lower(self, mate: dict, frame_a: ConnectorFrame,
              frame_b: ConnectorFrame | None) -> list[dict]:
        """Return the primitive records for ``mate``; raise MateError on an unknown type."""
        mate_type = mate.get("type", "")
        value = mate.get("value")
        if mate_type in ("coincident", "mate"):
            # Faces seat opposed by default (normals anti-parallel); flip makes them same-facing.
            second = "parallel_dirs" if mate.get("flip") else "anti_parallel_dirs"
            return [_prim("points_coincident", "A.origin", "B.origin"),
                    _prim(second, "A.axis", "B.axis")]
        if mate_type in ("flush", "align"):
            return [_prim("point_in_plane", "A.origin", "B.plane"),
                    _prim("parallel_dirs", "A.axis", "B.axis")]
        if mate_type == "concentric":
            return [_prim("axes_coincident", "A.axis", "B.axis")]
        if mate_type == "parallel":
            return [_prim("parallel_dirs", "A.axis", "B.axis")]
        if mate_type == "perpendicular":
            return [_prim("dirs_angle", "A.axis", "B.axis", 90.0)]
        if mate_type == "angle":
            return [_prim("dirs_angle", "A.axis", "B.axis", _num(value, mate))]
        if mate_type in ("distance", "offset"):
            return [_prim("point_plane_distance", "A.origin", "B.plane", _num(value, mate))]
        if mate_type == "lock":
            return [_prim("lock", "A", None)]
        if mate_type == "tangent":
            # A cylinder tangent to a plane: the cylinder axis origin sits `radius` from the
            # plane (reuses the point_plane_distance primitive; the radius comes from whichever
            # side is the cylinder connector).
            # Put the cylinder-axis origin `radius` from the plane; the cylinder may be either
            # side (radius-bearing side is the cylinder, the other is the plane).
            if frame_a.radius is not None:
                cyl_role, plane_role, radius = "A.origin", "B.plane", frame_a.radius
            elif frame_b is not None and frame_b.radius is not None:
                cyl_role, plane_role, radius = "B.origin", "A.plane", frame_b.radius
            else:
                raise MateError(
                    f"tangent mate {mate.get('id')!r} needs a cylindrical (radius-bearing) "
                    "connector")
            return [_prim("point_plane_distance", cyl_role, plane_role, float(radius))]
        if mate_type == "symmetric":
            # A and B mirror-positioned across the plane connector C (mate.between[2]). Reuses
            # point_plane_distance with equal-and-opposite seed distances so A and B sit
            # symmetrically about C's plane (one-shot placement, no workplane machinery).
            frame_c = mate.get("_frame_c")
            if frame_c is None:
                raise MateError(
                    f"symmetric mate {mate.get('id')!r} needs a third 'about' connector")
            da = _signed_distance(frame_a, frame_c)
            db = _signed_distance(frame_b, frame_c) if frame_b is not None else -da
            return [_prim("point_plane_distance", "A.origin", "C.plane", da),
                    _prim("point_plane_distance", "B.origin", "C.plane", db)]
        if mate_type == "width":
            # A centered between planes B and C: pin A at the midplane distance from B along B's
            # normal (half the B-to-C gap).
            frame_c = mate.get("_frame_c")
            if frame_c is None or frame_b is None:
                raise MateError(
                    f"width mate {mate.get('id')!r} needs two bounding plane connectors")
            half = 0.5 * _signed_distance(frame_c, frame_b)
            return [_prim("point_plane_distance", "A.origin", "B.plane", half)]
        raise MateError(f"unknown mate type {mate_type!r} (mate {mate.get('id')!r})")


def _prim(kind: str, a: str, b: str | None, value: float | None = None) -> dict:
    return {"kind": kind, "a": a, "b": b, "value": value}


def _num(value: float | int | str | None, mate: dict) -> float:
    if value is None:
        raise MateError(f"mate {mate.get('id')!r} ({mate.get('type')!r}) needs a numeric 'value'")
    return float(value)


def _signed_distance(frame: ConnectorFrame, plane: ConnectorFrame) -> float:
    """Signed distance from ``frame``'s origin to ``plane`` along the plane's normal (Z)."""
    d = (frame.origin[0] - plane.origin[0], frame.origin[1] - plane.origin[1],
         frame.origin[2] - plane.origin[2])
    return d[0] * plane.z[0] + d[1] * plane.z[1] + d[2] * plane.z[2]
