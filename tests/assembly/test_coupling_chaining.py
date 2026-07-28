"""Coupling chaining: _motion_secondaries propagates motion through the coupling graph, one input.

A coupling enforces when its primary joint is ALREADY driven - directly by the driver OR by an
upstream gear/belt coupling's derived joint - so a multi-stage train runs from one input, composing
cumulative ratios. Pure over a synthetic document (no kernel).
"""

import ast
import math
import operator

import pytest

from ncad.assembly.assembly_builder import AssemblyBuilder

_OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
        ast.Div: operator.truediv, ast.Pow: operator.pow, ast.USub: operator.neg}
_FUNCS = {"sin": math.sin, "cos": math.cos}


def _eval(expr, t):
    def walk(node):
        if isinstance(node, ast.Expression):
            return walk(node.body)
        if isinstance(node, ast.Constant):
            return float(node.value)
        if isinstance(node, ast.Name) and node.id == "time":
            return t
        if isinstance(node, ast.BinOp):
            return _OPS[type(node.op)](walk(node.left), walk(node.right))
        if isinstance(node, ast.UnaryOp):
            return _OPS[type(node.op)](walk(node.operand))
        if isinstance(node, ast.Call):
            return _FUNCS[node.func.id](walk(node.args[0]))
        raise ValueError(ast.dump(node))
    return walk(ast.parse(expr, mode="eval"))


def _secondaries(couplings, driver_joint="pinA"):
    doc = {"assembly": {"couplings": couplings}}
    driver = {"joint_id": driver_joint, "joint_type": "revolute", "start": 0.0, "end": 360.0}
    issues = []
    secs = AssemblyBuilder(kernel=None)._motion_secondaries(doc, driver_joint, driver, issues)
    return {s["joint_id"]: s for s in secs}, issues


def test_two_stage_belt_train_composes_cumulative_ratio():
    # pinA drives pinB (0.5), pinB drives pinC (0.5) -> pinC sweeps 0.25 of the driver.
    by, issues = _secondaries([
        {"id": "s1", "type": "belt", "between": ["pinA", "pinB"], "ratio": 0.5},
        {"id": "s2", "type": "belt", "between": ["pinB", "pinC"], "ratio": 0.5},
    ])
    assert set(by) == {"pinB", "pinC"}
    assert issues == []
    assert math.degrees(_eval(by["pinB"]["expression"], 1.0)) == pytest.approx(180.0)
    assert math.degrees(_eval(by["pinC"]["expression"], 1.0)) == pytest.approx(90.0)


def test_chaining_is_order_independent():
    # the downstream coupling is listed FIRST; the fixpoint still enforces it after its primary.
    by, issues = _secondaries([
        {"id": "s2", "type": "belt", "between": ["pinB", "pinC"], "ratio": 0.5},
        {"id": "s1", "type": "belt", "between": ["pinA", "pinB"], "ratio": 0.5},
    ])
    assert set(by) == {"pinB", "pinC"}
    assert math.degrees(_eval(by["pinC"]["expression"], 1.0)) == pytest.approx(90.0)


def test_gear_sense_composes_along_the_chain():
    # two external gear meshes: each reverses, so the third gear turns the SAME sense as the driver.
    by, _ = _secondaries([
        {"id": "s1", "type": "gear", "between": ["pinA", "pinB"], "ratio": 1.0},
        {"id": "s2", "type": "gear", "between": ["pinB", "pinC"], "ratio": 1.0},
    ])
    # pinB reversed (-360), pinC reversed again (+360) -> same sense as pinA.
    assert math.degrees(_eval(by["pinB"]["expression"], 1.0)) == pytest.approx(-360.0)
    assert math.degrees(_eval(by["pinC"]["expression"], 1.0)) == pytest.approx(360.0)


def test_coupling_whose_primary_is_never_driven_is_left_out():
    # s2's primary (pinX) is neither the driver nor a driven output -> not enforced, no crash.
    by, issues = _secondaries([
        {"id": "s1", "type": "belt", "between": ["pinA", "pinB"], "ratio": 0.5},
        {"id": "s2", "type": "belt", "between": ["pinX", "pinC"], "ratio": 0.5},
    ])
    assert set(by) == {"pinB"}
    assert issues == []


def test_rack_output_is_not_a_chainable_primary():
    # a rack_pinion slide cannot drive a further angular coupling; the downstream stays unenforced.
    by, _ = _secondaries([
        {"id": "s1", "type": "rack_pinion", "between": ["pinA", "rack"],
         "gears": {"driver": {"module": 2.0, "teeth": 20},
                   "driven": {"module": 2.0, "teeth": 6, "gear_type": "rack"}}},
        {"id": "s2", "type": "belt", "between": ["rack", "pinC"], "ratio": 1.0},
    ])
    assert "rack" in by                 # the rack slide is driven
    assert "pinC" not in by             # but nothing chains off it


def test_direct_multi_coupling_still_works():
    # the planetary shape: several couplings all primaried directly on the driver (round-1 enforce).
    by, issues = _secondaries([
        {"id": "p0", "type": "gear", "between": ["pinA", "p0"], "ratio": 0.75},
        {"id": "p1", "type": "belt", "between": ["pinA", "p1"], "ratio": 0.25},
    ])
    assert set(by) == {"p0", "p1"}
    assert issues == []
