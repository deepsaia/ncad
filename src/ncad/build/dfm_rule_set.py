"""Load a versioned, external DFM rule source (process limits) into a queryable object.

The manufacturability thresholds are DATA, never baked into the checker (the backlog's B10
discipline): a shop or vendor ships its own limits and points ncad at them; the default file is a
conservative, explicitly-non-authoritative starting point. This loader wraps the file so the
checker asks it for a process's rules without knowing where the numbers came from, and every rule
carries its own citation string for provenance in the emitted diagnostic.

The file shape (see ``dfm_rules/default_rules.json``):
``{"version", "source", "processes": {<process>: {"label", "rules": {<rule>: {"min"|"max", "unit",
"cite"}}}}}``. One class; loading is done once at construction.
"""

import os
from typing import Any

from ncad.spec.spec_loader import SpecLoader

# The shipped default limits live beside this module; a caller may pass its own file instead.
_DEFAULT_RULES = os.path.join(os.path.dirname(__file__), "dfm_rules", "default_rules.json")


class DfmRuleSet:
    """A loaded set of process-parameterized DFM rules with per-rule provenance."""

    def __init__(self, path: str | None = None) -> None:
        self._path = path or _DEFAULT_RULES
        self._data = SpecLoader().load(self._path)

    @property
    def version(self) -> str:
        """The rule file's version string (for provenance in the report)."""
        return str(self._data.get("version", "unknown"))

    @property
    def source(self) -> str:
        """The rule file's human-readable source/attribution string."""
        return str(self._data.get("source", ""))

    def processes(self) -> list[str]:
        """The process keys this rule set defines (laser, waterjet, cnc_sheet, fdm, ...)."""
        return sorted(self._data.get("processes", {}).keys())

    def label(self, process: str) -> str:
        """The human-readable label for ``process`` (falls back to the key)."""
        return str(self._process(process).get("label", process))

    def rules(self, process: str) -> dict[str, dict]:
        """The ``{rule_name: {min|max, unit, cite}}`` map for ``process`` (empty if none)."""
        return dict(self._process(process).get("rules", {}))

    def _process(self, process: str) -> dict[str, Any]:
        """The raw block for ``process``; raises KeyError naming the known processes if absent."""
        processes = self._data.get("processes", {})
        if process not in processes:
            raise KeyError(
                f"unknown DFM process {process!r}; known: {sorted(processes.keys())}")
        return processes[process]
