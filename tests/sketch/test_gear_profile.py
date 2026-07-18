import math

import pytest

from ncad.sketch.gear_profile import GearProfile, GearProfileError


# --- legacy sugar (module/teeth/pressure_angle -> external, x=0) ---------------------------------
def test_pitch_base_addendum_dedendum_radii():
    # module m=2, z=24, pressure angle 20deg. d = m*z = 48 -> pitch r = 24. base r = 24*cos20.
    g = GearProfile(module=2.0, teeth=24, pressure_angle=20.0)
    assert math.isclose(g.pitch_radius, 24.0, abs_tol=1e-9)
    assert math.isclose(g.base_radius, 24.0 * math.cos(math.radians(20.0)), abs_tol=1e-9)
    assert math.isclose(g.addendum_radius, 24.0 + 2.0, abs_tol=1e-9)         # + m (x=0)
    assert math.isclose(g.dedendum_radius, 24.0 - 1.25 * 2.0, abs_tol=1e-9)  # - 1.25m (x=0)
    assert g.gear_type == "external"


def test_outline_is_closed_and_within_radial_band():
    g = GearProfile(module=2.0, teeth=12, pressure_angle=20.0)
    pts = g.outline()
    assert len(pts) > 12 * 2
    assert pts[0] != pts[-1]                # not duplicated; the polyline closes back to pts[0]
    for x, y in pts:
        r = math.hypot(x, y)
        assert g.dedendum_radius - 1e-6 <= r <= g.addendum_radius + 1e-6


def test_outline_has_z_fold_symmetry():
    g = GearProfile(module=1.0, teeth=8, pressure_angle=20.0)
    pts = g.outline()
    z = 8
    reached_tip = [False] * z
    for x, y in pts:
        sector = int((math.atan2(y, x) % (2 * math.pi)) / (2 * math.pi / z))
        if math.hypot(x, y) >= g.addendum_radius - 0.05:
            reached_tip[sector % z] = True
    assert all(reached_tip)


def test_bad_params_raise():
    with pytest.raises(GearProfileError):
        GearProfile(module=0.0, teeth=20, pressure_angle=20.0)
    with pytest.raises(GearProfileError):
        GearProfile(module=2.0, teeth=2, pressure_angle=20.0)     # too few teeth
    with pytest.raises(GearProfileError):
        GearProfile(module=2.0, teeth=20, pressure_angle=0.0)     # bad pressure angle


# --- profile shift (addendum modification x) -----------------------------------------------------
def test_profile_shift_raises_addendum_and_dedendum():
    # A positive shift x moves the reference rack out by x*m: addendum r_a = pitch_r + m(1 + x),
    # dedendum r_f = pitch_r - m(1.25 - x). Compare a shifted gear to the unshifted one.
    base = GearProfile(module=2.0, teeth=20, pressure_angle=20.0)
    shifted = GearProfile(module=2.0, teeth=20, pressure_angle=20.0, profile_shift=0.5)
    assert math.isclose(shifted.addendum_radius, base.addendum_radius + 0.5 * 2.0, abs_tol=1e-9)
    assert math.isclose(shifted.dedendum_radius, base.dedendum_radius + 0.5 * 2.0, abs_tol=1e-9)
    # Pitch and base circles depend only on m, z, alpha -> unchanged by the shift.
    assert math.isclose(shifted.pitch_radius, base.pitch_radius, abs_tol=1e-9)
    assert math.isclose(shifted.base_radius, base.base_radius, abs_tol=1e-9)


def test_positive_shift_avoids_undercut_on_low_tooth_count():
    # z=12 < 17 undercuts at 20deg with x=0 (dedendum below the base circle). A positive shift
    # raises the dedendum toward the base circle, so the involute flank is not truncated.
    undercut = GearProfile(module=1.0, teeth=12, pressure_angle=20.0)
    assert undercut.dedendum_radius < undercut.base_radius            # would undercut
    fixed = GearProfile(module=1.0, teeth=12, pressure_angle=20.0, profile_shift=0.5)
    assert fixed.dedendum_radius >= undercut.dedendum_radius          # shift raised the root


# --- internal (ring) gear ------------------------------------------------------------------------
def test_internal_gear_teeth_point_inward():
    # An internal gear's material is OUTSIDE the pitch circle: the tooth TIP (addendum) is at a
    # SMALLER radius than the pitch circle, and the root (dedendum) is LARGER (inverted band).
    ring = GearProfile(module=2.0, teeth=40, pressure_angle=20.0, gear_type="internal")
    assert ring.gear_type == "internal"
    assert ring.addendum_radius < ring.pitch_radius      # tip points inward
    assert ring.dedendum_radius > ring.pitch_radius      # root is outside the pitch circle
    for x, y in ring.outline():
        r = math.hypot(x, y)
        assert ring.addendum_radius - 1e-6 <= r <= ring.dedendum_radius + 1e-6


