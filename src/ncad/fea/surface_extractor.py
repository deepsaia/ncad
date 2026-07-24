"""Rewrite a gmsh mesh .inp for CalculiX: drop 2D boundary elements, derive element *SURFACEs.

gmsh writes a named surface physical group as 2D plane-stress elements (CPS6), which CalculiX
rejects (a 2D element must lie in z=0). We do not want those as structural elements at all: for a
pressure/flux load CalculiX needs an element-based ``*SURFACE`` (each entry an element id + its
face label), and for a force/boundary it needs the surface's node set (which gmsh already writes as
``*NSET``). This class maps each boundary triangle back to its parent C3D10 tet face, emits one
``*SURFACE, TYPE=ELEMENT`` per named group, and strips the 2D element blocks. Pure: text in, text
out. One class.
"""

import logging
import re

logger = logging.getLogger(__name__)

# CalculiX C3D10 (and C3D4) face -> the corner-node positions in the element connectivity.
# Faces are S1..S4; a boundary triangle's 3 corner nodes identify which tet face it is.
_TET_FACES = {"S1": (0, 1, 2), "S2": (0, 1, 3), "S3": (1, 2, 3), "S4": (0, 2, 3)}
_2D_TYPES = ("CPS", "CPE", "S3", "S6", "STRI")


class SurfaceExtractor:
    """Rewrites a gmsh .inp: strips 2D elements and adds an element *SURFACE per named group."""

    def rewrite(self, mesh_inp_text: str, group_names: list[str]) -> dict:
        """Return ``{text, surfaces, faces}``: cleaned .inp, each group's *SURFACE name, its faces.

        ``surfaces`` maps a group -> its ``*SURFACE`` name (or None); ``faces`` maps a group -> its
        list of ``(element_id, face_label)`` pairs. Pressure/flux reference the surface; film and
        radiation (which CalculiX takes as element+face lines, not a surface) use ``faces``.

        :param group_names: the constraint/load set names GmshMesher created; only those that
            resolve to a set of boundary triangles get a derived element surface.
        """
        lines = mesh_inp_text.splitlines()
        tets = _read_tets(lines)
        tri_elements = _read_boundary_triangles(lines)   # 2d elem id -> (n1, n2, n3) corners
        elsets = _read_elsets(lines)                     # elset name -> [elem ids]
        face_of = _face_lookup(tets)

        surfaces: dict = {}
        faces_by_group: dict = {}
        triangles_by_group: dict = {}
        surface_blocks: list[str] = []
        for name in group_names:
            faces = _group_faces(name, elsets, tri_elements, face_of)
            faces_by_group[name] = faces
            triangles_by_group[name] = _group_triangles(name, elsets, tri_elements)
            if faces:
                surface_name = f"S{name}"
                surfaces[name] = surface_name
                surface_blocks.append(_surface_block(surface_name, faces))
            else:
                surfaces[name] = None
        cleaned = _strip_2d_elements(lines).rstrip()
        tail = ("\n" + "\n".join(surface_blocks)) if surface_blocks else ""
        return {"text": cleaned + tail + "\n", "surfaces": surfaces, "faces": faces_by_group,
                "triangles": triangles_by_group}


def _read_tets(lines: list[str]) -> dict:
    """Map each C3D4/C3D10 element id to its node-id connectivity list."""
    tets: dict = {}
    reading = False
    for line in lines:
        upper = line.strip().upper()
        if upper.startswith("*ELEMENT"):
            reading = "C3D" in upper.replace(" ", "")
            continue
        if upper.startswith("*"):
            reading = False
            continue
        if reading and line.strip():
            nums = [int(x) for x in line.strip().rstrip(",").split(",") if x.strip()]
            tets[nums[0]] = nums[1:]
    return tets


def _read_boundary_triangles(lines: list[str]) -> dict:
    """Map each 2D boundary element id to its 3 corner node ids (first three connectivity nodes)."""
    triangles: dict = {}
    reading = False
    for line in lines:
        upper = line.strip().upper().replace(" ", "")
        if upper.startswith("*ELEMENT"):
            reading = any(f"TYPE={t}" in upper for t in _2D_TYPES)
            continue
        if upper.startswith("*"):
            reading = False
            continue
        if reading and line.strip():
            nums = [int(x) for x in line.strip().rstrip(",").split(",") if x.strip()]
            triangles[nums[0]] = tuple(nums[1:4])
    return triangles


def _read_elsets(lines: list[str]) -> dict:
    """Map each ``*ELSET`` name to its list of element ids (multi-line lists accumulate)."""
    elsets: dict = {}
    current: str | None = None
    for line in lines:
        upper = line.strip().upper()
        if upper.startswith("*ELSET"):
            match = re.search(r"ELSET=(\S+)", line.strip(), re.IGNORECASE)
            current = match.group(1) if match else None
            if current is not None:
                elsets[current] = []
            continue
        if upper.startswith("*"):
            current = None
            continue
        if current is not None and line.strip():
            elsets[current] += [int(x) for x in line.strip().rstrip(",").split(",") if x.strip()]
    return elsets


def _face_lookup(tets: dict) -> dict:
    """Map a frozenset of 3 corner node ids to its (tet id, face label) for every tet face."""
    lookup: dict = {}
    for elem_id, nodes in tets.items():
        for face, positions in _TET_FACES.items():
            if all(pos < len(nodes) for pos in positions):
                key = frozenset(nodes[pos] for pos in positions)
                lookup[key] = (elem_id, face)
    return lookup


def _group_faces(name: str, elsets: dict, triangles: dict, face_of: dict) -> list[tuple]:
    """The (tet id, face) pairs for a group: its ELSET's triangles matched to parent tet faces."""
    faces = []
    for elem_id in elsets.get(name, []):
        corners = triangles.get(elem_id)
        if corners is None:
            continue
        match = face_of.get(frozenset(corners))
        if match is not None:
            faces.append(match)
    return faces


def _group_triangles(name: str, elsets: dict, triangles: dict) -> list[tuple]:
    """The group's boundary faces as ``(n1, n2, n3)`` corner-node triples (for glyph anchoring)."""
    out = []
    for elem_id in elsets.get(name, []):
        corners = triangles.get(elem_id)
        if corners is not None:
            out.append(corners)
    return out


def _surface_block(surface_name: str, faces: list[tuple]) -> str:
    """A ``*SURFACE, TYPE=ELEMENT`` block: one ``<elem>, S<face>`` line per boundary face."""
    lines = [f"*SURFACE, NAME={surface_name}, TYPE=ELEMENT"]
    lines += [f"{elem_id}, {face}" for elem_id, face in faces]
    return "\n".join(lines)


def _strip_2d_elements(lines: list[str]) -> str:
    """Drop every 2D (CPS/CPE/shell) ``*ELEMENT`` block; keep everything else verbatim."""
    out = []
    skipping = False
    for line in lines:
        upper = line.strip().upper().replace(" ", "")
        if upper.startswith("*ELEMENT"):
            skipping = any(f"TYPE={t}" in upper for t in _2D_TYPES)
            if skipping:
                continue
        elif upper.startswith("*"):
            skipping = False
        if not skipping:
            out.append(line)
    return "\n".join(out)
