import pytest

pytestmark = pytest.mark.slow


def test_variable_draft_per_face_angles():
    from build123d import Solid

    from ncad.kernel.build123d_kernel import Build123dKernel

    kernel = Build123dKernel()
    box = Solid.make_box(20, 20, 20)
    walls = [f for f in box.faces() if abs(f.normal_at().Z) < 0.1]
    # A variable draft applies a different taper to each wall about one neutral plane.
    result = kernel.draft_variable(box, [(walls[0], 3.0), (walls[1], 6.0)],
                                   neutral="XY", neutral_offset=0.0)
    assert result.volume > 0
    assert result.volume != box.volume


def test_per_face_multi_thickness_shell_is_called_out():
    from ncad.ops.shell_params import ShellParamError, shell_kwargs

    # Per-face wall thicknesses are not supported (OCCT MakeThickSolid is single-offset);
    # a per-face request is refused clearly rather than faked.
    with pytest.raises(ShellParamError, match="per-face"):
        shell_kwargs({"thickness": 2.0, "thicknesses": {"top": 3.0}})