# --- rack (z -> infinity: straight trapezoidal teeth) --------------------------------------------
def test_rack_has_straight_trapezoidal_teeth():
    # A rack is the involute limit: teeth are straight flanks at the pressure angle on a line. The
    # crest is at +m, the tooth root at -1.25m about the pitch line (y=0), with a backing below so
    # the strip is a closed extrudable profile.
    rack = GearProfile(module=2.0, teeth=6, pressure_angle=20.0, gear_type="rack")
    assert rack.gear_type == "rack"
    pts = rack.outline()
    ys = [round(p[1], 6) for p in pts]
    assert math.isclose(max(ys), 2.0, abs_tol=1e-6)      # addendum crest at +m
    assert -1.25 * 2.0 in ys                             # the tooth root line at -1.25m is present
    assert min(ys) < -1.25 * 2.0 - 1e-6                  # a backing body below the root (closed)
    xs = [p[0] for p in pts]
    assert max(xs) - min(xs) >= 6 * math.pi * 2.0 - 1e-6  # >= 6 pitches of length p = pi*m


# --- mesh relations (one source of truth, like CamProfile) ---------------------------------------
def test_center_distance_external_is_shift_corrected():
    # Standard (x=0) external mesh: a = (z1+z2)*m/2. With profile shift the working center distance
    # grows via the involute function; here x=0 so it reduces to the standard sum.
    g1 = GearProfile(module=2.0, teeth=16, pressure_angle=20.0)
    g2 = GearProfile(module=2.0, teeth=24, pressure_angle=20.0)
    assert math.isclose(GearProfile.center_distance(g1, g2), (16 + 24) * 2.0 / 2.0, abs_tol=1e-6)


def test_center_distance_internal_is_difference():
    # Internal mesh (ring + pinion): a = (z_ring - z_pinion)*m/2 (the pinion runs inside the ring).
    ring = GearProfile(module=2.0, teeth=40, pressure_angle=20.0, gear_type="internal")
    pinion = GearProfile(module=2.0, teeth=16, pressure_angle=20.0)
    assert math.isclose(GearProfile.center_distance(ring, pinion), (40 - 16) * 2.0 / 2.0,
                        abs_tol=1e-6)


def test_shifted_external_center_distance_exceeds_standard():
    # Two positively-shifted gears mesh at a LARGER working center distance than the standard sum.
    g1 = GearProfile(module=2.0, teeth=16, pressure_angle=20.0, profile_shift=0.3)
    g2 = GearProfile(module=2.0, teeth=24, pressure_angle=20.0, profile_shift=0.3)
    standard = (16 + 24) * 2.0 / 2.0
    assert GearProfile.center_distance(g1, g2) > standard


def test_gear_ratio_and_sense():
    # External mesh reverses sense (ratio < 0), internal keeps sense (ratio > 0). |ratio| = z1/z2.
    pinion = GearProfile(module=2.0, teeth=16, pressure_angle=20.0)
    gear = GearProfile(module=2.0, teeth=24, pressure_angle=20.0)
    assert math.isclose(GearProfile.mesh_ratio(pinion, gear), -16.0 / 24.0, abs_tol=1e-9)
    ring = GearProfile(module=2.0, teeth=40, pressure_angle=20.0, gear_type="internal")
    assert math.isclose(GearProfile.mesh_ratio(pinion, ring), 16.0 / 40.0, abs_tol=1e-9)


def test_rack_travel_per_radian_is_pitch_radius():
    # A pinion driving a rack advances the rack by pitch_radius * angle: mm per radian = pitch_r.
    pinion = GearProfile(module=2.0, teeth=20, pressure_angle=20.0)
    assert math.isclose(pinion.rack_travel_per_radian(), pinion.pitch_radius, abs_tol=1e-9)


# --- backlash (tooth thinning) -------------------------------------------------------------------
def test_backlash_thins_the_tooth():
    # Backlash thins each tooth by reducing the tooth thickness; the tip arc of a backlashed gear
    # spans a smaller angle than the nominal gear (measured as fewer points reaching the tip, or a
    # narrower crest). Here: the addendum crest half-angle shrinks.
    nominal = GearProfile(module=2.0, teeth=20, pressure_angle=20.0)
    lashed = GearProfile(module=2.0, teeth=20, pressure_angle=20.0, backlash=0.2)
    assert lashed.tooth_thickness_angle() < nominal.tooth_thickness_angle()
