"""End-to-end: a .physics doc exports MJCF that MuJoCo loads with the loop kept as an equality."""

import pytest

from ncad.kernel.build123d_kernel import Build123dKernel
from ncad.robotics import MjcfWriter, RobotModelBuilder

pytestmark = pytest.mark.slow

_PHYSICS = "examples/08-robotics/crank_slider_mjcf.physics.hocon"


def test_mjcf_loads_in_mujoco_with_loop_equality(tmp_path):
    import mujoco

    model, warnings = RobotModelBuilder(Build123dKernel()).build(_PHYSICS, str(tmp_path))
    xml_path = tmp_path / "robot.xml"
    xml_path.write_text(MjcfWriter().to_xml(model))

    mj = mujoco.MjModel.from_xml_path(str(xml_path))
    # world + 4 bodies; the crank-slider loop is kept as one equality constraint (URDF drops it).
    assert mj.nbody == 5
    assert mj.neq == 1
    assert mj.nu == 1                 # the actuated main pin
    data = mujoco.MjData(mj)
    mujoco.mj_step(mj, data)          # simulates a step without error


def test_mjcf_uses_computed_masses(tmp_path):
    import mujoco

    model, _ = RobotModelBuilder(Build123dKernel()).build(_PHYSICS, str(tmp_path))
    xml_path = tmp_path / "robot.xml"
    xml_path.write_text(MjcfWriter().to_xml(model))
    mj = mujoco.MjModel.from_xml_path(str(xml_path))
    # Distinct, real per-body masses (not the unit fallback that would make them all equal).
    masses = [round(float(m), 4) for m in mj.body_mass[1:]]  # skip the world body
    assert len(set(masses)) > 1
