import pytest

from ncad.ops.hole_sizes import HoleSizeTable


def test_metric_extended_sizes():
    table = HoleSizeTable()
    # Extended metric range beyond the original M3-M10.
    assert table.resolve_diameter("M12", "normal") > 12.0
    assert table.resolve_diameter("M2", "close") > 2.0


def test_imperial_number_and_fractional_sizes():
    table = HoleSizeTable()
    # A UNC number size and a fractional size resolve to inch-based drill diameters (mm).
    assert table.resolve_diameter("#10", "normal") > 0
    assert table.resolve_diameter("1/4", "normal") > 6.0   # 1/4in ~ 6.35mm


def test_thread_pitch_lookup():
    table = HoleSizeTable()
    # Modeled threads need the coarse-thread pitch for a named size.
    assert table.pitch("M6") == pytest.approx(1.0)
    assert table.pitch("M8") == pytest.approx(1.25)


def test_unknown_size_raises():
    with pytest.raises(ValueError, match="unknown hole size"):
        HoleSizeTable().resolve_diameter("M999", "normal")
