"""Pairwise static interference / clearance over an assembly's placed instances (bucket 5.6).

For each unordered pair of world-placed instance solids: measure the kernel distance; when the
solids are within tolerance of contact, measure the boolean-common volume; classify into
clearance / touching / interfering (InterferenceClassifier). common_volume is only computed for
close pairs (a positive-clearance pair skips the more expensive boolean). A measurement failure on
a pair is an id-attributed `error` finding; the rest continue (partial-result discipline).
"""

import logging
from typing import Any

from ncad.assembly.interference_classifier import InterferenceClassifier

logger = logging.getLogger(__name__)

_DIST_TOL = 1e-6


class InterferenceChecker:
    """Runs the kernel distance + common-volume over instance pairs and classifies each."""

    def __init__(self, kernel: Any) -> None:
        self._kernel = kernel
        self._classifier = InterferenceClassifier()

    def check(self, placed: list[dict]) -> list[dict]:
        """Return one finding per instance pair: {a, b, status, distance, volume}."""
        findings: list[dict] = []
        for i in range(len(placed)):
            for j in range(i + 1, len(placed)):
                findings.append(self._pair(placed[i], placed[j]))
        return findings

    def _pair(self, one: dict, two: dict) -> dict:
        a_id, b_id = one["id"], two["id"]
        try:
            distance = self._kernel.distance(one["shape"], two["shape"])
            # Only pay for the boolean when the solids are actually in contact.
            volume = (self._kernel.common_volume(one["shape"], two["shape"])
                      if distance <= _DIST_TOL else 0.0)
        except Exception as exc:  # noqa: BLE001 - a bad pair becomes an id-attributed finding
            logger.warning("interference check failed for %s<>%s: %s", a_id, b_id, exc)
            return {"a": a_id, "b": b_id, "status": "error", "message": str(exc)}
        status, value = self._classifier.classify(distance, volume, dist_tol=_DIST_TOL)
        return {"a": a_id, "b": b_id, "status": status,
                "distance": round(distance, 6),
                "volume": round(value, 6) if status == "interfering" else 0.0}
