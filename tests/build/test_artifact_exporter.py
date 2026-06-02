"""Tests for ArtifactExporter: writes a model file plus a BOM sidecar.

Runs against the FakeKernel (no OCP), since it only checks orchestration: the right
files appear with the right contents. The BOM is computed from the spec, written next to
the model so the viewer can load quantities without re-deriving them from the mesh.
"""

import json

from ncad.build.artifact_exporter import ArtifactExporter
from tests.kernel.fake_kernel import FakeKernel


def _spec() -> dict:
    return {
        "schema_version": 1,
        "seed": 1,
        "units": "m",
        "storeys": [
            {
                "elevation": 0.0,
                "height": 3.0,
                "walls": [{"id": "w0", "start": [0.0, 0.0], "end": [6.0, 0.0], "thickness": 0.2}],
                "rooms": [{"id": "r0", "polygon": [[0, 0], [6, 0], [6, 4], [0, 4]]}],
            }
        ],
        "roof": {"kind": "flat", "thickness": 0.2},
    }


def test_writes_model_bom_and_plan_sidecars(tmp_path) -> None:
    exporter = ArtifactExporter(FakeKernel())

    result = exporter.export(_spec(), str(tmp_path), "house")

    model = tmp_path / "house.glb"
    bom = tmp_path / "house.bom.json"
    plan = tmp_path / "house.plan.svg"
    assert model.exists()
    assert bom.exists()
    assert plan.exists()
    assert result["model"] == str(model)
    assert result["bom"] == str(bom)
    assert result["plan"] == str(plan)


def test_plan_sidecar_is_svg(tmp_path) -> None:
    ArtifactExporter(FakeKernel()).export(_spec(), str(tmp_path), "house")

    plan = (tmp_path / "house.plan.svg").read_text()
    assert "</svg>" in plan


def test_bom_sidecar_has_quantities(tmp_path) -> None:
    ArtifactExporter(FakeKernel()).export(_spec(), str(tmp_path), "house")

    data = json.loads((tmp_path / "house.bom.json").read_text())
    assert data["floor_area"] == 24.0
    assert "wall_volume" in data
    assert data["door_count"] == 0


def test_export_is_deterministic(tmp_path) -> None:
    ArtifactExporter(FakeKernel()).export(_spec(), str(tmp_path), "a")
    ArtifactExporter(FakeKernel()).export(_spec(), str(tmp_path), "b")

    assert (tmp_path / "a.bom.json").read_text() == (tmp_path / "b.bom.json").read_text()
