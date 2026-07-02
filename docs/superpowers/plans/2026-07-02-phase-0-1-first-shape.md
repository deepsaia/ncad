# Phase 0 Bucket 0.1 — First Shape on Screen — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Author a minimal feature-tree document (a rectangle sketch + extrude) in HOCON, run it through a pure op-dispatch executor onto the build123d kernel, export glTF, and see the extruded block in the `nv` browser viewer.

**Architecture:** A document (plain dict) declares `parts[].features[]`. A registry maps each feature `op` to a pure builder function with the uniform signature `op(shape_in, params, prov_in) -> (shape_out, prov_out, issues)`. A `Builder` walks a part's features in order, threading the shape, and produces a geometry handle. The existing `Build123dKernel` gains two general primitives (`polygon_face`, `extrude`) behind the `Kernel` contract; the existing `spec`/`viewer` layers and pytest/uv tooling are reused unchanged. A thin CLI (`python -m ncad.build <doc> --out out/`) ties author → build → glTF, then `nv out/` shows it.

**Tech Stack:** Python 3.13, build123d 0.10.0 (OCCT/OCP), jsonschema (draft 2020-12), leaf-common (HOCON/JSON → dict), pytest, ruff, uv-managed `.venv`.

## Global Constraints

- **Python 3.13**; run everything via the repo `.venv` (`.venv/bin/python`, `.venv/bin/pytest`, `.venv/bin/ruff`). Copied verbatim from `.python-version` = `3.13`.
- **No nested functions or nested classes.** Every function and class at module top level. (CLAUDE.md)
- **One class per module**; `__init__.py` holds only re-exports, never logic. (CLAUDE.md)
- **Explicit type hints on every function/method.** PEP 8. Imports grouped stdlib / third-party / local. (CLAUDE.md)
- **Structured logging** via `logging.getLogger(__name__)`, never `print` for diagnostics (CLI user-facing summary via `print` is fine). (CLAUDE.md)
- **Validation issues are data** (dataclass), returned in lists — never raised. Programmer/contract errors *do* raise typed exceptions. (CLAUDE.md, design §10)
- **Canonical internal unit is millimetres**; documents declare `units` (`"mm"`|`"m"`|`"in"`). Bucket 0.1 uses `"mm"`. (design §0)
- **Determinism:** the executor is pure — same document → identical geometry. No randomness, no global mutation in the build path. (design §0, §4)
- **Every node carries a stable string `id`.** (design §0)
- **Importing build123d/OCP is slow (~seconds).** Tests that import the real kernel must be marked `@pytest.mark.slow` (see `pyproject.toml [tool.pytest.ini_options] markers`). Fast tests must not import it.
- **Ruff must pass:** `.venv/bin/ruff check src tests` clean before each commit.

---

## File Structure

**Removed in Task 1** (v1 building-specific; preserved in git history, recast later as the Phase 11 building profile):
- `src/ncad/generate/`, `src/ncad/compile/`, `src/ncad/render/`, `src/ncad/bom/`, `src/ncad/validate/`, `src/ncad/build/`, `src/ncad/pipeline/`
- `schema/building_schema.hocon`, `examples/`, `tests/fixtures/` (building specs/goldens/briefs)
- building-specific tests: `tests/generate/`, `tests/compile/`, `tests/render/`, `tests/bom/`, `tests/validate/`, `tests/build/`, `tests/pipeline/`
- building-shaped kernel methods on `Build123dKernel` and the `Kernel` ABC (`prism`, `extrude_polygon`, `extrude_rounded_polygon`, `arc_wall`, `sphere`, `barrel`, `intersect`, `union`, `subtract` are trimmed to what 0.1 needs; see Task 3)

**Kept (reuse core):** `src/ncad/spec/` (loader, schema_validator, schema_issue), `src/ncad/viewer/` (all), `src/ncad/kernel/kernel.py` + `build123d_kernel.py` (trimmed), tooling (`pyproject.toml`, `.python-version`), `tests/kernel/`, `tests/spec/`, `tests/viewer/`, `tests/test_imports.py`.

