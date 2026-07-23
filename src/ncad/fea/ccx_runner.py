"""Solve a CalculiX .inp deck by delegating to an installed ccx; report honestly if none is present.

The FEA delegation seam ("never a solver we write"): ncad finds an installed ccx, hands it the deck,
and checks the .frd it produces. When no ccx is installed, or ccx fails, or it writes no .frd, the
run is reported as SKIPPED/FAILED with the reason (the delegation-report discipline: a missing
external tool is "skipped", never a silent "pass"). Mirrors cam.SliceRunner exactly.

One class. The subprocess invocation is isolated in ``_run`` so it is the single mockable seam.
"""

import logging
import os
import subprocess
from pathlib import Path

from ncad.fea.ccx_locator import CcxLocator

logger = logging.getLogger(__name__)

# An FEA solve can be long on a large mesh; cap the delegated call so a hang is reported, not hung.
_TIMEOUT_SECONDS = 1800


class CcxRunner:
    """Delegates a .inp -> .frd solve to an installed CalculiX and returns a structured report."""

    def __init__(self, locator: CcxLocator | None = None) -> None:
        self._locator = locator or CcxLocator()

    def solve(self, inp_path: str, out_dir: str) -> dict:
        """Solve ``inp_path`` with ccx in ``out_dir``; return the solve report.

        Report: ``{status, ccx, artifact, checks, skipped, reasons}`` where ``status`` is
        ``generated`` | ``skipped`` | ``failed``. ``skipped`` when no ccx installed; ``failed``
        when ccx errored or wrote no .frd. Never raises for an absent/failing tool. ccx takes the
        job name WITHOUT the .inp extension and writes ``<jobname>.frd`` in its working directory.
        """
        binary = self._locator.locate()
        if binary is None:
            return _report("skipped", None, None,
                           skipped=["no CalculiX installed (set NCAD_CCX or put ccx on PATH); "
                                    "ncad delegates the solve, it does not bundle one"])
        jobname = Path(inp_path).stem
        try:
            completed = self._run([binary, jobname], out_dir)
        except (OSError, subprocess.SubprocessError) as exc:
            return _report("failed", binary, None, reasons=[f"ccx invocation failed: {exc}"])
        if completed.returncode != 0:
            return _report("failed", binary, None,
                           reasons=[f"ccx exited {completed.returncode}: "
                                    f"{(completed.stderr or '').strip()[:200]}"])
        frd = os.path.join(out_dir, f"{jobname}.frd")
        if not os.path.isfile(frd) or os.path.getsize(frd) == 0:
            return _report("failed", binary, None,
                           reasons=["ccx reported success but wrote no .frd results file"])
        logger.info("ccx: solved %s -> %s", inp_path, frd)
        return _report("generated", binary, frd, checks=["ccx exited 0", ".frd results written"])

    def _run(self, argv: list[str], cwd: str) -> subprocess.CompletedProcess:
        """Invoke ccx in ``cwd`` (the single mockable subprocess seam)."""
        return subprocess.run(argv, cwd=cwd, capture_output=True, text=True,
                              timeout=_TIMEOUT_SECONDS, check=False)


def _report(status: str, ccx: str | None, artifact: str | None, *,
            checks: list[str] | None = None, skipped: list[str] | None = None,
            reasons: list[str] | None = None) -> dict:
    """Assemble a solve delegation report (generated/skipped/failed) with its evidence."""
    return {
        "status": status,
        "ccx": ccx,
        "artifact": artifact,
        "checks": checks or [],
        "skipped": skipped or [],
        "reasons": reasons or [],
    }
