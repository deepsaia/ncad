from pathlib import Path

from ncad.viewer.build_service import BuildService
from ncad.viewer.model_metadata import ModelMetadata


class _FakeBuilder:
    """Simulates DocumentBuilder: writes a glb into out/parts/box/ and reports it."""

    def build_file(self, path, out_dir, formats=("glb",), layout_kind="parts",
                   mesh_tolerance=None):
        part_dir = Path(out_dir) / "parts" / "box"
        part_dir.mkdir(parents=True, exist_ok=True)
        (part_dir / "box.glb").write_text("glb")
        return {"artifacts": {"box": str(part_dir / "box.glb")}, "diagnostics": []}


def test_build_writes_meta_into_part_dir(tmp_path):
    (tmp_path / "ex").mkdir()
    spec = tmp_path / "ex" / "box.hocon"
    spec.write_text("units = mm\nparts { box { features = [] } }\n")
    svc = BuildService(examples_dir=str(tmp_path / "ex"), models_dir=str(tmp_path / "out"),
                       builder_factory=lambda: _FakeBuilder(),
                       clock=lambda: "2026-01-01T00:00:00Z",
                       versions={"ncad": "t", "kernel": "t"})
    svc.build("box.hocon")
    meta_path = tmp_path / "out" / "parts" / "box" / "box.meta.json"
    assert meta_path.is_file()
    assert ModelMetadata(str(tmp_path / "out" / "parts" / "box")).read("box")["source"] \
        == "box.hocon"


def test_keyframes_path_is_in_robot_dir(tmp_path):
    # A robot exists (its tree sidecar present under out/robots/arm/) so _keyframes_path resolves
    # via the catalog's resolve_robot (which reads the new layout, Task 7). The keyframes sidecar
    # then lives WITH the robot, so delete_robot cleans it up.
    (tmp_path / "out" / "robots" / "arm").mkdir(parents=True)
    (tmp_path / "out" / "robots" / "arm" / "arm.robot.json").write_text("{}")
    svc = BuildService(examples_dir="", models_dir=str(tmp_path / "out"),
                       builder_factory=lambda: None)
    svc.save_robot_keyframes("arm", "wave", [{"time": 0, "pose": {}}])
    kf = tmp_path / "out" / "robots" / "arm" / "arm.keyframes.json"
    assert kf.is_file()
    assert "wave" in svc.read_robot_keyframes("arm")["sets"]
