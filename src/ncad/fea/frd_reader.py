"""Parse a CalculiX .frd results file into per-node fields + a summary; write a vtk field mesh.

meshio cannot read .frd (it reads abaqus .inp and writes vtk), so this parses the .frd ASCII
directly. The format (block key = the first 5 chars stripped: 2 = nodes, 3 = elements, 100 = a
nodal result block; 9999 = end) is a stable, documented, uncopyrightable layout. A result block
opens with ``-4  NAME  ncomps``, lists ``-5`` component names, then ``-1  node  values...`` data
records (continued on ``-2`` lines when a field has more than 6 components). We read DISP (3
components) and STRESS (6: SXX SYY SZZ SXY SYZ SZX), derive von Mises + displacement magnitude,
and compute a safety factor against the material yield. One class.
"""

import logging
import math

logger = logging.getLogger(__name__)

# Real ccx .frd records are FIXED-WIDTH, not whitespace-separated: after the leading marker
# (" -1"/" -2", 3 chars) the node number is 10 chars and each value is 12 chars, and CalculiX packs
# negatives with no separating space (e.g. "1-4.00000E+01"). So we slice columns, never split().
_MARKER_WIDTH = 3
_NODE_WIDTH = 10
_VALUE_WIDTH = 12


class FrdReader:
    """Reads a CalculiX .frd into ``{nodes, fields, summary}`` and writes a vtk field mesh."""

    def read(self, frd_path: str, material: dict) -> dict:
        """Parse ``frd_path``; return ``{nodes, fields, summary}``.

        ``fields`` maps a field name (DISP/STRESS) to ``{node: [values]}``. ``summary`` holds
        ``max_von_mises``, ``max_displacement``, ``frequencies`` and ``safety_factor`` (yield over
        max von Mises when both are known, else None).
        """
        with open(frd_path, encoding="utf-8", errors="ignore") as handle:
            lines = handle.readlines()
        nodes = _read_nodes(lines)
        fields = _read_result_fields(lines)
        summary = _summarize(fields, material)
        logger.info("read %s: %d nodes, fields %s, max von Mises %.3g",
                    frd_path, len(nodes), list(fields), summary["max_von_mises"] or 0.0)
        return {"nodes": nodes, "fields": fields, "summary": summary}

    def scalar_fields(self, read_result: dict) -> dict:
        """Per-node scalar fields ``{name: {node_id: value}}`` derived from a parsed result.

        ``von_mises`` + ``displacement`` come from a structural result (STRESS/DISP);
        ``temperature`` from a thermal result (NDTEMP). Only the fields present are returned, so a
        caller can merge structural + thermal parses (same node ordering) into one field set.
        """
        fields = read_result["fields"]
        out: dict = {}
        if "STRESS" in fields:
            out["von_mises"] = {n: _von_mises(v) for n, v in fields["STRESS"].items()}
        if "DISP" in fields:
            out["displacement"] = {n: math.sqrt(sum(c * c for c in v[:3]))
                                   for n, v in fields["DISP"].items()}
        if "NDTEMP" in fields:
            out["temperature"] = {n: (v[0] if v else 0.0) for n, v in fields["NDTEMP"].items()}
        return out

    def write_vtk(self, read_result: dict, elements: list, out_vtk: str) -> None:
        """Write ``out_vtk`` (nodes + tetra cells + point_data) from a parsed result via meshio.

        ``elements`` is a list of 4-node (or 10-node) connectivity lists over the .frd node ids;
        only the first 4 corner nodes are used for the linear tetra cells the viewer colors.
        """
        import meshio

        node_ids = sorted(read_result["nodes"])
        index_of = {node_id: i for i, node_id in enumerate(node_ids)}
        points = [read_result["nodes"][node_id] for node_id in node_ids]
        cells = [[index_of[n] for n in elem[:4]] for elem in elements if len(elem) >= 4]
        point_data = _point_data(read_result, node_ids)
        mesh = meshio.Mesh(points, [("tetra", cells)] if cells else [], point_data=point_data)
        # ASCII vtk so the viewer (and tests) can read the field mesh as text, not a binary blob.
        mesh.write(out_vtk, file_format="vtk", binary=False)
        logger.info("wrote vtk field mesh %s (%d points, %d cells)",
                    out_vtk, len(points), len(cells))


