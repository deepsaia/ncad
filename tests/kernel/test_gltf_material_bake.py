import pytest

pytestmark = pytest.mark.slow


def test_export_bakes_per_body_color_into_glb(tmp_path):
    # A two-body part exported with per-body colors bakes each body's baseColorFactor into the
    # glb so default colors port to other glTF renderers. Read the material colors back.
    from build123d import Pos, Solid

    from ncad.kernel.body import Body
    from ncad.kernel.body_set import BodySet
    from ncad.kernel.build123d_kernel import Build123dKernel

    a = Solid.make_box(10, 10, 10)
    b = Pos(20, 0, 0) * Solid.make_box(10, 10, 10)
    shape = BodySet([Body(id="s/body/0", kind="solid", shape=a, created_by="s"),
                     Body(id="s/body/1", kind="solid", shape=b, created_by="s")])
    colors = {"s/body/0": (1.0, 0.0, 0.0, 1.0), "s/body/1": (0.0, 0.0, 1.0, 1.0)}
    out = tmp_path / "two_body.glb"
    Build123dKernel().export(shape, str(out), body_colors=colors)
    assert out.is_file()

    import trimesh

    scene = trimesh.load(str(out))
    # Gather each mesh's baseColorFactor; both baked colors must be present.
    seen = set()
    for geom in scene.geometry.values():
        mat = getattr(geom.visual, "material", None)
        base = getattr(mat, "baseColorFactor", None)
        if base is not None:
            seen.add(tuple(round(c / 255 if c > 1 else c, 3) for c in base))
    assert any(abs(r - 1.0) < 0.05 and g < 0.05 and b < 0.05 for (r, g, b, _a) in seen), seen
    assert any(r < 0.05 and g < 0.05 and abs(b - 1.0) < 0.05 for (r, g, b, _a) in seen), seen
