import pytest

from ncad.ops.shell_params import ShellParamError, shell_kwargs


def test_thickness_parses():
    assert shell_kwargs({"thickness": 2})["thickness"] == 2.0


def test_missing_thickness_raises():
    with pytest.raises(ShellParamError, match="thickness"):
        shell_kwargs({})


def test_nonpositive_thickness_raises():
    with pytest.raises(ShellParamError, match="thickness"):
        shell_kwargs({"thickness": 0})
