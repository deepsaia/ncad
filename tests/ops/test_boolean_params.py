import pytest

from ncad.ops.boolean_params import BooleanParamError, boolean_kwargs


def test_ref_mode_single_tool():
    kw = boolean_kwargs({"operation": "cut", "target": "base", "tool": "hole"})
    assert kw["mode"] == "ref" and kw["operation"] == "cut"


def test_ref_mode_multi_tool():
    kw = boolean_kwargs({"operation": "cut", "target": "base", "tools": ["h1", "h2"]})
    assert kw["mode"] == "ref"


def test_scope_mode():
    kw = boolean_kwargs({"operation": "union", "scope": ["p/body/0", "p/body/2"]})
    assert kw["mode"] == "scope"
    assert kw["scope"] == ["p/body/0", "p/body/2"]


def test_default_operation_is_cut():
    kw = boolean_kwargs({"target": "base", "tool": "hole"})
    assert kw["operation"] == "cut"


def test_merge_flag_defaults_true():
    kw = boolean_kwargs({"operation": "union", "target": "a", "tool": "b"})
    assert kw["merge"] is True
    assert boolean_kwargs(
        {"operation": "union", "target": "a", "tool": "b", "merge": False})["merge"] is False


def test_unknown_operation_raises():
    with pytest.raises(BooleanParamError, match="operation"):
        boolean_kwargs({"operation": "xor", "target": "a", "tool": "b"})


def test_both_tool_and_scope_raises():
    with pytest.raises(BooleanParamError, match="scope"):
        boolean_kwargs({"operation": "cut", "target": "a", "tool": "b", "scope": ["x"]})


def test_ref_mode_missing_tool_raises():
    with pytest.raises(BooleanParamError, match="tool"):
        boolean_kwargs({"operation": "cut", "target": "base"})


def test_ref_mode_both_tool_and_tools_raises():
    with pytest.raises(BooleanParamError, match="tool"):
        boolean_kwargs({"operation": "cut", "target": "a", "tool": "b", "tools": ["c"]})


def test_scope_must_be_nonempty_list():
    with pytest.raises(BooleanParamError, match="scope"):
        boolean_kwargs({"operation": "union", "scope": []})
    with pytest.raises(BooleanParamError, match="scope"):
        boolean_kwargs({"operation": "union", "scope": "p/body/0"})
