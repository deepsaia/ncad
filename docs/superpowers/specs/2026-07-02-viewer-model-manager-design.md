# Viewer Model-Manager and Spec-Driven Build: Design

**Status:** approved (brainstorm), ready for implementation plan.
**Track:** viewer capabilities (tooling, parallel to the Phase 0 roadmap; not a Phase 0 bucket).

## Goal

Extend the ncad browser viewer so a user can, from the sidebar: pick an example spec
(searchable tree), build it with one click, see the resulting model appear in a
scrollable models list, and per model regenerate or delete it. The viewer never edits
a document; it triggers the existing `ncad build` and manages `out/` artifacts.

## Principle and framing

The viewer stays a **viewer, not an authoring GUI** (design section 13, section 17). It
gains a **local build-runner + model-manager** role: it lists specs, launches the
existing build path, and manages `out/` artifacts. It never edits a document. The
server stays **localhost-bound** (it already binds `127.0.0.1`), which is the boundary
that makes running the kernel and deleting files acceptable.

## Architecture

```
examples/*.hocon ──[GET /api/specs]──▶  Spec combobox (search + tree)
                                              │ Build (icon)
                                              ▼
Build / Regenerate ──[POST /api/build {spec}]──▶ BuildService >> DocumentBuilder
                                              │  writes  out/<part>.glb
                                              │        + out/<part>.meta.json
                                              ▼
out/*.glb + *.meta.json ──[GET /api/models]──▶ Models list (select · regenerate · delete)
                                              │ Delete (icon)
                                              ▼
                      [POST /api/models/<name>/delete] removes glb + sidecars (out/ only)
```

### Backend units (one responsibility each, matching current module style)

- **`SpecCatalog`** (new: `src/ncad/viewer/spec_catalog.py`): walks an examples
  directory for `.hocon`/`.json`, returns a nested tree; resolves a relative spec path
  to a safe absolute path (rejects traversal outside the examples dir). Mirrors
  `ModelCatalog`.
- **`ModelMetadata`** (new: `src/ncad/viewer/model_metadata.py`): reads and writes a
  model's `out/<stem>.meta.json`. Fields: `source` (repo-relative spec path or absolute),
  `built_at` (ISO-8601 string, supplied by the caller), `ncad_version`, `kernel_version`.
- **`ModelCatalog`** (extend: `src/ncad/viewer/model_catalog.py`): add `.meta.json` to
  the servable/sidecar set; add `resolve_meta(name)`; add `delete_model(name)` that
  removes the `.glb` and its `.meta.json`/`.bom.json`/`.plan.svg` sidecars, only within
  the models dir (path-safe), returning the list of removed paths.
- **`BuildService`** (new: `src/ncad/viewer/build_service.py`): the only server unit
  that touches the kernel. Validates the requested spec is allowed (resolves under the
  examples dir, or equals a recorded meta `source`), runs
  `DocumentBuilder(kernel).build_file(spec, out_dir)`, writes a `.meta.json` per built
  part, and returns the built model names. Raises a typed error for a disallowed or
  failing build; the server turns that into a JSON error response.
- **`viewer_server`** (extend): new routes below; `/api/models` payload grows to carry
  each model's recorded source.

### Frontend (sidebar, consistent with the current dark UI)

Replaces the `Model` `<select>` with a two-part block above the existing controls:

```
┌─ SPEC ───────────────────────────────┐
│ [ search examples…            ▾ ] [B] │   combobox (search+tree) + Build icon
│   gate-0.1-first-shape/               │   directory header (non-selectable)
│     block.hocon                       │   selectable leaf
├─ MODELS ─────────────────────────────┤
│ block.glb              [R] [X]        │   scrollable list; icons appear on hover
│ bracket.glb            [R] [X]        │
└───────────────────────────────────────┘
```

- **Spec combobox:** a text input filters a tree rendered from `/api/specs`.
  Directories are indented non-selectable headers reflecting the `examples/` structure;
  `.hocon`/`.json` leaves are selectable. Selecting a leaf sets the build target.
- **Build icon:** icon-only button right of the search input, tooltip "Build". Builds
  the selected spec.
- **Models list:** scrollable panel from `/api/models`; click a row to load it (replaces
  the old dropdown onchange). Each row shows the model name (truncated with ellipsis)
  and, on hover, two icon-only buttons: **Regenerate** (tooltip "Regenerate") and
  **Delete** (tooltip "Delete"), positioned so they never overlap the name.
