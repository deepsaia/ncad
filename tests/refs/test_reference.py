from ncad.refs.reference import Reference


def test_bare_name_is_semantic():
    r = Reference.parse("sk")
    assert r.kind == "semantic" and r.payload["feature"] == "sk"


def test_datums_path_is_semantic():
    r = Reference.parse("datums.base")
    assert r.kind == "semantic" and r.payload["feature"] == "datums.base"


def test_instance_is_semantic_with_index():
    r = Reference.parse("holes.instance(3)")
    assert r.kind == "semantic"
    assert r.payload["feature"] == "holes" and r.payload["instance"] == 3


def test_generative_cap_tag():
    r = Reference.parse("pad.cap(+Z)")
    assert r.kind == "generative"
    assert r.payload["feature"] == "pad" and r.payload["tag"] == "cap(+Z)"


def test_generative_side_tag():
    r = Reference.parse("pad.side")
    assert r.kind == "generative"
    assert r.payload["feature"] == "pad" and r.payload["tag"] == "side"


def test_selector_query():
    text = "select edges where created_by='pad'"
    r = Reference.parse(text)
    assert r.kind == "selector" and r.payload["query"] == text
