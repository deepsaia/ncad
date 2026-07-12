import json
from pathlib import Path

import pytest

pytestmark = pytest.mark.slow  # composes real part glbs via the real kernel


def _write(path: Path, text: str) -> None:
    path.write_text(text)


def test_assemble_composes_scene_sidecar(tmp_path) -> None:
    from ncad.assembly.assembly_builder import AssemblyBuilder
    from ncad.kernel.build123d_kernel import Build123dKernel

    part = tmp_path / "peg.hocon"
    _write(part, """
schema_version = 2
units = mm
parts { peg { profile = solid, features = [
  { id = sk, op = sketch, plane = XY, elements = [ { id = c, type = circle, d = 8 } ] }
  { id = ext, op = extrude, profile = sk, distance = 20 }
] } }
""")
    asm = tmp_path / "pegs.asm.hocon"
    _write(asm, f"""
schema_version = 1
units = mm
assembly {{ instances = [
  {{ id = p1, file = "{part.name}", part = peg }}
  {{ id = p2, file = "{part.name}", part = peg, placement = {{ position = [20, 0, 0] }} }}
] }}
""")
    out = tmp_path / "out"
    result = AssemblyBuilder(Build123dKernel()).assemble(str(asm), str(out))

    assert not result["issues"], result["issues"]
    sidecar = json.loads(Path(result["sidecar"]).read_text())
    assert [i["id"] for i in sidecar["instances"]] == ["p1", "p2"]
    glbs = {i["part_glb"] for i in sidecar["instances"]}
    assert len(glbs) == 1  # shared part glb deduped
    assert (out / next(iter(glbs))).is_file()
    p2 = next(i for i in sidecar["instances"] if i["id"] == "p2")
    assert p2["placement"][3][0] == pytest.approx(0.020)  # 20mm baked to metres (glb unit)


def test_assemble_reports_bad_instance_ref(tmp_path) -> None:
    from ncad.assembly.assembly_builder import AssemblyBuilder
    from ncad.kernel.build123d_kernel import Build123dKernel

    asm = tmp_path / "bad.asm.hocon"
    _write(asm, """
schema_version = 1
units = mm
assembly { instances = [ { id = x, file = "missing.hocon", part = nope } ] }
""")
    out = tmp_path / "out"
    result = AssemblyBuilder(Build123dKernel()).assemble(str(asm), str(out))
    assert any(iss["instance_id"] == "x" for iss in result["issues"])
