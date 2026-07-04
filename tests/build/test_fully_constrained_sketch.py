from pathlib import Path

import pytest

from ncad.build.document_builder import DocumentBuilder
from tests.kernel.fake_kernel import FakeKernel

_EXAMPLES = Path(__file__).resolve().parents[2] / "examples" / "gate-1.3"


def test_constrained_bracket_has_no_warnings():
    result = DocumentBuilder(FakeKernel()).build_file_document(
        str(_EXAMPLES / "constrained_bracket.hocon"))["constrained_bracket"]
    assert result.shape is not None
    # fully constrained -> no under-constrained warning
    assert result.issues == []


@pytest.mark.slow
def test_tangent_bar_builds_on_real_kernel():
    from ncad.kernel.build123d_kernel import Build123dKernel

    result = DocumentBuilder(Build123dKernel()).build_file_document(
        str(_EXAMPLES / "tangent_bar.hocon"))["tangent_bar"]
    assert result.shape is not None
    assert not any(i.level == "error" for i in result.issues)
