from ncad.viewer.model_metadata import ModelMetadata


def test_write_then_read_roundtrip(tmp_path) -> None:
    meta = ModelMetadata(str(tmp_path))

    path = meta.write(
        "block.glb",
        source="examples/g/block.hocon",
        built_at="2026-07-02T00:00:00Z",
        ncad_version="0.0.1",
        kernel_version="build123d-0.10.0",
    )

    assert path.endswith("block.meta.json")
    data = meta.read("block.glb")
    assert data["source"] == "examples/g/block.hocon"
    assert data["built_at"] == "2026-07-02T00:00:00Z"
    assert data["ncad_version"] == "0.0.1"
    assert data["kernel_version"] == "build123d-0.10.0"


def test_read_missing_returns_none(tmp_path) -> None:
    assert ModelMetadata(str(tmp_path)).read("absent.glb") is None
