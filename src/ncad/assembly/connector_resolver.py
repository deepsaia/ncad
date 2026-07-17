"""Resolve a part's connector specs to ConnectorFrames using the Phase 4 reference layer.

Each connector's ``at`` is a persistent-name / selector ref (Reference.parse + ReferenceResolver)
resolved against the part's element map. A planar face gives a normal+center frame; a cylindrical
face gives an axis frame (axis_location/axis_direction from describe_elements). A ref matching
nothing or an unsupported geometry is an id-attributed issue; that connector is dropped.
"""

import logging

from ncad.assembly.connector_frame import ConnectorFrame
from ncad.refs.element_map import ElementMap
from ncad.refs.reference import Reference
from ncad.refs.reference_resolver import ReferenceResolver

logger = logging.getLogger(__name__)

_PLANAR = frozenset({"plane", "planar"})


class ConnectorResolver:
    """Resolves connector specs to frames against a part's elements."""

    def resolve(self, connectors: list[dict],
                elements: list) -> tuple[dict[str, ConnectorFrame], list[dict]]:
        """Return ({connector_id: ConnectorFrame}, issues)."""
        # A ReferenceResolver over an empty ElementMap: face/selector refs resolve against the
        # passed current_elements, so no feature_shapes seeding is needed here.
        resolver = ReferenceResolver(ElementMap())
        frames: dict[str, ConnectorFrame] = {}
        issues: list[dict] = []
        for spec in connectors:
            cid = spec.get("id", "?")
            frame = self._one(spec, resolver, elements, issues, cid)
            if frame is not None:
                frames[cid] = frame
        return frames, issues

    def _one(self, spec: dict, resolver: ReferenceResolver, elements: list,
             issues: list, cid: str) -> ConnectorFrame | None:
        # A DIRECT-COORDINATE connector: `at_point = [x,y,z]` (+ optional `axis`, `secondary`,
        # `radius`) builds the frame from explicit local coordinates, bypassing face selection. The
        # terse, robust way to place a mechanism connector (name a point, like a datum), avoiding
        # fragile face/area selectors that break when a boolean reshapes a face. Z = axis.
        if spec.get("at_point") is not None:
            point = spec["at_point"]
            axis = spec.get("axis") or (0.0, 0.0, 1.0)
            radius = spec.get("radius")
            return ConnectorFrame.from_axis(
                (float(point[0]), float(point[1]), float(point[2])),
                (float(axis[0]), float(axis[1]), float(axis[2])),
                spec.get("secondary"), spec.get("offset"),
                radius=float(radius) if radius is not None else None)
        at = spec.get("at")
        if not at:
            issues.append({"connector_id": cid,
                           "message": "connector needs an 'at' reference or an 'at_point'"})
            return None
        resolution = resolver.resolve(Reference.parse(at), {}, elements)
        if resolution.error or not resolution.elements:
            issues.append({"connector_id": cid,
                           "message": f"connector {cid!r} ref matched nothing: {at!r}"})
            return None
        element = resolution.elements[0]
        attrs = element.attrs
        geom = attrs.get("geom_type") or attrs.get("type")
        secondary = spec.get("secondary")
        offset = spec.get("offset")
        if geom in _PLANAR and attrs.get("normal") is not None and attrs.get("center") is not None:
            return ConnectorFrame.from_planar(attrs["center"], attrs["normal"], secondary, offset)
        if geom == "cylinder" and attrs.get("axis_location") is not None:
            return ConnectorFrame.from_axis(attrs["axis_location"], attrs["axis_direction"],
                                            secondary, offset, radius=attrs.get("radius"))
        # An edge connector: a tangent frame at the edge midpoint, Z = edge direction (bucket 5.7).
        if element.kind == "edge" and attrs.get("center") is not None:
            direction = attrs.get("edge_direction") or (0.0, 0.0, 1.0)
            return ConnectorFrame.from_edge(attrs["center"], direction, secondary, offset)
        # A vertex/point connector: an origin-only frame at the point.
        if element.kind == "vertex" and attrs.get("center") is not None:
            return ConnectorFrame.from_point(attrs["center"], secondary, offset)
        # A datum connector: a datum plane's normal / a datum axis's direction as Z.
        if geom in ("datum_plane", "datum_axis"):
            origin = attrs.get("center") or attrs.get("axis_location")
            direction = (attrs.get("normal") or attrs.get("axis_direction")
                         or (0.0, 0.0, 1.0))
            if origin is not None:
                return ConnectorFrame.from_datum(origin, direction, secondary, offset)
        issues.append({"connector_id": cid,
                       "message": f"connector {cid!r} is not a planar/cylindrical/edge/point/"
                                  "datum element"})
        return None
