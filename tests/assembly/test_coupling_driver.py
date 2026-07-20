import ast
import math
import operator

import pytest

from ncad.assembly.coupling_driver import CouplingDriver, CouplingDriverError


# A primary driver as _run_motion builds it: the driven joint + its type + the degree value sweep.
def _primary(joint_id="pinionPin", jtype="revolute", start=0.0, end=360.0):
    return {"joint_id": joint_id, "joint_type": jtype, "start": start, "end": end}


def test_gear_reverses_sense_by_ratio():
    # gear: coupled angle = -ratio * primary. Second `between` joint is the coupled (derived) one.
    coupling = {"id": "mesh", "type": "gear", "between": ["pinionPin", "gearPin"], "ratio": 0.6667}
    sec = CouplingDriver().secondary(coupling, _primary())
    assert sec["joint_id"] == "gearPin"
    assert sec["joint_type"] == "revolute"
    # expression is radians in time: -ratio * (a0_rad + span_rad*time); a0=0, span=2pi.
    # sample it at a few times by eval with time substituted.
    for t in (0.0, 0.25, 0.5, 1.0):
        got = _eval(sec["expression"], t)
        want = -0.6667 * (math.radians(360.0) * t)
        assert math.isclose(got, want, rel_tol=1e-9, abs_tol=1e-12)


def test_belt_keeps_sense():
    coupling = {"id": "b", "type": "belt", "between": ["aPin", "bPin"], "ratio": 2.0}
    sec = CouplingDriver().secondary(coupling, _primary(joint_id="aPin"))
    got = _eval(sec["expression"], 0.5)
    want = 2.0 * (math.radians(360.0) * 0.5)   # +ratio, same sense
    assert math.isclose(got, want, rel_tol=1e-9)


def test_rack_pinion_converts_rotation_to_slide_mm_to_m():
    # rack_pinion: coupled SLIDE (metres) = ratio(mm/rad) * primary_angle(rad) / 1000.
    coupling = {"id": "rp", "type": "rack_pinion", "between": ["pinionPin", "rackSlide"],
                "ratio": 15.0}
    sec = CouplingDriver().secondary(coupling, _primary())
    assert sec["joint_type"] == "slider"   # the derived joint is a translational slide
    got = _eval(sec["expression"], 1.0)     # full sweep: 2pi rad
    want = 15.0 * math.radians(360.0) / 1000.0   # mm/rad * rad -> mm -> m
    assert math.isclose(got, want, rel_tol=1e-9)


def test_bad_ratio_raises():
    with pytest.raises(CouplingDriverError, match="ratio"):
        CouplingDriver().secondary(
            {"id": "g", "type": "gear", "between": ["a", "b"], "ratio": 0.0},
            _primary(joint_id="a"))


def test_primary_must_be_first_between_joint():
    # The driver must drive the coupling's FIRST between joint; else it is not enforceable here.
    coupling = {"id": "g", "type": "gear", "between": ["aPin", "bPin"], "ratio": 1.0}
    with pytest.raises(CouplingDriverError, match="drive"):
        CouplingDriver().secondary(coupling, _primary(joint_id="somethingElse"))


def test_unknown_type_raises():
    with pytest.raises(CouplingDriverError, match="type"):
        CouplingDriver().secondary(
            {"id": "u", "type": "universal", "between": ["a", "b"], "ratio": 1.0},
            _primary(joint_id="a"))


def test_gear_ratio_derived_from_gears_block():
    # With a `gears` block the ratio comes from GearProfile.mesh_ratio (one source of truth): a 16-
    # tooth pinion driving a 24-tooth gear -> external mesh, ratio = -16/24, reversing sense.
    coupling = {"id": "mesh", "type": "gear", "between": ["pinionPin", "gearPin"],
                "gears": {"driver": {"module": 2.0, "teeth": 16},
                          "driven": {"module": 2.0, "teeth": 24}}}
    sec = CouplingDriver().secondary(coupling, _primary())
    got = _eval(sec["expression"], 1.0)
    want = (-16.0 / 24.0) * math.radians(360.0)
    assert math.isclose(got, want, rel_tol=1e-9)


def test_internal_gear_ratio_keeps_sense_from_gears_block():
    # An internal (ring) mesh keeps sense: a pinion driving a ring gear -> positive ratio.
    coupling = {"id": "planet", "type": "gear", "between": ["pinionPin", "ringPin"],
                "gears": {"driver": {"module": 2.0, "teeth": 16},
                          "driven": {"module": 2.0, "teeth": 40, "gear_type": "internal"}}}
    sec = CouplingDriver().secondary(coupling, _primary())
    got = _eval(sec["expression"], 1.0)
    want = (16.0 / 40.0) * math.radians(360.0)   # positive: same sense
    assert math.isclose(got, want, rel_tol=1e-9)


