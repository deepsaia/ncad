"""Robot forward kinematics + self-collision: rest pose is identity, and non-adjacent overlaps at
a folded pose are detected while adjacent joint fits and in-limit poses stay clear."""

import json
import math

import pytest

from ncad.kernel.build123d_kernel import Build123dKernel
from ncad.robotics.robot_collision_checker import RobotCollisionChecker
from ncad.robotics.robot_forward_kinematics import RobotForwardKinematics
from ncad.robotics.robot_model_builder import RobotModelBuilder

pytestmark = pytest.mark.slow

_ARM = "examples/08-robotics/desk_arm.physics.hocon"


def _tree(tmp_path) -> dict:
    model, _ = RobotModelBuilder(Build123dKernel()).build(_ARM, str(tmp_path))
    return json.loads(
        json.dumps({  # the .robot.json shape the checker + FK consume
            "base_link": model.base_link,
            "joints": [{"name": j.name, "type": j.joint_type, "parent": j.parent, "child": j.child,
                        "axis": list(j.axis), "origin": list(j.origin_xyz),
                        "loop_closure": j.is_loop_closure} for j in model.joints],
        }))


def test_fk_rest_pose_is_identity_per_link(tmp_path):
    # At the all-zero pose the arm is unchanged (parts authored in-place), so every link's node
    # placement is the identity matrix - nothing shifts when the panel opens.
    nodes = RobotForwardKinematics().solve(_tree(tmp_path), {})
    identity = [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]
    for link, matrix in nodes.items():
        for r in range(4):
            for c in range(4):
                assert matrix[r][c] == pytest.approx(identity[r][c], abs=1e-9), link


def test_fk_elbow_rotation_folds_the_forearm_down(tmp_path):
    # Rotating the elbow 180 deg folds the forearm back around the elbow pin (z=0.184 m), so its
    # node translation carries it to ~2x the elbow height (a fold), not off into space.
    nodes = RobotForwardKinematics().solve(_tree(tmp_path), {"elbow": math.pi})
    tz = nodes["forearm"][3][2]   # row-major: translation in the last row
    assert tz == pytest.approx(0.368, abs=1e-3)


def test_pose_within_limits_is_collision_free(tmp_path):
    tree = _tree(tmp_path)
    checker = RobotCollisionChecker(Build123dKernel())
    for pose in ({}, {"elbow": math.radians(-120)}, {"wrist": math.radians(120)},
                 {"shoulder": math.radians(-95), "elbow": math.radians(-120)}):
        assert checker.check(_ARM, tree, pose) == []


def test_out_of_range_fold_is_detected_as_self_collision(tmp_path):
    # Beyond the authored limits the arm folds into itself; the checker reports the non-adjacent
    # colliding pairs (adjacent joint fits are excluded). elbow=180 overlaps the wrist-side links.
    tree = _tree(tmp_path)
    checker = RobotCollisionChecker(Build123dKernel())
    collisions = checker.check(_ARM, tree, {"elbow": math.pi})
    assert collisions, "elbow 180 deg should self-collide"
    pairs = {frozenset({c["a"], c["b"]}) for c in collisions}
    # the folded forearm/hand chain hits the upper arm or turret (non-adjacent), never a
    # parent-child pair (those touch at the pin by design and are filtered out).
    assert all(len(p) == 2 for p in pairs)
    assert any("hand" in p or "forearm" in p for p in pairs)
