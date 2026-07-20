from ncad.spec.dependency_validator import DependencyValidator


def _doc(features):
    return {"units": "mm",
            "parts": {"p": {"profile": "solid", "features": features}}}


def test_valid_order_is_clean():
    doc = _doc([
        {"id": "sk", "op": "sketch"},
        {"id": "pad", "op": "extrude", "profile": "sk"},
    ])
    assert DependencyValidator().validate(doc) == []


def test_forward_reference_is_flagged():
    doc = _doc([
        {"id": "pad", "op": "extrude", "profile": "sk"},
        {"id": "sk", "op": "sketch"},
    ])
    issues = DependencyValidator().validate(doc)
    assert len(issues) == 1 and "defined later" in issues[0].message
    assert "pad" in issues[0].message


def test_unknown_reference_is_flagged():
    doc = _doc([
        {"id": "sk", "op": "sketch"},
        {"id": "pad", "op": "extrude", "profile": "ghost"},
    ])
    issues = DependencyValidator().validate(doc)
    assert len(issues) == 1 and "unknown feature" in issues[0].message


def test_boolean_target_and_tool_checked():
    doc = _doc([
        {"id": "a", "op": "sketch"},
        {"id": "pa", "op": "extrude", "profile": "a"},
        {"id": "bool", "op": "boolean", "target": "pa", "tool": "later"},
        {"id": "later", "op": "extrude", "profile": "a"},
    ])
    issues = DependencyValidator().validate(doc)
    assert any("later" in i.message and "defined later" in i.message for i in issues)


def test_generative_and_selector_refs_are_not_checked():
    doc = _doc([
        {"id": "sk", "op": "sketch"},
        {"id": "pad", "op": "extrude", "profile": "sk"},
        {"id": "h", "op": "hole", "on": "pad.cap(+Z)"},
        {"id": "rnd", "op": "fillet", "edges": "select edges where created_by='pad'"},
    ])
    assert DependencyValidator().validate(doc) == []


def test_refs_are_scoped_per_part():
    doc = {"units": "mm", "parts": {
        "p1": {"profile": "solid", "features": [{"id": "sk", "op": "sketch"}]},
        "p2": {"profile": "solid", "features": [
            {"id": "pad", "op": "extrude", "profile": "sk"}]},
    }}
    issues = DependencyValidator().validate(doc)
    assert any("unknown feature" in i.message for i in issues)