def test_rack_pinion_travel_derived_from_gears_block():
    # rack_pinion with a `gears` block: the rack travel per radian is the pinion pitch radius
    # (module 2, teeth 20 -> pitch r = 20 mm/rad). Slide (metres) = pitch_r * angle / 1000.
    coupling = {"id": "rp", "type": "rack_pinion", "between": ["pinionPin", "rackSlide"],
                "gears": {"driver": {"module": 2.0, "teeth": 20},
                          "driven": {"module": 2.0, "teeth": 6, "gear_type": "rack"}}}
    sec = CouplingDriver().secondary(coupling, _primary())
    assert sec["joint_type"] == "slider"
    got = _eval(sec["expression"], 1.0)
    want = 20.0 * math.radians(360.0) / 1000.0
    assert math.isclose(got, want, rel_tol=1e-9)


def test_malformed_gears_block_raises():
    coupling = {"id": "mesh", "type": "gear", "between": ["pinionPin", "gearPin"],
                "gears": {"driver": {"module": 2.0}, "driven": {"module": 2.0, "teeth": 24}}}
    with pytest.raises(CouplingDriverError, match="gears"):
        CouplingDriver().secondary(coupling, _primary())


def test_scotch_yoke_slide_is_a_sine():
    # yoke slide (metres) = amplitude(mm)/1000 * sin(primary_angle). amplitude 30 mm, sweep 0..360.
    coupling = {"id": "sy", "type": "scotch_yoke", "between": ["crankPin", "yokeSlide"],
                "amplitude": 30.0}
    sec = CouplingDriver().secondary(coupling, _primary(joint_id="crankPin"))
    assert sec["joint_id"] == "yokeSlide" and sec["joint_type"] == "slider"
    for t in (0.0, 0.25, 0.5):
        got = _eval(sec["expression"], t)
        want = 0.030 * math.sin(math.radians(360.0) * t)
        assert math.isclose(got, want, rel_tol=1e-9, abs_tol=1e-12)


def test_geneva_expression_tracks_wheel_angle():
    from ncad.sketch.geneva_wheel import GenevaWheel

    coupling = {"id": "gv", "type": "geneva", "between": ["crankPin", "wheelPin"],
                "geneva": {"slots": 4, "crank_radius": 30.0}}
    sec = CouplingDriver().secondary(coupling, _primary(joint_id="crankPin"))
    assert sec["joint_id"] == "wheelPin" and sec["joint_type"] == "revolute"
    wheel = GenevaWheel(slots=4, crank_radius=30.0)
    for i in range(0, 100):
        t = i / 100.0
        got_deg = math.degrees(_eval(sec["expression"], t))
        assert abs(got_deg - wheel.wheel_angle(360.0 * t)) < 3.0   # Fourier fit within 3 deg


def test_geneva_expression_is_smooth():
    coupling = {"id": "gv", "type": "geneva", "between": ["crankPin", "wheelPin"],
                "geneva": {"slots": 4, "crank_radius": 30.0}}
    sec = CouplingDriver().secondary(coupling, _primary(joint_id="crankPin"))
    for token in ("min", "max", "abs", ">", "<", "if"):
        assert token not in sec["expression"]


def test_scotch_yoke_needs_amplitude():
    coupling = {"id": "sy", "type": "scotch_yoke", "between": ["crankPin", "yokeSlide"]}
    with pytest.raises(CouplingDriverError, match="amplitude"):
        CouplingDriver().secondary(coupling, _primary(joint_id="crankPin"))


_OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
        ast.Div: operator.truediv, ast.USub: operator.neg, ast.UAdd: operator.pos,
        ast.Pow: operator.pow}
_FUNCS = {"sin": math.sin, "cos": math.cos}


def _eval(expr, t):
    # Safely evaluate a coupling-driver arithmetic expression at time t via a numeric-only AST walk
    # (numbers + - * / ** , the name `time`, and bare sin()/cos()). No eval(); rejects anything
    # but arithmetic + sin/cos on `time`.
    def walk(node):
        if isinstance(node, ast.Expression):
            return walk(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return float(node.value)
        if isinstance(node, ast.Name) and node.id == "time":
            return t
        if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
            return _OPS[type(node.op)](walk(node.left), walk(node.right))
        if isinstance(node, ast.UnaryOp) and type(node.op) in _OPS:
            return _OPS[type(node.op)](walk(node.operand))
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                and node.func.id in _FUNCS and len(node.args) == 1):
            return _FUNCS[node.func.id](walk(node.args[0]))
        raise ValueError(f"unexpected node {ast.dump(node)}")

    return walk(ast.parse(expr, mode="eval"))
