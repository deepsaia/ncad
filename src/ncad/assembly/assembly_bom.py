"""Assembly bill of materials + roll-up mass properties across instances (bucket 5.6).

Groups instances by the {file, part} they reference into BOM line items (part, quantity, material,
per-unit + total mass), and rolls up the assembly's total mass + mass-weighted world COG. Per-part
mass comes from MassCalculator; each instance's COG is transformed to world by its SOLVED placement,
so the roll-up reflects the assembled configuration. A part with no density is counted in the BOM
quantity but omitted from the mass roll-up (mass needs density). Pure aggregation, no kernel.
"""

from typing import Any


class AssemblyBom:
    """Computes grouped BOM line items + a roll-up mass/COG for an assembly."""

    def compute(self, instances: list[dict], part_mass: dict, placements: dict) -> dict:
        """Return {items: [...], mass: {total_mass, cog}} for the assembly's instances."""
        items = self._line_items(instances, part_mass)
        mass = self._rollup(instances, part_mass, placements)
        return {"items": items, "mass": mass}

    def _line_items(self, instances: list[dict], part_mass: dict) -> list[dict]:
        order: list[tuple] = []
        counts: dict[tuple, int] = {}
        for inst in instances:
            key = (inst["file"], inst["part"])
            if key not in counts:
                order.append(key)
            counts[key] = counts.get(key, 0) + 1
        out: list[dict] = []
        for key in order:
            info = part_mass.get(key, {})
            unit = info.get("mass")
            qty = counts[key]
            out.append({
                "part": key[1], "file": key[0], "quantity": qty,
                "material": info.get("material"),
                "unit_mass": unit,
                "total_mass": (unit * qty) if unit is not None else None,
            })
        return out

    def _rollup(self, instances: list[dict], part_mass: dict, placements: dict) -> dict:
        total = 0.0
        weighted = [0.0, 0.0, 0.0]
        for inst in instances:
            info = part_mass.get((inst["file"], inst["part"]), {})
            mass = info.get("mass")
            if mass is None:
                continue
            world = _apply_point(placements.get(inst["id"]), info.get("cog", (0.0, 0.0, 0.0)))
            total += mass
            for i in range(3):
                weighted[i] += mass * world[i]
        cog = tuple(w / total for w in weighted) if total > 0 else (0.0, 0.0, 0.0)
        return {"total_mass": total, "cog": list(cog)}


def _apply_point(matrix: Any, p: tuple) -> tuple:
    """Map a local point through a row-major 4x4 (p' = p . R + t); identity if matrix is None."""
    if not matrix:
        return tuple(p)
    return tuple(sum(p[k] * matrix[k][i] for k in range(3)) + matrix[3][i] for i in range(3))
