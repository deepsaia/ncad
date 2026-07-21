"""robot_writer maps each export format to its writer + extension; rejects unknown formats."""

import pytest

from ncad.robotics.mjcf_writer import MjcfWriter
from ncad.robotics.robot_format import robot_writer
from ncad.robotics.sdf_writer import SdfWriter
from ncad.robotics.urdf_writer import UrdfWriter


def test_each_format_maps_to_its_writer_and_extension():
    for fmt, writer_type, ext in [
        ("urdf", UrdfWriter, "urdf"), ("mjcf", MjcfWriter, "xml"), ("sdf", SdfWriter, "sdf")]:
        writer, extension = robot_writer(fmt)
        assert isinstance(writer, writer_type)
        assert extension == ext


def test_unknown_format_raises():
    with pytest.raises(ValueError, match="unknown robot export format"):
        robot_writer("collada")
