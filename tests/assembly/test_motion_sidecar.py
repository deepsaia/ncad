import json
import os

import pytest

pytestmark = pytest.mark.slow

_PART = '''units = mm
parts {
  disk { profile = solid, material = steel_1018,
    connectors = [ { id = axis, at = "select faces where type = 'cylinder'" } ],
    features = [
      { id = sk, op = sketch, plane = XY, elements = [ { id = c, type = circle, d = 30 } ] },
      { id = ext, op = extrude, profile = sk, distance = 6 } ] }
}'''

_ASM = '''units = mm
assembly {
  instances = [
    { id = base, file = "p.hocon", part = disk, lock = true }
    { id = wheel, file = "p.hocon", part = disk }
  ]
  joints = [
    { id = spin, type = revolute, between = [
      { instance = base, connector = axis }, { instance = wheel, connector = axis } ] } ]
}'''

_MOTION = '''motion {
  assembly = "a.asm.hocon"
  driver = { joint = spin, from = 0, to = 360, steps = 8 }
}'''

_MOTION_WITH_OUTPUTS = '''motion {
  assembly = "a.asm.hocon"
  driver = { joint = spin, from = 0, to = 360, steps = 8 }
  outputs {
    traces = [ { id = rimPath, instance = wheel, point = [15, 0, 0] } ]
    measures = [ { id = rimX, kind = coordinate, instance = wheel, point = [15, 0, 0], axis = x } ]
  }
}'''


def _write(tmp, name, text):
    path = os.path.join(tmp, name)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(text)
    return path


def test_motion_sidecar_has_a_frame_per_step(tmp_path):
    # A motion DOCUMENT (its own kind) drives the referenced assembly + writes the trajectory.
    from ncad.assembly.motion_builder import MotionBuilder
    from ncad.kernel.build123d_kernel import Build123dKernel

    _write(str(tmp_path), "p.hocon", _PART)
    _write(str(tmp_path), "a.asm.hocon", _ASM)
    motion_doc = _write(str(tmp_path), "a.motion.hocon", _MOTION)
    result = MotionBuilder(Build123dKernel()).build(motion_doc, str(tmp_path))
    assert not result["issues"], result["issues"]
    assert result.get("motion") is not None
    motion = json.loads((tmp_path / "a.motion.json").read_text())
    assert motion["driver"]["joint"] == "spin"
    assert len(motion["frames"]) == 9  # steps=8 -> 9 inclusive frames
    frame = motion["frames"][2]
    assert "t" in frame and "driver_value" in frame and "status" in frame
    assert "wheel" in frame["placements"] and "base" in frame["placements"]


def test_motion_sidecar_always_has_dof_block(tmp_path):
    # The mobility (DoF) report is emitted for every motion, even without an outputs block:
    # schema_version bumps to 2, traces/measures are empty, dof carries the solver's free DoF.
    from ncad.assembly.motion_builder import MotionBuilder
    from ncad.kernel.build123d_kernel import Build123dKernel

    _write(str(tmp_path), "p.hocon", _PART)
    _write(str(tmp_path), "a.asm.hocon", _ASM)
    motion_doc = _write(str(tmp_path), "a.motion.hocon", _MOTION)
    MotionBuilder(Build123dKernel()).build(motion_doc, str(tmp_path))
    motion = json.loads((tmp_path / "a.motion.json").read_text())
    assert motion["schema_version"] == 2
    assert motion["traces"] == [] and motion["measures"] == []
    assert "gruebler" in motion["dof"] and "solver" in motion["dof"] and "status" in motion["dof"]


def test_motion_sidecar_emits_declared_traces_and_measures(tmp_path):
    # A motion with an `outputs` block emits a trace polyline (one vertex per frame) + a measure
    # time series (one value per frame) alongside the trajectory.
    from ncad.assembly.motion_builder import MotionBuilder
    from ncad.kernel.build123d_kernel import Build123dKernel

    _write(str(tmp_path), "p.hocon", _PART)
    _write(str(tmp_path), "a.asm.hocon", _ASM)
    motion_doc = _write(str(tmp_path), "a.motion.hocon", _MOTION_WITH_OUTPUTS)
    result = MotionBuilder(Build123dKernel()).build(motion_doc, str(tmp_path))
    assert not result["issues"], result["issues"]
    motion = json.loads((tmp_path / "a.motion.json").read_text())
    n = len(motion["frames"])
    assert len(motion["traces"]) == 1 and motion["traces"][0]["id"] == "rimPath"
    assert len(motion["traces"][0]["polyline"]) == n
    assert len(motion["measures"]) == 1 and motion["measures"][0]["id"] == "rimX"
    assert motion["measures"][0]["unit"] == "mm" and len(motion["measures"][0]["series"]) == n


def test_assembly_without_motion_writes_no_trajectory(tmp_path):
    # An assembly doc alone (no motion study) builds the scene but no trajectory sidecar.
    from ncad.assembly.assembly_builder import AssemblyBuilder
    from ncad.kernel.build123d_kernel import Build123dKernel

    _write(str(tmp_path), "p.hocon", _PART)
    asm = _write(str(tmp_path), "a.asm.hocon", _ASM)
    result = AssemblyBuilder(Build123dKernel()).assemble(asm, str(tmp_path))
    assert not result["issues"], result["issues"]
    assert result.get("motion") is None
    assert not (tmp_path / "a.motion.json").exists()
