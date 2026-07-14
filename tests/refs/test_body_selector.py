from ncad.refs.selector import Selector


class _BodyElem:
    def __init__(self, material, tag=""):
        self.kind = "body"
        self.attrs = {"material": material, "tag": tag}


def test_select_bodies_by_material():
    bodies = [_BodyElem("steel_1018"), _BodyElem("aluminium_6061")]
    picked = Selector().select("select bodies where material = 'steel_1018'", bodies)
    assert len(picked) == 1
    assert picked[0].attrs["material"] == "steel_1018"


def test_select_bodies_by_tag():
    bodies = [_BodyElem("steel_1018", tag="hub"), _BodyElem("steel_1018", tag="flange")]
    picked = Selector().select("select bodies where tag = 'hub'", bodies)
    assert len(picked) == 1 and picked[0].attrs["tag"] == "hub"
