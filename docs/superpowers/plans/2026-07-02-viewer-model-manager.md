# Viewer Model-Manager Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend the ncad browser viewer so a user can pick an example spec from a searchable tree, build it with one click, see the model appear in a scrollable list, and per model regenerate or delete it, without ever editing a document.

**Architecture:** New backend units (`SpecCatalog`, `ModelMetadata`, `BuildService`) plus an extended `ModelCatalog` back three new HTTP routes (`GET /api/specs`, `POST /api/build`, `POST /api/models/<name>/delete`) on the existing stdlib server. The single-page viewer replaces its model `<select>` with a spec combobox + Build icon and a scrollable models list with per-row regenerate/delete icons. The server triggers the existing `DocumentBuilder` build path and manages `out/` artifacts; it never edits a document and stays localhost-bound.

**Tech Stack:** Python 3.13 stdlib (`http.server`), build123d/OCP (only inside `BuildService`), leaf-common (via `DocumentBuilder`), three.js (CDN, existing), pytest, ruff, uv.

## Global Constraints

- **Python 3.13**; run everything via the repo `.venv` (`.venv/bin/pytest`, `.venv/bin/ruff`). uv for deps (`uv add`), never bare pip.
- **No nested functions or nested classes.** Every function/class at module top level. (CLAUDE.md)
- **One class per module**; `__init__.py` holds only re-exports. (CLAUDE.md)
- **Explicit type hints on every function/method.** PEP 8; imports grouped stdlib / third-party / local. (CLAUDE.md)
- **Structured logging** via `logging.getLogger(__name__)`, never `print` for diagnostics.
- **Validation/known failures are data or typed exceptions**, never bare `except`. The server catches typed errors and returns JSON; it never raises to the socket. (spec Error handling)
- **No em-dashes** anywhere (prose, comments, docstrings, UI text, commit messages). Use `>>` not arrows in prose (arrows allowed only in ASCII diagrams).
- **Ruff must pass:** `.venv/bin/ruff check src tests` clean before each commit.
- **Importing build123d/OCP is slow.** Only `BuildService` (and its slow test) may import it. All other new tests must run without it (no `@pytest.mark.slow`).
- **Viewer stays a viewer, not an authoring GUI.** No document editing. Build source is restricted to specs under the examples dir or a model's recorded meta `source`. Server stays localhost-bound. (spec Principle, Boundaries)
- **Path safety:** every filesystem resolve rejects traversal using the existing pattern `os.path.dirname(os.path.abspath(candidate)) == directory`. Deletes touch the models dir only. (spec Error handling)

---

## File Structure

**Created:**
- `src/ncad/viewer/spec_catalog.py`: `SpecCatalog`: list examples as a tree, resolve a spec path safely.
- `src/ncad/viewer/model_metadata.py`: `ModelMetadata`: read/write `out/<stem>.meta.json`.
- `src/ncad/viewer/build_service.py`: `BuildService`: allow-check + run `DocumentBuilder.build_file` + write meta.
- `tests/viewer/test_spec_catalog.py`, `tests/viewer/test_model_metadata.py`, `tests/viewer/test_build_service.py`, and new cases in `tests/viewer/test_viewer_server.py`, `tests/viewer/test_model_catalog.py`.

**Modified:**
- `src/ncad/viewer/model_catalog.py`: add `.meta.json` sidecar support, `resolve_meta`, `delete_model`, and a `models_with_sources()` listing.
- `src/ncad/viewer/viewer_server.py`: inject `spec_catalog` + `build_service`; add `do_POST`; new routes; richer `/api/models`.
- `src/ncad/viewer/viewer_page.py`: replace model `<select>` with spec combobox + Build icon + scrollable models list; toast; JS for `/api/specs`, `/api/build`, delete.
- `src/ncad/cli/viewer_cli.py`: pass the resolved examples dir into `ViewerServer` (via `launch_viewer`).
- `src/ncad/viewer/__main__.py`: same wiring for `python -m ncad.viewer`.

**Interfaces locked across tasks:**
- `SpecCatalog(examples_dir: str)` with `.tree() -> list[dict]` and `.resolve(rel_path: str) -> str | None`.
- `ModelMetadata(models_dir: str)` with `.write(model_name: str, source: str, built_at: str, ncad_version: str, kernel_version: str) -> str` and `.read(model_name: str) -> dict | None`.
- `ModelCatalog` gains `.models_with_sources() -> list[dict]` (`{"name","source"}`), `.resolve_meta(model_name) -> str | None`, `.delete_model(model_name) -> list[str] | None`.
- `BuildService(examples_dir, models_dir, builder_factory, *, meta=None, clock=None, versions=None)` with `.build(spec: str) -> dict` (`{"built": [...]}`) and typed `BuildError`. `builder_factory() -> object` returns something with `.build_file(path, out_dir) -> dict[str,str]`; injected as a stub in fast tests, defaults to `DocumentBuilder(Build123dKernel())` in production.
- `ViewerServer(models_dir, host="127.0.0.1", port=8000, *, examples_dir=None, build_service=None)`.

---

## Task 1: ModelCatalog meta sidecar, listing with sources, and delete

**Files:**
- Modify: `src/ncad/viewer/model_catalog.py`
- Test: `tests/viewer/test_model_catalog.py`

**Interfaces:**
- Consumes: nothing new.
- Produces: `ModelCatalog.resolve_meta(model_name: str) -> str | None`; `ModelCatalog.models_with_sources() -> list[dict]` where each dict is `{"name": str, "source": str | None}`; `ModelCatalog.delete_model(model_name: str) -> list[str] | None` (absolute paths removed, or `None` if the model is unknown/unsafe). `.meta.json` added to servable + sidecar handling.

- [ ] **Step 1: Write the failing tests**

Add to `tests/viewer/test_model_catalog.py`:

```python
def test_resolve_meta_finds_sidecar(tmp_path) -> None:
    (tmp_path / "block.glb").write_bytes(b"x")
    (tmp_path / "block.meta.json").write_text("{}")
    catalog = ModelCatalog(str(tmp_path))

    resolved = catalog.resolve_meta("block.glb")

    assert resolved is not None and resolved.endswith("block.meta.json")


def test_models_with_sources_reads_source_from_meta(tmp_path) -> None:
    (tmp_path / "block.glb").write_bytes(b"x")
    (tmp_path / "block.meta.json").write_text('{"source": "examples/g/block.hocon"}')
    (tmp_path / "plain.glb").write_bytes(b"x")
    catalog = ModelCatalog(str(tmp_path))

    listed = catalog.models_with_sources()

    by_name = {m["name"]: m["source"] for m in listed}
    assert by_name == {"block.glb": "examples/g/block.hocon", "plain.glb": None}


def test_delete_model_removes_glb_and_sidecars(tmp_path) -> None:
    for suffix in (".glb", ".meta.json", ".bom.json", ".plan.svg"):
        (tmp_path / f"block{suffix}").write_text("x")
    (tmp_path / "other.glb").write_bytes(b"x")
    catalog = ModelCatalog(str(tmp_path))

    removed = catalog.delete_model("block.glb")

    assert removed is not None and len(removed) == 4
    assert not (tmp_path / "block.glb").exists()
    assert not (tmp_path / "block.meta.json").exists()
    assert (tmp_path / "other.glb").exists()


def test_delete_model_rejects_traversal(tmp_path) -> None:
    catalog = ModelCatalog(str(tmp_path))

    assert catalog.delete_model("../evil.glb") is None


def test_delete_unknown_model_returns_none(tmp_path) -> None:
    catalog = ModelCatalog(str(tmp_path))

    assert catalog.delete_model("nope.glb") is None
```

