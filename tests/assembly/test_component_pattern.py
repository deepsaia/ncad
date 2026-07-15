def test_expand_circular_mints_ordinal_ids():
    from ncad.assembly.component_pattern import ComponentPattern
    inst = {"id": "bolt", "file": "b.hocon", "part": "bolt",
            "pattern": {"kind": "circular", "count": 4,
                        "axis": {"point": [0, 0, 0], "dir": [0, 0, 1]}}}
    out = ComponentPattern().expand(inst)
    assert [i["id"] for i in out] == ["bolt/0", "bolt/1", "bolt/2", "bolt/3"]
    assert all(i["file"] == "b.hocon" and i["part"] == "bolt" for i in out)
    assert all("pattern" not in i for i in out)


def test_expand_no_pattern_returns_single_unchanged():
    from ncad.assembly.component_pattern import ComponentPattern
    inst = {"id": "solo", "file": "b.hocon", "part": "bolt"}
    out = ComponentPattern().expand(inst)
    assert out == [inst]


def test_expand_linear_moves_each_copy():
    from ncad.assembly.component_pattern import ComponentPattern
    inst = {"id": "hole", "file": "b.hocon", "part": "h",
            "pattern": {"kind": "linear", "x": {"count": 3, "spacing": 10, "dir": [1, 0, 0]}}}
    out = ComponentPattern().expand(inst)
    assert len(out) == 3
    # Copy 2 is moved +20 in x from the base placement translation row.
    assert abs(out[2]["placement"]["position"][0] - 20.0) < 1e-9


def test_expand_bad_pattern_raises():
    import pytest

    from ncad.assembly.component_pattern import ComponentPattern, ComponentPatternError
    inst = {"id": "x", "file": "b.hocon", "part": "p", "pattern": {"kind": "bogus"}}
    with pytest.raises(ComponentPatternError):
        ComponentPattern().expand(inst)
