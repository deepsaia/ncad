# ncad: the manual

How to actually use the engine: author a part as a text document (HOCON/JSON), and a pure
executor replays it against an exact-geometry kernel to produce solids, assemblies, and motion.

- **Getting Started**: install, build a first part, edit and rebuild.
- **How-to Guides**: authoring a feature tree, sketching, modeling per op family, export and view.
- **Reference**: the schema, the operations reference (generated from the op registry), sketch
  entities and constraints, references and selectors, expressions, export and CLI, and the
  Capability Matrix.
- **ncad Explained**: the design rationale (document-as-truth, determinism, no authoring GUI).

The source of truth for what ncad can do is the code: the op registry, the schemas, and the
shipped examples. This manual is generated from and validated against them.
