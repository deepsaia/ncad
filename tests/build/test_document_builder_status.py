import json
import logging
from pathlib import Path

import pytest

from ncad.build.document_builder import DocumentBuilder


def _doc(tmp_path):
    src = """schema_version = 2
units = mm
parts {
  plate {
    profile = solid
    features = [
      {
        id = sk
        op = sketch
        plane = XY
        elements = [ { id = r, type = rectangle, w = 80, h = 60 } ]
      }
      { id = pad, op = extrude, profile = sk, distance = 8 }
    ]
  }
}
"""
    p = Path(tmp_path) / "plate.hocon"
    p.write_text(src)
    return str(p)


@pytest.mark.slow
def test_build_file_writes_status_sidecar(tmp_path):
    from ncad.kernel.build123d_kernel import Build123dKernel

    out = Path(tmp_path) / "out"
    DocumentBuilder(Build123dKernel()).build_file(_doc(tmp_path), str(out))
    sidecar = out / "plate.status.json"
    assert sidecar.is_file()
    data = json.loads(sidecar.read_text())
    assert data["sketches"][0]["feature_id"] == "sk"
    assert data["sketches"][0]["status"] == "well"


@pytest.mark.slow
def test_build_file_logs_status_line(tmp_path, caplog):
    from ncad.kernel.build123d_kernel import Build123dKernel

    caplog.set_level(logging.INFO)
    out = Path(tmp_path) / "out"
    DocumentBuilder(Build123dKernel()).build_file(_doc(tmp_path), str(out))
    assert any("sketch sk" in r.message and "well" in r.message for r in caplog.records)


@pytest.mark.slow
def test_underconstrained_example_reports_under(tmp_path):
    from ncad.kernel.build123d_kernel import Build123dKernel

    doc = "examples/gate-1.5/underconstrained_tab.hocon"
    out = str(tmp_path)
    DocumentBuilder(Build123dKernel()).build_file(doc, out)
    data = json.loads((Path(out) / "underconstrained_tab.status.json").read_text())
    sk = [s for s in data["sketches"] if s["feature_id"] == "sk"][0]
    assert sk["status"] == "under" and sk["dof"] > 0
