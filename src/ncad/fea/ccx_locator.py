"""Locate an installed CalculiX (ccx) binary. No solver is bundled.

CalculiX CrunchiX (ccx) is a desktop/CLI binary, not a pip package, so ncad DELEGATES to whatever
the user installed rather than bundling it. The ``NCAD_CCX`` environment variable overrides the
search with an explicit path; otherwise the common executable spellings are tried on PATH. Because
ncad only shells out to the separate binary (never links it), CalculiX's GPL licensing does not
affect ncad. One class.
"""

import logging
import os
import shutil

logger = logging.getLogger(__name__)

# Common ccx executable spellings across distributions/versions, best/most-generic first.
_CANDIDATES = ("ccx", "ccx_2.22", "ccx_2.21", "ccx_2.20", "ccx_2.19", "CalculiX")


class CcxLocator:
    """Finds an installed ccx binary (env override first, then PATH); reports its path or None."""

    def locate(self) -> str | None:
        """Return the ccx binary path, or None if CalculiX is not installed.

        ``NCAD_CCX`` (an explicit executable path) wins when set and runnable; otherwise the first
        candidate found on PATH via ``shutil.which``.
        """
        override = os.environ.get("NCAD_CCX")
        if override and os.path.isfile(override) and os.access(override, os.X_OK):
            return override
        for name in _CANDIDATES:
            found = shutil.which(name)
            if found:
                return found
        return None
