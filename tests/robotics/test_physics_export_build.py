"""End-to-end: a .physics doc exports a URDF (computed inertials + meshes) that MuJoCo loads."""

import pytest

from ncad.kernel.build123d_kernel import Build123dKernel
from ncad.robotics import RobotModelBuilder, UrdfWriter

pytestmark = pytest.mark.slow

_PHYSICS = "examples/08-robotics/crank_slider.physics.hocon"
# The 5-DoF arm is an OPEN serial chain with mixed joint axes (Z yaw, Y pitch, X grip) at distinct
# z-stations, so it exercises the parent-relative origin + per-joint axis derivation that the
# single-joint crank-slider could not.
_ARM = "examples/08-robotics/desk_arm.physics.hocon"


def test_model_has_computed_inertials_and_meshes(tmp_path):
    model, warnings = RobotModelBuilder(Build123dKernel()).build(_PHYSICS, str(tmp_path))
    # Four links, each with a real (non-fallback) computed mass and an exported mesh.
    assert len(model.links) == 4
    for link in model.links:
        assert link.mass > 0.0
        assert link.mesh is not None
        assert (tmp_path / link.mesh).is_file()
    # The masses are the distinct part masses, not the unit fallback (which would make them all 1).
    assert len({round(link.mass, 4) for link in model.links}) > 1


def test_closed_loop_is_flagged_and_excluded(tmp_path):
    model, warnings = RobotModelBuilder(Build123dKernel()).build(_PHYSICS, str(tmp_path))
    # The crank-slider closes a loop: 4 joints total, 3 in the tree, 1 loop closure reported.
    assert len(model.tree_joints()) == 3
    assert len(model.loop_closures()) == 1
    assert any("closes a kinematic loop" in w for w in warnings)


def test_arm_joint_origins_are_parent_relative_and_axes_derived(tmp_path):
    # Guards the two robot-export bugs the single-joint crank-slider masked:
    #  1. joint origin must be PARENT-relative (the URDF contract), not the child's absolute world
    #     position, and not double-converted to metres (elbow z=184mm -> 0.184 m relative to the
    #     upper-arm base, i.e. the 0.120 m upper-arm length, NOT 0.000184).
    #  2. the joint axis must come from the connector frame (Z pitch about world Y => (0,1,0)), not
    #     a hardcoded (0,0,1).
    model, _ = RobotModelBuilder(Build123dKernel()).build(_ARM, str(tmp_path))
    joints = {j.name: j for j in model.joints}
    # Parent-relative origins chain down the tree: each is the link length, not the absolute height.
    assert joints["base_yaw"].origin_xyz == pytest.approx((0.0, 0.0, 0.016), abs=1e-6)
    assert joints["shoulder"].origin_xyz == pytest.approx((0.0, 0.0, 0.048), abs=1e-6)
    assert joints["elbow"].origin_xyz == pytest.approx((0.0, 0.0, 0.120), abs=1e-6)
    assert joints["wrist"].origin_xyz == pytest.approx((0.0, 0.0, 0.100), abs=1e-6)
    assert joints["grip"].origin_xyz == pytest.approx((0.019, 0.0, 0.032), abs=1e-6)
    # Axes are per-joint: base_yaw about Z, the arm pitches about Y, the grip slides along X.
    assert joints["base_yaw"].axis == pytest.approx((0.0, 0.0, 1.0), abs=1e-6)
    assert joints["shoulder"].axis == pytest.approx((0.0, 1.0, 0.0), abs=1e-6)
    assert joints["elbow"].axis == pytest.approx((0.0, 1.0, 0.0), abs=1e-6)
    assert joints["wrist"].axis == pytest.approx((0.0, 1.0, 0.0), abs=1e-6)
    assert joints["grip"].axis == pytest.approx((1.0, 0.0, 0.0), abs=1e-6)


def test_arm_urdf_loads_in_mujoco_as_five_dof_chain(tmp_path):
    import mujoco

    model, _ = RobotModelBuilder(Build123dKernel()).build(_ARM, str(tmp_path))
    urdf_path = tmp_path / "arm.urdf"
    urdf_path.write_text(UrdfWriter().to_xml(model))
    mj = mujoco.MjModel.from_xml_path(str(urdf_path))
    assert mj.nbody == 6          # base + 5 tree-linked bodies (open chain, no loop closure)
    assert mj.njnt == 5           # all five joints are in the tree
    data = mujoco.MjData(mj)
    mujoco.mj_step(mj, data)      # it simulates a step without error


def test_exported_urdf_loads_in_mujoco(tmp_path):
    import mujoco

    model, _ = RobotModelBuilder(Build123dKernel()).build(_PHYSICS, str(tmp_path))
    urdf_path = tmp_path / "robot.urdf"
    urdf_path.write_text(UrdfWriter().to_xml(model))

    mj = mujoco.MjModel.from_xml_path(str(urdf_path))
    assert mj.nbody == 4          # base + 3 tree-linked bodies
    assert mj.njnt == 3           # the three spanning-tree joints
    data = mujoco.MjData(mj)
    mujoco.mj_step(mj, data)      # it simulates a step without error
