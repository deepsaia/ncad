"""Resolve a fixed face-set keyword against a solid's face descriptors.

The face-side twin of EdgeSelector: a five-word vocabulary (all, top, bottom, vertical,
horizontal) over the face metadata the kernel provides (normal, mid_z). Used by shell
(openings) and draft (faces to taper) until richer selectors (the general Selector) land.
"""

_KEYWORDS = ("all", "top", "bottom", "vertical", "horizontal")
_VERTICAL_NORMAL_Z = 1e-6


class FaceSelector:
    """Selects faces from kernel face descriptors by a fixed keyword."""

    def select(self, face_descriptors: list[dict], keyword: str) -> list:
        """Return the ``handle`` of each face matching ``keyword``.

        :raises ValueError: If ``keyword`` is not one of the supported keywords.
        """
        if keyword not in _KEYWORDS:
            raise ValueError(
                f"unknown face keyword {keyword!r}; expected one of {_KEYWORDS}")
        if keyword == "all":
            return [f["handle"] for f in face_descriptors]
        if keyword == "vertical":
            return [f["handle"] for f in face_descriptors
                    if abs(f["normal"][2]) < _VERTICAL_NORMAL_Z]
        if keyword == "horizontal":
            return [f["handle"] for f in face_descriptors
                    if abs(f["normal"][2]) >= _VERTICAL_NORMAL_Z]
        # top / bottom: the face(s) at the extreme mid_z.
        if not face_descriptors:
            return []
        target = (max(f["mid_z"] for f in face_descriptors) if keyword == "top"
                  else min(f["mid_z"] for f in face_descriptors))
        return [f["handle"] for f in face_descriptors if f["mid_z"] == target]
