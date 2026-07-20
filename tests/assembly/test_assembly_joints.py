import json
from pathlib import Path

import pytest

pytestmark = pytest.mark.slow


def _write(p: Path, s: str) -> None:
    p.write_text(s)


_PARTS = """
units = mm
parts {
  bracket { profile = solid,
    connectors = [ { id = pivot, at = "select faces where type = 'cylinder'" } ],
    features = [
      { id = sk, op = sketch, plane = XY, elements = [ { id = c, type = circle, d = 40 } ] }
      { id = ext, op = extrude, profile = sk, distance = 6 }
    ] }
  lever { profile = solid,
    connectors = [ { id = hub, at = "select faces where type = 'cylinder'" } ],
    features = [
      { id = sk, op = sketch, plane = XY, elements = [ { id = c, type = circle, d = 12 } ] }
      { id = ext, op = extrude, profile = sk, distance = 25 }
    ] }
}
"""


def test_revolute_joint_solves_and_records_signature(tmp_path) -> None:
    from ncad.assembly.assembly_builder import AssemblyBuilder
    from ncad.kernel.build123d_kernel import Build123dKernel

    part = tmp_path / "parts.hocon"
    _write(part, _PARTS)
    asm = tmp_path / "pinned.asm.hocon"
    _write(asm, f"""
units = mm
assembly {{
  instances = [
    {{ id = base, file = "{part.name}", part = bracket, lock = true }}
    {{ id = arm, file = "{part.name}", part = lever }}
  ]
  joints = [
    {{ id = j1, type = revolute, between = [
       {{ instance = base, connector = pivot }}, {{ instance = arm, connector = hub }} ] }}
  ]
}}
""")
    out = tmp_path / "out"
    result = AssemblyBuilder(Build123dKernel()).assemble(str(asm), str(out))
    assert not result["issues"], result["issues"]
    sidecar = json.loads((out / "pinned.assembly.json").read_text())
    joints = sidecar["joints"]
    assert len(joints) == 1
    j = joints[0]
    assert j["id"] == "j1" and j["type"] == "revolute"
    # The declared signature is authoritative for "leaves 1 rotational DoF"; the solver dof is a
    # gauge-sensitive cross-check (not asserted here).
    assert j["signature"] == [{"motion": "rotation", "axis": "Z"}]
    assert j["ok"] is True


_SLOT_PARTS = """
units = mm
parts {
  stand { profile = solid, material = steel_1018,
    connectors = [
      { id = crankBearing, at_point = [ 0, 0, 0 ], axis = [ 0, 0, 1 ] }
      { id = guide, at_point = [ 0, 0, 14 ], axis = [ 1, 0, 0 ] }
    ],
    features = [ { id = base, op = primitive, kind = box, w = 120, d = 80, h = 8,
      plane = XY, plane_offset = -16, at = [ -60, -40 ] } ] }
  crank { profile = solid, material = steel_4140,
    connectors = [
      { id = axis, at_point = [ 0, 0, 0 ], axis = [ 0, 0, 1 ] }
      { id = pin, at_point = [ 30, 0, 4 ], axis = [ 0, 0, 1 ] }
    ],
    features = [
      { id = disc, op = primitive, kind = cylinder, d = 20, h = 8, plane = XY, at = [ 0, 0 ] }
      { id = pinp, op = primitive, kind = cylinder, d = 8, h = 8, plane = XY, at = [ 30, 0 ] }
      { id = w, op = boolean, operation = union, target = disc, tool = pinp } ] }
  yoke { profile = solid, material = bronze,
    connectors = [
      { id = slide, at_point = [ 0, 0, 14 ], axis = [ 1, 0, 0 ] }
      { id = slot, at_point = [ 0, 0, 14 ], axis = [ 0, 1, 0 ] }
    ],
    features = [ { id = plate, op = primitive, kind = box, w = 20, d = 80, h = 8,
      plane = XY, plane_offset = 10, at = [ -10, -40 ] } ] }
}
"""


def test_point_in_line_joint_drives_scotch_yoke_natively(tmp_path) -> None:
    # A driven crank whose pin is held on the yoke's slot line by a REAL point_in_line joint (no
    # coupling law): the crank turns a full revolution and the yoke slides +/-30mm (2x the 30mm pin).
    from ncad.assembly.motion_builder import MotionBuilder
    from ncad.kernel.build123d_kernel import Build123dKernel

    part = tmp_path / "slot.hocon"
    _write(part, _SLOT_PARTS)
    asm = tmp_path / "slot.asm.hocon"
    _write(asm, f"""
units = mm
assembly {{
  instances = [
    {{ id = stand, file = "{part.name}", part = stand, lock = true }}
    {{ id = crank, file = "{part.name}", part = crank }}
    {{ id = yoke, file = "{part.name}", part = yoke }}
  ]
  joints = [
    {{ id = crankPin, type = revolute, between = [
       {{ instance = stand, connector = crankBearing }}, {{ instance = crank, connector = axis }} ] }}
    {{ id = yokeSlide, type = slider, between = [
       {{ instance = stand, connector = guide }}, {{ instance = yoke, connector = slide }} ] }}
    {{ id = pinInSlot, type = point_in_line, between = [
       {{ instance = crank, connector = pin }}, {{ instance = yoke, connector = slot }} ] }}
  ]
}}
""")
    motion = tmp_path / "slot.motion.hocon"
    _write(motion, """
units = mm
motion { assembly = "slot.asm.hocon"
  driver = { joint = crankPin, from = 0, to = 360, steps = 24 } }
""")
    out = tmp_path / "out"
    MotionBuilder(Build123dKernel()).build(str(motion), str(out))
    traj = json.loads((out / "slot.motion.json").read_text())
    xs = [fr["placements"]["yoke"][3][0] for fr in traj["frames"]]
    # yoke travel = 2 * crank pin radius = 0.06 m (metres); a real slot joint, not a scotch_yoke law.
    assert round(max(xs) - min(xs), 3) == 0.06