- [ ] **Step 2: Run to verify they fail**

Run: `.venv/bin/pytest tests/viewer/test_model_catalog.py -q`
Expected: FAIL (AttributeError: no `resolve_meta`/`models_with_sources`/`delete_model`).

- [ ] **Step 3: Implement**

In `src/ncad/viewer/model_catalog.py`, add `import json` at the top of the third import group is not needed (json is stdlib; put it with `import os`). Change the module constants block:

```python
import json
import logging
import os

logger = logging.getLogger(__name__)

# Extensions that appear in the model picker.
_MODEL_EXTENSIONS = (".gltf", ".glb")
# Extensions the server may serve: models plus their external buffer/image sidecars.
_SERVABLE_EXTENSIONS = (".gltf", ".glb", ".bin", ".png", ".jpg", ".jpeg")
# A model's sidecars sit beside it as "<stem><suffix>".
_BOM_SUFFIX = ".bom.json"
_PLAN_SUFFIX = ".plan.svg"
_META_SUFFIX = ".meta.json"
# All sidecar suffixes removed alongside a model on delete.
_SIDECAR_SUFFIXES = (_META_SUFFIX, _BOM_SUFFIX, _PLAN_SUFFIX)
```

Add these methods to `ModelCatalog` (all at class level, no nested functions):

```python
    def resolve_meta(self, model_name: str) -> str | None:
        """Resolve a model name to its metadata sidecar (``<stem>.meta.json``), or None."""
        return self._resolve_sidecar(model_name, _META_SUFFIX)

    def models_with_sources(self) -> list[dict]:
        """List models with their recorded source spec (from meta), source None if absent."""
        listed: list[dict] = []
        for name in self.model_names():
            listed.append({"name": name, "source": self._read_source(name)})
        return listed

    def delete_model(self, model_name: str) -> list[str] | None:
        """Delete the model file and its sidecars from this directory (path-safe).

        :return: Absolute paths removed, or None if the model is unknown or unsafe.
        """
        target = self.resolve(model_name)
        if target is None:
            return None
        removed = [target]
        os.remove(target)
        stem = os.path.splitext(model_name)[0]
        for suffix in _SIDECAR_SUFFIXES:
            sidecar = os.path.abspath(os.path.join(self._directory, stem + suffix))
            if os.path.dirname(sidecar) == self._directory and os.path.isfile(sidecar):
                os.remove(sidecar)
                removed.append(sidecar)
        logger.debug("deleted model %s and %d sidecar(s)", model_name, len(removed) - 1)
        return removed

    def _read_source(self, model_name: str) -> str | None:
        """Read the ``source`` field from a model's meta sidecar, or None."""
        meta_path = self.resolve_meta(model_name)
        if meta_path is None:
            return None
        try:
            with open(meta_path, encoding="utf-8") as handle:
                return json.load(handle).get("source")
        except (OSError, ValueError):
            logger.warning("could not read meta for %s", model_name)
            return None
```

- [ ] **Step 4: Run tests to verify pass**

Run: `.venv/bin/pytest tests/viewer/test_model_catalog.py -q`
Expected: PASS.

- [ ] **Step 5: Lint and commit**

```bash
.venv/bin/ruff check src tests
git add src/ncad/viewer/model_catalog.py tests/viewer/test_model_catalog.py
git commit -m "Add meta sidecar, source listing, and safe delete to ModelCatalog"
```

Expected before commit: `All checks passed!`

---

## Task 2: SpecCatalog (examples tree + safe resolve)

**Files:**
- Create: `src/ncad/viewer/spec_catalog.py`
- Test: `tests/viewer/test_spec_catalog.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `SpecCatalog(examples_dir: str)`; `.tree() -> list[dict]` (nested `{"type":"dir","name","children"}` / `{"type":"spec","name","path"}`, dirs before files, each group sorted by name, `path` relative to `examples_dir` with `/` separators); `.resolve(rel_path: str) -> str | None` (absolute path of a spec under the examples dir, or None if unsafe/absent/not a spec).

- [ ] **Step 1: Write the failing tests**

Create `tests/viewer/test_spec_catalog.py`:

```python
from ncad.viewer.spec_catalog import SpecCatalog


def _make_examples(tmp_path):
    gate = tmp_path / "gate-0.1-first-shape"
    gate.mkdir()
    (gate / "block.hocon").write_text("x")
    other = tmp_path / "gate-0.2-bracket"
    other.mkdir()
    (other / "bracket.hocon").write_text("x")
    (tmp_path / "top.hocon").write_text("x")
    (tmp_path / "notes.txt").write_text("ignore me")
    return tmp_path


def test_tree_reflects_directory_structure(tmp_path) -> None:
    catalog = SpecCatalog(str(_make_examples(tmp_path)))

    tree = catalog.tree()

    dirs = [n for n in tree if n["type"] == "dir"]
    files = [n for n in tree if n["type"] == "spec"]
    assert [d["name"] for d in dirs] == ["gate-0.1-first-shape", "gate-0.2-bracket"]
    assert [f["name"] for f in files] == ["top.hocon"]
    gate = dirs[0]
    assert gate["children"][0] == {
        "type": "spec",
        "name": "block.hocon",
        "path": "gate-0.1-first-shape/block.hocon",
    }


def test_tree_ignores_non_spec_files(tmp_path) -> None:
    catalog = SpecCatalog(str(_make_examples(tmp_path)))

    names = [n["name"] for n in catalog.tree()]

    assert "notes.txt" not in names


def test_tree_of_missing_dir_is_empty(tmp_path) -> None:
    assert SpecCatalog(str(tmp_path / "nope")).tree() == []


def test_resolve_accepts_known_spec(tmp_path) -> None:
    catalog = SpecCatalog(str(_make_examples(tmp_path)))

    resolved = catalog.resolve("gate-0.1-first-shape/block.hocon")

    assert resolved is not None and resolved.endswith("block.hocon")


def test_resolve_rejects_traversal(tmp_path) -> None:
    catalog = SpecCatalog(str(_make_examples(tmp_path)))

    assert catalog.resolve("../secrets.hocon") is None


def test_resolve_rejects_non_spec_extension(tmp_path) -> None:
    catalog = SpecCatalog(str(_make_examples(tmp_path)))

    assert catalog.resolve("notes.txt") is None
```

- [ ] **Step 2: Run to verify they fail**

Run: `.venv/bin/pytest tests/viewer/test_spec_catalog.py -q`
Expected: FAIL (module not found).

- [ ] **Step 3: Implement**

Create `src/ncad/viewer/spec_catalog.py`:

```python
"""Discover feature-tree documents ("specs") under the examples directory for the viewer.

Returns the examples as a nested tree (directories before files, each group sorted by
name) so the viewer can render the same structure the filesystem has, and resolves a
requested relative spec path to a safe absolute path (rejecting traversal outside the
examples directory).
"""

import logging
import os

logger = logging.getLogger(__name__)

