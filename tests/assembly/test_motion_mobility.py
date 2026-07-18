from ncad.assembly.motion_mobility import MotionMobility


def _joint(jtype):
    return {"type": jtype}


def test_crank_slider_planar_gruebler_is_one():
    # 4 links (ground, flywheel, rod, piston), 4 lower pairs (3 revolute + 1 slider):
    # M = 3(n-1) - 2*4 = 9 - 8 = 1. The static rest solve reports 0 free DoF (well-constrained), but
    # the mechanism's MOBILITY is 1, so status is mobile off the Gruebler count.
    joints = [_joint("revolute"), _joint("revolute"), _joint("revolute"), _joint("slider")]
    report = MotionMobility().report(joints, instance_count=4, solver_dof=0)
    assert report["gruebler"] == 1
    assert report["solver"] == 0
    assert report["status"] == "mobile"


def test_four_bar_planar_gruebler_is_one():
    # 4 links, 4 revolute: M = 3(3) - 2*4 = 1.
    joints = [_joint("revolute")] * 4
    report = MotionMobility().report(joints, instance_count=4, solver_dof=0)
    assert report["gruebler"] == 1 and report["status"] == "mobile"


def test_cam_follower_higher_pair_gives_one_dof():
    # 3 links (stand, cam, follower), a revolute + a slider (2 lower pairs) + a cam coupling (1
    # higher pair): M = 3(3-1) - 2 - 2 - 1 = 1. Without counting the coupling it would read 2.
    joints = [_joint("revolute"), _joint("slider")]
    report = MotionMobility().report(joints, instance_count=3, solver_dof=0, coupling_count=1)
    assert report["gruebler"] == 1 and report["status"] == "mobile"


def test_gear_pair_coupling_gives_one_dof():
    # 3 links (base, pinion, gear), 2 revolute + a gear coupling: M = 3(2) - 2 - 2 - 1 = 1.
    joints = [_joint("revolute"), _joint("revolute")]
    report = MotionMobility().report(joints, instance_count=3, solver_dof=0, coupling_count=1)
    assert report["gruebler"] == 1


def test_locked_when_gruebler_not_positive():
    joints = [_joint("revolute")] * 5   # over-constrained planar loop -> Gruebler 3(3)-2*5 = -1
    report = MotionMobility().report(joints, instance_count=4, solver_dof=0)
    assert report["gruebler"] == -1 and report["status"] == "locked"


def test_higher_pair_counts_one_constraint():
    # A slot/point_on_line is a higher pair (removes 1 planar DoF). 3 links, 1 revolute + 1 slot:
    # M = 3(2) - 2*1 - 1*1 = 6 - 3 = 3? no: revolute lower (2), slot higher (1) -> 6-2-1 = 3.
    joints = [_joint("revolute"), _joint("slot")]
    report = MotionMobility().report(joints, instance_count=3, solver_dof=3)
    assert report["gruebler"] == 3
