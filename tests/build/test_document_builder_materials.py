import json
from pathlib import Path

import pytest

from ncad.build.document_builder import DocumentBuilder

pytestmark = pytest.mark.slow

_EXAMPLES = Path(__file__).resolve().parents[2] / "examples"


def _sidecar(tmp_path, hocon, part_name):
    from ncad.kernel.build123d_kernel import Build123dKernel
    DocumentBuilder(Build123dKernel()).build_file(str(hocon), str(tmp_path))
    data = json.loads((tmp_path / f"{part_name}.elementmap.json").read_text())
    return data["elements"]


def test_multibody_sidecar_carries_per_body_material(tmp_path):
    els = _sidecar(tmp_path, _EXAMPLES / "gate-3.5" / "materials_part.hocon",
                   "materials_part")
    mats = {e.get("material") for e in els}
    assert "aluminium_6061" in mats and "steel_1018" in mats
    assert all("body_id" in e and "material" in e for e in els)


def test_materialless_part_sidecar_has_null_material(tmp_path):
    els = _sidecar(tmp_path, _EXAMPLES / "gate-0.1-first-shape" / "block.hocon", "block")
    assert all(e["material"] is None for e in els)
