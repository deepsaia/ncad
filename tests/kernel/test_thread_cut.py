import pytest

pytestmark = pytest.mark.slow


def test_external_thread_removes_material():
    from build123d import Solid

    from ncad.kernel.build123d_kernel import Build123dKernel

    kernel = Build123dKernel()
    stud = Solid.make_cylinder(5, 20)
    threaded = kernel.thread_cut(stud, axis_point=(0, 0, 0), axis_dir=(0, 0, 1),
                                 major_d=10.0, pitch=1.5, length=16.0, internal=False)
    # An external thread cuts a helical groove into the stud, so it removes material.
    assert threaded.volume < stud.volume
    assert threaded.volume > 0


def test_thread_needs_positive_pitch():
    from build123d import Solid

    from ncad.kernel.build123d_kernel import Build123dKernel
    from ncad.kernel.kernel_op_error import KernelOpError

    kernel = Build123dKernel()
    stud = Solid.make_cylinder(5, 20)
    with pytest.raises(KernelOpError):
        kernel.thread_cut(stud, axis_point=(0, 0, 0), axis_dir=(0, 0, 1),
                          major_d=10.0, pitch=0.0, length=16.0, internal=False)
