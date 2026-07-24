import json

import pytest

from ncad.viewer.build_service import BuildError, BuildService


class _StubBuilder:
    """Writes a fake glb per part, standing in for DocumentBuilder."""

    def __init__(self, out_names) -> None:
        self._out_names = out_names

    def build_file(self, path: str, out_dir: str) -> dict:
        import os

        artifacts = {}
        for name in self._out_names:
            glb = os.path.join(out_dir, f"{name}.glb")
            with open(glb, "wb") as handle:
                handle.write(b"glb")
            artifacts[name] = glb
        return {"artifacts": artifacts, "diagnostics": []}


class _FailingBuilder:
    """Raises as a real build would on a genuine kernel/OS error (not a design issue)."""

    def build_file(self, path: str, out_dir: str) -> dict:
        raise RuntimeError("kernel export failed")


def _service(tmp_path, out_names=("block",)):
    examples = tmp_path / "examples"
    (examples / "g").mkdir(parents=True)
    (examples / "g" / "block.hocon").write_text("x")
    out = tmp_path / "out"
    out.mkdir()
    service = BuildService(
        str(examples),
        str(out),
        builder_factory=lambda: _StubBuilder(out_names),
        clock=lambda: "2026-07-02T00:00:00Z",
        versions={"ncad": "0.0.1", "kernel": "build123d-0.10.0"},
    )
    return service, examples, out


def test_build_allows_spec_under_examples(tmp_path) -> None:
    service, _, out = _service(tmp_path)

    result = service.build("g/block.hocon")

    assert result["built"] == ["block.glb"]
    # build_ms is a wall-clock measurement (varies), so assert its presence + type, not a value.
    assert isinstance(result["build_ms"], float) and result["build_ms"] >= 0.0
    assert (out / "block.glb").is_file()
    assert (out / "block.meta.json").is_file()


def test_build_writes_source_into_meta(tmp_path) -> None:
    service, _, out = _service(tmp_path)

    service.build("g/block.hocon")

    data = json.loads((out / "block.meta.json").read_text())
    assert data["source"] == "g/block.hocon"
    assert data["built_at"] == "2026-07-02T00:00:00Z"


def test_build_rejects_spec_outside_examples(tmp_path) -> None:
    service, _, _ = _service(tmp_path)

    with pytest.raises(BuildError):
        service.build("../elsewhere/evil.hocon")


def test_build_allows_recorded_meta_source(tmp_path) -> None:
    service, _, out = _service(tmp_path)
    external = tmp_path / "external.hocon"
    external.write_text("x")
    (out / "prev.glb").write_bytes(b"x")
    (out / "prev.meta.json").write_text(json.dumps({"source": str(external)}))

    result = service.build(str(external))

    assert result["built"] == ["block.glb"]


def test_build_wraps_builder_failure_as_builderror(tmp_path) -> None:
    examples = tmp_path / "examples"
    (examples / "g").mkdir(parents=True)
    (examples / "g" / "block.hocon").write_text("x")
    out = tmp_path / "out"
    out.mkdir()
    service = BuildService(
        str(examples),
        str(out),
        builder_factory=lambda: _FailingBuilder(),
        clock=lambda: "t",
        versions={"ncad": "0.0.1", "kernel": "k"},
    )

    with pytest.raises(BuildError):
        service.build("g/block.hocon")


def test_motion_regenerate_allows_recorded_trajectory_source(tmp_path) -> None:
    # After a page reload the viewer's Regenerate passes the source recorded in <name>.motion.json
    # (an absolute path, not under examples). It must be allowed when a built trajectory records it.
    service, _, out = _service(tmp_path)
    external = tmp_path / "study.motion.hocon"
    external.write_text("x")
    (out / "mech.motion.json").write_text(json.dumps({"name": "mech", "source": str(external)}))

    assert service._allowed_motion_path(str(external)) == str(external)


def test_motion_regenerate_rejects_unrecorded_external_source(tmp_path) -> None:
    service, _, out = _service(tmp_path)
    external = tmp_path / "study.motion.hocon"
    external.write_text("x")
    # No trajectory records this source, and it is outside examples: not allowed.
    assert service._allowed_motion_path(str(external)) is None


def test_analyze_allows_spec_under_examples(tmp_path) -> None:
    service, examples, _ = _service(tmp_path)
    (examples / "g" / "bracket.analysis.hocon").write_text("x")
    assert service._allowed_analysis_path(str(examples / "g" / "bracket.analysis.hocon")) \
        is not None


def test_analyze_rejects_spec_outside_examples(tmp_path) -> None:
    service, _, _ = _service(tmp_path)
    with pytest.raises(BuildError):
        service.analyze("../elsewhere/evil.analysis.hocon")


def test_save_and_read_robot_keyframes_round_trip(tmp_path) -> None:
    # The sidecar keys off a built robot tree, so plant one; then save + read back a named set.
    service, _, out = _service(tmp_path)
    (out / "arm.robot.json").write_text('{"base_link": "b", "links": [], "joints": []}')
    frames = [{"time": 0.0, "pose": {"elbow": 0.0}}, {"time": 1.5, "pose": {"elbow": 1.2}}]

    result = service.save_robot_keyframes("arm", "kfmotion_01", frames)

    assert result == {"sets": ["kfmotion_01"]}
    assert service.read_robot_keyframes("arm")["sets"]["kfmotion_01"] == frames


def test_save_robot_keyframes_upserts_and_deletes_named_sets(tmp_path) -> None:
    service, _, out = _service(tmp_path)
    (out / "arm.robot.json").write_text('{"base_link": "b", "links": [], "joints": []}')
    service.save_robot_keyframes("arm", "a", [{"time": 0, "pose": {"j": 0.0}}])
    service.save_robot_keyframes("arm", "b", [{"time": 0, "pose": {"j": 1.0}}])
    assert service.read_robot_keyframes("arm")["sets"].keys() == {"a", "b"}

    # Saving an empty list deletes that set; the other set survives.
    assert service.save_robot_keyframes("arm", "a", []) == {"sets": ["b"]}
    assert set(service.read_robot_keyframes("arm")["sets"]) == {"b"}


def test_save_robot_keyframes_unknown_robot_raises(tmp_path) -> None:
    service, _, _ = _service(tmp_path)
    with pytest.raises(BuildError):
        service.save_robot_keyframes("ghost", "s", [{"time": 0, "pose": {}}])


def test_clean_keyframes_sanitizes_bad_entries(tmp_path) -> None:
    service, _, out = _service(tmp_path)
    (out / "arm.robot.json").write_text('{"base_link": "b", "links": [], "joints": []}')
    dirty = [
        {"time": 2, "pose": {"j": 3, "bad": "x"}},   # non-numeric pose value dropped
        {"time": "nope"},                            # no pose -> whole frame dropped
        "not-a-dict",                                # dropped
    ]
    service.save_robot_keyframes("arm", "s", dirty)
    saved = service.read_robot_keyframes("arm")["sets"]["s"]
    assert saved == [{"time": 2.0, "pose": {"j": 3.0}}]
