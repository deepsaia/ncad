import pytest

from ncad.sketch.naca_airfoil import NacaAirfoil


def test_symmetric_section_has_zero_camber():
    # 0012 is symmetric: for each upper point there is a mirrored lower point (y -> -y).
    pts = NacaAirfoil("0012").points(samples=40)
    ys = [y for _x, y in pts]
    assert max(ys) == pytest.approx(-min(ys), abs=1e-6)


def test_max_thickness_matches_the_code():
    # 0012 -> 12% thickness: the full section height is about 0.12 of the unit chord.
    pts = NacaAirfoil("0012").points(samples=120)
    ys = [y for _x, y in pts]
    assert (max(ys) - min(ys)) == pytest.approx(0.12, abs=0.01)


def test_leading_and_trailing_edges_on_the_chord():
    pts = NacaAirfoil("2412").points(samples=60)
    xs = [x for x, _y in pts]
    assert min(xs) == pytest.approx(0.0, abs=1e-6)   # leading edge at x=0
    # The trailing edge is at x~1; a cambered section nudges it slightly past 1 because the
    # half-thickness is applied normal to the (tilted) camber line, not vertically.
    assert max(xs) == pytest.approx(1.0, abs=2e-3)


def test_cambered_section_has_positive_mean_camber():
    # 2412 has 2% camber: the mean of upper+lower at mid-chord is above the chord line.
    pts = NacaAirfoil("2412").points(samples=80)
    near_mid = [y for x, y in pts if abs(x - 0.4) < 0.03]
    assert sum(near_mid) / len(near_mid) > 0


def test_point_count_is_deterministic():
    a = NacaAirfoil("2412").points(samples=50)
    b = NacaAirfoil("2412").points(samples=50)
    assert a == b and len(a) > 50


def test_non_four_digit_code_raises():
    with pytest.raises(ValueError):
        NacaAirfoil("241").points()
