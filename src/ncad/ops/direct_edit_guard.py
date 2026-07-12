"""Enforce the 4.0 direct-modeling envelope before a direct-edit op runs.

The envelope (docs/research/direct-modeling-envelope.md) is narrow: defeature is trustworthy
only on simple planar faces of a single-body part, and inward offset fails on thin walls. This
guard inspects the target face + neighbourhood and refuses RED preconditions BEFORE the kernel
op runs, so a fragile OCCT edit is never attempted. Fail-safe: when a needed fact is
unavailable, refuse rather than risk a silent corruption.
"""

import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


def _same_handle(descriptor_handle: Any, neighbour: Any) -> bool:
    """True if a describe_elements handle refers to the same face as a face_neighbours handle.

    Build123dKernel returns raw OCP TopoDS from face_neighbours but build123d Face wrappers from
    describe_elements, so compare on the underlying shape (.wrapped.IsSame). The FakeKernel uses
    plain objects on both sides, compared by identity.
    """
    wrapped = getattr(descriptor_handle, "wrapped", descriptor_handle)
    neighbour_wrapped = getattr(neighbour, "wrapped", neighbour)
    if hasattr(wrapped, "IsSame"):
        return bool(wrapped.IsSame(neighbour_wrapped))
    return descriptor_handle is neighbour

# Thresholds enforcing the envelope; each cites the envelope line it implements.
_SLIVER_AREA_MM2 = 1.0        # "sliver/small face" (envelope RED: defeature on sliver faces)
_MIN_WALL_FACTOR = 1.0        # inward offset/move refused when |distance| >= min wall thickness
_MAX_FACES_FOR_MOVE = 200     # move_face over-complexity refusal (envelope: complex solids fail)
_ENVELOPE = "docs/research/direct-modeling-envelope.md"

# FakeKernel and Build123dKernel now both emit the canonical "plane"; None tolerates a
# descriptor with no type set.
_PLANAR_NAMES = frozenset({"plane", None})


@dataclass
class GuardVerdict:
    """The guard's decision for one direct-edit attempt."""

    allowed: bool
    reason: str | None = None
    envelope_ref: str | None = None


