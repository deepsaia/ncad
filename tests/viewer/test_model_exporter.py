"""ModelExporter re-exports a source to a format and returns downloadable bytes (no out/ write)."""

import io
import zipfile

import pytest

from ncad.kernel.build123d_kernel import Build123dKernel
from ncad.viewer.model_exporter import ModelExporter

pytestmark = pytest.mark.slow

_PART = "examples/02-solid-features/revolved_washer.hocon"
_PHYSICS = "examples/08-robotics/crank_slider.physics.hocon"
_MOTION = "examples/07-motion/crank_slider.motion.hocon"
# crank_slider.hocon declares four parts (block/flywheel/rod/piston); the assembly composes them.
_MULTIPART = "examples/07-motion/crank_slider.hocon"


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


def test_motion_export_resolves_the_referenced_assembly():
    # A .motion.hocon is not an assembly document; exporting it to STEP must resolve + compose the
    # assembly it drives (regression: it used to feed the motion doc to AssemblyBuilder and fail
    # schema validation on the missing 'units'/'assembly' keys).
    name, ctype, data = ModelExporter(Build123dKernel()).export(_MOTION, "motion", "step", "crank")
    assert name == "crank.step" and ctype == "application/step"
    assert len(data) > 0


def test_part_export_selects_the_named_part_of_a_multipart_source():
    # An assembly member is one part of a multi-part document; the exporter must return THAT part,
    # not the first-written one (regression: no part selector meant a member export could be wrong).
    export = ModelExporter(Build123dKernel()).export
    sizes = {p: len(export(_MULTIPART, "part", "stl", p, part=p)[2])
             for p in ("block", "flywheel", "rod", "piston")}
    assert all(size > 0 for size in sizes.values())
    assert len(set(sizes.values())) > 1   # distinct parts -> distinct bytes (not always the same)


def test_part_export_unknown_part_raises():
    with pytest.raises(ValueError, match="not found"):
        ModelExporter(Build123dKernel()).export(_MULTIPART, "part", "step", "x", part="nope")
