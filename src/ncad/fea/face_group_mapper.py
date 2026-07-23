"""Map an ncad face selector to the gmsh surface tags it covers (pure; no gmsh import).

The spec's original plan correlated kernel faces to gmsh surfaces by centroid/area/normal, but
gmsh's OCC re-import of a STEP splits and renumbers faces, so the two frames do not line up. The
robust approach (the spec's authorized contingency) is to evaluate the selector keyword DIRECTLY
over the gmsh surfaces' own geometry. This class does that over plain descriptor dicts that
GmshMesher extracts, so it stays pure and unit-testable without gmsh. Semantics mirror
ncad.ops.face_selector.FaceSelector: all / top / bottom / vertical / horizontal.
"""

import logging

logger = logging.getLogger(__name__)

_KEYWORDS = ("all", "top", "bottom", "vertical", "horizontal")
_VERTICAL_NORMAL_Z = 1e-6
_Z_TOL = 1e-6


class FaceGroupError(Exception):
    """A face selector is malformed, uses an unknown keyword, or matches no surface."""


class FaceGroupMapper:
    """Selects gmsh surface tags for an analysis ``where`` selector over surface descriptors."""

    def select(self, surfaces: list[dict], where: dict) -> list[int]:
        """Return the gmsh surface tags matching ``where`` (``{"face": keyword}``).

        :param surfaces: descriptors ``{tag, com, normal, zmin, zmax, area}`` from GmshMesher.
        :raises FaceGroupError: on a malformed/unknown selector or an empty match.
        """
        keyword = where.get("face") if isinstance(where, dict) else None
        if keyword not in _KEYWORDS:
            raise FaceGroupError(
                f"selector {where!r} must be {{'face': one of {list(_KEYWORDS)}}}")
        tags = self._match(surfaces, keyword)
        if not tags:
            raise FaceGroupError(f"selector {where!r} matched no surface")
        return tags

    def _match(self, surfaces: list[dict], keyword: str) -> list[int]:
        """The tags matching ``keyword`` (may be empty; the caller raises on empty)."""
        if keyword == "all":
            return [s["tag"] for s in surfaces]
        if keyword == "vertical":
            return [s["tag"] for s in surfaces if abs(s["normal"][2]) < _VERTICAL_NORMAL_Z]
        horizontals = [s for s in surfaces if abs(s["normal"][2]) >= _VERTICAL_NORMAL_Z]
        if keyword == "horizontal":
            return [s["tag"] for s in horizontals]
        if not horizontals:
            return []
        target = (max(s["com"][2] for s in horizontals) if keyword == "top"
                  else min(s["com"][2] for s in horizontals))
        return [s["tag"] for s in horizontals if abs(s["com"][2] - target) <= _Z_TOL]
