"""SlicerProfile validates the wrapper: config ref, slicer preference, extra args."""

from pathlib import Path

import pytest

from ncad.cam.slicer_profile import SlicerProfile, SlicerProfileError


def test_reads_config_slicers_and_extra_args(tmp_path):
    profile = SlicerProfile(
        {"config": "petg.ini", "slicers": ["prusa", "cura"], "extra_args": ["--support-material"]},
        tmp_path)
    assert profile.config_path == tmp_path / "petg.ini"
    assert profile.slicers == ("prusa", "cura")
    assert profile.extra_args == ["--support-material"]


def test_defaults_slicer_preference_when_absent(tmp_path):
    profile = SlicerProfile({"config": "a.ini"}, tmp_path)
    assert profile.slicers[0] == "orca"          # best-first default
    assert profile.extra_args == []


def test_missing_config_raises(tmp_path):
    with pytest.raises(SlicerProfileError, match="needs a 'config'"):
        SlicerProfile({"slicers": ["prusa"]}, tmp_path)


def test_unknown_slicer_raises(tmp_path):
    with pytest.raises(SlicerProfileError, match="unknown slicer"):
        SlicerProfile({"config": "a.ini", "slicers": ["superslicer"]}, tmp_path)


def test_config_path_is_relative_to_wrapper_dir():
    profile = SlicerProfile({"config": "sub/x.ini"}, Path("/base"))
    assert profile.config_path == Path("/base/sub/x.ini")
