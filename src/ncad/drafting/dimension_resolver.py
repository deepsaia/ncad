"""Measure a dimension from projected 2D geometry (the value + its witness/dimension-line points).

The ViewProjector hands this resolver the 2D polylines of the geometry a dimension references (found
by resolving the dimension's selector against the model, then projecting those edges into the view).
This class turns those polylines into a measured value plus the geometry needed to draw the
dimension (witness lines, the dimension line, the text anchor). Pure arithmetic; no kernel. One
class.
"""

import math


class DimensionResolver:
    """Computes a dimension's value + draw geometry from projected 2D polylines."""

    def measure_linear(self, edges: list) -> dict:
        """Distance between two projected features (each a polyline of ``(x, y)`` points).

        The value is the minimum distance between the two point sets' centroids projected apart; for
        the common parallel-edge case this is the perpendicular gap. Also returns the two anchor
        points for the witness lines + a mid dimension-line point.
        """
        first, second = edges[0], edges[1]
        a = _centroid(first)
        b = _centroid(second)
        value = _distance(a, b)
        mid = ((a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0)
        return {"value": round(value, 6),
                "geometry": {"from": a, "to": b, "text_anchor": mid}}

    def measure_diameter(self, circle: list) -> dict:
        """Diameter of a projected circle sampled as a polyline of ``(x, y)`` points."""
        center, radius = _fit_circle(circle)
        return {"value": round(2.0 * radius, 6),
                "geometry": {"center": center, "radius": radius}}

    def measure_radius(self, circle: list) -> dict:
        """Radius of a projected circle sampled as a polyline of ``(x, y)`` points."""
        center, radius = _fit_circle(circle)
        return {"value": round(radius, 6),
                "geometry": {"center": center, "radius": radius}}


def _centroid(points: list) -> tuple[float, float]:
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return (sum(xs) / len(xs), sum(ys) / len(ys))


def _distance(a: tuple[float, float], b: tuple[float, float]) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def _fit_circle(points: list) -> tuple[tuple[float, float], float]:
    """Center + radius of a circle sampled as ``points``: centroid + mean point distance."""
    center = _centroid(points)
    radius = sum(_distance(p, center) for p in points) / len(points)
    return center, radius