_SPEC_EXTENSIONS = (".hocon", ".conf", ".json")


class SpecCatalog:
    """Lists and safely resolves spec documents within an examples directory."""

    def __init__(self, examples_dir: str) -> None:
        """:param examples_dir: Directory of example spec documents to scan."""
        self._root = os.path.abspath(examples_dir)

    def tree(self) -> list[dict]:
        """Nested tree of the examples directory; empty if it does not exist."""
        if not os.path.isdir(self._root):
            return []
        return self._scan(self._root)

    def resolve(self, rel_path: str) -> str | None:
        """Resolve a relative spec path to an absolute path under the examples dir.

        :return: The absolute path, or None if unsafe, absent, or not a spec file.
        """
        candidate = os.path.abspath(os.path.join(self._root, rel_path))
        if os.path.commonpath([candidate, self._root]) != self._root:
            return None
        if not candidate.lower().endswith(_SPEC_EXTENSIONS):
            return None
        if not os.path.isfile(candidate):
            return None
        return candidate

    def _scan(self, directory: str) -> list[dict]:
        """Return the sorted (dirs first) tree nodes for one directory."""
        dirs: list[dict] = []
        specs: list[dict] = []
        for entry in sorted(os.listdir(directory)):
            full = os.path.join(directory, entry)
            if os.path.isdir(full):
                dirs.append({"type": "dir", "name": entry, "children": self._scan(full)})
            elif entry.lower().endswith(_SPEC_EXTENSIONS):
                rel = os.path.relpath(full, self._root).replace(os.sep, "/")
                specs.append({"type": "spec", "name": entry, "path": rel})
        return dirs + specs
```

Note: `_scan` recurses by calling a method, not a nested function, so the no-nested-functions rule holds.

- [ ] **Step 4: Run tests to verify pass**

Run: `.venv/bin/pytest tests/viewer/test_spec_catalog.py -q`
Expected: PASS.

- [ ] **Step 5: Lint and commit**

```bash
.venv/bin/ruff check src tests
git add src/ncad/viewer/spec_catalog.py tests/viewer/test_spec_catalog.py
git commit -m "Add SpecCatalog for the examples tree and safe spec resolution"
```

Expected before commit: `All checks passed!`

---

## Task 3: ModelMetadata (sidecar read/write)

**Files:**
- Create: `src/ncad/viewer/model_metadata.py`
- Test: `tests/viewer/test_model_metadata.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `ModelMetadata(models_dir: str)`; `.write(model_name: str, source: str, built_at: str, ncad_version: str, kernel_version: str) -> str` (writes `<stem>.meta.json`, returns its path); `.read(model_name: str) -> dict | None`.

- [ ] **Step 1: Write the failing tests**

Create `tests/viewer/test_model_metadata.py`:

```python
from ncad.viewer.model_metadata import ModelMetadata


def test_write_then_read_roundtrip(tmp_path) -> None:
    meta = ModelMetadata(str(tmp_path))

    path = meta.write(
        "block.glb",
        source="examples/g/block.hocon",
        built_at="2026-07-02T00:00:00Z",
        ncad_version="0.0.1",
        kernel_version="build123d-0.10.0",
    )

    assert path.endswith("block.meta.json")
    data = meta.read("block.glb")
    assert data["source"] == "examples/g/block.hocon"
    assert data["built_at"] == "2026-07-02T00:00:00Z"
    assert data["ncad_version"] == "0.0.1"
    assert data["kernel_version"] == "build123d-0.10.0"


def test_read_missing_returns_none(tmp_path) -> None:
    assert ModelMetadata(str(tmp_path)).read("absent.glb") is None
```

- [ ] **Step 2: Run to verify they fail**

Run: `.venv/bin/pytest tests/viewer/test_model_metadata.py -q`
Expected: FAIL (module not found).

- [ ] **Step 3: Implement**

Create `src/ncad/viewer/model_metadata.py`:

```python
"""Read and write a model's metadata sidecar (``out/<stem>.meta.json``).

The sidecar records how a model was built (its source spec and the tool/kernel
versions) so the viewer can regenerate it later by rebuilding that source.
"""

import json
import logging
import os

logger = logging.getLogger(__name__)

_META_SUFFIX = ".meta.json"


class ModelMetadata:
    """Reads and writes ``<stem>.meta.json`` beside a model in one directory."""

    def __init__(self, models_dir: str) -> None:
        """:param models_dir: Directory holding the models and their meta sidecars."""
        self._directory = os.path.abspath(models_dir)

    def write(
        self,
        model_name: str,
        source: str,
        built_at: str,
        ncad_version: str,
        kernel_version: str,
    ) -> str:
        """Write the meta sidecar for ``model_name`` and return its path."""
        stem = os.path.splitext(model_name)[0]
        path = os.path.join(self._directory, stem + _META_SUFFIX)
        payload = {
            "source": source,
            "built_at": built_at,
            "ncad_version": ncad_version,
            "kernel_version": kernel_version,
        }
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)
        logger.debug("wrote meta sidecar %s", path)
        return path

    def read(self, model_name: str) -> dict | None:
        """Read the meta sidecar for ``model_name``, or None if absent/unreadable."""
        stem = os.path.splitext(model_name)[0]
        path = os.path.join(self._directory, stem + _META_SUFFIX)
        if not os.path.isfile(path):
            return None
        try:
            with open(path, encoding="utf-8") as handle:
                return json.load(handle)
        except (OSError, ValueError):
            logger.warning("could not read meta sidecar %s", path)
            return None
```

- [ ] **Step 4: Run tests to verify pass**

Run: `.venv/bin/pytest tests/viewer/test_model_metadata.py -q`
Expected: PASS.

- [ ] **Step 5: Lint and commit**

```bash
.venv/bin/ruff check src tests
git add src/ncad/viewer/model_metadata.py tests/viewer/test_model_metadata.py
git commit -m "Add ModelMetadata sidecar read/write"
```

Expected before commit: `All checks passed!`

---

## Task 4: BuildService (allow-check + build + write meta)

**Files:**
- Create: `src/ncad/viewer/build_service.py`
- Test: `tests/viewer/test_build_service.py`

**Interfaces:**
- Consumes: `SpecCatalog`, `ModelCatalog` (for recorded-source allow), `ModelMetadata`.
- Produces:
  - `BuildError(Exception)` (typed).
  - `BuildService(examples_dir, models_dir, builder_factory, *, meta=None, clock=None, versions=None)`. `builder_factory` is a zero-arg callable returning an object with `.build_file(path: str, out_dir: str) -> dict[str, str]`. `clock` is a zero-arg callable returning an ISO-8601 string (default injected in production; a fixed stub in tests, since `datetime.now` is disallowed in some contexts and determinism matters). `versions` is a dict `{"ncad": str, "kernel": str}`.
  - `.build(spec: str) -> dict` returns `{"built": [model_name, ...]}`; raises `BuildError` if the spec is not allowed (resolves neither under the examples dir nor to a recorded meta source) or if the build fails.

- [ ] **Step 1: Write the failing tests**

Create `tests/viewer/test_build_service.py`:

