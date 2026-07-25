# ncad: the manual

How to actually use the engine. You author a part as a text document (HOCON or JSON), and a pure
executor replays it against an exact-geometry kernel to produce solids, assemblies, motion, robots,
and analyses. The source of truth for what ncad can do is the code: the op registry, the schemas, and
the shipped examples. This manual is generated from and validated against them.

<div class="grid cards" markdown>

- __Getting Started__

    Install, build your first part, then compose an assembly and drive a motion study.
    [Start here](getting-started/index.md)

- __How-to guides__

    Author each document kind: parts, assemblies, motion, robots, analyses, and standard parts.
    [Browse the guides](guides/authoring-parts.md)

- __Workflows__

    End-to-end pipelines: part to motion, assembly to robot, part to FEA, import to export.
    [See the workflows](workflows/index.md)

- __Reference__

    The CLI, the HTTP API, the Python API, the document kinds, and the generated Operations Reference.
    [Open the reference](reference/cli.md)

- __ncad Explained__

    The design rationale: document-as-truth, determinism, no authoring GUI, delegate-not-bundle.
    [Read the rationale](explained/index.md)

- __Showcase__

    Live 3D scenes built by ncad from text documents, replaying the real solved trajectories.
    [Watch them move](showcase.md)

</div>
