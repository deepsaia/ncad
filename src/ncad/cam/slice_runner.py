"""Slice an STL to G-code by delegating to an installed slicer; report honestly if none is present.

The CAM delegation seam ("never a solver we write"): ncad finds an installed slicer, hands it the
STL + the profile's slicer config, and validates the G-code it produces. It DELIBERATELY stops at
G-code - printer/LAN control is out of ncad's scope. When no slicer is installed, or the slicer
fails, or its output is not valid G-code, the run is reported as SKIPPED/FAILED with the reason
(the delegation-report discipline: a missing external tool is "skipped", never a silent "pass").

One class. The subprocess invocation is isolated in ``_run`` so it is the single mockable seam.
"""

import logging
import subprocess
from pathlib import Path

from ncad.cam.gcode_validator import GcodeValidator
from ncad.cam.slicer_locator import SlicerLocator
from ncad.cam.slicer_profile import SlicerProfile

logger = logging.getLogger(__name__)

# A slicer can be slow on a big model; cap the delegated call so a hang is reported, not infinite.
_TIMEOUT_SECONDS = 600


class SliceRunner:
    """Delegates STL->G-code to an installed slicer and returns a structured slice report."""

    def __init__(self, locator: SlicerLocator | None = None) -> None:
        self._locator = locator or SlicerLocator()
        self._validator = GcodeValidator()

    def slice(self, stl_path: str, profile: SlicerProfile, out_path: str) -> dict:
        """Slice ``stl_path`` with ``profile`` into ``out_path``; return the slice report.

        Report: ``{status, slicer, artifact, checks, skipped, stats, reasons}`` where ``status`` is
        ``generated`` | ``skipped`` | ``failed``. ``skipped`` when no slicer installed; ``failed``
        when the slicer errored or produced non-G-code. Never raises for an absent/failing tool.
        """
        located = self._locator.locate(profile.slicers)
        if located is None:
            return _report("skipped", None, None,
                           skipped=[f"no slicer installed (tried {list(profile.slicers)})"])
        if not profile.config_path.is_file():
            return _report("failed", located["slicer"], None,
                           reasons=[f"slicer config not found: {profile.config_path}"])
        argv = self._locator.argv(
            located["binary"], located["dialect"], str(profile.config_path), stl_path,
            out_path, profile.extra_args)
        try:
            completed = self._run(argv)
        except (OSError, subprocess.SubprocessError) as exc:
            return _report("failed", located["slicer"], None,
                           reasons=[f"slicer invocation failed: {exc}"])
        if completed.returncode != 0:
            return _report("failed", located["slicer"], None,
                           reasons=[f"slicer exited {completed.returncode}: "
                                    f"{(completed.stderr or '').strip()[:200]}"])
        return self._validate_output(located["slicer"], out_path)

    def _validate_output(self, slicer: str, out_path: str) -> dict:
        """Validate the emitted G-code file into a generated/failed report."""
        path = Path(out_path)
        if not path.is_file():
            return _report("failed", slicer, None,
                           reasons=["slicer reported success but wrote no g-code file"])
        result = self._validator.validate(path.read_text(encoding="utf-8", errors="ignore"))
        if not result["valid"]:
            return _report("failed", slicer, out_path, reasons=result["reasons"],
                           stats=result["stats"])
        logger.info("slice: %s produced %s (%d layers, %d moves)", slicer, out_path,
                    result["stats"]["layers"], result["stats"]["motion_commands"])
        return _report("generated", slicer, out_path,
                       checks=["g-code has motion commands", "axis words present"],
                       stats=result["stats"])

    def _run(self, argv: list[str]) -> subprocess.CompletedProcess:
        """Invoke the slicer (the single mockable subprocess seam)."""
        return subprocess.run(argv, capture_output=True, text=True, timeout=_TIMEOUT_SECONDS,
                              check=False)


def _report(status: str, slicer: str | None, artifact: str | None, *,
            checks: list[str] | None = None, skipped: list[str] | None = None,
            reasons: list[str] | None = None, stats: dict | None = None) -> dict:
    """Assemble a slice delegation report (generated/skipped/failed) with its evidence."""
    return {
        "status": status,
        "slicer": slicer,
        "artifact": artifact,
        "checks": checks or [],
        "skipped": skipped or [],
        "reasons": reasons or [],
        "stats": stats or {},
    }
