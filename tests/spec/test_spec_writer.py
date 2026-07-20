"""Tests for the spec writer: dict -> JSON/HOCON file, round-tripping via the loader."""

import pytest

from ncad.spec.spec_loader import SpecLoader
from ncad.spec.spec_writer import SpecWriter

_SPEC = {"seed": 42,
    "units": "m",
    "storeys": [
        {
            "elevation": 0.0,
            "height": 3.0,
            "walls": [{"id": "wall_0", "start": [0.0, 0.0], "end": [6.0, 0.0], "thickness": 0.2}],
            "rooms": [{"id": "room_0", "polygon": [[0, 0], [6, 0], [6, 4], [0, 4]]}],
        }
    ],
    "roof": {"kind": "flat", "thickness": 0.2},
}


def test_json_round_trip(tmp_path) -> None:
    path = tmp_path / "spec.json"

    SpecWriter().dump(_SPEC, str(path))

    assert path.exists()
    assert SpecLoader().load(str(path)) == _SPEC


def test_hocon_round_trip(tmp_path) -> None:
    path = tmp_path / "spec.hocon"

    SpecWriter().dump(_SPEC, str(path))

    assert path.exists()
    assert SpecLoader().load(str(path)) == _SPEC


def test_unknown_extension_raises_value_error(tmp_path) -> None:
    with pytest.raises(ValueError, match="unsupported"):
        SpecWriter().dump(_SPEC, str(tmp_path / "spec.yaml"))
