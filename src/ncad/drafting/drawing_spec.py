"""Parse + validate a .drawing.hocon document against its own internal references.

A drawing is an overlay on a built part or assembly: it declares a sheet, a set of views (base /
projected / isometric), dimensions that reference model geometry via selectors, and annotations.
This spec resolves that document and validates the references it can check WITHOUT the model: every
projected view names an existing parent view, every dimension names an existing view, and every
selector string is syntactically valid. Model-geometry resolution (does the selector match an edge)
happens later, at build time, against the element map.

A bad reference here is an authoring error, not validation data, so it raises DrawingSpecError. One
class.
"""

from ncad.refs.selector import Selector
from ncad.refs.selector_error import SelectorError

_VIEW_TYPES = ("base", "projected", "iso")
_DIMENSION_TYPES = ("linear", "diameter", "radius")


class DrawingSpecError(ValueError):
    """Raised when a drawing document's internal references do not resolve or a selector is bad."""


class DrawingSpec:
    """The resolved, self-consistent contents of a .drawing.hocon (source, sheet, views, dims)."""

    def __init__(self, document: dict) -> None:
        """Parse + validate ``document['drawing']``.

        :param document: the loaded .drawing.hocon document dict.
        :raises DrawingSpecError: on a missing source, an unknown view/parent reference, an unknown
            view type, or a malformed dimension selector.
        """
        drawing = document.get("drawing")
        if not drawing:
            raise DrawingSpecError("document has no 'drawing' block")
        self._source = self._parse_source(drawing)
        self._sheet = dict(drawing.get("sheet") or {})
        self._views = self._parse_views(drawing.get("views") or [])
        self._view_ids = {view["id"] for view in self._views}
        self._dimensions = self._parse_dimensions(drawing.get("dimensions") or [])
        self._annotations = self._parse_annotations(drawing.get("annotations") or [])
        self._title_block = dict(drawing.get("title_block") or {})

    @property
    def source(self) -> tuple[str, str]:
        """The referenced model as ``(kind, path)`` where kind is ``part`` or ``assembly``."""
        return self._source

    @property
    def sheet(self) -> dict:
        """The sheet block (size + orientation)."""
        return self._sheet

    @property
    def views(self) -> list[dict]:
        """The views, each ``{id, type, ...}``."""
        return self._views

    @property
    def dimensions(self) -> list[dict]:
        """The dimensions, each ``{view, type, ...}``."""
        return self._dimensions

    @property
    def annotations(self) -> list[dict]:
        """The annotations, each ``{view, at, text}``."""
        return self._annotations

    @property
    def title_block(self) -> dict:
        """The title-block block (title, drawn_by, scale, ...)."""
        return self._title_block

    def _parse_source(self, drawing: dict) -> tuple[str, str]:
        if drawing.get("part"):
            return ("part", str(drawing["part"]))
        if drawing.get("assembly"):
            return ("assembly", str(drawing["assembly"]))
        raise DrawingSpecError("drawing needs a 'part' or 'assembly' source")

    def _parse_views(self, raw: list) -> list[dict]:
        views: list[dict] = []
        ids: set[str] = set()
        for entry in raw:
            view_id = entry.get("id")
            if not view_id:
                raise DrawingSpecError("each view needs an 'id'")
            view_type = entry.get("type")
            if view_type not in _VIEW_TYPES:
                raise DrawingSpecError(
                    f"view '{view_id}' has unknown type {view_type!r}; known: {_VIEW_TYPES}")
            views.append(dict(entry))
            ids.add(str(view_id))
        # Validate projected-view parents after all ids are known (a parent may appear later).
        for view in views:
            if view["type"] == "projected":
                parent = view.get("from")
                if parent not in ids:
                    raise DrawingSpecError(
                        f"projected view '{view['id']}' references unknown parent {parent!r}")
        return views

    def _parse_dimensions(self, raw: list) -> list[dict]:
        selector = Selector()
        dimensions: list[dict] = []
        for entry in raw:
            view = entry.get("view")
            if view not in self._view_ids:
                raise DrawingSpecError(
                    f"dimension references unknown view {view!r}")
            if entry.get("type") not in _DIMENSION_TYPES:
                raise DrawingSpecError(
                    f"dimension in view '{view}' has unknown type {entry.get('type')!r}")
            for key in ("between", "of"):
                if entry.get(key):
                    _validate_selector(selector, str(entry[key]))
            dimensions.append(dict(entry))
        return dimensions

    def _parse_annotations(self, raw: list) -> list[dict]:
        annotations: list[dict] = []
        for entry in raw:
            view = entry.get("view")
            if view not in self._view_ids:
                raise DrawingSpecError(f"annotation references unknown view {view!r}")
            annotations.append(dict(entry))
        return annotations


def _validate_selector(selector: Selector, text: str) -> None:
    """Parse a selector string against an empty element set to check its syntax only."""
    try:
        selector.select(text, [])
    except SelectorError as exc:
        raise DrawingSpecError(f"malformed dimension selector {text!r}: {exc}") from exc
