import pytest

from ncad.build.__main__ import _parse_formats


def test_parse_formats_default_glb():
    assert _parse_formats("glb") == ("glb",)


def test_parse_formats_comma_list():
    assert _parse_formats("glb,step") == ("glb", "step")


def test_parse_formats_strips_and_lowercases():
    assert _parse_formats(" GLB , Step ") == ("glb", "step")


def test_parse_formats_rejects_unknown():
    with pytest.raises(ValueError, match="glb"):
        _parse_formats("iges")
