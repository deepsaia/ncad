# ncad Explained

Why ncad is built the way it is. The guides show you how; this page is the rationale behind the
shape.

## Document as truth

There is one source of truth: the text document. Geometry, assemblies, motion, robots, and analyses
are all outputs of replaying a document, never separately-edited state. There is no authoring GUI to
drift from the file, and no hidden model behind the viewer. The same document is editable by a human,
an agent, or a generator, and it means the same thing to all three. The data flow is one way:

```
author (human / agent / generator)  >>  document (dict)  >>  build(document) >> model  >>  view / export
        (all authoring here)                              (pure, deterministic)
```

## Determinism

`build(document)` is a pure function: the same document always yields the same geometry. That is what
makes the whole system testable (golden specs, geometry hashes, golden BOMs) and what lets an agent
propose an edit and trust the result. Randomness, if any, is confined to a generator that emits a
document; once the document exists, the build is fixed.

## Ordered feature tree

A part is an ordered list of features, each consuming the previous result and its topology, like a
modifier stack. Order is part of the model's meaning, and it matters to the kernel: OpenCASCADE is
order-sensitive, so a late shell or fillet can fail on geometry a different order would accept. The
persistent-naming layer keeps references (an edge, a face) stable across rebuilds, so editing an
upstream parameter does not silently break a downstream feature.

## Delegate, never bundle

ncad owns the model and the engineering vocabulary; it delegates heavy external solves rather than
reimplementing or bundling them. The multibody solver (OndselSolver, via `pyondsel`) solves motion;
CalculiX (`ccx`) solves FEA; a slicer produces G-code; MuJoCo validates robot descriptions. Each
delegated tool is optional: when it is absent, the relevant command degrades to a reported `skipped`
status and the document still validates, rather than failing the whole build. This keeps the core
small and honest about what it computes versus what it hands off.

## Swappable kernel

The geometry backend (build123d / OpenCASCADE today) sits behind a `Kernel` interface, and each op is
a pure builder `(shape_in, params, provenance_in, kernel) >> OpResult` threaded by the executor. The
engine is not tied to one geometry library; the interface is the seam.

For the full field background behind these ideas, see [Learn](../../learn/index.md); for what the
engine can do today, see the [Operations Reference](../reference/index.md) and the
[Capability Matrix](../reference/capability-matrix.md).
