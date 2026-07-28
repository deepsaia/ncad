"""MotionLivenessChecker: detect a frozen-but-'solved' trajectory (no body actually moved)."""

import math

from ncad.assembly.motion_liveness import MotionLivenessChecker

_IDENTITY = [[1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]]


def _rot_z(deg):
    r = math.radians(deg)
    return [[math.cos(r), math.sin(r), 0.0, 0.0], [-math.sin(r), math.cos(r), 0.0, 0.0],
            [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]]


def _frame(placements):
    return {"status": "solved", "placements": placements}


def test_all_frozen_is_not_alive():
    # every body sits at rest on every frame: the frozen-but-solved case
    frames = [_frame({"ground": _IDENTITY, "arm": _IDENTITY}),
              _frame({"ground": _IDENTITY, "arm": _IDENTITY})]
    out = MotionLivenessChecker().assess(frames, ground_ids={"ground"})
    assert out["any_moved"] is False
    assert out["frozen"] == ["arm"]
    assert out["moved"] == []
    assert out["movable"] == 1


def test_a_rotating_body_counts_as_moved():
    frames = [_frame({"ground": _IDENTITY, "arm": _rot_z(0)}),
              _frame({"ground": _IDENTITY, "arm": _rot_z(90)})]
    out = MotionLivenessChecker().assess(frames, ground_ids={"ground"})
    assert out["any_moved"] is True
    assert out["moved"] == ["arm"]
    assert out["frozen"] == []


def test_partial_freeze_lists_both():
    # arm/0 sweeps, arm/1 stays frozen (a coupling the solver dropped)
    frames = [_frame({"post": _IDENTITY, "arm/0": _rot_z(0), "arm/1": _IDENTITY}),
              _frame({"post": _IDENTITY, "arm/0": _rot_z(90), "arm/1": _IDENTITY})]
    out = MotionLivenessChecker().assess(frames, ground_ids={"post"})
    assert out["any_moved"] is True                 # something moved...
    assert out["moved"] == ["arm/0"]
    assert out["frozen"] == ["arm/1"]               # ...but arm/1 is flagged frozen


def test_translation_only_counts_as_moved():
    slid = [row[:] for row in _IDENTITY]
    slid[3][0] = 0.05  # 50 mm in metres
    frames = [_frame({"base": _IDENTITY, "slider": _IDENTITY}),
              _frame({"base": _IDENTITY, "slider": slid})]
    out = MotionLivenessChecker().assess(frames, ground_ids={"base"})
    assert out["moved"] == ["slider"]


def test_grounded_bodies_are_not_expected_to_move():
    frames = [_frame({"base": _IDENTITY, "arm": _rot_z(0)}),
              _frame({"base": _IDENTITY, "arm": _rot_z(45)})]
    out = MotionLivenessChecker().assess(frames, ground_ids={"base"})
    assert out["movable"] == 1                       # base excluded from the movable count
    assert out["frozen"] == []


def test_single_frame_is_not_assessable():
    out = MotionLivenessChecker().assess([_frame({"arm": _IDENTITY})], ground_ids=set())
    assert out["any_moved"] is False
    assert out["movable"] == 0


def test_full_revolution_returns_to_start_but_is_not_frozen():
    # a 0..360 driver: first and LAST frame share the rest pose, yet the body genuinely spins.
    # A first-vs-last check would wrongly call this frozen; scanning all frames catches the swing.
    frames = [_frame({"base": _IDENTITY, "arm": _rot_z(0)}),
              _frame({"base": _IDENTITY, "arm": _rot_z(180)}),
              _frame({"base": _IDENTITY, "arm": _rot_z(360)})]  # back to start
    out = MotionLivenessChecker().assess(frames, ground_ids={"base"})
    assert out["any_moved"] is True
    assert out["moved"] == ["arm"]
    assert out["frozen"] == []


def test_noise_below_tolerance_is_still_frozen():
    jittered = [row[:] for row in _IDENTITY]
    jittered[3][0] = 1e-9  # sub-tolerance numeric noise
    frames = [_frame({"base": _IDENTITY, "arm": _IDENTITY}),
              _frame({"base": _IDENTITY, "arm": jittered})]
    out = MotionLivenessChecker().assess(frames, ground_ids={"base"})
    assert out["frozen"] == ["arm"]
