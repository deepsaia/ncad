import math

import pytest

from ncad.sketch.gear_profile import GearProfile, GearProfileError


def test_pitch_base_addendum_dedendum_radii():
    # module m=2, z=24, pressure angle 20deg. d = m*z = 48 -> pitch r = 24. base r = 24*cos20.
    g = GearProfile(module=2.0, teeth=24, pressure_angle=20.0)
    assert math.isclose(g.pitch_radius, 24.0, abs_tol=1e-9)
    assert math.isclose(g.base_radius, 24.0 * math.cos(math.radians(20.0)), abs_tol=1e-9)
    assert math.isclose(g.addendum_radius, 24.0 + 2.0, abs_tol=1e-9)     # + m
    assert math.isclose(g.dedendum_radius, 24.0 - 1.25 * 2.0, abs_tol=1e-9)  # - 1.25m


def test_outline_is_closed_and_has_tooth_periods():
    g = GearProfile(module=2.0, teeth=12, pressure_angle=20.0)
    pts = g.outline()
    assert len(pts) > 12 * 2                # several points per tooth
    assert pts[0] != pts[-1]                # not duplicated; the polyline closes back to pts[0]
    # every point is within [dedendum, addendum] radius (a small tolerance for the flank sampling).
    for x, y in pts:
        r = math.hypot(x, y)
        assert g.dedendum_radius - 1e-6 <= r <= g.addendum_radius + 1e-6


def test_outline_has_z_fold_symmetry():
    # Rotating the outline by one tooth pitch (360/z) maps the point set onto itself: check the
    # radial profile repeats z times (max radius occurs near each tooth tip).
    g = GearProfile(module=1.0, teeth=8, pressure_angle=20.0)
    pts = g.outline()
    # bin points by angle into z sectors; each sector should reach near the addendum radius.
    z = 8
    reached_tip = [False] * z
    for x, y in pts:
        sector = int((math.atan2(y, x) % (2 * math.pi)) / (2 * math.pi / z))
        if math.hypot(x, y) >= g.addendum_radius - 0.05:
            reached_tip[sector % z] = True
    assert all(reached_tip)


def test_center_distance_for_mesh():
    # Two gears with the same module mesh at center distance (z1+z2)*m/2.
    g1 = GearProfile(module=2.0, teeth=16, pressure_angle=20.0)
    g2 = GearProfile(module=2.0, teeth=24, pressure_angle=20.0)
    assert math.isclose(GearProfile.center_distance(g1, g2), (16 + 24) * 2.0 / 2.0, abs_tol=1e-9)


def test_bad_params_raise():
    with pytest.raises(GearProfileError):
        GearProfile(module=0.0, teeth=20, pressure_angle=20.0)
    with pytest.raises(GearProfileError):
        GearProfile(module=2.0, teeth=2, pressure_angle=20.0)     # too few teeth
    with pytest.raises(GearProfileError):
        GearProfile(module=2.0, teeth=20, pressure_angle=0.0)     # bad pressure angle
