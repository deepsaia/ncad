# ncad — Coding Guidelines & Best Practices

These are project-wide instructions for working in this repository. They take
precedence over default behavior. See [`docs/design.md`](./docs/design.md) for the
system design and [`docs/plan.md`](./docs/plan.md) for the phased build order.

---

## General Principles

- Write clear, maintainable, and modular code.
- Prefer explicitness over cleverness.
- Keep functions and modules small and focused.
- **Do not ever write nested functions or nested classes.** Define every function
  and class at module top level.
- Avoid duplication; reuse existing utilities where possible.
- Prioritize readability and maintainability over premature optimization.

## Code Style

- Follow **PEP 8** for formatting, naming conventions, and import conventions.
- Organize imports into three groups: standard library, third-party, local modules.
- Use **explicit type hints** for all functions and methods.
- Avoid untyped interfaces unless absolutely necessary.

## Module Design

- Each module has a **single clear responsibility** — and therefore **only a single
  class per module**.
- Avoid excessively large modules or functions.
- Group related functionality logically within packages.
- **Do not place any logic inside `__init__.py`.** Use it only for namespace
  exports (re-exports), nothing more.
- Avoid global variables unless absolutely necessary.
- Favor simple, well-understood design patterns when appropriate.

### Object-oriented modules + the pure-function design

The design's data-flow spine is conceptually functional —
`generate(seed, params) → spec`, the pure `build(spec) → geometry`, `quantities(spec)`,
the validators. Reconcile this with the single-class-per-module rule by wrapping each
responsibility in **one class** whose primary method carries the behavior, while keeping
that method **internally pure** (no hidden randomness, no global/instance mutation that
affects output):

- `Generator(params).generate(seed) -> dict` — all randomness confined here.
- `Builder(kernel).build(spec) -> Geometry` — pure: same spec → identical geometry.
- `BomCalculator().quantities(spec) -> Bom`
- `SpecValidator().validate(spec) -> list[Issue]`

The class gives us the single-responsibility module and a clean injection point for
dependencies (e.g. the swappable `Kernel`); purity of the core method preserves the
determinism the design depends on (see `docs/design.md` §0, §3). Do not let a class
accumulate unrelated responsibilities just because it exists — if it grows a second
reason to change, split it into another module.

## Error Handling & Logging

- Handle exceptions **explicitly and consistently**.
- **Never silently swallow exceptions.** No bare `except:`; catch specific types,
  and re-raise or wrap with context.
- Provide meaningful error messages.
- Use **structured logging** (the `logging` module / a logger per module), never
  `print` statements, for diagnostics.
- Ensure logs carry sufficient context for debugging and monitoring (the relevant
  entity `id`s, the operation, the inputs that matter).
- Prefer raising typed, domain-specific exceptions over returning sentinel values.
  Validation issues are data (the validators return structured `Issue`s), but
  *programmer/contract* errors should raise.

## Testing

- Write tests for new functionality whenever possible.
- Cover **normal behavior, edge cases, and failure scenarios.**
- Tests must be **deterministic and easy to run** (`pytest` from the repo root).
- Lean on the design's testability: **golden specs** (same `seed+params` → identical
  spec), **geometry hashes** (same spec → identical geometry), **golden BOM**, and
  **golden plan images**. These are regression nets, not afterthoughts.
- A bug fix starts with a failing test that reproduces it.

---

## Libraries & Reuse

Do not hand-roll what a vetted library already does well. For this project:

### `leaf-common` — file IO, HOCON/JSON persistence (adopt)

Use **`leaf-common`** for file IO and config/spec (de)serialization instead of
hand-rolling it. It is mature, and it is the same ecosystem as our agent framework
(`neuro-san`), so the spec layer and the agent layer stay consistent.

- HOCON: `leaf_common.persistence.easy.easy_hocon_persistence.EasyHoconPersistence`
- JSON: `leaf_common.persistence.easy.easy_json_persistence.EasyJsonPersistence`
- Both expose a simple `persist(obj, ...)` / `restore() -> dict` and return **plain
  dicts**, which matches our dict-spec design (`docs/design.md` §1) directly.

This means the `spec` unit's load/serialize functions wrap `leaf-common` rather than
calling `pyhocon`/`json` directly. The **JSON Schema validation** (`jsonschema`) still
sits on top — `leaf-common` handles bytes↔dict; we own the contract check.

### `dspu` — not adopted yet

`dspu` also offers io/config/validation, but at its current early version (`0.0.4`) we
do **not** depend on it for foundational persistence. Revisit if it matures or if it
offers something `leaf-common` lacks that we actually need.

### Reuse rule of thumb

Before writing a utility for file IO, parsing, retries, serialization, or config
overlay, check `leaf-common` first — much of it already exists there.
