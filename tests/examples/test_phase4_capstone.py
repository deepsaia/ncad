"""Phase 4 capstone gate: import a dumb solid, direct-edit it within the envelope, re-export.

Proves the phase-level promise end to end: an imported (history-free) solid is editable by
direct ops, the result re-exports to a valid STEP, and an out-of-envelope op is refused with an
id-attributed reason rather than silently corrupting.
"""

import pytest

pytestmark = pytest.mark.slow


def _box(kernel, s=30.0):
    return kernel.extrude(kernel.polygon_face([(0, 0), (s, 0), (s, s), (0, s)], "XY"), s)


def test_import_then_direct_edit_then_reexport(tmp_path) -> None:
    from build123d import import_step

    from ncad.build.builder import Builder
    from ncad.kernel.build123d_kernel import Build123dKernel
    from ncad.ops.op_registry import OpRegistry
    from ncad.spec.spec_loader import SpecLoader  # noqa: F401 - kept for parity/readability

    kernel = Build123dKernel()
    # Export a known part to STEP (our own kernel), then edit it as an imported base feature.
    box = _box(kernel)
    step = tmp_path / "capstone_in.step"
    kernel.export(box, str(step))

    document = {"parts": {"widget": {"profile": "solid", "features": [
        {"id": "base", "op": "import", "file": str(step)},
        {"id": "grow", "op": "offset", "distance": 1.0},
    ]}}}
    builder = Builder(kernel, OpRegistry.with_defaults())
    result, _, _ = builder.build_part_mapped(document["parts"]["widget"])
    errors = [i for i in result.issues if i.level == "error"]
    assert result.shape is not None and not errors, errors
    assert kernel.volume(result.shape) > kernel.volume(box)  # outward offset grew it

    # Re-export the edited imported solid to STEP and confirm it re-imports as a valid solid.
    out = tmp_path / "capstone_out.step"
    kernel.export(result.shape, str(out))
    assert abs(import_step(str(out)).volume) > 0


def test_out_of_envelope_op_is_refused(tmp_path) -> None:
    from ncad.build.builder import Builder
    from ncad.kernel.build123d_kernel import Build123dKernel
    from ncad.ops.op_registry import OpRegistry

    kernel = Build123dKernel()
    box = _box(kernel)
    step = tmp_path / "cap_in.step"
    kernel.export(box, str(step))

    # An inward offset far past the wall thickness is out-of-envelope: refused, not corrupted.
    document = {"parts": {"widget": {"profile": "solid", "features": [
        {"id": "base", "op": "import", "file": str(step)},
        {"id": "thin", "op": "offset", "distance": -40.0},
    ]}}}
    builder = Builder(kernel, OpRegistry.with_defaults())
    result, _, _ = builder.build_part_mapped(document["parts"]["widget"])
    errors = [i for i in result.issues if i.level == "error"]
    assert errors and errors[0].node_id == "thin"
    assert "wall" in errors[0].message.lower()
