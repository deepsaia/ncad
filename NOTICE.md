# ncad licensing

ncad is licensed under the **GNU General Public License, version 3** (GPL-3.0-only). The full text
is in `LICENSE`.

## Why GPL

ncad depends on and hard-imports **py-slvs** (the Python binding of SolveSpace's geometric constraint
solver), which is **GPL-3.0**. py-slvs is imported at module top level in two core solvers:

- `src/ncad/sketch/slvs_solver.py` (the 2D sketch constraint solver)
- `src/ncad/assembly/mate_solver.py` (the 3D assembly mate/joint solver)
