import pytest

from ncad.ops.hole_sizes import HoleSizeTable


def test_m6_normal_clearance():
    assert HoleSizeTable().resolve_diameter("M6", "normal") == 6.6


def test_m6_tapped_drill():
    assert HoleSizeTable().resolve_diameter("M6", "tapped") == 5.0


def test_m3_close_clearance():
    assert HoleSizeTable().resolve_diameter("M3", "close") == 3.2


def test_unknown_size_raises():
    with pytest.raises(ValueError, match="size"):
        HoleSizeTable().resolve_diameter("M99", "normal")


def test_unknown_fit_raises():
    with pytest.raises(ValueError, match="fit"):
        HoleSizeTable().resolve_diameter("M6", "snug")
