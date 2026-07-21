"""End-to-end: a .physics doc exports a URDF (computed inertials + meshes) that MuJoCo loads."""

import pytest

from ncad.kernel.build123d_kernel import Build123dKernel
from ncad.robotics import RobotModelBuilder, UrdfWriter

pytestmark = pytest.mark.slow

_PHYSICS = "examples/08-robotics/crank_slider.physics.hocon"


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
