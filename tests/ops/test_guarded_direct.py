import pytest


def _box(kernel, s=20.0):
    return kernel.extrude(kernel.polygon_face([(0, 0), (s, 0), (s, s), (0, s)], "XY"), s)


def test_offset_op_uses_guarded_path_when_imported(monkeypatch) -> None:
    # A direct op whose feature carries __imported__=True runs the subprocess-guarded path.
    from ncad.ops import direct_edit_runner
    from ncad.ops.offset_face_op import OffsetFaceOp
    from tests.kernel.fake_kernel import FakeKernel

    calls = {"subprocess": None}

    def _spy(self, kernel, kernel_call, before, op, subprocess=False, guarded_spec=None):
        calls["subprocess"] = subprocess
        from ncad.ops.direct_edit_runner import RunResult

        return RunResult(kernel_call(), True)

    monkeypatch.setattr(direct_edit_runner.DirectEditRunner, "run", _spy)
    kernel = FakeKernel()
    solid = _box(kernel)
    OffsetFaceOp().build(solid, {"id": "of", "distance": 1.0, "__imported__": True, "__refs__": {}},
                         {}, kernel)
    assert calls["subprocess"] is True


def test_offset_op_in_process_when_authored(monkeypatch) -> None:
    from ncad.ops import direct_edit_runner
    from ncad.ops.offset_face_op import OffsetFaceOp
    from tests.kernel.fake_kernel import FakeKernel

    calls = {"subprocess": None}

    def _spy(self, kernel, kernel_call, before, op, subprocess=False, guarded_spec=None):
        calls["subprocess"] = subprocess
        from ncad.ops.direct_edit_runner import RunResult

        return RunResult(kernel_call(), True)

    monkeypatch.setattr(direct_edit_runner.DirectEditRunner, "run", _spy)
    kernel = FakeKernel()
    solid = _box(kernel)
    OffsetFaceOp().build(solid, {"id": "of", "distance": 1.0, "__refs__": {}}, {}, kernel)
    assert calls["subprocess"] is False


@pytest.mark.slow
def test_guarded_offset_on_imported_step_round_trips(tmp_path) -> None:
    from ncad.kernel.build123d_kernel import Build123dKernel
    from ncad.ops.direct_edit_runner import DirectEditRunner

    kernel = Build123dKernel()
    box = _box(kernel, 30.0)
    step = tmp_path / "in.step"
    kernel.export(box, str(step))
    imported = kernel.import_solid(str(step))
    before = kernel.volume(imported)
    spec = {"kind": "offset", "distance": 1.0}
    run = DirectEditRunner().run(kernel, lambda: None, imported, "offset",
                                 subprocess=True, guarded_spec=spec)
    assert run.accepted and kernel.volume(run.shape) > before
