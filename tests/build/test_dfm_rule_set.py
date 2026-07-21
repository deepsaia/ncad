"""DfmRuleSet loads shipped + external process limits with provenance; rejects unknown processes."""

import json

import pytest

from ncad.build.dfm_rule_set import DfmRuleSet


def test_default_rule_set_exposes_processes():
    rs = DfmRuleSet()
    assert set(rs.processes()) >= {"laser", "waterjet", "cnc_sheet", "fdm"}
    assert rs.version  # a version string is present for provenance
    assert "min_hole_diameter" in rs.rules("laser")


def test_rule_carries_citation_and_fact():
    rule = DfmRuleSet().rules("fdm")["min_hole_diameter"]
    assert rule["fact"] == "smallest_hole_diameter"
    assert rule["min"] == 2.0
    assert rule["cite"]  # every rule cites its rationale


def test_unknown_process_raises():
    with pytest.raises(KeyError, match="unknown DFM process"):
        DfmRuleSet().rules("plasma")


def test_external_rule_file_overrides_defaults(tmp_path):
    custom = tmp_path / "shop.json"
    custom.write_text(json.dumps({
        "version": "shop-1",
        "source": "acme shop",
        "processes": {"laser": {"label": "acme laser", "rules": {
            "min_wall_thickness": {"fact": "min_wall_thickness", "min": 3.0, "unit": "mm",
                                   "cite": "acme minimum"}}}},
    }))
    rs = DfmRuleSet(str(custom))
    assert rs.version == "shop-1"
    assert rs.label("laser") == "acme laser"
    assert rs.rules("laser")["min_wall_thickness"]["min"] == 3.0
