import pytest

from ncad.ops.fillet_params import FilletParamError, fillet_kwargs


def test_constant_radius():
    kw = fillet_kwargs({"radius": 3.0})
    assert kw == {"variable": False, "radius": 3.0}


def test_variable_radius_pair():
    kw = fillet_kwargs({"radius_start": 2.0, "radius_end": 6.0})
    assert kw == {"variable": True, "radius_start": 2.0, "radius_end": 6.0}


def test_missing_radius_raises():
    with pytest.raises(FilletParamError):
        fillet_kwargs({})


def test_half_variable_raises():
    with pytest.raises(FilletParamError):
        fillet_kwargs({"radius_start": 2.0})
