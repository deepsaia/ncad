from ncad.ops.pattern_placements import PatternPlacements


def test_curve_specs_move_relative_to_seed():
    kw = {"kind": "curve", "merge": True, "suppress": [],
          "curve": {"points": [(0.0, 0.0, 0.0), (10.0, 0.0, 0.0), (20.0, 0.0, 0.0)],
                    "tangents": [(1.0, 0.0, 0.0)] * 3, "align": False}}
    specs = PatternPlacements(kw).specs()
    assert specs[0] == {}                        # seed at the first sample
    assert specs[1]["move"] == (10.0, 0.0, 0.0)
    assert specs[2]["move"] == (20.0, 0.0, 0.0)
