"""Compare a part's DFM facts against an external rule set: a tri-state manufacturability preflight.

The comparison layer of the DFM seam (backlog B10). It owns NO thresholds - it reads facts from
DfmFacts and limits from DfmRuleSet, and for each rule emits one of three verdicts:

- ``pass``  - the fact satisfies the limit.
- ``fail``  - the fact violates the limit (a ``warning`` Diagnostic; never blocks a build, because
  a design may target a process ncad was not told about).
- ``need_more_info`` - the rule references a fact the part does not provide (e.g. no round holes to
  measure a min-hole rule against), so no honest verdict is possible (an ``info`` Diagnostic). A
  missing fact is reported as need-more-info, NEVER silently as a pass.

Every verdict cites its rule name, the process label, the limit + fact values, and the rule's own
citation string, so the report is self-explaining. ``check`` returns the structured report and the
Diagnostics; ``write_sidecar`` persists ``<name>.dfm.json``. One class; pure over its inputs.
"""

import json
import logging
import os
from typing import Any

from ncad.build.dfm_facts import DfmFacts
from ncad.build.dfm_rule_set import DfmRuleSet
from ncad.diagnostics import codes
from ncad.diagnostics.diagnostic import Diagnostic
from ncad.kernel.kernel import Kernel

logger = logging.getLogger(__name__)

_SIDECAR_SUFFIX = ".dfm.json"


class ManufacturabilityChecker:
    """Runs process-parameterized DFM rules over a part's facts into tri-state verdicts."""

    def __init__(self, kernel: Kernel, rule_set: DfmRuleSet | None = None) -> None:
        self._facts = DfmFacts(kernel)
        self._rules = rule_set or DfmRuleSet()

    def check(self, part_name: str, shape: Any, processes: list[str]) -> dict:
        """Evaluate every rule of each process against ``shape``; return the DFM report dict.

        Report shape: ``{"part", "rule_version", "rule_source", "facts", "results": [{process,
        rule, verdict, fact_value, limit, unit, cite, message}]}``. ``verdict`` is
        pass|fail|need_more_info.
        """
        facts = self._facts.extract(shape)
        results: list[dict] = []
        for process in processes:
            label = self._rules.label(process)
            for name, rule in self._rules.rules(process).items():
                results.append(self._evaluate(process, label, name, rule, facts))
        return {
            "part": part_name,
            "rule_version": self._rules.version,
            "rule_source": self._rules.source,
            "facts": facts,
            "results": results,
        }

    def diagnostics(self, report: dict) -> list[Diagnostic]:
        """The Diagnostics for a report: a warning per fail, an info per need_more_info."""
        diags: list[Diagnostic] = []
        for result in report["results"]:
            if result["verdict"] == "pass":
                continue
            severity = "warning" if result["verdict"] == "fail" else "info"
            diags.append(Diagnostic(
                severity=severity, code=codes.DFM_VIOLATION,
                location=f"parts.{report['part']}",
                message=result["message"],
                hint=f"rule '{result['rule']}' ({result['cite']}); "
                     f"DFM rules v{report['rule_version']}",
                stage="build"))
        return diags

    def write_sidecar(self, report: dict, out_dir: str, name: str) -> str:
        """Write ``<name>.dfm.json`` and return its path."""
        path = os.path.join(out_dir, f"{name}{_SIDECAR_SUFFIX}")
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(report, handle, indent=2)
        logger.info("dfm: wrote %s (%d rules)", path, len(report["results"]))
        return path

    def _evaluate(self, process: str, label: str, name: str, rule: dict, facts: dict) -> dict:
        """One rule vs the facts into a tri-state result record (see check for the shape)."""
        fact_key = rule.get("fact")
        value = facts.get(fact_key) if fact_key else None
        unit = rule.get("unit", "mm")
        base = {"process": process, "rule": name, "fact": fact_key,
                "fact_value": value, "unit": unit, "cite": rule.get("cite", "")}
        if value is None:
            # No fact to judge against: honest need-more-info, never a silent pass.
            limit_desc = _limit_desc(rule)
            return {**base, "verdict": "need_more_info", "limit": limit_desc,
                    "message": f"{label}: cannot evaluate '{name}' ({limit_desc}); "
                               f"the part provides no '{fact_key}' fact"}
        passed, limit_desc = _within(value, rule)
        verdict = "pass" if passed else "fail"
        relation = "ok" if passed else "violates"
        return {**base, "verdict": verdict, "limit": limit_desc,
                "message": f"{label}: '{name}' {relation} - {fact_key} {value:.3g} {unit} "
                           f"vs {limit_desc}"}


def _within(value: float, rule: dict) -> tuple[bool, str]:
    """(passes, human-limit-string) for a value against a rule's min and/or max bounds."""
    lo, hi = rule.get("min"), rule.get("max")
    ok = True
    if lo is not None and value < lo:
        ok = False
    if hi is not None and value > hi:
        ok = False
    return ok, _limit_desc(rule)


def _limit_desc(rule: dict) -> str:
    """A compact description of a rule's bounds, e.g. ``>= 1.0``, ``<= 20.0``, ``[1.0, 20.0]``."""
    lo, hi = rule.get("min"), rule.get("max")
    if lo is not None and hi is not None:
        return f"[{lo}, {hi}]"
    if lo is not None:
        return f">= {lo}"
    if hi is not None:
        return f"<= {hi}"
    return "no bound"