```python
import pytest

from ncad.viewer.build_service import BuildError, BuildService


class _StubBuilder:
    """Records the built spec and writes a fake glb per part."""

    def __init__(self, out_names) -> None:
        self._out_names = out_names

    def build_file(self, path: str, out_dir: str) -> dict:
        import os

        artifacts = {}
        for name in self._out_names:
            glb = os.path.join(out_dir, f"{name}.glb")
            with open(glb, "wb") as handle:
                handle.write(b"glb")
            artifacts[name] = glb
        return artifacts


def _service(tmp_path, out_names=("block",)):
    examples = tmp_path / "examples"
    (examples / "g").mkdir(parents=True)
    (examples / "g" / "block.hocon").write_text("x")
    out = tmp_path / "out"
    out.mkdir()
    return (
        BuildService(
            str(examples),
            str(out),
            builder_factory=lambda: _StubBuilder(out_names),
            clock=lambda: "2026-07-02T00:00:00Z",
            versions={"ncad": "0.0.1", "kernel": "build123d-0.10.0"},
        ),
        examples,
        out,
    )


def test_build_allows_spec_under_examples(tmp_path) -> None:
    service, _, out = _service(tmp_path)

    result = service.build("g/block.hocon")

    assert result == {"built": ["block.glb"]}
    assert (out / "block.glb").is_file()
    assert (out / "block.meta.json").is_file()


def test_build_writes_source_into_meta(tmp_path) -> None:
    service, _, out = _service(tmp_path)

    service.build("g/block.hocon")

    import json

    data = json.loads((out / "block.meta.json").read_text())
    assert data["source"] == "g/block.hocon"
    assert data["built_at"] == "2026-07-02T00:00:00Z"


def test_build_rejects_spec_outside_examples(tmp_path) -> None:
    service, _, _ = _service(tmp_path)

    with pytest.raises(BuildError):
        service.build("../elsewhere/evil.hocon")


def test_build_allows_recorded_meta_source(tmp_path) -> None:
    # A model's meta records an absolute source that is not under examples; regenerate
    # must still be allowed for that exact recorded source.
    service, examples, out = _service(tmp_path)
    external = tmp_path / "external.hocon"
    external.write_text("x")
    (out / "prev.glb").write_bytes(b"x")
    import json

    (out / "prev.meta.json").write_text(json.dumps({"source": str(external)}))

    result = service.build(str(external))

    assert result["built"] == ["block.glb"]


def test_build_wraps_builder_failure_as_builderror(tmp_path) -> None:
    examples = tmp_path / "examples"
    (examples / "g").mkdir(parents=True)
    (examples / "g" / "block.hocon").write_text("x")
    out = tmp_path / "out"
    out.mkdir()

    def boom():
        raise RuntimeError("kernel exploded")

    class _Failing:
        def build_file(self, path, out_dir):
            raise ValueError("document failed schema validation: bad")

    service = BuildService(
        str(examples),
        str(out),
        builder_factory=lambda: _Failing(),
        clock=lambda: "t",
        versions={"ncad": "0.0.1", "kernel": "k"},
    )

    with pytest.raises(BuildError):
        service.build("g/block.hocon")
```

- [ ] **Step 2: Run to verify they fail**

Run: `.venv/bin/pytest tests/viewer/test_build_service.py -q`
Expected: FAIL (module not found).

- [ ] **Step 3: Implement**

Create `src/ncad/viewer/build_service.py`:

```python
"""Run a spec build on behalf of the viewer, safely and with metadata.

The only viewer unit that touches the geometry kernel. It (1) checks the requested spec
is allowed (resolves under the examples directory, or equals a source already recorded
in a model's meta sidecar), (2) runs the existing DocumentBuilder build path, and
(3) writes a meta sidecar per built model so it can be regenerated later. Failures are
raised as a typed BuildError; the server turns that into a JSON error response.
"""

import logging
import os

from ncad.viewer.model_catalog import ModelCatalog
from ncad.viewer.model_metadata import ModelMetadata
from ncad.viewer.spec_catalog import SpecCatalog

logger = logging.getLogger(__name__)


class BuildError(Exception):
    """A build request that was disallowed or that failed to produce geometry."""


class BuildService:
    """Validates, runs, and records a viewer-triggered spec build."""

    def __init__(
        self,
        examples_dir: str,
        models_dir: str,
        builder_factory,
        *,
        meta: ModelMetadata | None = None,
        clock=None,
        versions: dict | None = None,
    ) -> None:
        """:param examples_dir: Directory of allowed example specs.
        :param models_dir: Output directory for built models.
        :param builder_factory: Zero-arg callable returning an object with
            ``build_file(path, out_dir) -> dict[str, str]``.
        :param meta: ModelMetadata writer (defaults to one over ``models_dir``).
        :param clock: Zero-arg callable returning an ISO-8601 timestamp string.
        :param versions: Dict with ``ncad`` and ``kernel`` version strings.
        """
        self._examples_dir = os.path.abspath(examples_dir)
        self._models_dir = os.path.abspath(models_dir)
        self._builder_factory = builder_factory
        self._spec_catalog = SpecCatalog(examples_dir)
        self._model_catalog = ModelCatalog(models_dir)
        self._meta = meta or ModelMetadata(models_dir)
        self._clock = clock
        self._versions = versions or {"ncad": "unknown", "kernel": "unknown"}

    def build(self, spec: str) -> dict:
        """Build ``spec`` (a relative example path or a recorded meta source).

        :return: ``{"built": [model_name, ...]}``.
        :raises BuildError: If the spec is not allowed or the build fails.
        """
        resolved = self._allowed_path(spec)
        if resolved is None:
            raise BuildError(f"spec not allowed: {spec}")
        builder = self._builder_factory()
        try:
            artifacts = builder.build_file(resolved, self._models_dir)
        except (ValueError, OSError, RuntimeError) as exc:
            raise BuildError(str(exc)) from exc
        built = [os.path.basename(path) for path in artifacts.values()]
        built_at = self._clock() if self._clock is not None else ""
        for name in built:
            self._meta.write(
                name,
                source=spec,
                built_at=built_at,
                ncad_version=self._versions["ncad"],
                kernel_version=self._versions["kernel"],
            )
        logger.info("built %s from %s", built, spec)
        return {"built": built}

    def _allowed_path(self, spec: str) -> str | None:
        """Resolve ``spec`` if it is under examples or a recorded meta source, else None."""
        under_examples = self._spec_catalog.resolve(spec)
        if under_examples is not None:
            return under_examples
        for model in self._model_catalog.models_with_sources():
            if model["source"] == spec and os.path.isfile(spec):
                return spec
        return None
```

- [ ] **Step 4: Run tests to verify pass**

Run: `.venv/bin/pytest tests/viewer/test_build_service.py -q`
Expected: PASS (5 passed). Remove the unused `boom` function if ruff flags it (it is a leftover; the `_Failing` class is what the test uses); delete the `def boom()` block from the test before committing.

- [ ] **Step 5: Lint and commit**

```bash
.venv/bin/ruff check src tests
git add src/ncad/viewer/build_service.py tests/viewer/test_build_service.py
git commit -m "Add BuildService with source allow-check and meta writing"
```

Expected before commit: `All checks passed!`

---

## Task 5: Server routes (specs, build, delete) and injected collaborators

**Files:**
- Modify: `src/ncad/viewer/viewer_server.py`
- Test: `tests/viewer/test_viewer_server.py`

