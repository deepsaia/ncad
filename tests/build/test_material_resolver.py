import pytest

from ncad.build.material_error import MaterialError
from ncad.build.material_resolver import MaterialResolver
from ncad.kernel.body import Body
from ncad.spec.material_library import MaterialLibrary


def _body(created_by):
    return Body(id=f"{created_by}/body/0", kind="solid", shape=object(), created_by=created_by)


def _lib():
    return MaterialLibrary({})


def test_feature_material_overrides_part_default():
    part = {"material": "aluminium_6061",
            "features": [{"id": "tw", "op": "transform", "material": "steel_1018"}]}
    r = MaterialResolver(part, _lib())
    assert r.material_name(_body("tw")) == "steel_1018"
    assert r.for_body(_body("tw"))["physical"]["density"] == 7870


def test_body_without_feature_material_inherits_part_default():
    part = {"material": "aluminium_6061",
            "features": [{"id": "row", "op": "pattern"}]}
    r = MaterialResolver(part, _lib())
    assert r.material_name(_body("row")) == "aluminium_6061"
    assert r.for_body(_body("row"))["physical"]["density"] == 2700


def test_single_body_empty_created_by_uses_part_default():
    part = {"material": "abs", "features": [{"id": "blk", "op": "extrude"}]}
    r = MaterialResolver(part, _lib())
    body = Body(id="body/0", kind="solid", shape=object(), created_by="")
    assert r.material_name(body) == "abs"


def test_no_material_anywhere_returns_none():
    part = {"features": [{"id": "blk", "op": "extrude"}]}
    r = MaterialResolver(part, _lib())
    assert r.material_name(_body("blk")) is None
    assert r.for_body(_body("blk")) is None


def test_inline_mat_data_override_merges():
    part = {"features": [{"id": "tw", "op": "transform", "material": "steel_1018",
                          "mat_data": {"physical": {"density": 7000}}}]}
    r = MaterialResolver(part, _lib())
    assert r.for_body(_body("tw"))["physical"]["density"] == 7000  # overridden


def test_unknown_material_raises_on_resolve():
    part = {"material": "unobtanium", "features": [{"id": "blk", "op": "extrude"}]}
    r = MaterialResolver(part, _lib())
    with pytest.raises(MaterialError, match="unobtanium"):
        r.for_body(_body("blk"))
