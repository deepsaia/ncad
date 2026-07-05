"""End-to-end coverage for Bucket 1.4c sketch topology ops.

Both examples are built on the real build123d kernel (slow), proving a trimmed + mirrored
profile and a filleted rectangle each weld into one closed face and extrude.
"""

from pathlib import Path

import pytest

from ncad.build.document_builder import DocumentBuilder

_EXAMPLES = Path(__file__).resolve().parents[2] / "examples" / "gate-1.4c"


@pytest.mark.slow
@pytest.mark.parametrize("name", ["trimmed_mirror", "filleted_plate"])
def test_topology_example_builds_on_real_kernel(name: str, tmp_path) -> None:
    from ncad.kernel.build123d_kernel import Build123dKernel

    doc = _EXAMPLES / f"{name}.hocon"
    artifacts = DocumentBuilder(Build123dKernel()).build_file(str(doc), str(tmp_path))

    glb = Path(artifacts[name])
    assert glb.is_file() and glb.stat().st_size > 0
