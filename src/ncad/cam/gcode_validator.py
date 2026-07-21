"""Validate a slicer's G-code output and extract a few summary facts. Pure text analysis.

A slicer is an external tool ncad delegates to; this checks that what it produced is actually
usable G-code, rather than trusting the exit code. The checks are the minimal necessary conditions
for real toolpath output (RS-274 vocabulary):

- the file is non-empty;
- it contains motion commands (``G0``/``G1`` linear moves) - the actual toolpath;
- at least one axis word (X/Y/Z) appears on a motion line.

It also extracts summary facts an agent/report can use: line count, motion-command count, layer
count (slicer ``;LAYER`` / ``; layer`` markers), and whether extrusion (an ``E`` word) is present.
Returns a structured result; raises nothing (a malformed file is reported as ``valid=False``). One
class; the analysis is pure over the text.
"""

import re

# A G-code motion command at the start of a line (after optional whitespace): G0 or G1, then a
# non-digit boundary so G10/G17/G28 etc. do not count as linear moves.
_MOTION = re.compile(r"^\s*G[01](?![0-9])", re.IGNORECASE)
# A layer marker as emitted by common slicers: ``;LAYER:n`` (Cura) or ``; layer n`` (Prusa/Orca).
_LAYER = re.compile(r"^\s*;\s*layer[:\s]", re.IGNORECASE)
_AXIS_WORD = re.compile(r"[XYZ]-?\d", re.IGNORECASE)
_EXTRUDE_WORD = re.compile(r"\bE-?\d", re.IGNORECASE)


class GcodeValidator:
    """Checks that slicer output is usable G-code and summarizes it (lines/moves/layers)."""

    def validate(self, gcode_text: str) -> dict:
        """Return ``{valid, reasons, stats}`` for ``gcode_text``.

        ``valid`` is True when the text is non-empty, has at least one motion command, and at least
        one motion line carries an axis word. ``reasons`` lists why it failed (empty when valid).
        ``stats`` = ``{lines, motion_commands, layers, has_extrusion}``.
        """
        lines = gcode_text.splitlines()
        motion_lines = [ln for ln in lines if _MOTION.search(ln)]
        layers = sum(1 for ln in lines if _LAYER.search(ln))
        has_axis = any(_AXIS_WORD.search(ln) for ln in motion_lines)
        has_extrusion = any(_EXTRUDE_WORD.search(ln) for ln in motion_lines)
        reasons: list[str] = []
        if not gcode_text.strip():
            reasons.append("g-code output is empty")
        if not motion_lines:
            reasons.append("no G0/G1 motion commands found (not a toolpath)")
        elif not has_axis:
            reasons.append("motion commands carry no X/Y/Z axis words")
        return {
            "valid": not reasons,
            "reasons": reasons,
            "stats": {
                "lines": len(lines),
                "motion_commands": len(motion_lines),
                "layers": layers,
                "has_extrusion": has_extrusion,
            },
        }
