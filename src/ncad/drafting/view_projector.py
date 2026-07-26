"""Run a drawing view's hidden-line-removal projection over a built model shape.

Maps each view (base / projected / isometric) to a view DIRECTION + up axis, then calls the kernel's
``hlr_view`` to get the visible + hidden 2D edges. A base view projects onto a named plane (its
normal is the view direction); a projected view derives its direction from a parent base view plus a
relative direction (up / down / left / right, third-angle); an isometric view looks along a body
diagonal. Depends only on the swappable kernel. One class.
"""

from typing import Any

# A base view names the plane it projects ONTO; the view direction is that plane's normal (looking
# toward the origin along -normal). Front = the XZ plane (look along -Y), Top = XY (look along -Z),
# Right = YZ (look along -X). These are the standard third-angle stations.
_BASE_DIRECTIONS = {
    "XY": (0.0, 0.0, -1.0),   # top / plan
    "XZ": (0.0, -1.0, 0.0),   # front
    "YZ": (-1.0, 0.0, 0.0),   # right / side
}

# A projected view rotates the parent's direction 90 degrees about a sheet axis (third-angle). We
# express the rotation as which world axis the child looks along relative to the parent's frame.
_PROJECTED_ROTATION = {"up", "down", "left", "right"}

_ISO_DIRECTION = (-1.0, -1.0, -1.0)


class ViewProjector:
    """Projects a model shape into a drawing view's 2D visible + hidden edges via kernel HLR."""

    def __init__(self, kernel: Any) -> None:
        """:param kernel: the geometry kernel providing ``hlr_view``."""
        self._kernel = kernel

    def project(self, shape: Any, view: dict, parent: dict | None = None) -> dict:
        """Return ``{"visible":[...],"hidden":[...]}`` 2D edges for ``view`` of ``shape``.

        :param shape: the built model solid.
        :param view: the view dict (``type`` base/projected/iso + its parameters).
        :param parent: the parent view dict, required when ``view`` is projected.
        """
        direction, up = self._direction_for(view, parent)
        return self._kernel.hlr_view(shape, direction, up)

    def project_edges(self, edges: list, view: dict, parent: dict | None = None) -> list:
        """Project specific model ``edges`` into ``view``'s 2D frame (for dimension attachment).

        Uses the same view direction as :meth:`project`, so the returned polylines align with the
        view's HLR geometry.
        """
        direction, up = self._direction_for(view, parent)
        return self._kernel.project_edges_to_view(edges, direction, up)

    def _direction_for(self, view: dict, parent: dict | None) -> tuple[tuple, tuple | None]:
        view_type = view["type"]
        if view_type == "iso":
            return (_ISO_DIRECTION, None)
        if view_type == "base":
            projection = str(view.get("projection", "XZ")).upper()
            if projection not in _BASE_DIRECTIONS:
                raise ValueError(f"base view '{view['id']}' has unknown projection {projection!r}")
            return (_BASE_DIRECTIONS[projection], None)
        # projected: rotate the parent base direction 90 degrees for the requested station.
        if parent is None:
            raise ValueError(f"projected view '{view['id']}' needs a parent view")
        base = str(parent.get("projection", "XZ")).upper()
        parent_dir = _BASE_DIRECTIONS.get(base)
        if parent_dir is None:
            raise ValueError(
                f"projected view '{view['id']}' parent has unknown projection {base!r}")
        relative = str(view.get("direction", "up")).lower()
        if relative not in _PROJECTED_ROTATION:
            raise ValueError(f"projected view '{view['id']}' has unknown direction {relative!r}")
        return (_rotate_station(parent_dir, relative), None)


def _rotate_station(parent_dir: tuple, relative: str) -> tuple:
    """The view direction for a projected station relative to a parent base direction.

    Third-angle placement: a `top` (above front) looks straight down (-Z); `right` looks along -X;
    mirrored for `down`/`left`. This maps the four in-sheet stations to their standard world axes,
    deriving from the parent so a rotated base still yields coherent orthographic neighbours.
    """
    dx, dy, dz = parent_dir
    if relative in ("up", "down"):
        # Above/below the front view: the plan direction, straight down/up.
        return (0.0, 0.0, -1.0) if relative == "up" else (0.0, 0.0, 1.0)
    # Left/right of the front view: the side direction, along -X/+X.
    return (-1.0, 0.0, 0.0) if relative == "right" else (1.0, 0.0, 0.0)
