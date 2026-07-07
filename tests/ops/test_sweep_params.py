import pytest

from ncad.ops.sweep_params import SweepParamError, sweep_kwargs


def test_single_path_defaults():
    kw = sweep_kwargs({"path": "path_sk"}, {})
    assert kw["is_frenet"] is False and kw["transition"] == "transformed"
    assert kw["anchor"] == "origin" and "helix" not in kw


def test_helix_resolves_params():
    kw = sweep_kwargs(
        {"helix": {"pitch": 5, "height": 40, "radius": 12, "axis": "Z"}}, {})
    h = kw["helix"]
    assert h["pitch"] == 5.0 and h["height"] == 40.0 and h["radius"] == 12.0
    assert h["axis_point"] == (0.0, 0.0, 0.0) and h["axis_dir"] == (0.0, 0.0, 1.0)
    assert h["lefthand"] is False and h["cone_angle"] == 0.0


def test_anchor_centroid_and_coords():
    assert sweep_kwargs({"path": "p", "anchor": "centroid"}, {})["anchor"] == "centroid"
    assert sweep_kwargs({"path": "p", "anchor": [1, 2]}, {})["anchor"] == (1.0, 2.0)


def test_is_frenet_and_transition():
    kw = sweep_kwargs({"path": "p", "is_frenet": True, "transition": "round"}, {})
    assert kw["is_frenet"] is True and kw["transition"] == "round"


def test_path_and_helix_both_raises():
    with pytest.raises(SweepParamError, match="path"):
        sweep_kwargs({"path": "p", "helix": {"pitch": 1, "height": 1, "radius": 1}}, {})


def test_neither_path_nor_helix_raises():
    with pytest.raises(SweepParamError, match="path"):
        sweep_kwargs({}, {})


def test_sections_min_two():
    kw = sweep_kwargs({"path": "p", "sections": ["a", "b"]}, {})
    assert kw["sections"] == ["a", "b"]
    with pytest.raises(SweepParamError, match="sections"):
        sweep_kwargs({"path": "p", "sections": ["a"]}, {})


def test_helix_missing_or_nonpositive_raises():
    with pytest.raises(SweepParamError, match="helix"):
        sweep_kwargs({"helix": {"pitch": 5, "height": 40}}, {})  # missing radius
    with pytest.raises(SweepParamError, match="helix"):
        sweep_kwargs({"helix": {"pitch": 0, "height": 40, "radius": 12}}, {})


def test_bad_transition_raises():
    with pytest.raises(SweepParamError, match="transition"):
        sweep_kwargs({"path": "p", "transition": "wobble"}, {})
