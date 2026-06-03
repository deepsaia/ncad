# Example briefs

These are **agent-authorable briefs** — the coarse, round-number input an LLM agent (or a
human) writes. A brief is compiled into a precise, buildable spec by
`ncad.compile.spec_compiler.SpecCompiler`; the agent never hand-authors tangent points,
arc centers, or per-floor wall coordinates.

A brief is intentionally small — round numbers and indices only:

```hocon
footprint = [[0, 0], [12, 0], [12, 9], [0, 9]]   # coarse CCW polygon, round numbers
rounded_corners = { "1" = 1.5, "3" = 1.0 }        # vertex index -> fillet radius (optional)
num_rooms = 4
num_storeys = 2                                   # optional, default 1
storey_height = 3.0
roof = "flat"                                     # flat | gable | shed | hip
balconies = [                                     # optional; upper storeys only (index >= 1)
  { storey = 1, wall = 0, along = 0.5, length = 4.0, depth = 1.5 }
]
```

The briefs here cover the range: flat/gable/hip/shed roofs, rounded corners, L-shape and
irregular footprints, multi-storey, and balconies (incl. a combined rounded + two-storey +
balcony example).

## Build & view

`out/` is generated (gitignored). Build every brief into it, then view in the browser:

```bash
ncad-examples        # compiles examples/*.hocon -> out/  (model + BOM + plan each)
nv out               # serve the browser 3D viewer at http://127.0.0.1:8000
```

Deep-link straight to a model: `http://127.0.0.1:8000/09_three_storey_balconies.glb`
preselects it in the viewer.

Compile one brief in code:

```python
from ncad.compile.spec_compiler import SpecCompiler
from ncad.spec.spec_loader import SpecLoader
spec = SpecCompiler().compile(SpecLoader().load("examples/05_rounded_corners.hocon"))
```
