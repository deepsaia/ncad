import json
from pathlib import Path

import pytest

pytestmark = pytest.mark.slow


def _write(p: Path, s: str) -> None:
    p.write_text(s)


# A part file with ONE part, instanced many times, so redundant per-instance rebuilds would show as
# load/build counts scaling with the instance count.
_PART = """
schema_version = 2
units = mm
parts {
  peg { profile = solid,
    connectors = [ { id = base, at = "select faces where normal_z < -0.9" } ],
    features = [
      { id = sk, op = sketch, plane = XY, elements = [ { id = c, type = circle, d = 8 } ] }
      { id = ext, op = extrude, profile = sk, distance = 10 }
    ] }
}
"""


def test_part_file_built_once_regardless_of_instance_count(tmp_path, monkeypatch) -> None:
    from ncad.assembly import assembly_builder as ab
    from ncad.build.document_builder import DocumentBuilder
    from ncad.kernel.build123d_kernel import Build123dKernel

    part = tmp_path / "p.hocon"
    _write(part, _PART)
    # Five instances of the SAME part+file, placed apart (no solve needed).
    insts = "\n".join(
        f'    {{ id = i{n}, file = "p.hocon", part = peg,'
        f' placement = {{ position = [{n * 15}, 0, 0] }} }}'
        for n in range(5))
    asm = tmp_path / "many.asm.hocon"
    _write(asm, f"schema_version = 1\nunits = mm\nassembly {{ instances = [\n{insts}\n] }}\n")

    # Count how many times the part document is actually built (build_part_mapped runs the ops).
    calls = {"n": 0}
    real = DocumentBuilder.build_file
    real_resolve = DocumentBuilder.resolve_part_elements

    def counting_build_file(self, path, out_dir, formats=("glb",)):
        calls["n"] += 1
        return real(self, path, out_dir, formats=formats)

    def counting_resolve(self, path):
        calls["n"] += 1
        return real_resolve(self, path)

    monkeypatch.setattr(DocumentBuilder, "build_file", counting_build_file)
    monkeypatch.setattr(DocumentBuilder, "resolve_part_elements", counting_resolve)

    out = tmp_path / "out"
    result = ab.AssemblyBuilder(Build123dKernel()).assemble(str(asm), str(out))
    assert not result["issues"], result["issues"]
    # One distinct part file: it should build for the glb once + resolve connectors once, NOT once
    # per instance. So the combined count is bounded (<= 2), not 5+ (the O(N-instances) blowup).
    assert calls["n"] <= 2, f"part file rebuilt {calls['n']} times for 5 instances (should dedup)"
    # And the composed scene still has all five instances placed.
    sidecar = json.loads((out / "many.assembly.json").read_text())
    assert len(sidecar["instances"]) == 5
