"""Build-stage: a normal solid's computed inertia passes the validator (no invalid_inertia)."""

import pytest

from ncad.build.document_builder import DocumentBuilder
from ncad.diagnostics import codes
from ncad.kernel.build123d_kernel import Build123dKernel

pytestmark = pytest.mark.slow

_BOX = """
units = mm
parts { blk { profile = solid, material = steel_1018, features = [
  { id = a, op = primitive, kind = box, w = 40, d = 30, h = 20, plane = XY, at = [ 0, 0 ] } ] } }
"""


def test_valid_solid_has_no_invalid_inertia(tmp_path):
    doc = tmp_path / "p.hocon"
    doc.write_text(_BOX)
    result = DocumentBuilder(Build123dKernel()).build_file(str(doc), str(tmp_path / "out"))
    # A plain steel box has a physically realizable centroidal tensor -> validator stays silent.
    assert not any(d.code == codes.INVALID_INERTIA for d in result["diagnostics"])
    assert result["artifacts"]        # geometry still built
