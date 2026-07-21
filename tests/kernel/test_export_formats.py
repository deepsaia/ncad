"""Stage 0 export breadth: STL/3MF/OBJ/PLY/IGES write + round-trip on the real kernel."""

import pytest

from ncad.kernel.build123d_kernel import Build123dKernel

pytestmark = pytest.mark.slow


def _block(kernel: Build123dKernel):
    face = kernel.polygon_face([(0, 0), (20, 0), (20, 10), (0, 10)], "XY")
    return kernel.extrude(face, 5.0)


@pytest.mark.parametrize("ext", ["stl", "obj", "ply"])
def test_trimesh_formats_roundtrip(tmp_path, ext) -> None:
    # STL (native) + OBJ/PLY (trimesh) all load back as a non-empty mesh via trimesh.
    import trimesh

    kernel = Build123dKernel()
    out = tmp_path / f"block.{ext}"
    kernel.export(_block(kernel), str(out))

    assert out.is_file() and out.stat().st_size > 0
    mesh = trimesh.load(str(out))
    assert len(mesh.vertices) > 0 and len(mesh.faces) > 0


def test_3mf_writes_readable_model(tmp_path) -> None:
    # 3MF via build123d's Mesher round-trips through the same Mesher reader.
    from build123d import Mesher

    kernel = Build123dKernel()
    out = tmp_path / "block.3mf"
    kernel.export(_block(kernel), str(out))

    assert out.is_file() and out.stat().st_size > 0
    reader = Mesher()
    reader.read(str(out))
    assert reader.mesh_count >= 1


def test_iges_writes_nonempty(tmp_path) -> None:
    # IGES via the OCCT writer; a non-trivial ASCII IGES file is produced.
    kernel = Build123dKernel()
    out = tmp_path / "block.iges"
    kernel.export(_block(kernel), str(out))

    assert out.is_file() and out.stat().st_size > 0
    assert "IGES" in out.read_text(errors="ignore").upper()


def test_mesh_tolerance_controls_triangle_count(tmp_path) -> None:
    # A curved solid: a coarse tolerance yields fewer triangles than a fine one (the knob works).
    import trimesh

    kernel = Build123dKernel()
    cyl = kernel.cylinder((0, 0, 0), "Z", diameter=20.0, length=20.0)

    coarse = tmp_path / "coarse.stl"
    fine = tmp_path / "fine.stl"
    kernel.export(cyl, str(coarse), mesh_tolerance=2.0)
    kernel.export(cyl, str(fine), mesh_tolerance=0.05)

    assert len(trimesh.load(str(fine)).faces) > len(trimesh.load(str(coarse)).faces)


def test_unknown_extension_raises(tmp_path) -> None:
    kernel = Build123dKernel()
    with pytest.raises(ValueError, match="unsupported export format"):
        kernel.export(_block(kernel), str(tmp_path / "block.xyz"))
