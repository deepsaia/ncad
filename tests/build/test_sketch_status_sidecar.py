from ncad.build.sketch_status_sidecar import SketchStatusSidecar
from ncad.ops.sketch_status import SketchStatus


def test_write_then_read_round_trips(tmp_path):
    sidecar = SketchStatusSidecar(str(tmp_path))
    statuses = [SketchStatus("sk", "well", 0), SketchStatus("slot", "over", 0, ["c3"])]
    sidecar.write("bracket.glb", statuses)
    data = sidecar.read("bracket.glb")
    assert data == {"sketches": [
        {"feature_id": "sk", "status": "well", "dof": 0, "failing_ids": []},
        {"feature_id": "slot", "status": "over", "dof": 0, "failing_ids": ["c3"]},
    ]}


def test_empty_statuses_writes_empty_list(tmp_path):
    sidecar = SketchStatusSidecar(str(tmp_path))
    sidecar.write("plate.glb", [])
    assert sidecar.read("plate.glb") == {"sketches": []}


def test_read_missing_returns_none(tmp_path):
    assert SketchStatusSidecar(str(tmp_path)).read("nope.glb") is None
