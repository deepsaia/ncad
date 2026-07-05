from pathlib import Path

import pytest

from ncad.build.document_builder import DocumentBuilder

_EXAMPLES = Path(__file__).resolve().parents[2] / "examples" / "gate-1.4"

# Reference-into-sketch projects real 3D edges, so it needs the build123d kernel; the
# FakeKernel has no curved edges to project. These are slow (OCP) tests. The
# project/offset units themselves are unit-tested on the fast path.


@pytest.mark.slow
def test_projected_ring_builds_on_real_kernel():
    from ncad.kernel.build123d_kernel import Build123dKernel

    result = DocumentBuilder(Build123dKernel()).build_file_document(
        str(_EXAMPLES / "projected_ring.hocon"))["projected_ring"]
    assert result.shape is not None
    assert not any(i.level == "error" for i in result.issues)


@pytest.mark.slow
def test_projected_inset_builds_on_real_kernel():
    from ncad.kernel.build123d_kernel import Build123dKernel

    result = DocumentBuilder(Build123dKernel()).build_file_document(
        str(_EXAMPLES / "projected_inset.hocon"))["projected_inset"]
    assert result.shape is not None
    assert not any(i.level == "error" for i in result.issues)