def _read_nodes(lines: list[str]) -> dict:
    """Read the nodal coordinate block: ``-1 node x y z`` records under the ``2`` block key."""
    nodes: dict = {}
    in_block = False
    for line in lines:
        key = line[:5].strip()
        if key == "2":
            in_block = True
            continue
        if not in_block:
            continue
        marker = line[:_MARKER_WIDTH].strip()
        if marker == "-1":
            node = int(line[_MARKER_WIDTH:_MARKER_WIDTH + _NODE_WIDTH])
            coords = _fixed_floats(line[_MARKER_WIDTH + _NODE_WIDTH:], 3)
            nodes[node] = (coords[0], coords[1], coords[2])
        elif marker == "-3":
            in_block = False
    return nodes


def _read_result_fields(lines: list[str]) -> dict:
    """Read every nodal result block into ``{field_name: {node: [values]}}``."""
    fields: dict = {}
    current: str | None = None
    ncomps = 0
    index = 0
    while index < len(lines):
        line = lines[index]
        marker = line[:3].strip()
        if marker == "-4":
            parts = line.split()
            current = parts[1]
            ncomps = int(parts[2])
            fields[current] = {}
        elif marker == "-1" and current is not None:
            node, values, index = _read_data_record(lines, index, ncomps)
            fields[current][node] = values
            continue
        elif marker == "-3":
            current = None
        index += 1
    return fields


def _read_data_record(lines: list[str], index: int, ncomps: int) -> tuple[int, list[float], int]:
    """Read one ``-1`` record (plus any ``-2`` continuation); return (node, values, next_index).

    Fixed-width: node number is 10 chars after the marker, then 12-char value fields (up to 6 per
    line, continued on ``-2`` lines). ccx packs negatives with no space, so columns are sliced.
    """
    line = lines[index]
    node = int(line[_MARKER_WIDTH:_MARKER_WIDTH + _NODE_WIDTH])
    values = _fixed_floats(line[_MARKER_WIDTH + _NODE_WIDTH:], min(6, ncomps))
    index += 1
    while (len(values) < ncomps and index < len(lines)
           and lines[index][:_MARKER_WIDTH].strip() == "-2"):
        remaining = min(6, ncomps - len(values))
        values += _fixed_floats(lines[index][_MARKER_WIDTH:], remaining)
        index += 1
    return node, values[:ncomps], index


def _fixed_floats(segment: str, count: int) -> list[float]:
    """Parse ``count`` fixed-width (12-char) float fields from ``segment`` (trailing empties ok)."""
    values = []
    for i in range(count):
        field = segment[i * _VALUE_WIDTH:(i + 1) * _VALUE_WIDTH].strip()
        if not field:
            break
        values.append(float(field))
    return values


def _summarize(fields: dict, material: dict) -> dict:
    """Reduce the raw fields to the headline scalars the CLI + sidecar report."""
    max_disp = 0.0
    for values in fields.get("DISP", {}).values():
        max_disp = max(max_disp, math.sqrt(sum(v * v for v in values[:3])))
    max_vm = 0.0
    for values in fields.get("STRESS", {}).values():
        max_vm = max(max_vm, _von_mises(values))
    yield_strength = (material.get("structural") or {}).get("yield")
    safety = (yield_strength / max_vm) if (yield_strength and max_vm > 0) else None
    return {"max_von_mises": max_vm, "max_displacement": max_disp,
            "frequencies": [], "safety_factor": safety}


def _von_mises(stress: list[float]) -> float:
    """Von Mises stress from the CalculiX 6-tuple (SXX, SYY, SZZ, SXY, SYZ, SZX)."""
    if len(stress) < 6:
        return 0.0
    sxx, syy, szz, sxy, syz, szx = stress[:6]
    deviatoric = 0.5 * ((sxx - syy) ** 2 + (syy - szz) ** 2 + (szz - sxx) ** 2)
    shear = 3.0 * (sxy * sxy + syz * syz + szx * szx)
    return math.sqrt(deviatoric + shear)


def _point_data(read_result: dict, node_ids: list[int]) -> dict:
    """Build meshio point_data (von_mises, displacement) aligned to ``node_ids`` order."""
    fields = read_result["fields"]
    data: dict = {}
    if "STRESS" in fields:
        data["von_mises"] = [_von_mises(fields["STRESS"].get(n, [])) for n in node_ids]
    if "DISP" in fields:
        data["displacement"] = [
            math.sqrt(sum(v * v for v in fields["DISP"].get(n, [0, 0, 0])[:3]))
            for n in node_ids]
    return data
