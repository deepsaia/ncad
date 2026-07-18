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
        return artifacts


class _FailingBuilder:
    """Raises as a real build would on a schema-invalid document."""

    def build_file(self, path: str, out_dir: str) -> dict:
        raise ValueError("document failed schema validation: bad")


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