class DirectEditGuard:
    """Allows or refuses a direct-edit op per the measured 4.0 envelope."""

    def check(self, kernel: Any, solid: Any, face: Any, op: str, params: dict) -> GuardVerdict:
        """Return allow / refuse-with-reason for ``op`` on ``face`` of ``solid``.

        ``face`` is the resolved face Element (with ``.handle`` and ``.attrs``) for defeature, or
        None for offset (whole-solid). Reading geom_type/area from the Element's attrs avoids a
        second ``describe_elements`` call, whose handles are not identity-stable on every kernel.
        """
        if op == "defeature":
            return self._check_defeature(kernel, solid, face)
        if op == "offset":
            return self._check_offset(kernel, solid, params)
        if op == "move_face":
            return self._check_move_face(kernel, solid, face, params)
        # Unknown direct op: fail safe.
        return GuardVerdict(False, f"no envelope rule for direct op {op!r}", _ENVELOPE)

    def _check_defeature(self, kernel: Any, solid: Any, face: Any) -> GuardVerdict:
        if face is None:
            return GuardVerdict(False, "defeature requires a target face", _ENVELOPE)
        if len(kernel.bodies(solid)) > 1:
            return GuardVerdict(False, "defeature refused: multibody solid (envelope RED)",
                                _ENVELOPE)
        attrs = getattr(face, "attrs", None)
        if attrs is None:
            return GuardVerdict(False, "defeature refused: unresolved target face", _ENVELOPE)
        geom_type = attrs.get("geom_type") or attrs.get("type")
        if geom_type not in _PLANAR_NAMES:
            return GuardVerdict(False, "defeature refused: non-planar target face (envelope RED)",
                                _ENVELOPE)
        if self._is_sliver(attrs):
            return GuardVerdict(False, "defeature refused: sliver/small target face (envelope RED)",
                                _ENVELOPE)
        if kernel.is_tangent_adjacent(solid, face.handle):
            return GuardVerdict(False,
                                "defeature refused: tangent-adjacent face (envelope RED)",
                                _ENVELOPE)
        return GuardVerdict(True)

    def _check_offset(self, kernel: Any, solid: Any, params: dict) -> GuardVerdict:
        distance = float(params.get("distance", 0.0))
        if distance == 0.0:
            return GuardVerdict(False, "offset requires a non-zero distance", _ENVELOPE)
        if distance > 0.0:
            return GuardVerdict(True)  # outward: the most robust op (envelope GREEN)
        # Inward: refuse if it would exceed the wall, and fail safe when unknown.
        thickness = kernel.min_wall_thickness(solid)
        if thickness is None:
            return GuardVerdict(False,
                                "inward offset refused: wall thickness unknown (fail-safe)",
                                _ENVELOPE)
        if abs(distance) >= _MIN_WALL_FACTOR * thickness:
            return GuardVerdict(False,
                                "inward offset refused: exceeds min wall thickness (envelope RED)",
                                _ENVELOPE)
        return GuardVerdict(True)

    def _check_move_face(self, kernel: Any, solid: Any, face: Any, params: dict) -> GuardVerdict:
        if face is None:
            return GuardVerdict(False, "move_face requires a target face", _ENVELOPE)
        attrs = getattr(face, "attrs", None)
        if attrs is None:
            return GuardVerdict(False, "move_face refused: unresolved target face", _ENVELOPE)
        geom_type = attrs.get("geom_type") or attrs.get("type")
        if geom_type not in _PLANAR_NAMES:
            return GuardVerdict(False, "move_face refused: non-planar target face (envelope RED)",
                                _ENVELOPE)
        # A non-planar (fillet/blend) neighbour is the valid-but-empty trigger the spike found.
        for neighbour in kernel.face_neighbours(solid, face.handle):
            if not self._neighbour_is_planar(kernel, solid, neighbour):
                return GuardVerdict(False,
                                    "move_face refused: non-planar neighbour (envelope RED)",
                                    _ENVELOPE)
        face_count = len([d for d in kernel.describe_elements(solid) if d["kind"] == "face"])
        if face_count > _MAX_FACES_FOR_MOVE:
            return GuardVerdict(False, "move_face refused: solid too complex (envelope RED)",
                                _ENVELOPE)
        distance = float(params.get("distance", 0.0))
        if distance == 0.0:
            return GuardVerdict(False, "move_face requires a non-zero distance", _ENVELOPE)
        if distance < 0.0:
            thickness = kernel.min_wall_thickness(solid)
            if thickness is None:
                return GuardVerdict(False,
                                    "inward move_face refused: wall thickness unknown (fail-safe)",
                                    _ENVELOPE)
            if abs(distance) >= _MIN_WALL_FACTOR * thickness:
                return GuardVerdict(False,
                                    "inward move_face refused: exceeds min wall thickness "
                                    "(envelope RED)", _ENVELOPE)
        return GuardVerdict(True)

    def _neighbour_is_planar(self, kernel: Any, solid: Any, neighbour: Any) -> bool:
        # neighbour is a kernel face handle; find its descriptor to read geom_type. face_neighbours
        # returns raw OCP TopoDS on the real kernel while describe_elements handles are build123d
        # Face wrappers, so compare on the underlying shape (.wrapped.IsSame). On the FakeKernel
        # both sides are plain objects compared by identity.
        for descriptor in kernel.describe_elements(solid):
            if descriptor["kind"] != "face":
                continue
            if _same_handle(descriptor["handle"], neighbour):
                return descriptor.get("geom_type") in _PLANAR_NAMES
        # Unknown neighbour: fail safe (treat as non-planar so we refuse).
        return False

    def _is_sliver(self, attrs: dict) -> bool:
        area = attrs.get("area")
        return area is not None and float(area) < _SLIVER_AREA_MM2
