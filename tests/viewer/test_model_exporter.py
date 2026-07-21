"""ModelExporter re-exports a source to a format and returns downloadable bytes (no out/ write)."""

import io
import zipfile

import pytest

from ncad.kernel.build123d_kernel import Build123dKernel
from ncad.viewer.model_exporter import ModelExporter

pytestmark = pytest.mark.slow

_PART = "examples/02-solid-features/revolved_washer.hocon"
_PHYSICS = "examples/08-robotics/crank_slider.physics.hocon"


@pytest.mark.parametrize("fmt,ext", [("step", "step"), ("stl", "stl"), ("glb", "glb"),
                                     ("iges", "iges")])
def test_part_export_returns_named_bytes(fmt, ext):
    name, ctype, data = ModelExporter(Build123dKernel()).export(_PART, "part", fmt, "washer")
    assert name == f"washer.{ext}"
    assert len(data) > 0


def test_robot_export_is_a_zip_of_artifact_plus_meshes():
    name, ctype, data = ModelExporter(Build123dKernel()).export(_PHYSICS, "physics", "urdf", "arm")
    assert name == "arm.zip" and ctype == "application/zip"   # the download is named per base_name
    names = zipfile.ZipFile(io.BytesIO(data)).namelist()
    # Just the robot artifact (named per the robot's model name) + its per-link meshes; no stray
    # assembly/step byproducts.
    urdf = [n for n in names if n.endswith(".urdf")]
    assert len(urdf) == 1
    assert all(n.endswith(".urdf") or n.startswith("meshes/") for n in names)
    assert any(n.startswith("meshes/") and n.endswith(".stl") for n in names)


def test_invalid_kind_format_combo_raises():
    with pytest.raises(ValueError, match="cannot be exported"):
        ModelExporter(Build123dKernel()).export(_PART, "part", "urdf", "washer")
    with pytest.raises(ValueError, match="cannot be exported"):
        ModelExporter(Build123dKernel()).export(_PHYSICS, "physics", "step", "arm")
