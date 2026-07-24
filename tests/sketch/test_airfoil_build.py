"""Real-kernel build: a single airfoil extrudes to a solid; two airfoil sections loft to a wing."""

from ncad.build.document_builder import DocumentBuilder
from ncad.kernel.build123d_kernel import Build123dKernel


def test_single_airfoil_extrudes_to_one_solid():
    doc = {"units": "mm", "parts": {"blade": {"profile": "solid", "features": [
        {"id": "sk", "op": "sketch", "plane": "XY",
         "entities": [{"id": "a", "type": "airfoil", "naca": "0012", "chord": 200}]},
        {"id": "ext", "op": "extrude", "profile": "sk", "distance": 50}]}}}
    result = DocumentBuilder(Build123dKernel()).build(doc)
    assert result["blade"].shape is not None


def test_two_airfoil_sections_loft_to_one_solid():
    # Root + tip airfoil on offset planes (tip a smaller chord = taper), lofted. Matches the loft
    # vocabulary in examples/02-solid-features/lofted_transition.hocon (sections on plane_offset).
    doc = {"units": "mm", "parts": {"wing": {"profile": "solid", "features": [
        {"id": "root_sk", "op": "sketch", "plane": "XY", "plane_offset": 0,
         "entities": [{"id": "root", "type": "airfoil", "naca": "2412", "chord": 300}]},
        {"id": "tip_sk", "op": "sketch", "plane": "XY", "plane_offset": 400,
         "entities": [{"id": "tip", "type": "airfoil", "naca": "2412", "chord": 180}]},
        {"id": "wing", "op": "loft", "sections": ["root_sk", "tip_sk"]}]}}}
    result = DocumentBuilder(Build123dKernel()).build(doc)
    assert result["wing"].shape is not None
