import json
import os

import pytest

pytestmark = pytest.mark.slow

_PART = '''schema_version = 2
units = mm
parts {
  disk { profile = solid, material = steel_1018,
    connectors = [ { id = axis, at = "select faces where type = 'cylinder'" } ],
    features = [
      { id = sk, op = sketch, plane = XY, elements = [ { id = c, type = circle, d = 30 } ] },
      { id = ext, op = extrude, profile = sk, distance = 6 } ] }
}'''

_ASM = '''schema_version = 1
units = mm
assembly {
  instances = [
    { id = base, file = "p.hocon", part = disk, lock = true }
    { id = wheel, file = "p.hocon", part = disk }
  ]
  joints = [
    { id = spin, type = revolute, between = [
      { instance = base, connector = axis }, { instance = wheel, connector = axis } ] } ]
}
motion { driver = { joint = spin, from = 0, to = 360, steps = 8 } }'''


def _write(tmp, name, text):
    path = os.path.join(tmp, name)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(text)
    return path


def test_motion_sidecar_has_a_frame_per_step(tmp_path):
    from ncad.assembly.assembly_builder import AssemblyBuilder
    from ncad.kernel.build123d_kernel import Build123dKernel

    _write(str(tmp_path), "p.hocon", _PART)
    asm = _write(str(tmp_path), "a.asm.hocon", _ASM)
    result = AssemblyBuilder(Build123dKernel()).assemble(asm, str(tmp_path))
    assert not result["issues"], result["issues"]
    assert result.get("motion") is not None
    motion = json.loads((tmp_path / "a.motion.json").read_text())
    assert motion["driver"]["joint"] == "spin"
    assert len(motion["frames"]) == 9  # steps=8 -> 9 inclusive frames
    frame = motion["frames"][2]
    assert "t" in frame and "driver_value" in frame and "status" in frame
    assert "wheel" in frame["placements"] and "base" in frame["placements"]
