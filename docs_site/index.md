---
hide:
  - navigation
  - toc
---

<div class="ncad-hero" markdown>

<div class="ncad-hero-copy" markdown>

# ncad

**A data-driven CAD engine.** Declarative, parametric and direct.

Define a part as a text document; a pure executor replays it against an exact-geometry kernel to
produce solids, assemblies, motion, robots, and analyses. No authoring GUI. The same document is
editable by a human, an agent, or a generator, and rebuilds deterministically.

[Get started](ncad/getting-started/index.md){ .md-button .md-button--primary }
[Showcase](ncad/showcase.md){ .md-button }
[Learn the field](learn/index.md){ .md-button }

</div>

<div class="ncad-viewer" data-ncad-model="assets/models/crank_slider" data-ncad-motion="true"></div>

</div>

The whole model is one text document. This builds an L-bracket: a sketch, an extrude, a fillet, and a
sized hole, replayed deterministically.

```properties
units = mm
parts {
  bracket {
    profile = solid
    features = [
      { id = sk, op = sketch, plane = XY,
        elements = [ { id = r, type = rectangle, w = 60, h = 40 } ] }
      { id = body, op = extrude, profile = sk, distance = 8 }
      { id = soft, op = fillet, edges = vertical, radius = 5 }
      { id = bore, op = hole, plane = XY, positions = [ [ 0, 0 ] ],
        size = M8, fit = normal, depth = 8 }
    ]
  }
}
```

<div class="grid cards" markdown>

- __Parametric & direct__

    An ordered feature tree (sketch >> extrude >> hole >> fillet) plus history-free direct edits
    (defeature, offset, move-face) guarded by a robustness envelope.
    [Author parts](ncad/guides/authoring-parts.md)

- __Assemblies__

    Instances placed by mates and lower-pair joints, solved by a constraint solver, with
    interference checks and rolled-up mass properties.
    [Author assemblies](ncad/guides/authoring-assemblies.md)

- __Motion__

    Forward-kinematics mechanisms: drivers sweep joints; gear, cam, and geneva couplings are
    enforced; traces and measures come out over time.
    [Author motion](ncad/guides/authoring-motion.md)

- __Robotics__

    Export an assembly as URDF, MJCF, or SDF with link inertials computed from the geometry, never
    authored.
    [Author robots](ncad/guides/authoring-robots.md)

- __Analysis (FEA)__

    Structural load cases meshed with Gmsh and solved by CalculiX: static stress, modes, thermal.
    [Author analyses](ncad/guides/authoring-analyses.md)

- __Standard parts__

    Generate fasteners, pipes, flanges, bearings, and profiles natively, each with a standards
    citation.
    [Standard parts](ncad/guides/standard-parts.md)

- __Exact geometry__

    Precise B-rep solids on an OpenCASCADE kernel behind a swappable interface. STEP for interchange,
    glTF for the browser viewer.

- __Deterministic__

    A pure executor: the same document always yields the same model. The document is the single
    source of truth.

</div>
