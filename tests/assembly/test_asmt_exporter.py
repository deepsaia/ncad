"""Unit tests for AsmtExporter: ncad assembly -> pyondsel model mapping.

Verifies the mapping pieces without invoking the solver: pose (mm 4x4 -> metres pose), mass terms
(with the unit fallback for density-less parts), joint-kind translation, per-part markers + anchor,
and in-place grounding. A slow end-to-end solve is covered by the motion examples.
"""

import pytest

from ncad.assembly.asmt_exporter import AsmtExporter
from ncad.assembly.connector_frame import ConnectorFrame

pyondsel = pytest.importorskip("pyondsel")

_IDENTITY = [[1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]]


def _placement(tx_mm, ty_mm, tz_mm):
    m = [row[:] for row in _IDENTITY]
    m[3][0], m[3][1], m[3][2] = tx_mm, ty_mm, tz_mm
    return m


def _base_args():
    instances = [{"id": "base"}, {"id": "arm"}]
    local_frames = {
        "base": {"pivot": ConnectorFrame.from_axis((0, 0, 0), (0, 0, 1))},
        "arm": {"hub": ConnectorFrame.from_axis((10, 0, 0), (0, 0, 1))},
    }
    placements = {"base": _placement(0, 0, 0), "arm": _placement(0, 0, 0)}
    mass = {"base": {"mass": 2.0, "cog": (1.0, 0.0, 0.0),
                     "inertia": {"principal": [0.1, 0.2, 0.3]}}}
    joints = [{"id": "spin", "type": "revolute",
               "between": [{"instance": "base", "connector": "pivot"},
                           {"instance": "arm", "connector": "hub"}]}]
    driver = {"joint_id": "spin", "joint_type": "revolute",
              "pivot": joints[0]["between"][0], "moving": joints[0]["between"][1],
              "values": [0.0, 90.0, 180.0]}
    return instances, local_frames, placements, mass, joints, driver


def test_build_model_maps_parts_markers_joints_and_driver():
    instances, frames, placements, mass, joints, driver = _base_args()
    model = AsmtExporter().build_model("Rig", instances, frames, placements, mass, joints,
                                       {"base"}, driver, to_metres=0.001)
    names = {p.name for p in model.parts}
    assert names == {"base", "arm"}
    # base carries real mass + principal inertia; every part gets an _anchor marker.
    base = next(p for p in model.parts if p.name == "base")
    assert base.mass == 2.0
    assert base.moments_of_inertia == (0.1, 0.2, 0.3)
    assert "_anchor" in {m.name for m in base.markers}
    assert "pivot" in {m.name for m in base.markers}
    # the declared revolute + the driver motion are present.
    asmt = model.to_asmt()
    assert "RevoluteJoint" in asmt
    assert "RotationalMotion" in asmt


def test_grounded_part_is_fixed_in_place():
    instances, frames, placements, mass, joints, driver = _base_args()
    placements["base"] = _placement(5000, 0, 0)  # base sits 5 m out; must be held THERE
    model = AsmtExporter().build_model("Rig", instances, frames, placements, mass, joints,
                                       {"base"}, driver, to_metres=0.001)
    asmt = model.to_asmt()
    assert "FixedJoint" in asmt
    # the world marker grounding base is placed at base's rest position (5 m), not the origin.
    ground = next(m for m in model.ground_markers if m.name == "world_base")
    assert ground.position == (5.0, 0.0, 0.0)


def test_density_less_part_falls_back_to_unit_mass():
    instances, frames, placements, _mass, joints, driver = _base_args()
    model = AsmtExporter().build_model("Rig", instances, frames, placements, {}, joints,
                                       {"base"}, driver, to_metres=0.001)
    arm = next(p for p in model.parts if p.name == "arm")
    assert arm.mass == 1.0  # unit fallback keeps the solve well-posed
    assert arm.moments_of_inertia == (1.0, 1.0, 1.0)


def test_slider_driver_maps_to_translational_motion():
    instances, frames, placements, mass, _joints, _driver = _base_args()
    joints = [{"id": "slide", "type": "slider",
               "between": [{"instance": "base", "connector": "pivot"},
                           {"instance": "arm", "connector": "hub"}]}]
    driver = {"joint_id": "slide", "joint_type": "slider",
              "pivot": joints[0]["between"][0], "moving": joints[0]["between"][1],
              "values": [0.0, 12.0]}
    model = AsmtExporter().build_model("Rig", instances, frames, placements, mass, joints,
                                       {"base"}, driver, to_metres=0.001)
    asmt = model.to_asmt()
    assert "TranslationalJoint" in asmt
    assert "TranslationalMotion" in asmt


def test_non_drivable_joint_type_raises():
    instances, frames, placements, mass, joints, driver = _base_args()
    driver["joint_type"] = "fixed"
    with pytest.raises(ValueError):
        AsmtExporter().build_model("Rig", instances, frames, placements, mass, joints,
                                   {"base"}, driver, to_metres=0.001)