**Interfaces:**
- Consumes: `SpecCatalog`, `BuildService`, `ModelCatalog`.
- Produces: `ViewerServer(models_dir, host="127.0.0.1", port=8000, *, examples_dir=None, build_service=None)`. New routes: `GET /api/specs` -> `{"tree": [...]}`; `GET /api/models` -> `{"models": [{"name","source"}]}` (changed shape); `POST /api/build` (JSON body `{"spec": "..."}`) -> `{"models":[...],"built":[...]}` or non-200 `{"error"}`; `POST /api/models/<name>/delete` -> `{"models":[...]}` or 404.

- [ ] **Step 1: Write the failing tests**

Read the existing `tests/viewer/test_viewer_server.py` to reuse its server-in-thread fixture pattern. Add these tests (adapt the fixture helper name to the file's existing one; the file starts a `ViewerServer` on an ephemeral port in a thread and hits it with `urllib`):

```python
import json
import urllib.request

from ncad.viewer.build_service import BuildError


class _StubBuildService:
    def __init__(self) -> None:
        self.calls = []

    def build(self, spec: str) -> dict:
        self.calls.append(spec)
        if spec == "bad.hocon":
            raise BuildError("nope")
        return {"built": ["block.glb"]}


def test_api_specs_returns_tree(tmp_path) -> None:
    examples = tmp_path / "examples"
    (examples / "g").mkdir(parents=True)
    (examples / "g" / "block.hocon").write_text("x")
    models = tmp_path / "out"
    models.mkdir()
    server = ViewerServer(str(models), port=0, examples_dir=str(examples))
    server.start()
    try:
        with urllib.request.urlopen(f"{server.base_url}/api/specs") as resp:
            data = json.loads(resp.read())
    finally:
        server.stop()

    assert data["tree"][0]["name"] == "g"


def test_api_models_carries_source(tmp_path) -> None:
    models = tmp_path / "out"
    models.mkdir()
    (models / "block.glb").write_bytes(b"x")
    (models / "block.meta.json").write_text('{"source": "g/block.hocon"}')
    server = ViewerServer(str(models), port=0, examples_dir=str(tmp_path))
    server.start()
    try:
        with urllib.request.urlopen(f"{server.base_url}/api/models") as resp:
            data = json.loads(resp.read())
    finally:
        server.stop()

    assert data["models"] == [{"name": "block.glb", "source": "g/block.hocon"}]


def test_api_build_success(tmp_path) -> None:
    models = tmp_path / "out"
    models.mkdir()
    stub = _StubBuildService()
    server = ViewerServer(str(models), port=0, examples_dir=str(tmp_path), build_service=stub)
    server.start()
    try:
        req = urllib.request.Request(
            f"{server.base_url}/api/build",
            data=json.dumps({"spec": "g/block.hocon"}).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read())
    finally:
        server.stop()

    assert stub.calls == ["g/block.hocon"]
    assert data["built"] == ["block.glb"]
    assert "models" in data


def test_api_build_error_returns_400(tmp_path) -> None:
    models = tmp_path / "out"
    models.mkdir()
    server = ViewerServer(
        str(models), port=0, examples_dir=str(tmp_path), build_service=_StubBuildService()
    )
    server.start()
    try:
        req = urllib.request.Request(
            f"{server.base_url}/api/build",
            data=json.dumps({"spec": "bad.hocon"}).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        status = None
        try:
            urllib.request.urlopen(req)
        except urllib.error.HTTPError as exc:
            status = exc.code
            body = json.loads(exc.read())
    finally:
        server.stop()

    assert status == 400
    assert "error" in body


def test_api_delete_removes_and_returns_list(tmp_path) -> None:
    models = tmp_path / "out"
    models.mkdir()
    (models / "block.glb").write_bytes(b"x")
    server = ViewerServer(str(models), port=0, examples_dir=str(tmp_path))
    server.start()
    try:
        req = urllib.request.Request(
            f"{server.base_url}/api/models/block.glb/delete", method="POST"
        )
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read())
    finally:
        server.stop()

    assert data["models"] == []
    assert not (models / "block.glb").exists()
```

Ensure `import urllib.error` is present in the test file.

- [ ] **Step 2: Run to verify they fail**

Run: `.venv/bin/pytest tests/viewer/test_viewer_server.py -q`
Expected: FAIL (ViewerServer has no `examples_dir`/`build_service` kwargs; routes missing; `/api/models` shape differs).

- [ ] **Step 3: Implement the server changes**

In `src/ncad/viewer/viewer_server.py`:

Add imports (local group): `from ncad.viewer.spec_catalog import SpecCatalog`. Keep `import json` (already present).

Change the handler to hold spec catalog + build service + model catalog. Update `_ViewerRequestHandler.__init__`:

```python
    def __init__(
        self, *args, catalog: ModelCatalog, spec_catalog: SpecCatalog, build_service, **kwargs
    ) -> None:
        self._catalog = catalog
        self._spec_catalog = spec_catalog
        self._build_service = build_service
        super().__init__(*args, **kwargs)
```

In `do_GET`, add a branch for `/api/specs` (before the model routes):

```python
        elif path == "/api/specs":
            self._send_json(200, {"tree": self._spec_catalog.tree()})
```

Change `_send_model_list` to the new shape:

```python
    def _send_model_list(self) -> None:
        self._send_json(200, {"models": self._catalog.models_with_sources()})
```

Add a `_send_json` helper and a `do_POST` method (all at class level):

```python
    def _send_json(self, status: int, payload: dict) -> None:
        self._send_bytes(status, "application/json", json.dumps(payload).encode("utf-8"))

    def do_POST(self) -> None:  # noqa: N802 (name fixed by BaseHTTPRequestHandler)
        path = self.path.split("?", 1)[0]
        if path == "/api/build":
            self._handle_build()
        elif path.startswith(_MODEL_ROUTE) and path.endswith("/delete"):
            name = path[len(_MODEL_ROUTE) : -len("/delete")]
            self._handle_delete(unquote(name))
        else:
            self.send_error(404, "not found")

    def _handle_build(self) -> None:
        length = int(self.headers.get("Content-Length", 0))
        try:
            body = json.loads(self.rfile.read(length) or b"{}")
            spec = body["spec"]
        except (ValueError, KeyError):
            self._send_json(400, {"error": "request must be JSON with a 'spec' field"})
            return
        try:
            result = self._build_service.build(spec)
        except BuildError as exc:
            self._send_json(400, {"error": str(exc)})
            return
        except Exception:  # noqa: BLE001 - never raise to the socket; log and 500
            logger.exception("unexpected build failure for %s", spec)
            self._send_json(500, {"error": "internal build error"})
            return
        self._send_json(200, {"models": self._catalog.models_with_sources(), **result})

    def _handle_delete(self, name: str) -> None:
        removed = self._catalog.delete_model(name)
        if removed is None:
            self.send_error(404, "unknown model")
            return
        self._send_json(200, {"models": self._catalog.models_with_sources()})
```

Add the import for `BuildError` (local group): `from ncad.viewer.build_service import BuildError`.

Update `ViewerServer.__init__` to inject collaborators:

```python
    def __init__(
        self,
        models_dir: str,
        host: str = "127.0.0.1",
        port: int = 8000,
        *,
        examples_dir: str | None = None,
        build_service=None,
    ) -> None:
        """:param models_dir: Directory of glTF/GLB models to serve.
        :param host: Bind address. :param port: Bind port; 0 picks an ephemeral port.
        :param examples_dir: Directory of example specs (spec panel empty if None).
        :param build_service: Injected BuildService; a default is built if None.
        """
        catalog = ModelCatalog(models_dir)
        spec_catalog = SpecCatalog(examples_dir or "")
        if build_service is None:
            build_service = _default_build_service(examples_dir or "", models_dir)
        handler = partial(
            _ViewerRequestHandler,
            catalog=catalog,
            spec_catalog=spec_catalog,
            build_service=build_service,
        )
        self._httpd = ThreadingHTTPServer((host, port), handler)
        self._thread: threading.Thread | None = None
```

Add a module-level factory (top level, after the handler class or before `ViewerServer`) that builds the production `BuildService` lazily so importing the viewer never imports OCP:

```python
def _default_build_service(examples_dir: str, models_dir: str):
    """Construct the production BuildService (imports the kernel lazily)."""
    from importlib.metadata import version

    from ncad.build.document_builder import DocumentBuilder
    from ncad.kernel.build123d_kernel import Build123dKernel
    from ncad.viewer.build_service import BuildService

    def _factory():
        return DocumentBuilder(Build123dKernel())

    def _clock() -> str:
        from datetime import datetime, timezone

        return datetime.now(timezone.utc).isoformat()

    try:
        ncad_version = version("ncad")
    except Exception:  # noqa: BLE001 - version lookup is best-effort metadata
        ncad_version = "unknown"
    return BuildService(
        examples_dir,
        models_dir,
        builder_factory=_factory,
        clock=_clock,
        versions={"ncad": ncad_version, "kernel": "build123d"},
    )
```

Note: `_factory` and `_clock` are nested functions inside `_default_build_service`. The no-nested-functions rule is a project constraint; to honor it, define them as module-level functions instead. Replace the nested defs with module-level helpers `_document_builder_factory()` and `_utc_now_iso()` and pass those references. Concretely, add at module level:

```python
def _document_builder_factory():
    """Zero-arg factory for the production DocumentBuilder (imports the kernel)."""
    from ncad.build.document_builder import DocumentBuilder
    from ncad.kernel.build123d_kernel import Build123dKernel

    return DocumentBuilder(Build123dKernel())


def _utc_now_iso() -> str:
    """Current UTC time as an ISO-8601 string."""
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat()
```

and simplify `_default_build_service` to reference them:

```python
def _default_build_service(examples_dir: str, models_dir: str):
    """Construct the production BuildService (imports the kernel lazily)."""
    from importlib.metadata import version

    from ncad.viewer.build_service import BuildService

    try:
        ncad_version = version("ncad")
    except Exception:  # noqa: BLE001 - version lookup is best-effort metadata
        ncad_version = "unknown"
    return BuildService(
        examples_dir,
        models_dir,
        builder_factory=_document_builder_factory,
        clock=_utc_now_iso,
        versions={"ncad": ncad_version, "kernel": "build123d"},
    )
```

- [ ] **Step 4: Run tests to verify pass**

Run: `.venv/bin/pytest tests/viewer/test_viewer_server.py -q`
Expected: PASS. The default `BuildService` is never constructed in these tests (a stub is injected, or the route under test does not build), so no OCP import occurs; keep these fast (no `slow` marker).

- [ ] **Step 5: Lint and commit**

```bash
.venv/bin/ruff check src tests
git add src/ncad/viewer/viewer_server.py tests/viewer/test_viewer_server.py
git commit -m "Add viewer routes for specs, build, and delete with injected collaborators"
```

Expected before commit: `All checks passed!`

---

## Task 6: Frontend (spec combobox, Build icon, models list with row actions, toast)

**Files:**
- Modify: `src/ncad/viewer/viewer_page.py`
- Test: manual (browser); backend already covered. A fast smoke test asserts the served HTML contains the new element ids.

**Interfaces:**
- Consumes: `GET /api/specs`, `GET /api/models` (new shape), `POST /api/build`, `POST /api/models/<name>/delete`.
- Produces: DOM with ids `spec-search`, `spec-tree`, `spec-build`, `model-list`, `toast`. Removes `model-select`.

- [ ] **Step 1: Write a failing smoke test**

Add to `tests/viewer/test_viewer_server.py`:

```python
def test_index_contains_new_ui_elements(tmp_path) -> None:
    models = tmp_path / "out"
    models.mkdir()
    server = ViewerServer(str(models), port=0, examples_dir=str(tmp_path))
    server.start()
    try:
        with urllib.request.urlopen(f"{server.base_url}/") as resp:
            html = resp.read().decode()
    finally:
        server.stop()

    for token in ('id="spec-search"', 'id="spec-tree"', 'id="spec-build"', 'id="model-list"'):
        assert token in html
```

- [ ] **Step 2: Run to verify it fails**

Run: `.venv/bin/pytest tests/viewer/test_viewer_server.py::test_index_contains_new_ui_elements -q`
Expected: FAIL (tokens not in HTML yet).

- [ ] **Step 3: Implement the markup**

In `src/ncad/viewer/viewer_page.py`, replace the Model block:

```html
    <div>
      <div class="label">Model</div>
      <select id="model-select"></select>
    </div>
```

with:

```html
    <div>
      <div class="label">Spec</div>
      <div class="spec-row">
        <div class="combo">
          <input id="spec-search" type="text" placeholder="search examples..." autocomplete="off" />
          <div id="spec-tree" class="spec-tree" hidden></div>
        </div>
        <button id="spec-build" class="icon-btn" title="Build" aria-label="Build">
          <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 3v18M5 8l7-5 7 5M5 16l7 5 7-5"/></svg>
        </button>
      </div>
    </div>
    <div>
      <div class="label">Models</div>
      <div id="model-list" class="model-list"></div>
    </div>
```

Add CSS (near the existing `select, .btn` rules):

```css
  .spec-row { display: flex; gap: 8px; align-items: stretch; }
  .combo { position: relative; flex: 1; }
  #spec-search { width: 100%; font: inherit; font-size: 13px; color: var(--text);
    background: var(--panel-2); border: 1px solid var(--border); border-radius: 9px;
    padding: 8px 10px; }
  #spec-search:focus { border-color: var(--accent); outline: none; }
  .spec-tree { position: absolute; z-index: 20; left: 0; right: 0; top: calc(100% + 4px);
    max-height: 40vh; overflow: auto; background: var(--panel); border: 1px solid var(--border);
    border-radius: 9px; padding: 6px; }
  .spec-tree .dir { font-size: 11px; text-transform: uppercase; letter-spacing: .04em;
    color: var(--muted); padding: 6px 6px 2px; }
  .spec-tree .spec { padding: 6px 8px; border-radius: 6px; cursor: pointer; font-size: 13px; }
  .spec-tree .spec:hover, .spec-tree .spec.active { background: var(--panel-2); color: var(--accent); }
  .icon-btn { display: inline-flex; align-items: center; justify-content: center;
    width: 36px; background: var(--panel-2); border: 1px solid var(--border);
    border-radius: 9px; color: var(--text); cursor: pointer; }
  .icon-btn:hover { border-color: var(--accent); color: var(--accent); }
  .model-list { display: flex; flex-direction: column; gap: 4px; max-height: 30vh; overflow: auto; }
  .model-row { display: flex; align-items: center; gap: 6px; padding: 7px 9px;
    background: var(--panel-2); border: 1px solid transparent; border-radius: 8px; cursor: pointer; }
  .model-row:hover { border-color: var(--border); }
  .model-row.active { border-color: var(--accent); }
  .model-row .name { flex: 1; font-size: 13px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .model-row .row-actions { display: none; gap: 4px; }
  .model-row:hover .row-actions { display: flex; }
  .row-actions .icon-btn { width: 26px; height: 26px; }
  #toast { position: absolute; bottom: 18px; left: 50%; transform: translateX(-50%);
    background: var(--panel); border: 1px solid var(--border); border-radius: 9px;
    padding: 10px 16px; font-size: 13px; color: var(--text); opacity: 0;
    transition: opacity .25s; pointer-events: none; z-index: 50; max-width: 70%; }
  #toast.show { opacity: 1; }
  #toast.error { border-color: var(--no, #d9534f); }
```

Add a toast element inside `#stage` (near `#hint`):

```html
    <div id="toast"></div>
```

- [ ] **Step 4: Implement the JS**

Locate the existing model-select population and load logic (the code that does `fetch('/api/models')` and sets `<select>` options, and the `onchange` that calls the model loader). Replace it with the combobox + list logic. Add this JS in the script section, and remove the old `model-select` code:

```javascript
// ---- Spec combobox + models list ----
let specTree = [], selectedSpec = null, activeModel = null;

function toast(message, isError) {
  const el = document.getElementById("toast");
  el.textContent = message;
  el.classList.toggle("error", !!isError);
  el.classList.add("show");
  setTimeout(() => el.classList.remove("show"), 3200);
}

function flattenSpecs(nodes, prefix, out) {
  for (const node of nodes) {
    if (node.type === "dir") flattenSpecs(node.children, prefix + node.name + "/", out);
    else out.push({ name: node.name, path: node.path });
  }
  return out;
}

function renderSpecTree(filter) {
  const box = document.getElementById("spec-tree");
  const all = flattenSpecs(specTree, "", []);
  const q = (filter || "").toLowerCase();
  const matches = all.filter(s => s.path.toLowerCase().includes(q));
  box.innerHTML = "";
  let currentDir = null;
  for (const s of matches) {
    const dir = s.path.includes("/") ? s.path.slice(0, s.path.lastIndexOf("/")) : "";
    if (dir !== currentDir) {
      currentDir = dir;
      if (dir) { const d = document.createElement("div"); d.className = "dir"; d.textContent = dir; box.appendChild(d); }
    }
    const row = document.createElement("div");
    row.className = "spec" + (selectedSpec === s.path ? " active" : "");
    row.textContent = s.name;
    row.title = s.path;
    row.addEventListener("mousedown", () => {
      selectedSpec = s.path;
      document.getElementById("spec-search").value = s.path;
      box.hidden = true;
    });
    box.appendChild(row);
  }
  box.hidden = matches.length === 0;
}

function loadSpecs() {
  fetch("/api/specs").then(r => r.json()).then(data => { specTree = data.tree || []; });
}

function renderModelList(models) {
  const list = document.getElementById("model-list");
  list.innerHTML = "";
  if (!models.length) { list.innerHTML = '<div class="panel-empty">no models in out/</div>'; return; }
  for (const m of models) {
    const row = document.createElement("div");
    row.className = "model-row" + (activeModel === m.name ? " active" : "");
    const name = document.createElement("div");
    name.className = "name"; name.textContent = m.name; name.title = m.name;
    row.appendChild(name);
    const actions = document.createElement("div");
    actions.className = "row-actions";
    const regen = iconButton("Regenerate", REGEN_SVG);
    regen.addEventListener("click", ev => { ev.stopPropagation(); regenerate(m); });
    const del = iconButton("Delete", DELETE_SVG);
    del.addEventListener("click", ev => { ev.stopPropagation(); removeModel(m.name); });
    actions.appendChild(regen); actions.appendChild(del);
    row.appendChild(actions);
    row.addEventListener("click", () => selectModel(m.name));
    list.appendChild(row);
  }
}

function iconButton(tip, svg) {
  const b = document.createElement("button");
  b.className = "icon-btn"; b.title = tip; b.setAttribute("aria-label", tip); b.innerHTML = svg;
  return b;
}

const REGEN_SVG = '<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12a9 9 0 1 1-3-6.7L21 8"/><path d="M21 3v5h-5"/></svg>';
const DELETE_SVG = '<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 6h18M8 6V4h8v2M6 6l1 14h10l1-14"/></svg>';

function refreshModels() {
  return fetch("/api/models").then(r => r.json()).then(data => { renderModelList(data.models); return data.models; });
}

function selectModel(name) {
  activeModel = name;
  loadModel(name);   // existing model loader from the current viewer
  refreshModels();
}

function build(spec) {
  if (!spec) { toast("select a spec first", true); return; }
  document.getElementById("spinner").style.display = "block";
  fetch("/api/build", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ spec }) })
    .then(async r => { const d = await r.json(); if (!r.ok) throw new Error(d.error || "build failed"); return d; })
    .then(d => { renderModelList(d.models); const first = (d.built || [])[0]; if (first) selectModel(first); toast("built " + (d.built || []).join(", ")); })
    .catch(e => toast(e.message, true))
    .finally(() => { document.getElementById("spinner").style.display = "none"; });
}

function regenerate(model) {
  if (!model.source) { toast("no source recorded for " + model.name, true); return; }
  build(model.source);
}

function removeModel(name) {
  if (!window.confirm("Delete " + name + "?")) return;
  fetch("/api/models/" + encodeURIComponent(name) + "/delete", { method: "POST" })
    .then(r => r.json())
    .then(d => { if (activeModel === name) { activeModel = null; clearModel(); } renderModelList(d.models); toast("deleted " + name); })
    .catch(() => toast("could not delete " + name, true));
}

document.getElementById("spec-search").addEventListener("input", ev => renderSpecTree(ev.target.value));
document.getElementById("spec-search").addEventListener("focus", ev => renderSpecTree(ev.target.value));
document.getElementById("spec-search").addEventListener("blur", () => setTimeout(() => { document.getElementById("spec-tree").hidden = true; }, 150));
document.getElementById("spec-build").addEventListener("click", () => build(selectedSpec));

loadSpecs();
refreshModels();
```

Wire to the existing viewer functions. Confirmed in the current `viewer_page.py`: `loadModel(name)` (around line 332) loads a model into the scene, and `clearModel()` (around line 298) removes `modelRoot`. The new JS calls both directly, so no renaming or extraction is needed; just remove the old code that populated and handled `#model-select` (the `fetch('/api/models')` block that filled the `<select>` and its `onchange` handler) and keep `loadModel`/`clearModel` as-is.

- [ ] **Step 5: Run the smoke test + full fast suite**

Run: `.venv/bin/pytest tests/viewer -q && .venv/bin/ruff check src tests`
Expected: PASS; `All checks passed!`

- [ ] **Step 6: Commit**

```bash
git add src/ncad/viewer/viewer_page.py tests/viewer/test_viewer_server.py
git commit -m "Replace model dropdown with spec combobox, Build icon, and models list"
```

---

## Task 7: CLI wiring (pass examples dir into the viewer) and end-to-end demo

**Files:**
- Modify: `src/ncad/cli/viewer_cli.py`
- Modify: `src/ncad/viewer/__main__.py`
- Test: `tests/cli/test_viewer_cli.py`

**Interfaces:**
- Consumes: `find_project_root`, `ViewerServer(..., examples_dir=...)`.
- Produces: `launch_viewer` resolves and passes `examples_dir` (project-root `examples/`); `resolve_examples_dir(start=None) -> Path | None`.

- [ ] **Step 1: Write the failing test**

Add to `tests/cli/test_viewer_cli.py`:

```python
def test_resolve_examples_dir_is_examples_under_root(tmp_path) -> None:
    (tmp_path / "pyproject.toml").write_text("[project]\nname='x'\n")
    (tmp_path / "examples").mkdir()
    nested = tmp_path / "src"
    nested.mkdir()

    from ncad.cli.viewer_cli import resolve_examples_dir

    assert resolve_examples_dir(start=nested) == tmp_path / "examples"


def test_resolve_examples_dir_none_when_absent(tmp_path) -> None:
    (tmp_path / "pyproject.toml").write_text("[project]\nname='x'\n")

    from ncad.cli.viewer_cli import resolve_examples_dir

    assert resolve_examples_dir(start=tmp_path) is None
```

- [ ] **Step 2: Run to verify it fails**

Run: `.venv/bin/pytest tests/cli/test_viewer_cli.py -q`
Expected: FAIL (no `resolve_examples_dir`).

- [ ] **Step 3: Implement**

In `src/ncad/cli/viewer_cli.py`, add:

```python
def resolve_examples_dir(start: Path | None = None) -> Path | None:
    """Return ``<project-root>/examples`` if it exists, else None."""
    root = find_project_root(start)
    candidate = root / "examples"
    return candidate if candidate.is_dir() else None
```

and change `launch_viewer` to pass it:

```python
def launch_viewer(models_dir: str | None, host: str, port: int) -> None:
    """Resolve the models directory and run the viewer server in the foreground."""
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    resolved = resolve_models_dir(models_dir)
    examples = resolve_examples_dir()
    server = ViewerServer(
        models_dir=str(resolved),
        host=host,
        port=port,
        examples_dir=str(examples) if examples else None,
    )
    print(f"ncad viewer >> {server.base_url}  (serving '{resolved}', Ctrl+C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nstopping...")
        server.stop()
```

In `src/ncad/viewer/__main__.py`, mirror the wiring so `python -m ncad.viewer` also gets examples: import `find_project_root` and pass `examples_dir` the same way (resolve `<root>/examples` if present).

- [ ] **Step 4: Run tests to verify pass**

Run: `.venv/bin/pytest tests/cli/test_viewer_cli.py -q`
Expected: PASS.

- [ ] **Step 5: Full fast suite + ruff**

Run: `.venv/bin/pytest -m "not slow" -q && .venv/bin/ruff check src tests`
Expected: all fast PASS; `All checks passed!`

- [ ] **Step 6: Slow end-to-end via the real build service**

Add to `tests/viewer/test_viewer_server.py`:

```python
import pytest


@pytest.mark.slow
def test_real_build_route_produces_model(tmp_path) -> None:
    import os
    from pathlib import Path

    repo = Path(__file__).resolve().parents[2]
    examples = repo / "examples"
    models = tmp_path / "out"
    models.mkdir()
    server = ViewerServer(str(models), port=0, examples_dir=str(examples))
    server.start()
    try:
        req = urllib.request.Request(
            f"{server.base_url}/api/build",
            data=json.dumps({"spec": "gate-0.1-first-shape/block.hocon"}).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read())
    finally:
        server.stop()

    assert "block.glb" in data["built"]
    assert (models / "block.glb").is_file()
    assert (models / "block.meta.json").is_file()
```

Run: `.venv/bin/pytest tests/viewer/test_viewer_server.py -m slow -q`
Expected: PASS (1 slow test; imports OCP via the default build service).

- [ ] **Step 7: Manual demo (feature gate)**

```bash
rm -rf out
.venv/bin/ncad build examples/gate-0.1-first-shape/block.hocon   # seed one model
.venv/bin/ncad view --port 0
```
In the browser: the Spec search lists `gate-0.1-first-shape/block.hocon`; typing filters it; clicking the Build icon rebuilds and the model appears/updates in the Models list; hovering a model row shows Regenerate and Delete icons; Regenerate rebuilds from the recorded source; Delete (after confirm) removes it from the list. **Gate met when build, regenerate, and delete all work from the browser.**

- [ ] **Step 8: Commit**

```bash
git add src/ncad/cli/viewer_cli.py src/ncad/viewer/__main__.py tests/cli/test_viewer_cli.py tests/viewer/test_viewer_server.py
git commit -m "Wire examples dir into the viewer and add end-to-end build route test"
```

---

## Self-Review

**1. Spec coverage:**
- SpecCatalog tree + `/api/specs` -> Task 2, Task 5. ✓
- ModelMetadata sidecar (`source`, `built_at`, `ncad_version`, `kernel_version`) -> Task 3. ✓
- ModelCatalog `.meta.json` + delete (glb + sidecars, out/ only, path-safe) -> Task 1. ✓
- BuildService allow-check (examples or recorded source) + build + meta -> Task 4. ✓
- Routes (`/api/specs`, `/api/build`, `/api/models/<name>/delete`, richer `/api/models`) -> Task 5. ✓
- Synchronous build + spinner + toast -> Task 6 JS. ✓
- Frontend: combobox tree with search, Build icon+tooltip, scrollable models list, per-row regenerate/delete icons with tooltips, delete confirm -> Task 6. ✓
- CLI passes examples dir; localhost-bound unchanged -> Task 7. ✓
- Error handling: JSON errors, never raise to socket, 400 disallowed, 404 unknown -> Task 5. ✓
- Testing (fast backend units + routes with stub, 1 slow real build) -> Tasks 1-5, 7. ✓
- No document editing; build source restricted -> Tasks 4, 5 (boundary enforced in BuildService + server). ✓

**2. Placeholder scan:** No TBD/TODO. Task 6 references the existing model-loader function by behavior and instructs adapting the two call sites; this is necessary because the exact current function name must be read from `viewer_page.py` at implementation time (the JS in the current file is inline and may be renamed). Flagged explicitly, not left vague.

**3. Type consistency:** `models_with_sources()` shape `{"name","source"}` used identically in Tasks 1, 5, 6. `BuildService.build(spec) -> {"built":[...]}` used in Tasks 4, 5. `resolve_meta`, `delete_model`, `SpecCatalog.tree/resolve`, `ModelMetadata.write/read` signatures match across tasks. `ViewerServer(..., examples_dir=, build_service=)` consistent in Tasks 5, 7. ✓

**4. Ambiguity:** The no-nested-functions constraint conflicts with a natural closure-based factory in Task 5; the plan resolves it explicitly by mandating module-level `_document_builder_factory`/`_utc_now_iso`. The `clock` injection avoids a hidden `datetime.now` in tested code (determinism). Delete confirmation uses `window.confirm` (spec says "small in-UI confirmation"; `window.confirm` satisfies it simply; a custom modal is out of scope/YAGNI).
