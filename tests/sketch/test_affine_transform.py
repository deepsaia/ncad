from ncad.sketch.affine_transform import AffineTransform


def test_translation_moves_point():
    t = AffineTransform.translation(3.0, -2.0)
    assert t.apply_point(1.0, 1.0) == (4.0, -1.0)
    assert t.radius_factor == 1.0


def test_rotation_ninety_degrees_about_origin():
    t = AffineTransform.rotation(0.0, 0.0, 90.0)
    x, y = t.apply_point(1.0, 0.0)
    assert round(x, 6) == 0.0 and round(y, 6) == 1.0


def test_rotation_about_center():
    t = AffineTransform.rotation(2.0, 0.0, 180.0)
    x, y = t.apply_point(3.0, 0.0)
    assert round(x, 6) == 1.0 and round(y, 6) == 0.0


def test_scaling_scales_position_and_radius():
    t = AffineTransform.scaling(0.0, 0.0, 2.0)
    assert t.apply_point(3.0, 4.0) == (6.0, 8.0)
    assert t.radius_factor == 2.0


def test_scaling_about_center():
    t = AffineTransform.scaling(1.0, 1.0, 3.0)
    assert t.apply_point(2.0, 1.0) == (4.0, 1.0)


def test_reflection_across_y_axis():
    t = AffineTransform.reflection(0.0, 0.0, 0.0, 1.0)
    x, y = t.apply_point(5.0, 2.0)
    assert round(x, 6) == -5.0 and round(y, 6) == 2.0
    assert t.radius_factor == 1.0


def test_reflection_across_x_axis():
    t = AffineTransform.reflection(0.0, 0.0, 1.0, 0.0)
    x, y = t.apply_point(5.0, 2.0)
    assert round(x, 6) == 5.0 and round(y, 6) == -2.0
