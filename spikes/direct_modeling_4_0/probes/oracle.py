"""The three-tier success oracle for a direct-edit attempt.

BRepCheck_Analyzer sometimes reports invalid geometry as valid (OCCT #1315), so passing the
validity gate is not proof the edit was correct. Every attempt records three INDEPENDENT
tiers; the driver counts a run as PASS only when all three agree, and records any
gate-vs-reality disagreement as a measured instance of the #1315 problem.
"""

from typing import Any


def _face_count(shape: Any) -> int:
    faces = shape.faces() if hasattr(shape, "faces") else []
    return len(faces)


def _volume(shape: Any) -> float:
    try:
        return float(shape.volume)
    except Exception:  # noqa: BLE001 - a shape with no computable volume is itself a signal (record 0.0)
        return 0.0


def _gate_pass(shape: Any) -> bool:
    # Tier 1: the kernel's own validity notion (BRepCheck-backed). Trusted but known-fallible.
    # build123d exposes is_valid as a bool attribute on some versions and a method on others;
    # tolerate both so the gate reflects OCCT, not an accessor mismatch.
    try:
        flag = shape.is_valid
        return bool(flag() if callable(flag) else flag)
    except Exception:  # noqa: BLE001 - an is_valid that itself throws counts as gate failure
        return False


def _sanity_pass(shape: Any) -> bool:
    # Tier 2: independent of BRepCheck. Finite positive volume + at least one solid + some faces.
    volume = _volume(shape)
    if not (volume > 0.0 and volume < 1e15):
        return False
    solids = shape.solids() if hasattr(shape, "solids") else []
    return len(solids) >= 1 and _face_count(shape) >= 1


def _intent_pass(before: Any, after: Any, op: str) -> bool:
    # Tier 3: the result matches the edit's expected delta for this op.
    before_faces = _face_count(before)
    after_faces = _face_count(after)
    before_volume = _volume(before)
    after_volume = _volume(after)
    if op == "defeature":
        # Removing a face should not increase the face count, and volume should change.
        return after_faces <= before_faces and abs(after_volume - before_volume) > 1e-9
    if op == "move_face":
        # Moving a planar face should change volume (and keep a valid positive volume).
        return abs(after_volume - before_volume) > 1e-9 and after_volume > 0.0
    if op == "offset":
        # Offsetting should change volume in a consistent direction.
        return abs(after_volume - before_volume) > 1e-9 and after_volume > 0.0
    return False


def evaluate(before: Any, after: Any, op: str) -> dict[str, Any]:
    """Return the three-tier oracle verdict plus the raw measures used."""
    return {
        "gate_pass": _gate_pass(after),
        "sanity_pass": _sanity_pass(after),
        "intent_pass": _intent_pass(before, after, op),
        "before_faces": _face_count(before),
        "after_faces": _face_count(after),
        "before_volume": _volume(before),
        "after_volume": _volume(after),
    }
