import json
import struct
from pathlib import Path

import pytest

pytestmark = pytest.mark.slow

_EXAMPLES = Path(__file__).resolve().parents[2] / "examples"


def _glb_mesh_names(path: str) -> list[str]:
    """Parse a .glb and return its glTF mesh names in order."""
    with open(path, "rb") as handle:
        handle.read(12)  # magic, version, length
        chunk_len, _chunk_type = struct.unpack("<II", handle.read(8))
        gltf = json.loads(handle.read(chunk_len))
    return [m.get("name") for m in gltf.get("meshes", [])]


def test_multibody_glb_meshes_named_by_body_id(tmp_path):
    from ncad.build.document_builder import DocumentBuilder
    from ncad.kernel.build123d_kernel import Build123dKernel

    kernel = Build123dKernel()
    builder = DocumentBuilder(kernel)
    doc = _EXAMPLES / "gate-3.6" / "flanged_coupling.hocon"
    artifacts = builder.build_file(str(doc), str(tmp_path), formats=("glb",))
    names = _glb_mesh_names(artifacts["flanged_coupling"])

    resolved = builder._resolve_and_validate(builder._loader.load(str(doc)))
    result, _, _ = builder._builder.build_part_mapped(resolved["parts"]["flanged_coupling"])
    body_ids = [b.id for b in kernel.bodies(result.shape)]

    assert names == body_ids
