import pytest

from ncad.ops.rib_params import RibParamError, rib_kwargs


def test_thickness_and_depth_parse():
    kw = rib_kwargs({"thickness": 3, "depth": 20}, {})
    assert kw["thickness"] == 3.0 and kw["depth"] == 20.0


def test_missing_thickness_raises():
    with pytest.raises(RibParamError, match="thickness"):
        rib_kwargs({"depth": 20}, {})


def test_missing_depth_raises():
    with pytest.raises(RibParamError, match="depth"):
        rib_kwargs({"thickness": 3}, {})


def test_nonpositive_raises():
    with pytest.raises(RibParamError, match="thickness"):
        rib_kwargs({"thickness": 0, "depth": 20}, {})
    with pytest.raises(RibParamError, match="depth"):
        rib_kwargs({"thickness": 3, "depth": -1}, {})
