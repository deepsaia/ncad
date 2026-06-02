"""Tests for the spec loader: JSON and HOCON files -> plain dict.

The loader wraps leaf-common's easy persistence. HOCON is the eventual authoring
format for architecture specs, so it is a first-class path here, not an afterthought.
"""

import pytest

from ncad.spec.spec_loader import SpecLoader


def test_loads_json_file_to_dict(tmp_path) -> None:
    path = tmp_path / "spec.json"
    path.write_text('{"schema_version": 1, "seed": 42}')

    result = SpecLoader().load(str(path))

    assert result == {"schema_version": 1, "seed": 42}


def test_loads_hocon_file_to_dict(tmp_path) -> None:
    path = tmp_path / "spec.hocon"
    path.write_text("schema_version = 1\nseed = 42\n")

    result = SpecLoader().load(str(path))

    assert result == {"schema_version": 1, "seed": 42}


def test_hocon_resolves_substitutions(tmp_path) -> None:
    """HOCON ${...} substitutions resolve at load time — useful for shared defaults."""
    path = tmp_path / "spec.hocon"
    path.write_text("thickness = 0.2\nwall_thickness = ${thickness}\n")

    result = SpecLoader().load(str(path))

    assert result["wall_thickness"] == 0.2


def test_unknown_extension_raises_value_error(tmp_path) -> None:
    path = tmp_path / "spec.yaml"
    path.write_text("schema_version: 1")

    with pytest.raises(ValueError, match="unsupported"):
        SpecLoader().load(str(path))


def test_missing_file_raises_file_not_found(tmp_path) -> None:
    with pytest.raises(FileNotFoundError):
        SpecLoader().load(str(tmp_path / "nope.json"))
