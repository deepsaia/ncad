# ncad: the manual

How to actually use the engine: author a part as a text document (HOCON/JSON), and a pure
executor replays it against an exact-geometry kernel to produce solids, assemblies, and motion.
The source of truth for what ncad can do is the code: the op registry, the schemas, and the
shipped examples. This manual is generated from and validated against them.

## Getting Started

Install, build a first part, edit and rebuild. The `ncad` CLI is the single entry point:
`ncad build <document>` produces geometry, `ncad view` serves the browser viewer.

## How-to Guides

Authoring a feature tree, sketching, modeling per op family, and export and view.

## Reference

The schema, the operations reference (generated from the op registry), sketch entities and
constraints, references and selectors, expressions, export and CLI, and the Capability Matrix.

## ncad Explained

The design rationale: document-as-truth, determinism, and no authoring GUI.
