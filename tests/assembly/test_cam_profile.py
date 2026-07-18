import ast
import math
import operator

import pytest

from ncad.assembly.cam_profile import CamProfile, CamProfileError

# --- a safe numeric evaluator for the emitted motion expressions --------------------------------
# The cam expression is arithmetic on `time` plus bare sin()/cos() calls (the OndselSolver grammar).
# Evaluate it without eval(): a numeric-only AST walk that also understands sin/cos calls.
_OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
        ast.Div: operator.truediv, ast.USub: operator.neg, ast.UAdd: operator.pos,
        ast.Pow: operator.pow}
_FUNCS = {"sin": math.sin, "cos": math.cos}


def _eval(expr, t):
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


def _engine_cam():
    # A recognizable engine-style cam: a 180 deg base-circle dwell, then a cycloidal rise to 12 mm
    # over 90 deg, then a cycloidal return over 90 deg. Closes back to the base circle at 360.
    return CamProfile.from_profile({
        "base_r": 20,
        "segments": [
            {"kind": "dwell", "angle": 180},
            {"kind": "rise", "law": "cycloidal", "angle": 90, "lift": 12},
            {"kind": "return", "law": "cycloidal", "angle": 90},
        ],
    })


# --- legacy single-law form (backward compatible sugar) -----------------------------------------
def test_legacy_harmonic_displacement_rises_and_returns():
    cam = CamProfile.from_profile({"law": "harmonic", "base_r": 20, "lift": 12, "lobes": 1})
    assert math.isclose(cam.displacement(0.0), 0.0, abs_tol=1e-9)
    assert math.isclose(cam.displacement(180.0), 12.0, abs_tol=1e-9)
    assert math.isclose(cam.displacement(360.0), 0.0, abs_tol=1e-9)
    assert math.isclose(cam.displacement(90.0), 6.0, abs_tol=1e-9)


def test_legacy_harmonic_two_lobes_peaks_twice():
    cam = CamProfile.from_profile({"law": "harmonic", "base_r": 20, "lift": 10, "lobes": 2})
    assert math.isclose(cam.displacement(90.0), 10.0, abs_tol=1e-9)
    assert math.isclose(cam.displacement(180.0), 0.0, abs_tol=1e-9)
    assert math.isclose(cam.displacement(270.0), 10.0, abs_tol=1e-9)


def test_legacy_sine_law_rises_and_returns():
    cam = CamProfile.from_profile({"law": "sine", "base_r": 15, "lift": 8, "lobes": 1})
    assert math.isclose(cam.displacement(0.0), 0.0, abs_tol=1e-9)
    assert math.isclose(cam.displacement(180.0), 8.0, abs_tol=1e-9)
    assert math.isclose(cam.displacement(360.0), 0.0, abs_tol=1e-9)


def test_displacement_is_never_negative():
    cam = _engine_cam()
    for deg in range(0, 361, 3):
        assert cam.displacement(float(deg)) >= -1e-9


def test_radius_is_base_plus_displacement():
    cam = CamProfile.from_profile({"law": "harmonic", "base_r": 20, "lift": 12, "lobes": 1})
    assert math.isclose(cam.radius(0.0), 20.0, abs_tol=1e-9)
    assert math.isclose(cam.radius(180.0), 32.0, abs_tol=1e-9)


def test_legacy_expression_is_smooth_and_in_metres():
    cam = CamProfile.from_profile({"law": "harmonic", "base_r": 20, "lift": 12, "lobes": 1})
    expr = cam.expression(a0_deg=0.0, span_deg=360.0)
    assert isinstance(expr, str) and "time" in expr
    for token in ("min", "max", "abs", ">", "<", "if"):
        assert token not in expr


def test_bad_law_raises():
    with pytest.raises(CamProfileError, match="law"):
        CamProfile.from_profile({"law": "nope", "base_r": 20, "lift": 12, "lobes": 1})


def test_bad_legacy_params_raise():
    with pytest.raises(CamProfileError):
        CamProfile.from_profile({"law": "harmonic", "base_r": -1, "lift": 12, "lobes": 1})
    with pytest.raises(CamProfileError):
        CamProfile.from_profile({"law": "harmonic", "base_r": 20, "lift": 0, "lobes": 1})
    with pytest.raises(CamProfileError):
        CamProfile.from_profile({"law": "harmonic", "base_r": 20, "lift": 12, "lobes": 0})


# --- segmented (general) form -------------------------------------------------------------------
def test_segmented_dwell_rise_return_hits_exact_levels():
    cam = _engine_cam()
    # Dwell region: flat on the base circle.
    for deg in (0.0, 90.0, 179.0):
        assert math.isclose(cam.displacement(deg), 0.0, abs_tol=1e-9)
    # Rise midpoint (225 deg, half of the 180..270 rise): half the lift for cycloidal.
    assert math.isclose(cam.displacement(225.0), 6.0, abs_tol=1e-9)
    # Nose: peak lift at the rise/return junction (270 deg).
    assert math.isclose(cam.displacement(270.0), 12.0, abs_tol=1e-9)
    # Closed: back to the base circle at 360.
    assert math.isclose(cam.displacement(360.0), 0.0, abs_tol=1e-9)


def test_segments_must_sum_to_360():
    with pytest.raises(CamProfileError, match="360"):
        CamProfile.from_profile({"base_r": 20, "segments": [
            {"kind": "dwell", "angle": 180},
            {"kind": "rise", "law": "cycloidal", "angle": 90, "lift": 12},
        ]})


def test_segments_must_return_to_base():
    # Rises 12 but never returns: not a closed periodic profile.
    with pytest.raises(CamProfileError, match="base"):
        CamProfile.from_profile({"base_r": 20, "segments": [
            {"kind": "dwell", "angle": 180},
            {"kind": "rise", "law": "cycloidal", "angle": 180, "lift": 12},
        ]})


def test_segmented_expression_fourier_tracks_displacement():
    cam = _engine_cam()
    expr = cam.expression(a0_deg=0.0, span_deg=360.0)
    assert isinstance(expr, str) and "time" in expr
    for token in ("min", "max", "abs", ">", "<", "if"):
        assert token not in expr
    # The Fourier expression (metres, over t 0..1) must approximate displacement (mm) within 0.3 mm.
    for i in range(0, 100):
        t = i / 100.0
        theta = 360.0 * t
        got_mm = _eval(expr, t) * 1000.0
        assert abs(got_mm - cam.displacement(theta)) < 0.3


def test_profile_points_show_base_circle_and_a_distinct_nose():
    cam = _engine_cam()
    pts = cam.profile_points(360)
    radii = [math.hypot(x, y) for x, y in pts]
    # Most of the outline sits on the base circle (the 180 deg dwell), and there is a clear nose.
    assert max(radii) > 20 + 0.9 * 12         # nose reaches near base + lift
    assert min(radii) == pytest.approx(20.0, abs=1e-6)   # base circle
    on_base = sum(1 for r in radii if abs(r - 20.0) < 0.5)
    assert on_base > len(radii) * 0.4          # a large flat base-circle arc (the dwell)