**Created:**
- `schema/part_schema.hocon` — the feature-tree JSON-Schema vocabulary (HOCON).
- `src/ncad/ops/__init__.py` — re-exports.
- `src/ncad/ops/op_result.py` — `OpResult` dataclass (shape_out, provenance_out, issues).
- `src/ncad/ops/op_registry.py` — `OpRegistry` (op name → builder fn dispatch).
- `src/ncad/ops/sketch_op.py` — `build_sketch` (rectangle → face handle).
- `src/ncad/ops/extrude_op.py` — `build_extrude` (face → solid).
- `src/ncad/build/__init__.py` — re-exports.
- `src/ncad/build/build_issue.py` — `BuildIssue` dataclass (id-tagged).
- `src/ncad/build/builder.py` — `Builder` (walks a part's features, threads shape).
- `src/ncad/build/__main__.py` — CLI: document → build → glTF into out-dir.
- `tests/ops/`, `tests/build/` (new), fixtures under `tests/fixtures/parts/`.

**Interfaces locked across tasks (names/types every task must match):**
- `Kernel.polygon_face(self, points: list[Point2], plane: str) -> Any` — closed planar face on plane `"XY"|"XZ"|"YZ"` from 2D points (mm).
- `Kernel.extrude(self, face: Any, distance: float) -> Any` — solid by extruding `face` its normal by `distance` (mm).
- `OpResult` — `dataclass(frozen=True)` with `shape: Any`, `provenance: dict[str, str]`, `issues: list[BuildIssue]`.
- `BuildIssue` — `dataclass(frozen=True)` with `node_id: str`, `message: str`.
- op builder signature: `def build_<op>(shape_in: Any, params: dict, provenance_in: dict[str, str], kernel: Kernel) -> OpResult`.
- `OpRegistry.get(self, op: str) -> Callable` ; `OpRegistry.register(self, op: str, fn: Callable) -> None`.
- `Builder.__init__(self, kernel: Kernel, registry: OpRegistry)` ; `Builder.build_part(self, part: dict) -> OpResult` (final shape + merged provenance + accumulated issues).

---

## Task 1: Clean slate — remove v1 building code, keep the reuse core

**Files:**
- Delete (dirs): `src/ncad/generate/`, `src/ncad/compile/`, `src/ncad/render/`, `src/ncad/bom/`, `src/ncad/validate/`, `src/ncad/build/`, `src/ncad/pipeline/`
- Delete: `schema/building_schema.hocon`, `examples/` (whole dir), `tests/fixtures/box_house.hocon`, `tests/fixtures/L_house.hocon`, `tests/fixtures/irregular_house.hocon`, `tests/fixtures/golden_spec_seed42.json`, `tests/fixtures/golden_spec_L_seed42.json`, `tests/fixtures/briefs/` (whole dir)
- Delete (test dirs): `tests/generate/`, `tests/compile/`, `tests/render/`, `tests/bom/`, `tests/validate/`, `tests/build/`, `tests/pipeline/`
- Modify: `pyproject.toml` (remove building-only `[project.scripts]` entries `ncad` and `ncad-examples`; keep `nv`), `tests/spec/test_fixture_specs.py` (delete — it asserts building fixtures), `src/ncad/spec/schema_validator.py` (repoint default schema; done in Task 2)

**Interfaces:**
- Consumes: nothing.
- Produces: a repo whose `src/ncad/` contains only `spec/`, `kernel/`, `viewer/`, plus `__init__.py`; tests contain only `spec/`, `kernel/`, `viewer/`, `test_imports.py`.

- [ ] **Step 1: Confirm the working tree is clean and on main**

Run: `cd /Users/228496/exp/ncad && git status --short && git branch --show-current`
Expected: no output from status; branch is `main`. (Task 1 will create a branch in Step 8.)

- [ ] **Step 2: Create the working branch**

```bash
cd /Users/228496/exp/ncad
git checkout -b phase-0/bucket-0.1-first-shape
```

- [ ] **Step 3: Delete v1 building-specific source modules**

```bash
cd /Users/228496/exp/ncad
git rm -r src/ncad/generate src/ncad/compile src/ncad/render src/ncad/bom src/ncad/validate src/ncad/build src/ncad/pipeline
```

- [ ] **Step 4: Delete v1 building schema, examples, fixtures, and their tests**

```bash
cd /Users/228496/exp/ncad
git rm schema/building_schema.hocon
git rm -r examples
git rm tests/fixtures/box_house.hocon tests/fixtures/L_house.hocon tests/fixtures/irregular_house.hocon tests/fixtures/golden_spec_seed42.json tests/fixtures/golden_spec_L_seed42.json
git rm -r tests/fixtures/briefs
git rm -r tests/generate tests/compile tests/render tests/bom tests/validate tests/build tests/pipeline
git rm tests/spec/test_fixture_specs.py
```

- [ ] **Step 5: Remove building-only console scripts from pyproject.toml**

In `pyproject.toml`, the `[project.scripts]` block currently reads:

```toml
[project.scripts]
# `ncad` = run the full spine (generate → validate → build → export).
ncad = "ncad.pipeline.__main__:main"
# `nv` = ncad viewer — launch the browser 3D viewer (alias for `python -m ncad.viewer`).
nv = "ncad.viewer.__main__:main"
# `ncad-examples` = compile every example brief into out/ for the viewer.
ncad-examples = "ncad.pipeline.build_examples:main"
```

Replace that whole block with:

```toml
[project.scripts]
# `nv` = ncad viewer — launch the browser 3D viewer (alias for `python -m ncad.viewer`).
nv = "ncad.viewer.__main__:main"
# `ncad-build` = build a feature-tree document to glTF (added in Task 8).
ncad-build = "ncad.build.__main__:main"
```

- [ ] **Step 6: Verify remaining source tree is exactly the reuse core**

Run: `cd /Users/228496/exp/ncad && find src/ncad -name '*.py' | sort`
Expected: exactly these paths:
```
src/ncad/__init__.py
src/ncad/kernel/__init__.py
src/ncad/kernel/build123d_kernel.py
src/ncad/kernel/kernel.py
src/ncad/spec/__init__.py
src/ncad/spec/schema_issue.py
src/ncad/spec/schema_validator.py
src/ncad/spec/spec_loader.py
src/ncad/spec/spec_writer.py
```

- [ ] **Step 7: Run the surviving fast tests to confirm nothing dangling imports deleted code**

Run: `cd /Users/228496/exp/ncad && .venv/bin/pytest -m "not slow" -q`
Expected: PASS. NOTE — `tests/kernel/test_kernel_interface.py`, `tests/kernel/fake_kernel.py`, `tests/kernel/test_build123d_kernel.py`, and `tests/spec/test_schema_validator.py` will still reference building-shaped kernel methods and the building schema; they are updated in Tasks 2–3. If they fail to *collect* (import errors), that is expected here — instead run only the import smoke test:
Run: `.venv/bin/pytest tests/test_imports.py -q`
Expected: PASS. If `tests/test_imports.py` imports any deleted module, edit it to import only `ncad.spec`, `ncad.kernel`, `ncad.viewer`, then re-run.

- [ ] **Step 8: Commit**

```bash
cd /Users/228496/exp/ncad
git add -A
git commit -m "Remove v1 building code; keep spec/kernel/viewer reuse core"
```

---

## Task 2: The feature-tree schema + validator repoint

**Files:**
- Create: `schema/part_schema.hocon`
- Modify: `src/ncad/spec/schema_validator.py:19` (default `_SCHEMA_PATH` → `part_schema.hocon`)
- Modify: `tests/spec/test_schema_validator.py` (replace building spec with a part document)
- Test: `tests/spec/test_schema_validator.py`

**Interfaces:**
- Consumes: `SpecLoader` (unchanged), `SchemaValidator`, `SchemaIssue` (unchanged, `location`+`message`).
- Produces: `schema/part_schema.hocon` validating a document with `schema_version`, `units`, `parts{ <name>: { profile, features:[ {id, op, ...} ] } }`. `SchemaValidator()` (no arg) defaults to this schema.

- [ ] **Step 1: Write the failing test**

Replace the contents of `tests/spec/test_schema_validator.py` with:

```python
"""Tests for the schema validator against the feature-tree part schema.

Issues are returned as data (a list of SchemaIssue); an empty list means valid.
"""

from ncad.spec.schema_validator import SchemaValidator


def _valid_document() -> dict:
    return {
        "schema_version": 2,
        "units": "mm",
        "parts": {
            "block": {
                "profile": "solid",
                "features": [
                    {
                        "id": "sk",
                        "op": "sketch",
                        "plane": "XY",
                        "elements": [
                            {"id": "r", "type": "rectangle", "w": 80.0, "h": 60.0}
                        ],
                    },
                    {"id": "pad", "op": "extrude", "profile": "sk", "distance": 8.0},
                ],
            }
        },
    }


def test_valid_document_has_no_issues() -> None:
    assert SchemaValidator().validate(_valid_document()) == []


def test_missing_units_is_flagged() -> None:
    doc = _valid_document()
    del doc["units"]

    issues = SchemaValidator().validate(doc)

    assert any(issue.location == "<root>" for issue in issues)


def test_feature_without_id_is_flagged() -> None:
    doc = _valid_document()
    del doc["parts"]["block"]["features"][0]["id"]

    issues = SchemaValidator().validate(doc)

    assert issues != []


def test_negative_extrude_distance_is_flagged() -> None:
    doc = _valid_document()
    doc["parts"]["block"]["features"][1]["distance"] = -8.0

    issues = SchemaValidator().validate(doc)

    assert issues != []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/228496/exp/ncad && .venv/bin/pytest tests/spec/test_schema_validator.py -q`
Expected: FAIL — the default schema is still the (now-deleted) building schema, so `SchemaValidator()` raises `FileNotFoundError`, or validation flags the new document shape.

- [ ] **Step 3: Create the part schema**

Create `schema/part_schema.hocon`:

```hocon
# ncad feature-tree part schema (HOCON) — JSON-Schema draft 2020-12 vocabulary.
#
# Authored in HOCON: comments, and DRY via ${...} substitution rather than $ref.
# Avoid every $-prefixed key ($schema/$id/$ref) — HOCON's `$` is its substitution
# sigil. The validator loads this to a dict (via leaf-common) and hands it to
# jsonschema, which never reads the file itself.
#
# Units are declared per-document (mm | m | in); canonical internal unit is mm.
# Intentionally PERMISSIVE while young: no additionalProperties=false, so unknown
# fields pass and the schema grows without rejecting future documents. Only settled
# structural fields are constrained. Bump schema_version on incompatible changes.

definitions {
  # A 2D point (x, y).
  vec2 {
    type = array
    items { type = number }
    minItems = 2
    maxItems = 2
  }

  # A sketch element. Bucket 0.1 supports the rectangle only; the enum grows later.
  sketch_element {
    type = object
    required = ["id", "type"]
    properties {
      id { type = string }
      type { enum = ["rectangle"] }
      w { type = number, exclusiveMinimum = 0 }
      h { type = number, exclusiveMinimum = 0 }
    }
  }

  # One feature in a part's ordered feature tree. `op` selects the builder; the
  # remaining fields are op-specific and validated permissively here.
  feature {
    type = object
    required = ["id", "op"]
    properties {
      id { type = string }
      op { type = string }
      plane { enum = ["XY", "XZ", "YZ"] }
      elements {
        type = array
        items = ${definitions.sketch_element}
      }
      profile { type = string }
      distance { type = number, exclusiveMinimum = 0 }
    }
  }

  # A part: a profile kind plus an ordered list of features.
  part {
    type = object
    required = ["profile", "features"]
    properties {
      profile { type = string }
      features {
        type = array
        items = ${definitions.feature}
      }
    }
  }
}

type = object
required = ["schema_version", "units", "parts"]
properties {
  schema_version { type = integer, minimum = 1 }
  units { enum = ["mm", "m", "in"] }
  parameters { type = object }
  datums { type = object }
  parts {
    type = object
    minProperties = 1
    additionalProperties = ${definitions.part}
  }
}
```

- [ ] **Step 4: Repoint the validator default schema**

In `src/ncad/spec/schema_validator.py`, line 19 currently reads:

```python
_SCHEMA_PATH = Path(__file__).resolve().parents[3] / "schema" / "building_schema.hocon"
```

Change it to:

```python
_SCHEMA_PATH = Path(__file__).resolve().parents[3] / "schema" / "part_schema.hocon"
```

Also update the class docstring on line 24 from `building schema` to `part (feature-tree) schema`.

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd /Users/228496/exp/ncad && .venv/bin/pytest tests/spec/test_schema_validator.py -q`
Expected: PASS (4 passed).

- [ ] **Step 6: Lint**

Run: `cd /Users/228496/exp/ncad && .venv/bin/ruff check src tests`
Expected: no errors (`All checks passed!`).

- [ ] **Step 7: Commit**

```bash
cd /Users/228496/exp/ncad
git add schema/part_schema.hocon src/ncad/spec/schema_validator.py tests/spec/test_schema_validator.py
git commit -m "Add feature-tree part schema; repoint validator default"
```

---

## Task 3: Trim the Kernel contract and add general primitives

**Files:**
- Modify: `src/ncad/kernel/kernel.py` (trim building methods; add `polygon_face`, `extrude`; keep `volume`, `bounding_box`, `export`)
- Modify: `src/ncad/kernel/build123d_kernel.py` (implement the two new primitives; delete building methods + their helpers)
- Modify: `tests/kernel/fake_kernel.py` (implement the trimmed contract)
- Modify: `tests/kernel/test_kernel_interface.py` (test against the trimmed contract via the fake)
- Modify: `tests/kernel/test_build123d_kernel.py` (slow; test the two real primitives)

**Interfaces:**
- Consumes: `Point2 = tuple[float, float]`, `Point3`, `Bounds` (unchanged, in `kernel.py`).
- Produces:
  - `Kernel.polygon_face(self, points: list[Point2], plane: str) -> Any`
  - `Kernel.extrude(self, face: Any, distance: float) -> Any`
  - `Kernel.volume(self, solid: Any) -> float` (kept)
  - `Kernel.bounding_box(self, solid: Any) -> Bounds` (kept)
  - `Kernel.export(self, solid: Any, path: str) -> None` (kept)

- [ ] **Step 1: Write the failing interface test (fast, uses the fake)**

Replace `tests/kernel/test_kernel_interface.py` with:

```python
"""Contract tests for the trimmed Kernel, exercised through the fake kernel.

Fast: no OCP import. The real build123d kernel is tested (slow) separately.
"""

from tests.kernel.fake_kernel import FakeKernel


def test_extrude_rectangle_has_expected_volume() -> None:
    kernel = FakeKernel()
    face = kernel.polygon_face([(0, 0), (80, 0), (80, 60), (0, 60)], "XY")

    solid = kernel.extrude(face, 8.0)

    assert kernel.volume(solid) == 80.0 * 60.0 * 8.0


def test_extrude_rectangle_bounds() -> None:
    kernel = FakeKernel()
    face = kernel.polygon_face([(0, 0), (80, 0), (80, 60), (0, 60)], "XY")

    solid = kernel.extrude(face, 8.0)

    (minx, miny, minz), (maxx, maxy, maxz) = kernel.bounding_box(solid)
    assert (minx, miny, minz) == (0.0, 0.0, 0.0)
    assert (maxx, maxy, maxz) == (80.0, 60.0, 8.0)
```

- [ ] **Step 2: Run it to verify it fails**

Run: `cd /Users/228496/exp/ncad && .venv/bin/pytest tests/kernel/test_kernel_interface.py -q`
Expected: FAIL — `FakeKernel` has no `polygon_face`/`extrude` yet (AttributeError) or import error from the old contract.

- [ ] **Step 3: Rewrite the Kernel ABC (trimmed)**

Replace the entire body of `src/ncad/kernel/kernel.py` with:

```python
"""Abstract geometry-kernel contract.

The Builder talks only to this interface, never to a concrete backend, so the kernel
is swappable (build123d today, something else later) and Builder logic is testable
against a lightweight fake without importing a heavy CAD backend. Shapes are opaque
handles whose concrete type is the backend's business.

Coordinates and distances are in the document's canonical internal unit (millimetres).
"""

from abc import ABC, abstractmethod
from typing import Any

Point3 = tuple[float, float, float]
Point2 = tuple[float, float]
Bounds = tuple[Point3, Point3]

_PLANES = ("XY", "XZ", "YZ")


class Kernel(ABC):
    """Operations a geometry backend must provide for the general feature spine."""

    @abstractmethod
    def polygon_face(self, points: list[Point2], plane: str) -> Any:
        """A closed planar face from ordered 2D ``points`` (not closed: first != last).

        ``plane`` is one of ``"XY"``, ``"XZ"``, ``"YZ"``; the 2D coordinates are placed
        on that plane through the world origin. Used to turn a solved sketch profile
        into a face for extrusion.
        """

    @abstractmethod
    def extrude(self, face: Any, distance: float) -> Any:
        """Extrude ``face`` along its normal by ``distance`` into a solid."""

    @abstractmethod
    def volume(self, solid: Any) -> float:
        """Volume of ``solid`` in cubic (internal-unit) units."""

    @abstractmethod
    def bounding_box(self, solid: Any) -> Bounds:
        """Axis-aligned bounds of ``solid`` as ``((minx,miny,minz),(maxx,maxy,maxz))``."""

    @abstractmethod
    def export(self, solid: Any, path: str) -> None:
        """Write ``solid`` to ``path``; format inferred from the extension."""
```

- [ ] **Step 4: Implement the two primitives in the build123d kernel**

Replace the entire body of `src/ncad/kernel/build123d_kernel.py` with:

```python
"""Concrete geometry kernel backed by build123d (OpenCASCADE / OCP).

Implements the Kernel contract with precise B-rep solids and exports to glTF / STEP /
STL. Importing this module pulls in OCP, which is slow on first load — keep it out of
the fast test path.
"""

import logging
from typing import Any

from build123d import (
    Edge,
    Face,
    Plane,
    Unit,
    Vector,
    Wire,
    export_gltf,
    export_step,
    export_stl,
    extrude,
)

from ncad.kernel.kernel import Bounds, Kernel, Point2

logger = logging.getLogger(__name__)

_PLANES = {"XY": Plane.XY, "XZ": Plane.XZ, "YZ": Plane.YZ}


class Build123dKernel(Kernel):
    """build123d-backed kernel. Shapes are build123d ``Face``/``Solid`` objects."""

    def polygon_face(self, points: list[Point2], plane: str) -> Any:
        if plane not in _PLANES:
            raise ValueError(f"plane must be one of {tuple(_PLANES)}, got {plane!r}")
        basis = _PLANES[plane]
        world = [basis.from_local_coords(Vector(x, y, 0)) for x, y in points]
        closed = world + [world[0]]
        edges = [Edge.make_line(closed[i], closed[i + 1]) for i in range(len(world))]
        return Face(Wire(edges))

    def extrude(self, face: Any, distance: float) -> Any:
        return extrude(face, amount=distance)

    def volume(self, solid: Any) -> float:
        return solid.volume

    def bounding_box(self, solid: Any) -> Bounds:
        box = solid.bounding_box()
        return (tuple(box.min), tuple(box.max))

    def export(self, solid: Any, path: str) -> None:
        lowered = path.lower()
        if lowered.endswith(".glb"):
            export_gltf(solid, path, unit=Unit.MM, binary=True)
        elif lowered.endswith(".gltf"):
            export_gltf(solid, path, unit=Unit.MM, binary=False)
        elif lowered.endswith((".step", ".stp")):
            export_step(solid, path, unit=Unit.MM)
        elif lowered.endswith(".stl"):
            export_stl(solid, path)
        else:
            raise ValueError(
                f"unsupported export format for {path!r}; expected .gltf/.glb/.step/.stp/.stl"
            )
        logger.debug("exported solid to %s", path)
```

- [ ] **Step 5: Rewrite the fake kernel (fast, no OCP)**

Replace the entire body of `tests/kernel/fake_kernel.py` with:

```python
"""A lightweight, dependency-free Kernel for fast tests.

A face is modeled as its 2D point ring plus plane; a solid as (face, distance). Volume
and bounds are computed analytically for the axis-aligned extrusion cases Bucket 0.1
uses. Not for production geometry — enough to assert Builder behaviour without OCP.
"""

from typing import Any

from ncad.kernel.kernel import Bounds, Kernel, Point2


class _FakeFace:
    """A planar polygon: its 2D point ring and the plane it lives on."""

    def __init__(self, points: list[Point2], plane: str) -> None:
        self.points = points
        self.plane = plane


class _FakeSolid:
    """A face extruded by a distance along the plane normal."""

    def __init__(self, face: _FakeFace, distance: float) -> None:
        self.face = face
        self.distance = distance


class FakeKernel(Kernel):
    """In-memory kernel: analytic volume/bounds for axis-aligned extrusions."""

    def polygon_face(self, points: list[Point2], plane: str) -> Any:
        return _FakeFace(points, plane)

    def extrude(self, face: Any, distance: float) -> Any:
        return _FakeSolid(face, distance)

    def volume(self, solid: Any) -> float:
        return _polygon_area(solid.face.points) * solid.distance

    def bounding_box(self, solid: Any) -> Bounds:
        xs = [x for x, _ in solid.face.points]
        ys = [y for _, y in solid.face.points]
        # Bucket 0.1 uses the XY plane; extrude along +Z by distance.
        return ((min(xs), min(ys), 0.0), (max(xs), max(ys), solid.distance))

    def export(self, solid: Any, path: str) -> None:
        raise NotImplementedError("FakeKernel does not export geometry")


def _polygon_area(points: list[Point2]) -> float:
    """Shoelace area of a closed ring given as non-repeating vertices."""
    n = len(points)
    total = 0.0
    for i in range(n):
        x0, y0 = points[i]
        x1, y1 = points[(i + 1) % n]
        total += x0 * y1 - x1 * y0
    return abs(total) / 2.0
```

- [ ] **Step 6: Run the fast interface test**

Run: `cd /Users/228496/exp/ncad && .venv/bin/pytest tests/kernel/test_kernel_interface.py -q`
Expected: PASS (2 passed).

- [ ] **Step 7: Rewrite the slow build123d kernel test**

Replace `tests/kernel/test_build123d_kernel.py` with:

```python
"""Slow tests for the real build123d kernel (imports OCP)."""

import pytest

from ncad.kernel.build123d_kernel import Build123dKernel


@pytest.mark.slow
def test_extrude_rectangle_volume_is_exact() -> None:
    kernel = Build123dKernel()
    face = kernel.polygon_face([(0, 0), (80, 0), (80, 60), (0, 60)], "XY")

    solid = kernel.extrude(face, 8.0)

    assert kernel.volume(solid) == pytest.approx(80.0 * 60.0 * 8.0)


@pytest.mark.slow
def test_extrude_rectangle_bounds_are_exact() -> None:
    kernel = Build123dKernel()
    face = kernel.polygon_face([(0, 0), (80, 0), (80, 60), (0, 60)], "XY")

    solid = kernel.extrude(face, 8.0)

    (minx, miny, minz), (maxx, maxy, maxz) = kernel.bounding_box(solid)
    assert (minx, miny, minz) == pytest.approx((0.0, 0.0, 0.0))
    assert (maxx, maxy, maxz) == pytest.approx((80.0, 60.0, 8.0))


@pytest.mark.slow
def test_export_glb_writes_file(tmp_path) -> None:
    kernel = Build123dKernel()
    face = kernel.polygon_face([(0, 0), (10, 0), (10, 10), (0, 10)], "XY")
    solid = kernel.extrude(face, 5.0)

    out = tmp_path / "block.glb"
    kernel.export(solid, str(out))

    assert out.is_file() and out.stat().st_size > 0
```

- [ ] **Step 8: Run the slow kernel test (first OCP import is slow, ~tens of seconds)**

Run: `cd /Users/228496/exp/ncad && .venv/bin/pytest tests/kernel/test_build123d_kernel.py -m slow -q`
Expected: PASS (3 passed). If `Plane.from_local_coords` is unavailable in build123d 0.10.0, use `basis.location * Vector(x, y, 0)` instead in `polygon_face` and re-run.

- [ ] **Step 9: Lint**

Run: `cd /Users/228496/exp/ncad && .venv/bin/ruff check src tests`
Expected: `All checks passed!`

- [ ] **Step 10: Commit**

```bash
cd /Users/228496/exp/ncad
git add src/ncad/kernel tests/kernel
git commit -m "Trim Kernel to general primitives (polygon_face, extrude)"
```

---

## Task 4: OpResult and BuildIssue data types

**Files:**
- Create: `src/ncad/build/__init__.py`
- Create: `src/ncad/build/build_issue.py`
- Create: `src/ncad/ops/__init__.py`
- Create: `src/ncad/ops/op_result.py`
- Test: `tests/ops/__init__.py`, `tests/ops/test_op_result.py`, `tests/build/__init__.py`, `tests/build/test_build_issue.py`

**Interfaces:**
- Consumes: nothing.
- Produces:
  - `BuildIssue` — `dataclass(frozen=True)`, fields `node_id: str`, `message: str`.
  - `OpResult` — `dataclass(frozen=True)`, fields `shape: Any`, `provenance: dict[str, str]`, `issues: list[BuildIssue]`.

- [ ] **Step 1: Write the failing tests**

Create `tests/build/__init__.py` (empty file).
Create `tests/build/test_build_issue.py`:

```python
from ncad.build.build_issue import BuildIssue


def test_build_issue_is_frozen_and_carries_node_id() -> None:
    issue = BuildIssue(node_id="soften", message="cannot find edges")

    assert issue.node_id == "soften"
    assert issue.message == "cannot find edges"
```

Create `tests/ops/__init__.py` (empty file).
Create `tests/ops/test_op_result.py`:

```python
from ncad.build.build_issue import BuildIssue
from ncad.ops.op_result import OpResult


def test_op_result_holds_shape_provenance_issues() -> None:
    result = OpResult(shape="S", provenance={"f1": "sketch"}, issues=[])

    assert result.shape == "S"
    assert result.provenance == {"f1": "sketch"}
    assert result.issues == []


def test_op_result_carries_issues() -> None:
    issue = BuildIssue(node_id="pad", message="boom")
    result = OpResult(shape=None, provenance={}, issues=[issue])

    assert result.issues == [issue]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/228496/exp/ncad && .venv/bin/pytest tests/build/test_build_issue.py tests/ops/test_op_result.py -q`
Expected: FAIL — modules not found (ModuleNotFoundError).

- [ ] **Step 3: Create the data types**

Create `src/ncad/build/__init__.py`:

```python
"""The pure feature executor: builds a document's parts into geometry."""

from ncad.build.build_issue import BuildIssue

__all__ = ["BuildIssue"]
```

Create `src/ncad/build/build_issue.py`:

```python
"""A single build-time issue, returned as data rather than raised (design §10)."""

from dataclasses import dataclass


@dataclass(frozen=True)
class BuildIssue:
    """One problem encountered while building a feature, tagged by node id.

    :ivar node_id: The ``id`` of the feature/node the issue is attributed to.
    :ivar message: Human-readable description of the problem.
    """

    node_id: str
    message: str
```

Create `src/ncad/ops/__init__.py`:

```python
"""Per-feature builder functions and the op-dispatch registry."""

from ncad.ops.op_result import OpResult

__all__ = ["OpResult"]
```

Create `src/ncad/ops/op_result.py`:

```python
"""The uniform result of a feature op: shape, provenance, and issues."""

from dataclasses import dataclass, field
from typing import Any

from ncad.build.build_issue import BuildIssue


@dataclass(frozen=True)
class OpResult:
    """What every feature op returns.

    :ivar shape: The output geometry handle (kernel-opaque), or ``None`` on failure.
    :ivar provenance: Map from output-element tag to the feature ``id`` that produced
        it. Bucket 0.1 records the producing feature per shape; it grows into the full
        element map in later buckets (design §2).
    :ivar issues: Build issues attributed to node ids; empty means clean.
    """

    shape: Any
    provenance: dict[str, str] = field(default_factory=dict)
    issues: list[BuildIssue] = field(default_factory=list)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/228496/exp/ncad && .venv/bin/pytest tests/build/test_build_issue.py tests/ops/test_op_result.py -q`
Expected: PASS (3 passed).

- [ ] **Step 5: Lint**

Run: `cd /Users/228496/exp/ncad && .venv/bin/ruff check src tests`
Expected: `All checks passed!`

- [ ] **Step 6: Commit**

```bash
cd /Users/228496/exp/ncad
git add src/ncad/build/__init__.py src/ncad/build/build_issue.py src/ncad/ops/__init__.py src/ncad/ops/op_result.py tests/build/__init__.py tests/build/test_build_issue.py tests/ops/__init__.py tests/ops/test_op_result.py
git commit -m "Add OpResult and BuildIssue data types"
```

---

## Task 5: The sketch op (rectangle → face)

**Files:**
- Create: `src/ncad/ops/sketch_op.py`
- Test: `tests/ops/test_sketch_op.py`

**Interfaces:**
- Consumes: `Kernel.polygon_face`, `OpResult`, `BuildIssue`.
- Produces: `build_sketch(shape_in: Any, params: dict, provenance_in: dict[str, str], kernel: Kernel) -> OpResult`. `params` is the feature dict (`{"id","op","plane","elements":[...]}`). For a `rectangle` element `{w,h}`, produces a face centred on the origin of `plane` (corners at ±w/2, ±h/2). On unknown element type, returns an `OpResult` with `shape=None` and one `BuildIssue`.

- [ ] **Step 1: Write the failing test**

Create `tests/ops/test_sketch_op.py`:

```python
from ncad.ops.sketch_op import build_sketch
from tests.kernel.fake_kernel import FakeKernel


def _rect_feature() -> dict:
    return {
        "id": "sk",
        "op": "sketch",
        "plane": "XY",
        "elements": [{"id": "r", "type": "rectangle", "w": 80.0, "h": 60.0}],
    }


def test_sketch_builds_a_face_with_expected_area() -> None:
    kernel = FakeKernel()

    result = build_sketch(None, _rect_feature(), {}, kernel)

    assert result.issues == []
    # A rectangle face extruded by 1 gives volume == area.
    solid = kernel.extrude(result.shape, 1.0)
    assert kernel.volume(solid) == 80.0 * 60.0


def test_sketch_records_provenance_for_the_feature() -> None:
    kernel = FakeKernel()

    result = build_sketch(None, _rect_feature(), {}, kernel)

    assert result.provenance.get("sk") == "sketch"


def test_sketch_with_unknown_element_reports_issue_by_id() -> None:
    kernel = FakeKernel()
    feature = _rect_feature()
    feature["elements"][0]["type"] = "trapezoid"

    result = build_sketch(None, feature, {}, kernel)

    assert result.shape is None
    assert len(result.issues) == 1
    assert result.issues[0].node_id == "sk"
```

- [ ] **Step 2: Run it to verify it fails**

Run: `cd /Users/228496/exp/ncad && .venv/bin/pytest tests/ops/test_sketch_op.py -q`
Expected: FAIL — `ncad.ops.sketch_op` not found.

- [ ] **Step 3: Implement the sketch op**

Create `src/ncad/ops/sketch_op.py`:

```python
"""The ``sketch`` feature op: turn 2D elements into a planar face.

Bucket 0.1 supports a single ``rectangle`` element, centred on the plane origin. The
element vocabulary (circle, polygon, constraints) grows in Phase 1.
"""

from typing import Any

from ncad.build.build_issue import BuildIssue
from ncad.kernel.kernel import Kernel, Point2
from ncad.ops.op_result import OpResult


def build_sketch(
    shape_in: Any, params: dict, provenance_in: dict[str, str], kernel: Kernel
) -> OpResult:
    """Build a planar face from the feature's sketch elements.

    :param shape_in: Ignored; a sketch originates geometry (no upstream shape).
    :param params: The feature dict (``id``, ``plane``, ``elements``).
    :param provenance_in: Provenance accumulated from earlier features.
    :param kernel: Geometry backend.
    :return: An :class:`OpResult` whose shape is the face, or ``None`` + an issue.
    """
    feature_id = params["id"]
    plane = params.get("plane", "XY")
    elements = params.get("elements", [])
    if len(elements) != 1 or elements[0].get("type") != "rectangle":
        kinds = [element.get("type") for element in elements]
        issue = BuildIssue(
            node_id=feature_id,
            message=f"sketch supports exactly one rectangle element; got {kinds}",
        )
        return OpResult(shape=None, provenance=dict(provenance_in), issues=[issue])

    element = elements[0]
    points = _rectangle_points(element["w"], element["h"])
    face = kernel.polygon_face(points, plane)
    provenance = dict(provenance_in)
    provenance[feature_id] = "sketch"
    return OpResult(shape=face, provenance=provenance, issues=[])


def _rectangle_points(width: float, height: float) -> list[Point2]:
    """Corner ring of a ``width`` x ``height`` rectangle centred on the origin."""
    half_w, half_h = width / 2.0, height / 2.0
    return [(-half_w, -half_h), (half_w, -half_h), (half_w, half_h), (-half_w, half_h)]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/228496/exp/ncad && .venv/bin/pytest tests/ops/test_sketch_op.py -q`
Expected: PASS (3 passed).

- [ ] **Step 5: Lint, then commit**

```bash
cd /Users/228496/exp/ncad
.venv/bin/ruff check src tests
git add src/ncad/ops/sketch_op.py tests/ops/test_sketch_op.py
git commit -m "Add sketch op (rectangle to face)"
```

Expected before commit: `All checks passed!`

---

## Task 6: The extrude op (face → solid)

**Files:**
- Create: `src/ncad/ops/extrude_op.py`
- Test: `tests/ops/test_extrude_op.py`

**Interfaces:**
- Consumes: `Kernel.extrude`, `OpResult`, `BuildIssue`.
- Produces: `build_extrude(shape_in: Any, params: dict, provenance_in: dict[str, str], kernel: Kernel) -> OpResult`. Requires `shape_in` (the face to extrude) and `params["distance"] > 0`; if `shape_in is None`, returns an issue tagged with the feature id.

- [ ] **Step 1: Write the failing test**

Create `tests/ops/test_extrude_op.py`:

```python
from ncad.ops.extrude_op import build_extrude
from ncad.ops.sketch_op import build_sketch
from tests.kernel.fake_kernel import FakeKernel


def _rect_feature() -> dict:
    return {
        "id": "sk",
        "op": "sketch",
        "plane": "XY",
        "elements": [{"id": "r", "type": "rectangle", "w": 80.0, "h": 60.0}],
    }


def test_extrude_produces_solid_with_expected_volume() -> None:
    kernel = FakeKernel()
    face = build_sketch(None, _rect_feature(), {}, kernel).shape

    result = build_extrude(face, {"id": "pad", "op": "extrude", "distance": 8.0}, {}, kernel)

    assert result.issues == []
    assert kernel.volume(result.shape) == 80.0 * 60.0 * 8.0
    assert result.provenance.get("pad") == "extrude"


def test_extrude_without_input_shape_reports_issue_by_id() -> None:
    kernel = FakeKernel()

    result = build_extrude(None, {"id": "pad", "op": "extrude", "distance": 8.0}, {}, kernel)

    assert result.shape is None
    assert len(result.issues) == 1
    assert result.issues[0].node_id == "pad"
```

- [ ] **Step 2: Run it to verify it fails**

Run: `cd /Users/228496/exp/ncad && .venv/bin/pytest tests/ops/test_extrude_op.py -q`
Expected: FAIL — `ncad.ops.extrude_op` not found.

- [ ] **Step 3: Implement the extrude op**

Create `src/ncad/ops/extrude_op.py`:

```python
"""The ``extrude`` feature op: turn a face into a solid by extruding its normal."""

from typing import Any

from ncad.build.build_issue import BuildIssue
from ncad.kernel.kernel import Kernel
from ncad.ops.op_result import OpResult


def build_extrude(
    shape_in: Any, params: dict, provenance_in: dict[str, str], kernel: Kernel
) -> OpResult:
    """Extrude the upstream face by ``params["distance"]``.

    :param shape_in: The face produced by the referenced sketch feature.
    :param params: The feature dict (``id``, ``distance``).
    :param provenance_in: Provenance accumulated from earlier features.
    :param kernel: Geometry backend.
    :return: An :class:`OpResult` whose shape is the solid, or ``None`` + an issue.
    """
    feature_id = params["id"]
    if shape_in is None:
        issue = BuildIssue(
            node_id=feature_id,
            message="extrude has no input face; its referenced profile did not build",
        )
        return OpResult(shape=None, provenance=dict(provenance_in), issues=[issue])

    solid = kernel.extrude(shape_in, params["distance"])
    provenance = dict(provenance_in)
    provenance[feature_id] = "extrude"
    return OpResult(shape=solid, provenance=provenance, issues=[])
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/228496/exp/ncad && .venv/bin/pytest tests/ops/test_extrude_op.py -q`
Expected: PASS (2 passed).

- [ ] **Step 5: Lint, then commit**

```bash
cd /Users/228496/exp/ncad
.venv/bin/ruff check src tests
git add src/ncad/ops/extrude_op.py tests/ops/test_extrude_op.py
git commit -m "Add extrude op (face to solid)"
```

Expected before commit: `All checks passed!`

---

## Task 7: The op registry and the Builder

**Files:**
- Create: `src/ncad/ops/op_registry.py`
- Create: `src/ncad/build/builder.py`
- Modify: `src/ncad/ops/__init__.py` (re-export `OpRegistry`, `default_registry`)
- Modify: `src/ncad/build/__init__.py` (re-export `Builder`)
- Test: `tests/ops/test_op_registry.py`, `tests/build/test_builder.py`

**Interfaces:**
- Consumes: `build_sketch`, `build_extrude`, `OpResult`, `BuildIssue`, `Kernel`.
- Produces:
  - `OpRegistry.register(self, op: str, fn: Callable) -> None`
  - `OpRegistry.get(self, op: str) -> Callable` (raises `KeyError` for unknown op — a contract error, per CLAUDE.md)
  - `default_registry() -> OpRegistry` (module-level function returning a registry with `sketch` and `extrude` registered)
  - `Builder.__init__(self, kernel: Kernel, registry: OpRegistry)`
  - `Builder.build_part(self, part: dict) -> OpResult` — walks `part["features"]` in order, threads the shape, merges provenance, accumulates issues; a feature that references a `profile` receives that referenced feature's shape as `shape_in`, otherwise the previous feature's shape.

- [ ] **Step 1: Write the failing registry test**

Create `tests/ops/test_op_registry.py`:

```python
import pytest

from ncad.ops.op_registry import OpRegistry, default_registry


def test_register_and_get_roundtrip() -> None:
    registry = OpRegistry()
    sentinel = object()
    registry.register("noop", lambda *a: sentinel)

    assert registry.get("noop")() is sentinel


def test_unknown_op_raises_keyerror() -> None:
    with pytest.raises(KeyError):
        OpRegistry().get("nope")


def test_default_registry_has_sketch_and_extrude() -> None:
    registry = default_registry()

    assert registry.get("sketch") is not None
    assert registry.get("extrude") is not None
```

- [ ] **Step 2: Run it to verify it fails**

Run: `cd /Users/228496/exp/ncad && .venv/bin/pytest tests/ops/test_op_registry.py -q`
Expected: FAIL — `ncad.ops.op_registry` not found.

- [ ] **Step 3: Implement the registry**

Create `src/ncad/ops/op_registry.py`:

```python
"""Op-dispatch registry: feature ``op`` name → builder function.

Adding an operation is registering a function; this is the generalization of v1's
``roof_builders[kind]`` pattern (design §4).
"""

from collections.abc import Callable

from ncad.ops.extrude_op import build_extrude
from ncad.ops.sketch_op import build_sketch


class OpRegistry:
    """Maps feature op names to their builder functions."""

    def __init__(self) -> None:
        self._ops: dict[str, Callable] = {}

    def register(self, op: str, fn: Callable) -> None:
        """Register ``fn`` as the builder for feature op ``op``."""
        self._ops[op] = fn

    def get(self, op: str) -> Callable:
        """Return the builder for ``op``.

        :raises KeyError: If no builder is registered for ``op`` (a contract error;
            the schema should have caught an unknown op earlier).
        """
        return self._ops[op]


def default_registry() -> OpRegistry:
    """A registry with Bucket 0.1's ops (``sketch``, ``extrude``) registered."""
    registry = OpRegistry()
    registry.register("sketch", build_sketch)
    registry.register("extrude", build_extrude)
    return registry
```

- [ ] **Step 4: Run the registry test**

Run: `cd /Users/228496/exp/ncad && .venv/bin/pytest tests/ops/test_op_registry.py -q`
Expected: PASS (3 passed).

- [ ] **Step 5: Write the failing Builder test**

Create `tests/build/test_builder.py`:

```python
from ncad.build.builder import Builder
from ncad.ops.op_registry import default_registry
from tests.kernel.fake_kernel import FakeKernel


def _block_part() -> dict:
    return {
        "profile": "solid",
        "features": [
            {
                "id": "sk",
                "op": "sketch",
                "plane": "XY",
                "elements": [{"id": "r", "type": "rectangle", "w": 80.0, "h": 60.0}],
            },
            {"id": "pad", "op": "extrude", "profile": "sk", "distance": 8.0},
        ],
    }


def test_builder_produces_solid_with_expected_volume() -> None:
    builder = Builder(FakeKernel(), default_registry())

    result = builder.build_part(_block_part())

    assert result.issues == []
    assert FakeKernel().volume(result.shape) == 80.0 * 60.0 * 8.0


def test_builder_merges_provenance_across_features() -> None:
    builder = Builder(FakeKernel(), default_registry())

    result = builder.build_part(_block_part())

    assert result.provenance == {"sk": "sketch", "pad": "extrude"}


def test_builder_extrude_references_named_profile() -> None:
    # 'pad' references 'sk' by name; even if another feature were appended between
    # them, the extrude must consume 'sk'. Here we assert the happy path threads it.
    builder = Builder(FakeKernel(), default_registry())

    result = builder.build_part(_block_part())

    assert result.shape is not None


def test_builder_reports_issue_when_referenced_profile_missing() -> None:
    builder = Builder(FakeKernel(), default_registry())
    part = _block_part()
    part["features"][1]["profile"] = "does_not_exist"

    result = builder.build_part(part)

    assert any(issue.node_id == "pad" for issue in result.issues)
```

- [ ] **Step 6: Run it to verify it fails**

Run: `cd /Users/228496/exp/ncad && .venv/bin/pytest tests/build/test_builder.py -q`
Expected: FAIL — `ncad.build.builder` not found.

- [ ] **Step 7: Implement the Builder**

Create `src/ncad/build/builder.py`:

```python
"""The per-part feature executor: walk features in order, thread the shape.

Pure: same part dict → identical geometry (design §0, §4). Randomness and authoring
live upstream. A feature's input shape is the shape of the feature named by its
``profile`` field, if present, else the previous feature's shape. Provenance and
issues accumulate across the walk; a feature that references a missing profile is
reported by id rather than crashing the build.
"""

import logging
from typing import Any

from ncad.build.build_issue import BuildIssue
from ncad.kernel.kernel import Kernel
from ncad.ops.op_registry import OpRegistry
from ncad.ops.op_result import OpResult

logger = logging.getLogger(__name__)


class Builder:
    """Builds a single part's feature tree into a geometry handle."""

    def __init__(self, kernel: Kernel, registry: OpRegistry) -> None:
        """:param kernel: Geometry backend. :param registry: Op-dispatch registry."""
        self._kernel = kernel
        self._registry = registry

    def build_part(self, part: dict) -> OpResult:
        """Execute ``part["features"]`` in order and return the final result.

        :param part: A part dict (``profile``, ``features``).
        :return: An :class:`OpResult` for the last feature, carrying merged provenance
            and all accumulated issues.
        """
        shape_by_id: dict[str, Any] = {}
        provenance: dict[str, str] = {}
        issues: list[BuildIssue] = []
        previous_shape: Any = None

        for feature in part["features"]:
            feature_id = feature["id"]
            shape_in = self._resolve_input(feature, shape_by_id, previous_shape, issues)
            builder_fn = self._registry.get(feature["op"])
            result = builder_fn(shape_in, feature, provenance, self._kernel)
            provenance = result.provenance
            issues.extend(result.issues)
            shape_by_id[feature_id] = result.shape
            previous_shape = result.shape

        return OpResult(shape=previous_shape, provenance=provenance, issues=issues)

    def _resolve_input(
        self,
        feature: dict,
        shape_by_id: dict[str, Any],
        previous_shape: Any,
        issues: list[BuildIssue],
    ) -> Any:
        """Input shape for ``feature``: its named ``profile``, else previous shape."""
        profile_ref = feature.get("profile")
        if profile_ref is None:
            return previous_shape
        if profile_ref not in shape_by_id:
            issues.append(
                BuildIssue(
                    node_id=feature["id"],
                    message=f"feature references profile {profile_ref!r} which does not exist",
                )
            )
            return None
        return shape_by_id[profile_ref]
```

Note: `"profile"` is overloaded — a part has a `profile` kind (`"solid"`) and an `extrude` feature has a `profile` reference (the sketch id). They live at different levels (part vs feature), so there is no collision: `_resolve_input` only reads `feature.get("profile")`.

- [ ] **Step 8: Wire the re-exports**

Replace `src/ncad/ops/__init__.py` with:

```python
"""Per-feature builder functions and the op-dispatch registry."""

from ncad.ops.op_registry import OpRegistry, default_registry
from ncad.ops.op_result import OpResult

__all__ = ["OpRegistry", "OpResult", "default_registry"]
```

Replace `src/ncad/build/__init__.py` with:

```python
"""The pure feature executor: builds a document's parts into geometry."""

from ncad.build.build_issue import BuildIssue
from ncad.build.builder import Builder

__all__ = ["BuildIssue", "Builder"]
```

- [ ] **Step 9: Run the Builder tests**

Run: `cd /Users/228496/exp/ncad && .venv/bin/pytest tests/build/test_builder.py tests/ops -q`
Expected: PASS (all).

- [ ] **Step 10: Lint, then commit**

```bash
cd /Users/228496/exp/ncad
.venv/bin/ruff check src tests
git add src/ncad/ops src/ncad/build tests/ops/test_op_registry.py tests/build/test_builder.py
git commit -m "Add op registry and pure part Builder"
```

Expected before commit: `All checks passed!`

---

## Task 8: The build CLI (document → glTF) and the end-to-end demo

**Files:**
- Create: `src/ncad/build/document_builder.py` — `DocumentBuilder` (load + validate + build all parts + export).
- Create: `src/ncad/build/__main__.py` — CLI entrypoint.
- Create: `tests/fixtures/parts/block.hocon` — the demo document.
- Test: `tests/build/test_document_builder.py`

**Interfaces:**
- Consumes: `SpecLoader`, `SchemaValidator`, `SchemaIssue`, `Builder`, `default_registry`, `Kernel`, `OpResult`, `BuildIssue`.
- Produces:
  - `DocumentBuilder.__init__(self, kernel: Kernel)`
  - `DocumentBuilder.build(self, document: dict) -> dict[str, OpResult]` — validates (raises `ValueError` listing schema issues on invalid input — a contract error), then builds each part, returning `{part_name: OpResult}`.
  - `DocumentBuilder.build_file(self, path: str, out_dir: str) -> dict[str, str]` — load + build + export each part to `<out_dir>/<part_name>.glb`, returning `{part_name: glb_path}`.
  - `main() -> None` — CLI.

- [ ] **Step 1: Write the demo document fixture**

Create `tests/fixtures/parts/block.hocon`:

```hocon
# Bucket 0.1 demo: a rectangle sketched on XY, extruded into a block.
schema_version = 2
units = mm
parts {
  block {
    profile = solid
    features = [
      {
        id = sk
        op = sketch
        plane = XY
        elements = [ { id = r, type = rectangle, w = 80, h = 60 } ]
      }
      { id = pad, op = extrude, profile = sk, distance = 8 }
    ]
  }
}
```

- [ ] **Step 2: Write the failing test (fast parts use FakeKernel; export path is slow)**

Create `tests/build/test_document_builder.py`:

```python
from pathlib import Path

import pytest

from ncad.build.document_builder import DocumentBuilder
from tests.kernel.fake_kernel import FakeKernel

_FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "parts" / "block.hocon"


def _document() -> dict:
    return {
        "schema_version": 2,
        "units": "mm",
        "parts": {
            "block": {
                "profile": "solid",
                "features": [
                    {
                        "id": "sk",
                        "op": "sketch",
                        "plane": "XY",
                        "elements": [{"id": "r", "type": "rectangle", "w": 80.0, "h": 60.0}],
                    },
                    {"id": "pad", "op": "extrude", "profile": "sk", "distance": 8.0},
                ],
            }
        },
    }


def test_build_returns_result_per_part() -> None:
    builder = DocumentBuilder(FakeKernel())

    results = builder.build(_document())

    assert set(results) == {"block"}
    assert results["block"].issues == []
    assert FakeKernel().volume(results["block"].shape) == 80.0 * 60.0 * 8.0


def test_build_rejects_schema_invalid_document() -> None:
    builder = DocumentBuilder(FakeKernel())
    bad = _document()
    del bad["units"]

    with pytest.raises(ValueError, match="schema"):
        builder.build(bad)


def test_fixture_document_is_loadable_and_builds() -> None:
    builder = DocumentBuilder(FakeKernel())

    results = builder.build_file_document(str(_FIXTURE))

    assert results["block"].issues == []


@pytest.mark.slow
def test_build_file_exports_glb(tmp_path) -> None:
    from ncad.kernel.build123d_kernel import Build123dKernel

    builder = DocumentBuilder(Build123dKernel())

    artifacts = builder.build_file(str(_FIXTURE), str(tmp_path))

    glb = Path(artifacts["block"])
    assert glb.is_file() and glb.stat().st_size > 0
    assert glb.name == "block.glb"
```

- [ ] **Step 3: Run it to verify it fails**

Run: `cd /Users/228496/exp/ncad && .venv/bin/pytest tests/build/test_document_builder.py -m "not slow" -q`
Expected: FAIL — `ncad.build.document_builder` not found.

- [ ] **Step 4: Implement the DocumentBuilder**

Create `src/ncad/build/document_builder.py`:

```python
"""Load, validate, build, and export a feature-tree document.

Ties the reuse-core spec layer (loader + schema validator) to the pure Builder and the
kernel's export. Schema-invalid input is a contract error and raises; per-feature build
problems are returned as issues on each part's OpResult (design §10).
"""

import logging
import os

from ncad.build.builder import Builder
from ncad.kernel.kernel import Kernel
from ncad.ops.op_registry import default_registry
from ncad.ops.op_result import OpResult
from ncad.spec.schema_validator import SchemaValidator
from ncad.spec.spec_loader import SpecLoader

logger = logging.getLogger(__name__)


class DocumentBuilder:
    """Builds every part in a document into geometry, optionally exporting glTF."""

    def __init__(self, kernel: Kernel) -> None:
        """:param kernel: Geometry backend used by the Builder and for export."""
        self._kernel = kernel
        self._builder = Builder(kernel, default_registry())
        self._validator = SchemaValidator()
        self._loader = SpecLoader()

    def build(self, document: dict) -> dict[str, OpResult]:
        """Validate ``document`` and build each part.

        :param document: A loaded feature-tree document dict.
        :return: Map from part name to its :class:`OpResult`.
        :raises ValueError: If the document fails schema validation.
        """
        issues = self._validator.validate(document)
        if issues:
            rendered = "; ".join(f"{issue.location}: {issue.message}" for issue in issues)
            raise ValueError(f"document failed schema validation: {rendered}")
        results: dict[str, OpResult] = {}
        for name, part in document["parts"].items():
            logger.debug("building part %s", name)
            results[name] = self._builder.build_part(part)
        return results

    def build_file_document(self, path: str) -> dict[str, OpResult]:
        """Load the document at ``path`` and build it (no export)."""
        return self.build(self._loader.load(path))

    def build_file(self, path: str, out_dir: str) -> dict[str, str]:
        """Load, build, and export each part to ``<out_dir>/<part>.glb``.

        :return: Map from part name to the written ``.glb`` path.
        """
        os.makedirs(out_dir, exist_ok=True)
        results = self.build_file_document(path)
        artifacts: dict[str, str] = {}
        for name, result in results.items():
            if result.shape is None:
                logger.warning("part %s did not build; skipping export", name)
                continue
            glb_path = os.path.join(out_dir, f"{name}.glb")
            self._kernel.export(result.shape, glb_path)
            artifacts[name] = glb_path
        return artifacts
```

- [ ] **Step 5: Run the fast tests**

Run: `cd /Users/228496/exp/ncad && .venv/bin/pytest tests/build/test_document_builder.py -m "not slow" -q`
Expected: PASS (3 passed).

- [ ] **Step 6: Create the CLI**

Create `src/ncad/build/__main__.py`:

```python
"""Build a feature-tree document to glTF:

    python -m ncad.build tests/fixtures/parts/block.hocon --out out

Loads the document, validates it, builds every part, and writes ``<part>.glb`` into the
output directory. View the result with ``nv <out-dir>``.
"""

import argparse
import logging

from ncad.build.document_builder import DocumentBuilder
from ncad.kernel.build123d_kernel import Build123dKernel

logger = logging.getLogger(__name__)


def main() -> None:
    """Parse args and build a document with the build123d kernel."""
    parser = argparse.ArgumentParser(description="ncad — build a feature-tree document to glTF")
    parser.add_argument("document", help="path to a .hocon/.json feature-tree document")
    parser.add_argument("--out", default="out", help="output directory for .glb files")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logging.getLogger("build123d").setLevel(logging.WARNING)

    artifacts = DocumentBuilder(Build123dKernel()).build_file(args.document, args.out)

    print(f"\nncad build — {args.document}")
    for name, path in artifacts.items():
        print(f"  part {name:12} {path}")
    if artifacts:
        out_dir = next(iter(artifacts.values())).rsplit("/", 1)[0]
        print(f"\nview with:  nv {out_dir}\n")
    else:
        print("  no parts built\n")


if __name__ == "__main__":
    main()
```

- [ ] **Step 7: Run the slow export test**

Run: `cd /Users/228496/exp/ncad && .venv/bin/pytest tests/build/test_document_builder.py -m slow -q`
Expected: PASS (1 passed).

- [ ] **Step 8: Run the full fast suite + lint**

Run: `cd /Users/228496/exp/ncad && .venv/bin/pytest -m "not slow" -q && .venv/bin/ruff check src tests`
Expected: all fast tests PASS; `All checks passed!`

- [ ] **Step 9: Manual end-to-end demo (the bucket gate)**

```bash
cd /Users/228496/exp/ncad
.venv/bin/python -m ncad.build tests/fixtures/parts/block.hocon --out out
ls -l out/block.glb
```
Expected: `out/block.glb` exists, non-empty. Then:
```bash
.venv/bin/python -m ncad.viewer out --port 0
```
Expected: prints a `ncad viewer → http://127.0.0.1:<port>` URL. Open it; the model picker lists `block.glb`; selecting it renders an 80×60×8 block. Ctrl+C to stop. **Gate met when the block renders in the browser.**

- [ ] **Step 10: Commit**

```bash
cd /Users/228496/exp/ncad
git add src/ncad/build/document_builder.py src/ncad/build/__main__.py tests/build/test_document_builder.py tests/fixtures/parts/block.hocon pyproject.toml
git commit -m "Add build CLI and document builder; first shape renders end to end"
```

---

## Self-Review

**1. Spec coverage (Bucket 0.1 checklist items from `docs/plan.md`):**
- "Minimal feature-tree schema (parameters/datums/parts[features], stable id, schema_version, profile default solid)" → Task 2 (`part_schema.hocon`). `parameters`/`datums` are permitted-but-optional objects; `profile` required on parts.
- "Op registry: feature_ops[op] dispatch; uniform pure signature (shape_in, params, prov_in) → (shape_out, prov_out, issues)" → Tasks 4 (OpResult), 7 (OpRegistry). Signature realized as `build_<op>(shape_in, params, provenance_in, kernel) -> OpResult`.
- "Ops sketch (rectangle) + extrude; general kernel interface v0 over build123d" → Tasks 3, 5, 6.
- "glTF export; the nv viewer shows the extruded block" → Task 8 (export + demo).
- Demo "author a rectangle+extrude HOCON → ncad build → block appears in nv" → Task 8 Step 9.
- Gate "a hand-authored document renders in the viewer" → Task 8 Step 9.

**2. Placeholder scan:** No TBD/TODO; every code step shows complete code; every test step shows the assertion; no "similar to Task N" references. ✓

**3. Type consistency:** `OpResult(shape, provenance, issues)`, `BuildIssue(node_id, message)`, `build_<op>(shape_in, params, provenance_in, kernel) -> OpResult`, `Kernel.polygon_face(points, plane)` / `Kernel.extrude(face, distance)`, `OpRegistry.register/get` + `default_registry()`, `Builder(kernel, registry).build_part(part)`, `DocumentBuilder(kernel).build/build_file_document/build_file` — used identically across Tasks 3–8. ✓ (Note: `build_file_document` is the load-then-build helper used by both the fixture test and `build_file`; named consistently in Task 8.)

**4. Ambiguity:** The `profile` key is overloaded (part-kind vs feature-level sketch reference); Task 7 Step 7 calls this out explicitly and shows they never collide (different dict levels). The build123d `Plane.from_local_coords` API risk is flagged with a fallback in Task 3 Step 8.
