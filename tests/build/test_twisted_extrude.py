import math

import pytest

pytestmark = pytest.mark.slow


def test_twisted_column_valid_same_volume_and_rotated_top():
    from ncad.kernel.build123d_kernel import Build123dKernel

    kernel = Build123dKernel()
    profile = kernel.polygon_face([(-10, -10), (10, -10), (10, 10), (-10, 10)], "XY")
    straight = kernel.extrude(profile, 40.0)
    # A 45deg twist (a 90deg twist of a square maps corners back onto corners, so it would not
    # witness the rotation; 45deg clearly moves the top corners onto the axes).
    twisted = kernel.extrude(profile, 40.0, twist=45.0)
    assert twisted.is_valid
    # Twist preserves volume.
    assert math.isclose(kernel.volume(twisted), kernel.volume(straight), rel_tol=1e-3)
    # The top face is rotated vs the base: a top-face vertex is off the untwisted corner lattice
    # (a straight column's top corners sit at |x| == |y| == 10; a 45deg twist moves them off it).
    top_z = kernel.bounding_box(twisted)[1][2]
    top_verts = [tuple(v) for v in twisted.vertices() if abs(tuple(v)[2] - top_z) < 1e-6]
    assert top_verts
    assert any(not (math.isclose(abs(x), 10.0, abs_tol=0.5)
                    and math.isclose(abs(y), 10.0, abs_tol=0.5))
               for x, y, _ in top_verts)
