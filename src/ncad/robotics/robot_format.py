"""Map an export-format key to its RobotModel writer + file extension.

The single place that binds a physics-overlay ``export.format`` (urdf/mjcf/sdf) to the writer that
serializes the RobotModel and the artifact's file extension. A new format registers here with a
writer + extension; the CLI needs no change. Not a class (a tiny dispatch table + a lookup).
"""

from typing import Any

from ncad.robotics.mjcf_writer import MjcfWriter
from ncad.robotics.sdf_writer import SdfWriter
from ncad.robotics.urdf_writer import UrdfWriter

# format key -> (writer factory, artifact extension). MJCF is an .xml file (MuJoCo convention).
_WRITERS: dict[str, tuple[Any, str]] = {
    "urdf": (UrdfWriter, "urdf"),
    "mjcf": (MjcfWriter, "xml"),
    "sdf": (SdfWriter, "sdf"),
}


def robot_writer(export_format: str) -> tuple[Any, str]:
    """Return ``(writer_instance, extension)`` for ``export_format``; raise on an unknown format."""
    if export_format not in _WRITERS:
        raise ValueError(
            f"unknown robot export format {export_format!r}; known: {sorted(_WRITERS)}")
    factory, extension = _WRITERS[export_format]
    return factory(), extension
