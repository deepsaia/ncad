import json
import struct
from pathlib import Path

import pytest

pytestmark = pytest.mark.slow

_EXAMPLES = Path(__file__).resolve().parents[2] / "examples"


def _glb_primitive_count(path: str) -> int:
    """Parse a .glb and return its total glTF primitive count (one per face).

    GLTFLoader turns each primitive into its own three.js Mesh, so the viewer's per-primitive
    pickParts must line up 1:1 with the sidecar `meshes` list.
    """
    with open(path, "rb") as handle:
        handle.read(12)  # magic, version, length
        chunk_len, _chunk_type = struct.unpack("<II", handle.read(8))
        gltf = json.loads(handle.read(chunk_len))
    return sum(len(m.get("primitives", [])) for m in gltf.get("meshes", []))


def test_multibody_meshes_list_is_per_primitive_aligned(tmp_path):
    # The sidecar `meshes` list carries one {body_id, material} per exported glTF PRIMITIVE
    # (face), in export order, so the viewer maps pickParts[i] -> body -> material positionally.
    from ncad.build.document_builder import DocumentBuilder
    from ncad.kernel.build123d_kernel import Build123dKernel

    kernel = Build123dKernel()
    builder = DocumentBuilder(kernel)
    doc = _EXAMPLES / "gate-3.6" / "flanged_coupling.hocon"
    artifacts = builder.build_file(str(doc), str(tmp_path), formats=("glb",))
    primitive_count = _glb_primitive_count(artifacts["flanged_coupling"])

    sidecar = json.loads((tmp_path / "flanged_coupling.elementmap.json").read_text())
    meshes = sidecar["meshes"]
    # one sidecar entry per exported primitive (face)
    assert len(meshes) == primitive_count
    body_ids = {m["body_id"] for m in meshes}
    materials = {m["material"] for m in meshes}
    assert len(body_ids) == 4  # 2 flanges + 2 hubs
    assert materials == {"aluminium_6061", "steel_1018"}