- Icons are inline SVG (no icon-font dependency, consistent with the CDN-only frontend).
  Tooltips use the `title` attribute. Styling reuses existing CSS variables
  (`--panel-2`, `--accent`, `--border`, `--muted`).

## Data shapes

- `GET /api/specs` ->
  ```json
  {"tree": [
    {"type": "dir", "name": "gate-0.1-first-shape", "children": [
      {"type": "spec", "name": "block.hocon", "path": "gate-0.1-first-shape/block.hocon"}
    ]}
  ]}
  ```
  Paths are relative to the examples dir. Directories sort before files; both sorted by name.
- `GET /api/models` ->
  ```json
  {"models": [{"name": "block.glb", "source": "examples/gate-0.1-first-shape/block.hocon"}]}
  ```
  `source` is the recorded meta source, or `null` if there is no meta sidecar.
- `POST /api/build` body `{"spec": "gate-0.1-first-shape/block.hocon"}` ->
  200 `{"models": [...], "built": ["block.glb"]}` on success;
  non-200 `{"error": "..."}` on a disallowed source, schema-invalid document, or build failure.
  **Regenerate** posts the model's recorded `source` to the same endpoint.
- `POST /api/models/<name>/delete` -> 200 `{"models": [...]}` after removing the glb +
  sidecars; 404 for an unknown/unsafe name.

## Data flow

- After a successful build, the frontend refreshes the models list and auto-selects the
  newly built model (loading it into the scene).
- After a delete, the frontend refreshes the list; if the deleted model was selected, the
  scene is cleared and no model is auto-selected.
- Build and Regenerate are **synchronous**: the POST blocks until the build finishes; the
  UI shows a spinner during the request and a success or error toast after.

## Error handling

- Build failure (schema-invalid, kernel error, or disallowed source) returns a non-200
  JSON `{"error"}`; the UI shows a toast with the message and leaves the list unchanged.
- Delete requires a small in-UI confirmation ("Delete <name>?") before the POST.
- Path-traversal and out/-only guards live in `ModelCatalog`/`SpecCatalog`, reusing the
  existing `os.path.dirname(candidate) == dir` pattern. A build `spec` that resolves
  neither under the examples dir nor to a recorded meta source returns HTTP 400.
- The server never raises to the socket: handler methods catch the typed `BuildService`
  error and known IO errors, and return a JSON error; unexpected errors return 500 with a
  generic message (details logged, not leaked).

## Testing

- **Backend, fast (no OCP):**
  - `SpecCatalog`: builds the expected tree from a temp examples dir; rejects a traversal
    path; sorts dirs-before-files.
  - `ModelMetadata`: write-then-read round-trip; reading a missing file returns `None`.
  - `ModelCatalog.delete_model`: removes exactly the glb + its sidecars; refuses a name
    resolving outside the models dir; unknown name returns no-op/None.
  - `BuildService`: allows a spec under the examples dir and a recorded meta source;
    rejects an arbitrary outside path; on a stub/fake builder, writes the meta sidecar and
    returns built names.
  - New routes via the existing `test_viewer_server.py` background-thread pattern, with a
    stub builder injected so the route tests stay fast: `/api/specs` shape,
    `/api/build` success and error, `/api/models` carries source, delete removes and
    returns the updated list.
- **Slow (1):** real `POST /api/build` of `examples/gate-0.1-first-shape/block.hocon` ->
  `out/block.glb` and `out/block.meta.json` exist and the model is listed.
- `.meta.json` is gitignored along with the other `out/` artifacts.

## Boundaries and non-goals

- No document editing in the browser (no authoring GUI).
- Build source is restricted to specs under `examples/` or a model's recorded meta
  source; arbitrary filesystem paths are rejected.
- Synchronous build only (no async job queue/progress); acceptable for a local,
  single-user viewer. Revisit if builds grow long or concurrent.
- Server remains localhost-bound; these mutating routes are not intended for a public bind.

## Dependency injection note

`ViewerServer` currently constructs its `ModelCatalog` internally. To keep the new routes
testable without OCP, `ViewerServer` gains optional injected collaborators
(`spec_catalog`, `build_service`) with sensible defaults wired from `models_dir` and an
examples dir; route tests inject a stub `BuildService`. This preserves the existing
constructor contract (`models_dir`, `host`, `port`) with added optional keyword args.

The examples directory defaults to `<project-root>/examples`, resolved via the existing
`ncad.cli.project_root.find_project_root` (so the viewer finds examples the same way the
CLI resolves `out/`). The `ncad`/`ncad view` CLI passes the resolved examples dir into
`ViewerServer`; when it cannot be found, the spec panel is simply empty (no error).
