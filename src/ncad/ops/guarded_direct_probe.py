"""Top-level, picklable probe run in a child process to guard a direct op on imported geometry.

GuardedRunner requires picklable args and no live OCP handles cross the process boundary, so the
child re-imports the solid from a STEP path, applies the op, and exports the result to another
STEP path (returned to the parent). Scoped to whole-solid offset first (no face to re-resolve);
face-targeted ops on imports stay in-process (still oracle-verified) until face re-resolve by a
geometric key is proven (see the bucket spec).
"""


def guarded_offset_probe(step_path: str, distance: float, out_path: str) -> str:
    """Import ``step_path``, offset by ``distance``, export to ``out_path``; return ``out_path``."""
    from ncad.kernel.build123d_kernel import Build123dKernel

    kernel = Build123dKernel()
    solid = kernel.import_solid(step_path)
    result = kernel.offset_solid(solid, distance)
    kernel.export(result, out_path)
    return out_path
