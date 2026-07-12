import copy
from pathlib import Path

import pytest

pytestmark = pytest.mark.slow

_EXAMPLE = Path(__file__).resolve().parents[2] / "examples" / "gate-4.2b" / "imported_edit.hocon"


def test_import_then_offset_round_trips(tmp_path) -> None:
    from ncad.build.builder import Builder
    from ncad.kernel.build123d_kernel import Build123dKernel
    from ncad.ops.op_registry import OpRegistry
    from ncad.spec.spec_loader import SpecLoader

    kernel = Build123dKernel()
    # Export a known solid to STEP, then point the imported_edit example at it.
    box = kernel.extrude(kernel.polygon_face([(0, 0), (30, 0), (30, 30), (0, 30)], "XY"), 20.0)
    step = tmp_path / "input.step"
    kernel.export(box, str(step))

    document = SpecLoader().load(str(_EXAMPLE))
    part = copy.deepcopy(document["parts"]["imported_edit"])
    for feature in part["features"]:
        if feature["op"] == "import":
            feature["file"] = str(step)

    builder = Builder(kernel, OpRegistry.with_defaults())
    result, _, _ = builder.build_part_mapped(part)
    errors = [i for i in result.issues if i.level == "error"]
    assert result.shape is not None and not errors, errors
    # The outward offset grew the imported solid.
    assert kernel.volume(result.shape) > kernel.volume(box)
