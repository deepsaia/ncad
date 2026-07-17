from ncad.refs.attribute_model import AttributeModel


def test_known_attributes():
    m = AttributeModel()
    for name in ["kind", "type", "created_by", "tag", "orientation",
                 "normal_x", "normal_y", "normal_z", "area", "length",
                 "min_z", "mid_z", "max_z"]:
        assert m.is_known(name), name


def test_position_attributes_are_known():
    # v2: mid_x / mid_y let a selector pick an element by WHERE it is (not only by area).
    m = AttributeModel()
    assert m.is_known("mid_x")
    assert m.is_known("mid_y")


def test_deferred_attributes_are_unknown():
    m = AttributeModel()
    assert not m.is_known("convexity")
    assert not m.is_known("bogus")


def test_version_is_positive_int():
    assert isinstance(AttributeModel.VERSION, int) and AttributeModel.VERSION >= 1
