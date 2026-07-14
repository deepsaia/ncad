"""Re-parent a built sub-assembly's instances under a parent placement (bucket 5.7).

A nested ``assembly`` instance is built independently (its own solve frozen), then its solved
instances are composed into the parent's frame: each child placement is multiplied by the parent
matrix and its id namespaced ``parent/child``, so the flat scene sidecar stays unique and the child
moves rigidly with the parent. Pure row-major 4x4 math (the AssemblyPlacement convention).
"""


class SubAssemblyComposer:
    """Composes a child assembly's instances into a parent placement frame."""

    def compose(self, child_instances: list, parent_matrix: list[list[float]],
                id_prefix: str) -> list[dict]:
        """Return child instances re-parented under ``parent_matrix``, ids prefixed."""
        out: list[dict] = []
        for child in child_instances:
            composed = dict(child)
            composed["id"] = f"{id_prefix}/{child['id']}"
            composed["placement"] = _matmul(child["placement"], parent_matrix)
            out.append(composed)
        return out


def _matmul(a: list[list[float]], b: list[list[float]]) -> list[list[float]]:
    """Row-major 4x4 product ``a @ b`` (child-local pose, then the parent transform)."""
    return [[sum(a[i][k] * b[k][j] for k in range(4)) for j in range(4)] for i in range(4)]
