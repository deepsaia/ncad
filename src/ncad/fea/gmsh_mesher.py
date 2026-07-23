"""Mesh an exported STEP into a CalculiX .inp volume mesh with named node/element sets.

Behind the optional ``ncad[fea]`` extra: gmsh reads the STEP through its own OpenCASCADE kernel
(lossless B-rep, not tessellation), meshes it into linear (C3D4) or quadratic (C3D10) tets, and
writes the mesh + one physical group per analysis constraint/load. FaceGroupMapper decides which
gmsh surfaces each named group covers. gmsh is imported inside methods so importing this module
never requires the extra.
"""

import logging

from ncad.fea.face_group_mapper import FaceGroupMapper

logger = logging.getLogger(__name__)

_ELEMENT_TYPE = {1: "C3D4", 2: "C3D10"}


class GmshMesher:
    """Meshes a STEP into a CalculiX .inp with named groups for the load case."""

    def __init__(self, mapper: FaceGroupMapper | None = None) -> None:
        self._mapper = mapper or FaceGroupMapper()

    def mesh(self, step_path: str, mesh_opts: dict, groups: dict, out_inp: str) -> dict:
        """Mesh ``step_path`` into ``out_inp``; return a report.

        :param mesh_opts: ``{element_size, order, min_quality}`` (AnalysisSpec.mesh).
        :param groups: ``{set_name: where_selector}`` for each constraint/load.
        :return: ``{nodes, elements, element_type, groups {name: [tags]}, warnings}``.
        :raises FaceGroupError: if a group's selector matches no surface.
        """
        import gmsh

        gmsh.initialize()
        try:
            return self._build_mesh(gmsh, step_path, mesh_opts, groups, out_inp)
        finally:
            gmsh.finalize()

    def _build_mesh(self, gmsh, step_path: str, mesh_opts: dict, groups: dict,
                    out_inp: str) -> dict:
        """Import, tag groups, mesh, and write the .inp (all gmsh calls live here)."""
        gmsh.option.setNumber("General.Terminal", 0)
        gmsh.model.add("part")
        gmsh.model.occ.importShapes(step_path)
        gmsh.model.occ.synchronize()

        surfaces = _surface_descriptors(gmsh)
        group_tags: dict = {}
        for name, where in groups.items():
            tags = self._mapper.select(surfaces, where)
            gmsh.model.addPhysicalGroup(2, tags, name=name)
            group_tags[name] = tags
        volumes = [tag for (_dim, tag) in gmsh.model.getEntities(3)]
        gmsh.model.addPhysicalGroup(3, volumes, name="all")

        order = int(mesh_opts.get("order", 2))
        gmsh.option.setNumber("Mesh.CharacteristicLengthMax", float(mesh_opts["element_size"]))
        gmsh.option.setNumber("Mesh.ElementOrder", order)
        gmsh.option.setNumber("Mesh.SaveGroupsOfNodes", 1)
        gmsh.model.mesh.generate(3)

        warnings = _quality_warnings(gmsh, float(mesh_opts.get("min_quality", 0.0)))
        node_tags, _, _ = gmsh.model.mesh.getNodes()
        elem_type = _ELEMENT_TYPE.get(order, "C3D10")
        elements = _volume_element_count(gmsh)
        gmsh.write(out_inp)
        logger.info("meshed %s: %d nodes, %d %s elements, groups %s",
                    step_path, len(node_tags), elements, elem_type, list(group_tags))
        return {"nodes": len(node_tags), "elements": elements, "element_type": elem_type,
                "groups": group_tags, "warnings": warnings}


def _surface_descriptors(gmsh) -> list[dict]:
    """Extract ``{tag, com, normal, zmin, zmax, area}`` for every model surface (plain floats)."""
    out = []
    for (_dim, tag) in gmsh.model.getEntities(2):
        com = gmsh.model.occ.getCenterOfMass(2, tag)
        box = gmsh.model.getBoundingBox(2, tag)
        pmin, pmax = gmsh.model.getParametrizationBounds(2, tag)
        uv = [(a + b) / 2.0 for a, b in zip(pmin, pmax)]
        normal = gmsh.model.getNormal(tag, uv)
        out.append({
            "tag": int(tag),
            "com": (float(com[0]), float(com[1]), float(com[2])),
            "normal": (float(normal[0]), float(normal[1]), float(normal[2])),
            "zmin": float(box[2]), "zmax": float(box[5]),
            "area": float(gmsh.model.occ.getMass(2, tag)),
        })
    return out


def _volume_element_count(gmsh) -> int:
    """Total number of 3D (volume) elements across the mesh."""
    _types, tags, _nodes = gmsh.model.mesh.getElements(3)
    return sum(len(t) for t in tags)


def _quality_warnings(gmsh, min_quality: float) -> list[str]:
    """Warn (do not fail) if any tet's gamma quality is below ``min_quality`` (0 disables)."""
    if min_quality <= 0.0:
        return []
    etypes, etags, _ = gmsh.model.mesh.getElements(3)
    worst = 1.0
    for _etype, tags in zip(etypes, etags):
        if not len(tags):
            continue
        qualities = gmsh.model.mesh.getElementQualities(tags, "gamma")
        worst = min(worst, min(float(q) for q in qualities))
    if worst < min_quality:
        return [f"mesh quality {worst:.3f} below min_quality {min_quality:.3f}"]
    return []
