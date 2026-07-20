"""Build-stage: a part that fuses into disjoint solids emits the disconnected_solid info diagnostic."""

import pytest

from ncad.build.document_builder import DocumentBuilder
from ncad.diagnostics import codes
from ncad.kernel.build123d_kernel import Build123dKernel

pytestmark = pytest.mark.slow

_DISJOINT = """
units = mm
parts { twobox { profile = solid, material = steel_1018, features = [
  { id = a, op = primitive, kind = box, w = 10, d = 10, h = 10, plane = XY, at = [ 0, 0 ] }
  { id = b, op = primitive, kind = box, w = 10, d = 10, h = 10, plane = XY, at = [ 50, 0 ] }
  { id = u, op = boolean, operation = union, target = a, tool = b } ] } }
"""

_CONNECTED = """
units = mm
parts { onebox { profile = solid, material = steel_1018, features = [
  { id = a, op = primitive, kind = box, w = 10, d = 10, h = 10, plane = XY, at = [ 0, 0 ] }
  { id = b, op = primitive, kind = box, w = 10, d = 10, h = 10, plane = XY, at = [ 5, 0 ] }
  { id = u, op = boolean, operation = union, target = a, tool = b } ] } }
"""


def _build(tmp_path, hocon):
    doc = tmp_path / "p.hocon"
    doc.write_text(hocon)
    return DocumentBuilder(Build123dKernel()).build_file(str(doc), str(tmp_path / "out"))


def test_disjoint_fuse_reports_disconnected_solid(tmp_path):
    result = _build(tmp_path, _DISJOINT)
    disc = [d for d in result["diagnostics"] if d.code == codes.DISCONNECTED_SOLID]
    assert len(disc) == 1
    assert disc[0].severity == "info"        # never blocks; the part still exported
    assert "2 disjoint solids" in disc[0].message
    assert result["artifacts"]               # geometry still built


def test_connected_fuse_is_silent(tmp_path):
    # Two overlapping boxes fuse into ONE solid -> no disconnected_solid diagnostic.
    result = _build(tmp_path, _CONNECTED)
    assert not any(d.code == codes.DISCONNECTED_SOLID for d in result["diagnostics"])
