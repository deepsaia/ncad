"""Pairwise static interference / clearance over an assembly's placed instances (bucket 5.6).

For each unordered pair of world-placed instance solids: measure the kernel distance; when the
solids are within tolerance of contact, measure the boolean-common volume; classify into
clearance / touching / interfering (InterferenceClassifier). common_volume is only computed for
close pairs (a positive-clearance pair skips the more expensive boolean). A measurement failure on
a pair is an id-attributed `error` finding; the rest continue (partial-result discipline).

Two prunings keep the exact-distance cost (OCCT ``BRepExtrema_DistShapeShape``, which is expensive
on dense tooth/thread geometry) off pairs that cannot be a real clash:

- Expected-contact pairs (``expected``): pairs a mechanism DECLARES as meshing by design (two bodies
  joined by a joint, tied by a coupling, or listed in an ``expected_contact`` block). Meshing gears
  touch on purpose, so measuring them wastes the most time for no signal; they are reported
  ``expected_contact`` and skipped. This mirrors a robotics SRDF ``disable_collisions`` allow-list.
- AABB pre-filter: if the two solids' axis-aligned bounding boxes are separated by a gap ``g``
  beyond tolerance, the true minimum distance is at least ``g`` (a box contains its solid), so it is
  clearance with no exact call. Only pairs whose AABBs touch/overlap fall through to the exact
  distance, so a real clash is never missed.
"""

import logging
import math
from typing import Any

from ncad.assembly.interference_classifier import InterferenceClassifier

logger = logging.getLogger(__name__)

_DIST_TOL = 1e-6


class InterferenceChecker:
    """Runs the kernel distance + common-volume over instance pairs and classifies each."""

    def __init__(self, kernel: Any) -> None:
        self._kernel = kernel
        self._classifier = InterferenceClassifier()

    def check(self, placed: list[dict],
              expected: set[frozenset] | None = None) -> list[dict]:
        """Return one finding per instance pair: {a, b, status, distance, volume}.

        :param placed: world-placed instance solids ``[{id, shape}, ...]``.
        :param expected: unordered id pairs (as ``frozenset({a, b})``) that mesh by design; each is
            reported ``expected_contact`` and NOT measured. None means measure every pair.
        """
        expected = expected or set()
        findings: list[dict] = []
        for i in range(len(placed)):
            for j in range(i + 1, len(placed)):
                one, two = placed[i], placed[j]
                if frozenset((one["id"], two["id"])) in expected:
                    findings.append({"a": one["id"], "b": two["id"],
                                     "status": "expected_contact", "distance": 0.0, "volume": 0.0})
                    continue
                findings.append(self._pair(one, two))
        return findings

    def _pair(self, one: dict, two: dict) -> dict:
        a_id, b_id = one["id"], two["id"]
        try:
            # AABB pre-filter: a positive box gap is a lower bound on the true distance, so a
            # clearly separated pair is clearance without the expensive exact call. Only when boxes
            # touch/overlap (gap <= tol) do we pay for BRepExtrema + (if in contact) the boolean.
            gap = self._aabb_gap(one["shape"], two["shape"])
            if gap is not None and gap > _DIST_TOL:
                distance, volume = gap, 0.0
            else:
                distance = self._kernel.distance(one["shape"], two["shape"])
                volume = (self._kernel.common_volume(one["shape"], two["shape"])
                          if distance <= _DIST_TOL else 0.0)
        except Exception as exc:  # noqa: BLE001 - a bad pair becomes an id-attributed finding
            logger.warning("interference check failed for %s<>%s: %s", a_id, b_id, exc)
            return {"a": a_id, "b": b_id, "status": "error", "message": str(exc)}
        status, value = self._classifier.classify(distance, volume, dist_tol=_DIST_TOL)
        return {"a": a_id, "b": b_id, "status": status,
                "distance": round(distance, 6),
                "volume": round(value, 6) if status == "interfering" else 0.0}

    def _aabb_gap(self, shape_a: Any, shape_b: Any) -> float | None:
        """Euclidean gap between the two axis-aligned bounding boxes (0.0 if they overlap/touch).

        A box contains its solid, so this gap is a lower bound on the solids' true minimum distance:
        a positive value proves clearance. Per axis the separation is the positive part of the
        low-minus-high on either side; the gap is the norm of the per-axis separations.

        Returns None when the kernel exposes no ``bounding_box`` (a minimal test/analytic kernel):
        the caller then measures the exact distance, so the pre-filter is a pure optimisation that
        never changes a verdict, only skips work when a box gap can prove clearance.
        """
        bbox = getattr(self._kernel, "bounding_box", None)
        if bbox is None:
            return None
        (a_min, a_max) = bbox(shape_a)
        (b_min, b_max) = bbox(shape_b)
        seps = [max(a_min[k] - b_max[k], b_min[k] - a_max[k], 0.0) for k in range(3)]
        return math.sqrt(sum(s * s for s in seps))
