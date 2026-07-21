"""Parse a slice-profile wrapper: which slicer + which slicer config to hand the delegated tool.

ncad does NOT own slicer settings (layer height, temperatures, supports) - those live in a slicer's
own config file, authored in the slicer. A slice profile is a thin WRAPPER that points ncad at that
config and says which slicer(s) to prefer, so the delegation is reproducible and the settings stay
where the fabricator maintains them. This validates the wrapper into a queryable object.

Wrapper shape (JSON)::

    { "config": "petg_0.2mm.ini",         # the slicer's own config, relative to the wrapper
      "slicers": ["orca", "prusa"],        # preference order; default = all known, best first
      "extra_args": ["--support-material"] }  # optional extra CLI flags passed through verbatim
"""

from pathlib import Path

# Known slicers, best-first, used when the wrapper does not pin a preference order.
_DEFAULT_SLICERS = ("orca", "prusa", "cura")


class SlicerProfileError(Exception):
    """A slice profile is missing its config reference or names an unknown slicer."""


class SlicerProfile:
    """A validated slice-profile wrapper: the slicer config path, slicer preference, extra args."""

    def __init__(self, wrapper: dict, base_dir: Path) -> None:
        config = wrapper.get("config")
        if not config:
            raise SlicerProfileError("slice profile needs a 'config' (the slicer's config file)")
        self._config_path = base_dir / str(config)
        slicers = wrapper.get("slicers") or list(_DEFAULT_SLICERS)
        unknown = [s for s in slicers if s not in _DEFAULT_SLICERS]
        if unknown:
            raise SlicerProfileError(
                f"unknown slicer(s) {unknown}; known: {list(_DEFAULT_SLICERS)}")
        self._slicers = tuple(slicers)
        self._extra_args = [str(a) for a in (wrapper.get("extra_args") or [])]

    @property
    def config_path(self) -> Path:
        """Path to the slicer's own config file (resolved against the wrapper's directory)."""
        return self._config_path

    @property
    def slicers(self) -> tuple[str, ...]:
        """The slicer preference order to try (best first)."""
        return self._slicers

    @property
    def extra_args(self) -> list[str]:
        """Extra CLI flags passed through to the slicer verbatim."""
        return list(self._extra_args)
