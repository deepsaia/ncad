"""Classify a pair of placed solids as clearance / touching / interfering (bucket 5.6).

Pure decision over two kernel measurements: the min distance and the boolean-common volume.
Distance alone cannot separate a flush MATE (distance 0, no shared volume) from a real OVERLAP
(distance 0, shared volume > 0), so the common volume is the arbiter. Positive distance is a
clearance gap. No kernel here (the checker supplies the measurements); trivially unit-testable.
"""


class InterferenceClassifier:
    """Turns (distance, common_volume) into an interference verdict."""

    def classify(self, distance: float, common_volume: float,
                 dist_tol: float = 1e-6, vol_tol: float = 1e-6) -> tuple[str, float]:
        """Return (status, value): clearance(distance) / interfering(volume) / touching(0.0)."""
        if distance > dist_tol:
            return "clearance", distance
        if common_volume > vol_tol:
            return "interfering", common_volume
        return "touching", 0.0
