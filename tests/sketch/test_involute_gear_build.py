import os

import pytest

pytestmark = pytest.mark.slow

_DOC = """units = mm
parts {
  gear { profile = solid, material = steel_4140,
    features = [
      { id = sk, op = sketch, plane = XY,
        entities = [
          { id = c, type = point, at = [0,0] }
          { id = g, type = involute_gear, module = 2, teeth = 16, pressure_angle = 20, center = c }
        ]
        constraints = [ { type = fix, of = c } ] }
      { id = body, op = extrude, profile = sk, distance = 6 }
    ] }
}"""


def test_involute_gear_entity_extrudes_to_a_solid(tmp_path):
    # An involute_gear sketch entity expands to a closed involute outline that extrudes to a valid
    # single-solid gear body (the sketch->extrude spine, no special op).
    from ncad.build.document_builder import DocumentBuilder
    from ncad.kernel.build123d_kernel import Build123dKernel

    path = os.path.join(str(tmp_path), "gear.hocon")
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(_DOC)
    artifacts = DocumentBuilder(Build123dKernel()).build_file(path, str(tmp_path))
    assert list(artifacts) == ["gear"]
    assert os.path.isfile(artifacts["gear"])
