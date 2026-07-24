"""Lower sugar sketch entities to primitive point/line/arc entities before solving.

`polyline`, `slot`, and regular `polygon` are author conveniences; the solver and wire
builder only understand primitive `point`/`line`/`arc`/`circle` entities. This class
expands the sugar deterministically (child ids are ``<id>/<tag><index>``, no randomness)
and passes primitives through unchanged. Child-point seeds are derived from the
referenced points' ``at`` seeds plus the sugar's own numeric seeds; the solver then
refines them under any constraints.
"""

import logging
import math

from ncad.assembly.cam_profile import CamProfile
from ncad.sketch.airfoil_profile import AirfoilProfile
from ncad.sketch.gear_profile import GearProfile
from ncad.sketch.geneva_wheel import GenevaWheel
from ncad.sketch.id_padding import PaddedNaming

logger = logging.getLogger(__name__)

_PASSTHROUGH = frozenset({"point", "line", "arc", "circle"})


class EntityExpander:
    """Expands sugar entities (polyline/slot/polygon) into primitives."""

    def __init__(self) -> None:
        self._naming = PaddedNaming()

    def expand(self, entities: list[dict], base_dir: str | None = None) -> list[dict]:
        """Return a new entity list with sugar lowered to primitives.

        ``base_dir`` is the referring document's directory, used only by the ``airfoil`` ``dat``
        form to resolve its coordinate file; every other entity ignores it.
        """
        by_id = {e["id"]: e for e in entities}
        out: list[dict] = []
        for entity in entities:
            kind = entity.get("type")
            if kind in _PASSTHROUGH:
                out.append(entity)
            elif kind == "airfoil":
                out.extend(self._expand_airfoil(entity, base_dir))
            elif kind == "polyline":
                out.extend(self._expand_polyline(entity))
            elif kind == "polygon":
                out.extend(self._expand_polygon(entity, by_id))
            elif kind == "slot":
                out.extend(self._expand_slot(entity, by_id))
            elif kind == "arc_polar":
                out.extend(self._expand_arc_polar(entity, by_id))
            elif kind == "involute_gear":
                out.extend(self._expand_involute_gear(entity, by_id))
            elif kind == "cam_profile":
                out.extend(self._expand_cam_profile(entity, by_id))
            elif kind == "geneva_wheel":
                out.extend(self._expand_geneva_wheel(entity, by_id))
            else:
                logger.debug("passing through unknown entity type %r", kind)
                out.append(entity)
        return out

    def _expand_airfoil(self, entity: dict, base_dir: str | None) -> list[dict]:
        """An airfoil (naca | dat) -> fixed section points + one interpolated spline through them.

        The section is generated/parsed + scaled to chord by AirfoilProfile; the points are fixed
        (well-constrained by construction, like geneva/offset-derived geometry). ``at`` (default
        [0, 0]) offsets the leading edge on the sketch plane. A bad airfoil raises AirfoilParamError
        (like the other sugar profiles that cannot produce valid geometry).
        """
        aid = entity["id"]
        pts = AirfoilProfile().points(entity, base_dir)
        ox, oy = entity.get("at", [0.0, 0.0])
        point_ids = self._naming.child_ids(f"{aid}/p", len(pts))
        result: list[dict] = [
            {"id": point_ids[i], "type": "point", "at": [ox + x, oy + y], "fixed": True}
            for i, (x, y) in enumerate(pts)]
        result.append({"id": aid, "type": "interpolated", "points": point_ids})
        return result

    def _expand_polyline(self, entity: dict) -> list[dict]:
        """A polyline is an open chain of lines between consecutive point ids."""
        points = entity["points"]
        line_ids = self._naming.child_ids(f"{entity['id']}/l", len(points) - 1)
        return [{"id": line_ids[i], "type": "line", "p1": points[i], "p2": points[i + 1]}
                for i in range(len(points) - 1)]

    def _expand_polygon(self, entity: dict, by_id: dict) -> list[dict]:
        """A regular polygon: n points on a circle about the center, joined by n lines."""
        sid = entity["id"]
        sides = int(entity["sides"])
        radius = float(entity["r"])
        cx, cy = _seed_of(by_id, entity["center"])
        point_ids = self._naming.child_ids(f"{sid}/p", sides)
        line_ids = self._naming.child_ids(f"{sid}/l", sides)
        result: list[dict] = []
        for i in range(sides):
            angle = 2.0 * math.pi * i / sides
            result.append({"id": point_ids[i], "type": "point",
                           "at": [cx + radius * math.cos(angle), cy + radius * math.sin(angle)]})
        for i in range(sides):
            result.append({"id": line_ids[i], "type": "line",
                           "p1": point_ids[i], "p2": point_ids[(i + 1) % sides]})
        return result

    def _expand_arc_polar(self, entity: dict, by_id: dict) -> list[dict]:
        """A polar arc: center + radius + start_angle + sweep >> a three-point arc.

        Radius and the angles fully define the arc, so the two derived endpoint points are
        emitted as ``fixed`` primitives (their positions are locked at the computed radius +
        angle, exactly like offset-derived geometry). This makes an ``arc_polar`` sketch
        well-constrained by construction: the author does not have to pin each endpoint. The
        endpoints are computed relative to the center's seed; pin the center too (or the arc
        rides its seed) for a fully-locked feature.
        """
        aid = entity["id"]
        cx, cy = _seed_of(by_id, entity["center"])
        radius = float(entity["radius"])
        start_angle = math.radians(float(entity["start_angle"]))
        end_angle = math.radians(float(entity["start_angle"]) + float(entity["sweep"]))
        start = (cx + radius * math.cos(start_angle), cy + radius * math.sin(start_angle))
        end = (cx + radius * math.cos(end_angle), cy + radius * math.sin(end_angle))
        return [
            {"id": f"{aid}/start", "type": "point", "at": [start[0], start[1]], "fixed": True},
            {"id": f"{aid}/end", "type": "point", "at": [end[0], end[1]], "fixed": True},
            {"id": aid, "type": "arc", "center": entity["center"],
             "start": f"{aid}/start", "end": f"{aid}/end"},
        ]

    def _expand_involute_gear(self, entity: dict, by_id: dict) -> list[dict]:
        """An involute gear (external/internal/rack) -> a closed loop of lines from GearProfile.

        GearProfile.outline() gives the tooth outline as [x, y] points (about the origin for a
        radial gear, along +x for a rack); offset by the (optional) center point's seed and joined
        consecutively with a closing line, so the whole gear is a closed profile the wire builder +
        extrude consume. Passes through the full gear vocabulary (gear_type, profile_shift,
        backlash, length) so the same generator that drives the mesh coupling draws the body. The
        points are ``fixed`` (locked at the computed coordinates), well-constrained by construction.
        """
        gid = entity["id"]
        profile = GearProfile(
            module=float(entity["module"]), teeth=int(entity["teeth"]),
            pressure_angle=float(entity.get("pressure_angle", 20.0)),
            gear_type=entity.get("gear_type", "external"),
            profile_shift=float(entity.get("profile_shift", 0.0)),
            backlash=float(entity.get("backlash", 0.0)),
            length=float(entity.get("length", 0.0)),
            phase=float(entity.get("phase", 0.0)))
        cx, cy = _seed_of(by_id, entity["center"]) if entity.get("center") else (0.0, 0.0)
        outline = profile.outline()
        n = len(outline)
        point_ids = self._naming.child_ids(f"{gid}/p", n)
        line_ids = self._naming.child_ids(f"{gid}/l", n)
        result: list[dict] = []
        for i, (x, y) in enumerate(outline):
            result.append({"id": point_ids[i], "type": "point",
                           "at": [cx + x, cy + y], "fixed": True})
        for i in range(n):
            result.append({"id": line_ids[i], "type": "line",
                           "p1": point_ids[i], "p2": point_ids[(i + 1) % n]})
        return result

    def _expand_cam_profile(self, entity: dict, by_id: dict) -> list[dict]:
        """A cam plate outline -> a closed loop of lines from CamProfile.

        Draws the cam body from the SAME cam profile that drives the follower
        (CamProfile.profile_points), so the drawn base circle + nose lift the follower in sync. The
        entity carries the coupling's ``profile`` keys directly (either the legacy
        ``law``/``lift``/``lobes`` form or the segmented ``segments`` form); ``id``/``type``/
        ``center`` are stripped. Derived points are ``fixed`` (locked at the computed profile
        coordinates), well-constrained by construction.
        """
        cid = entity["id"]
        profile = {k: v for k, v in entity.items() if k not in ("id", "type", "center")}
        cam = CamProfile.from_profile(profile)
        cx, cy = _seed_of(by_id, entity["center"]) if entity.get("center") else (0.0, 0.0)
        outline = cam.profile_points()
        n = len(outline)
        point_ids = self._naming.child_ids(f"{cid}/p", n)
        line_ids = self._naming.child_ids(f"{cid}/l", n)
        result: list[dict] = [
            {"id": point_ids[i], "type": "point", "at": [cx + x, cy + y], "fixed": True}
            for i, (x, y) in enumerate(outline)]
        result += [{"id": line_ids[i], "type": "line",
                    "p1": point_ids[i], "p2": point_ids[(i + 1) % n]} for i in range(n)]
        return result

    def _expand_geneva_wheel(self, entity: dict, by_id: dict) -> list[dict]:
        """A Geneva star wheel -> a closed loop of lines from GenevaWheel.outline().

        Draws the slotted wheel from the SAME GenevaWheel that drives the coupling (one source of
        truth). Derived points are ``fixed`` (locked at the computed coordinates), well-constrained
        by construction. The entity carries slots/crank_radius (+ optional pin_radius/clearance);
        ``id``/``type``/``center`` are stripped.
        """
        gid = entity["id"]
        wheel = GenevaWheel(
            slots=int(entity["slots"]), crank_radius=float(entity["crank_radius"]),
            pin_radius=float(entity.get("pin_radius", 3.0)),
            slot_clearance=float(entity.get("slot_clearance", 0.4)))
        cx, cy = _seed_of(by_id, entity["center"]) if entity.get("center") else (0.0, 0.0)
        outline = wheel.outline()
        n = len(outline)
        point_ids = self._naming.child_ids(f"{gid}/p", n)
        line_ids = self._naming.child_ids(f"{gid}/l", n)
        result: list[dict] = [
            {"id": point_ids[i], "type": "point", "at": [cx + x, cy + y], "fixed": True}
            for i, (x, y) in enumerate(outline)]
        result += [{"id": line_ids[i], "type": "line",
                    "p1": point_ids[i], "p2": point_ids[(i + 1) % n]} for i in range(n)]
        return result

    def _expand_slot(self, entity: dict, by_id: dict) -> list[dict]:
        """A straight slot: two side lines plus two semicircular end caps.

        Given center points a (p1) and b (p2) and a width, the four corner points sit at
        +/- half-width perpendicular to the a->b axis. The caps are CCW arcs whose mids
        bulge outward (arc a mid points away from b; arc b mid points away from a).
        """
        sid = entity["id"]
        ax, ay = _seed_of(by_id, entity["p1"])
        bx, by = _seed_of(by_id, entity["p2"])
        half = float(entity["width"]) / 2.0
        px, py = _unit_perpendicular(ax, ay, bx, by)
        ox, oy = px * half, py * half
        # Corner points and the two arc centers (the original a, b positions).
        pts = {
            "ap": (ax + ox, ay + oy), "am": (ax - ox, ay - oy),
            "bp": (bx + ox, by + oy), "bm": (bx - ox, by - oy),
            "ca": (ax, ay), "cb": (bx, by),
        }
        result = [{"id": f"{sid}/{name}", "type": "point", "at": [x, y]}
                  for name, (x, y) in pts.items()]
        result.append({"id": f"{sid}/top", "type": "line",
                       "p1": f"{sid}/ap", "p2": f"{sid}/bp"})
        result.append({"id": f"{sid}/bottom", "type": "line",
                       "p1": f"{sid}/am", "p2": f"{sid}/bm"})
        result.append({"id": f"{sid}/cap_b", "type": "arc", "center": f"{sid}/cb",
                       "start": f"{sid}/bm", "end": f"{sid}/bp"})
        result.append({"id": f"{sid}/cap_a", "type": "arc", "center": f"{sid}/ca",
                       "start": f"{sid}/ap", "end": f"{sid}/am"})
        return result


def _seed_of(by_id: dict, point_id: str) -> tuple[float, float]:
    """The ``at`` seed of a referenced point entity (defaults to origin)."""
    entity = by_id.get(point_id, {})
    at = entity.get("at", [0.0, 0.0])
    return float(at[0]), float(at[1])


def _unit_perpendicular(ax: float, ay: float, bx: float, by: float) -> tuple[float, float]:
    """A unit vector perpendicular to a->b (defaults to +Y for a degenerate axis)."""
    dx, dy = bx - ax, by - ay
    length = math.hypot(dx, dy)
    if length < 1e-12:
        return 0.0, 1.0
    return -dy / length, dx / length
