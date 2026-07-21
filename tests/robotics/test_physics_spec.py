"""PhysicsSpec validates the .physics overlay: assembly ref, base, per-joint semantics, export."""

import pytest

from ncad.robotics.physics_spec import PhysicsSpec, PhysicsSpecError


def _doc():
    return {"physics": {
        "assembly": "arm.asm.hocon", "base": "link0",
        "joints": {"j1": {"actuated": True, "limit": [-3.14, 3.14], "effort": 50, "damping": 0.1}},
        "export": {"format": "urdf", "mesh": "stl"}}}


def test_reads_assembly_base_and_export():
    spec = PhysicsSpec(_doc())
    assert spec.assembly == "arm.asm.hocon"
    assert spec.base_link == "link0"
    assert spec.export_format == "urdf"
    assert spec.mesh_format == "stl"


def test_joint_overlay_returns_authored_semantics():
    overlay = PhysicsSpec(_doc()).joint_overlay("j1")
    assert overlay["limit"] == [-3.14, 3.14]
    assert overlay["effort"] == 50
    assert PhysicsSpec(_doc()).joint_overlay("absent") == {}


def test_missing_physics_block_raises():
    with pytest.raises(PhysicsSpecError, match="top-level 'physics'"):
        PhysicsSpec({"assembly": "x"})


def test_missing_assembly_raises():
    with pytest.raises(PhysicsSpecError, match="'assembly' reference"):
        PhysicsSpec({"physics": {"base": "l0"}})


def test_unsupported_format_raises():
    with pytest.raises(PhysicsSpecError, match="unsupported export format"):
        PhysicsSpec({"physics": {"assembly": "a", "export": {"format": "step"}}})


def test_base_defaults_to_none_when_absent():
    spec = PhysicsSpec({"physics": {"assembly": "a"}})
    assert spec.base_link is None
    assert spec.mesh_format == "stl"  # default
