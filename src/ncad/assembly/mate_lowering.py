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
        raise MateError(f"unknown mate type {mate_type!r} (mate {mate.get('id')!r})")


def _prim(kind: str, a: str, b: str | None, value: float | None = None) -> dict:
    return {"kind": kind, "a": a, "b": b, "value": value}


def _num(value: float | int | str | None, mate: dict) -> float:
    if value is None:
        raise MateError(f"mate {mate.get('id')!r} ({mate.get('type')!r}) needs a numeric 'value'")
    return float(value)
