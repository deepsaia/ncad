"""ManufacturabilityChecker maps facts vs rules to pass/fail/need-info with cited diagnostics."""

import json
from typing import Any

from ncad.build.dfm_rule_set import DfmRuleSet
from ncad.build.manufacturability_checker import ManufacturabilityChecker
from ncad.diagnostics import codes


class StubKernel:
    """A minimal kernel exposing only the three facts DfmFacts reads, driven by fixed values."""

    def __init__(self, thickness: float | None, size: tuple[float, float, float],
                 hole_radii: list[float]) -> None:
        self._thickness = thickness
        self._size = size
        self._radii = hole_radii

    def bounding_box(self, shape: Any):
        dx, dy, dz = self._size
        return (0.0, 0.0, 0.0), (dx, dy, dz)

    def min_wall_thickness(self, shape: Any) -> float | None:
        return self._thickness

    def describe_elements(self, shape: Any) -> list:
        return [{"kind": "face", "radius": r, "axis_direction": [0, 0, 1]} for r in self._radii]


def _rules(tmp_path) -> DfmRuleSet:
    path = tmp_path / "rules.json"
    path.write_text(json.dumps({
        "version": "test-1", "source": "test",
        "processes": {"laser": {"label": "laser", "rules": {
            "min_hole_diameter": {"fact": "smallest_hole_diameter", "min": 2.0, "unit": "mm",
                                  "cite": "kerf floor"},
            "min_wall_thickness": {"fact": "min_wall_thickness", "min": 1.0, "unit": "mm",
                                   "cite": "clean cut"},
        }}},
    }))
    return DfmRuleSet(str(path))


def test_all_pass_emits_no_diagnostics(tmp_path):
    kernel = StubKernel(thickness=3.0, size=(50, 40, 3), hole_radii=[3.0])  # 6mm hole, 3mm wall
    checker = ManufacturabilityChecker(kernel, _rules(tmp_path))
    report = checker.check("plate", object(), ["laser"])
    assert all(r["verdict"] == "pass" for r in report["results"])
    assert checker.diagnostics(report) == []


def test_violation_is_a_warning_citing_the_rule(tmp_path):
    kernel = StubKernel(thickness=0.4, size=(20, 20, 0.4), hole_radii=[0.4])  # 0.8mm hole, 0.4 wall
    checker = ManufacturabilityChecker(kernel, _rules(tmp_path))
    report = checker.check("foil", object(), ["laser"])
    fails = [r for r in report["results"] if r["verdict"] == "fail"]
    assert {r["rule"] for r in fails} == {"min_hole_diameter", "min_wall_thickness"}
    diags = checker.diagnostics(report)
    assert diags and all(d.severity == "warning" for d in diags)
    assert all(d.code == codes.DFM_VIOLATION for d in diags)
    assert "kerf floor" in " ".join(d.hint or "" for d in diags)  # citation rides the hint


def test_missing_fact_is_need_more_info_not_pass(tmp_path):
    # No holes: the min_hole_diameter rule cannot be judged -> need_more_info (info), never pass.
    kernel = StubKernel(thickness=3.0, size=(50, 40, 3), hole_radii=[])
    checker = ManufacturabilityChecker(kernel, _rules(tmp_path))
    report = checker.check("solid", object(), ["laser"])
    hole = [r for r in report["results"] if r["rule"] == "min_hole_diameter"][0]
    assert hole["verdict"] == "need_more_info"
    info = [d for d in checker.diagnostics(report) if d.severity == "info"]
    assert info and "cannot evaluate" in info[0].message


def test_sidecar_is_written(tmp_path):
    kernel = StubKernel(thickness=3.0, size=(50, 40, 3), hole_radii=[3.0])
    checker = ManufacturabilityChecker(kernel, _rules(tmp_path))
    report = checker.check("plate", object(), ["laser"])
    path = checker.write_sidecar(report, str(tmp_path), "plate")
    assert path.endswith("plate.dfm.json")
    written = json.loads((tmp_path / "plate.dfm.json").read_text())
    assert written["part"] == "plate" and written["rule_version"] == "test-1"
    assert written["results"]
