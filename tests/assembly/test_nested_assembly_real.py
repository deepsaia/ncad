import json
import os

import pytest

pytestmark = pytest.mark.slow

_PART = '''units = mm
parts {
  block { profile = solid,
    features = [
      { id = sk, op = sketch, plane = XY,
        elements = [ { id = r, type = rectangle, w = 10, h = 10 } ] },
      { id = ext, op = extrude, profile = sk, distance = 10 } ] }
}'''

_CHILD = '''units = mm
assembly {
  instances = [
    { id = lower, file = "p.hocon", part = block, lock = true }
    { id = upper, file = "p.hocon", part = block, placement = { position = [0, 0, 10] } }
  ]
}'''

_PARENT = '''units = mm
assembly {
  instances = [
    { id = left, assembly = "child.asm.hocon", placement = { position = [0, 0, 0] } }
    { id = right, assembly = "child.asm.hocon", placement = { position = [40, 0, 0] } }
  ]
}'''

_SELF = '''units = mm
assembly {
  instances = [
    { id = me, assembly = "loop.asm.hocon" }
  ]
}'''


def _write(tmp, name, text):
    path = os.path.join(tmp, name)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(text)
    return path


def test_nested_sub_assembly_composes_and_namespaces(tmp_path):
    from ncad.assembly.assembly_builder import AssemblyBuilder
    from ncad.kernel.build123d_kernel import Build123dKernel

    _write(str(tmp_path), "p.hocon", _PART)
    _write(str(tmp_path), "child.asm.hocon", _CHILD)
    parent = _write(str(tmp_path), "parent.asm.hocon", _PARENT)
    result = AssemblyBuilder(Build123dKernel()).assemble(parent, str(tmp_path))
    assert not result["issues"], result["issues"]
    sidecar = json.loads((tmp_path / "parent.assembly.json").read_text())
    ids = {i["id"] for i in sidecar["instances"]}
    # Each sub-assembly's instances are namespaced under the parent instance id.
    assert {"left/lower", "left/upper", "right/lower", "right/upper"} <= ids
    left_lower = next(i for i in sidecar["instances"] if i["id"] == "left/lower")
    right_lower = next(i for i in sidecar["instances"] if i["id"] == "right/lower")
    # right is offset +40 mm in x from left (baked to metres: +0.04).
    assert right_lower["placement"][3][0] - left_lower["placement"][3][0] > 0.0


def test_circular_sub_assembly_is_id_attributed(tmp_path):
    from ncad.assembly.assembly_builder import AssemblyBuilder
    from ncad.kernel.build123d_kernel import Build123dKernel

    loop = _write(str(tmp_path), "loop.asm.hocon", _SELF)
    result = AssemblyBuilder(Build123dKernel()).assemble(loop, str(tmp_path))
    # The self-reference is caught as an id-attributed issue, not an infinite recursion.
    assert any("circular" in i["message"].lower() for i in result["issues"])
