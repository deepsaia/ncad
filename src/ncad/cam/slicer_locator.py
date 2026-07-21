"""Locate an installed slicer binary and describe its CLI dialect. No slicer is bundled.

The open-source slicers (OrcaSlicer, PrusaSlicer, CuraEngine, Slic3r) are desktop/CLI apps, not pip
packages, so ncad cannot bundle one: it DELEGATES to whatever the user installed. This finds the
first available slicer from a preference order (via ``shutil.which``, trying each slicer's known
executable names) and returns its command dialect. Because ncad only shells out to a separate
binary (never links it), the slicers' AGPL/GPL licensing does not affect ncad.

Each dialect describes how to build the argv: OrcaSlicer/PrusaSlicer/Slic3r share the Slic3r-derived
``--load <cfg> --export-gcode --output <out> <stl>`` form; CuraEngine uses ``slice -j <cfg> -l <stl>
-o <out>``. One class.
"""

import shutil

# slicer key -> (candidate executable names, dialect). Executable names cover the common install
# spellings across macOS/Linux/Windows-in-PATH.
_SLICERS: dict[str, tuple[tuple[str, ...], str]] = {
    "orca": (("orca-slicer", "OrcaSlicer", "orcaslicer"), "slic3r"),
    "prusa": (("prusa-slicer", "PrusaSlicer", "prusaslicer"), "slic3r"),
    "cura": (("CuraEngine", "curaengine"), "cura"),
}


class SlicerLocator:
    """Finds the first installed slicer from a preference order; reports its binary + dialect."""

    def locate(self, preference: tuple[str, ...]) -> dict | None:
        """Return ``{slicer, binary, dialect}`` for the first available slicer, or None if none.

        ``preference`` is the slicer keys to try, best first. A slicer is available when one of its
        candidate executables is found on PATH.
        """
        for slicer in preference:
            names, dialect = _SLICERS.get(slicer, ((), ""))
            for name in names:
                found = shutil.which(name)
                if found:
                    return {"slicer": slicer, "binary": found, "dialect": dialect}
        return None

    def argv(self, binary: str, dialect: str, config: str, stl: str, out: str,
             extra_args: list[str]) -> list[str]:
        """Build the slicer command line for ``dialect`` (slic3r-derived or cura)."""
        if dialect == "cura":
            return [binary, "slice", "-j", config, "-l", stl, "-o", out, *extra_args]
        # slic3r-derived (Orca/Prusa/Slic3r): load config, export g-code to the output path.
        return [binary, "--load", config, "--export-gcode", "--output", out, *extra_args, stl]
