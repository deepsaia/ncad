import pytest

from ncad.build.document_builder import DocumentBuilder
from ncad.kernel.build123d_kernel import Build123dKernel

pytestmark = pytest.mark.slow

_BOX = ('units = mm\nparts { box { profile = solid, features = [\n'
        '  { id = a, op = primitive, kind = box, w = 40, d = 30, h = 20, plane = XY,'
        ' at = [ 0, 0 ] } ] } }\n')


def test_build_file_writes_part_into_kind_subdir(tmp_path):
    doc = tmp_path / "box.hocon"
    doc.write_text(_BOX)
    out = tmp_path / "out"
    result = DocumentBuilder(Build123dKernel()).build_file(str(doc), str(out), formats=("glb",))
    art = result["artifacts"]["box"].replace("\\", "/")
    assert art.endswith("/out/parts/box/box.glb")
    assert (out / "parts" / "box" / "box.facts.json").is_file()
    assert (out / "parts" / "box" / "box.hierarchy.json").is_file()


def test_build_file_layout_kind_none_writes_flat(tmp_path):
    doc = tmp_path / "box.hocon"
    doc.write_text(_BOX)
    exact = tmp_path / "assemblies" / "crank"   # caller-chosen exact dir (assembly member case)
    result = DocumentBuilder(Build123dKernel()).build_file(
        str(doc), str(exact), formats=("glb",), layout_kind=None)
    art = result["artifacts"]["box"].replace("\\", "/")
    assert art.endswith("/assemblies/crank/box.glb")   # flat, bare name, no parts/ subdir
    assert (exact / "box.glb").is_file()
