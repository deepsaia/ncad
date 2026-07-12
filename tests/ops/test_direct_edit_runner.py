from ncad.ops.direct_edit_runner import DirectEditRunner, RunResult
from tests.kernel.fake_kernel import FakeKernel


def _box(kernel, h=10.0):
    return kernel.extrude(kernel.polygon_face([(0, 0), (10, 0), (10, 10), (0, 10)], "XY"), h)


def test_accepts_a_good_offset() -> None:
    kernel = FakeKernel()
    before = _box(kernel)
    result = DirectEditRunner().run(kernel, lambda: kernel.offset_solid(before, 1.0),
                                    before, "offset")
    assert isinstance(result, RunResult) and result.accepted


def test_rejects_a_noop_defeature() -> None:
    kernel = FakeKernel()
    before = _box(kernel)
    # A "defeature" that returns the identical solid violates the face-count/volume intent.
    result = DirectEditRunner().run(kernel, lambda: before, before, "defeature")
    assert not result.accepted


def test_rejects_a_degenerate_result() -> None:
    kernel = FakeKernel()
    before = _box(kernel)
    # A zero-volume result fails the independent sanity tier.
    from tests.kernel.fake_kernel import _FakeCombined

    empty = _FakeCombined(0.0, kernel.bounding_box(before))
    result = DirectEditRunner().run(kernel, lambda: empty, before, "offset")
    assert not result.accepted
