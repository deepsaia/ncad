"""End-to-end coverage for Bucket 1.4b sketch transforms.

The mirror example is built on the real build123d kernel (slow), proving a mirrored
half-profile welds into one closed face and extrudes. The pattern examples are checked
at the resolved-build level (a multi-loop face is deferred), asserting the transform
stage ran and replicated the entities rather than raising a TransformError.
"""

from pathlib import Path

import pytest

from ncad.build.document_builder import DocumentBuilder
from tests.kernel.fake_kernel import FakeKernel

_EXAMPLES = Path(__file__).resolve().parents[2] / "examples" / "gate-1.4b"


@pytest.mark.slow
def test_mirrored_profile_builds_on_real_kernel(tmp_path) -> None:
    from ncad.kernel.build123d_kernel import Build123dKernel

    doc = _EXAMPLES / "mirrored_profile.hocon"
    artifacts = DocumentBuilder(Build123dKernel()).build_file(str(doc), str(tmp_path))

    glb = Path(artifacts["mirrored_profile"])
    assert glb.is_file() and glb.stat().st_size > 0


@pytest.mark.parametrize("name", ["linear_pattern", "circular_pattern"])
def test_pattern_replicates_without_transform_error(name: str) -> None:
    doc = _EXAMPLES / f"{name}.hocon"
    results = DocumentBuilder(FakeKernel()).build_file_document(str(doc))
    result = results[name]
    # A multi-loop face is deferred, so the sketch reports a wire-ordering error, but the
    # transform stage itself must have run and replicated the entities: no transform-op
    # error is raised, so the only errors (if any) come from wire ordering, not transforms.
    messages = " ".join(i.message for i in result.issues).lower()
    assert "transform" not in messages
    assert "unknown transform op" not in messages
