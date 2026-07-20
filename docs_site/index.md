---
hide:
  - navigation
  - toc
---

# ncad

**A data-driven CAD engine.** Declarative, parametric and direct.

Define a part as a text document; a pure executor replays it against an exact-geometry kernel
to produce solids, assemblies, and motion. No authoring GUI. The same document is editable by a
human, an agent, or a generator, and rebuilds deterministically.

[Learn the field](learn/index.md){ .md-button .md-button--primary }
[Use ncad](ncad/index.md){ .md-button }

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

- __Parametric__

    An ordered feature tree: sketch >> extrude >> hole >> fillet. Edit a parameter or reorder a
    feature and the part rebuilds deterministically.

- __Direct__

    History-free face and relational edits on the current B-rep: defeature, offset, move-face,
    guarded by a measured robustness envelope.

- __Assemblies__

    Instances placed by mates and lower-pair joints, solved by a constraint solver, with
    interference checks and rolled-up mass properties.

- __Motion__

    Forward-kinematics mechanisms: drivers sweep joints; gear, cam and slot couplings are
    enforced; traces and measures come out over time.

- __Exact geometry__

    Precise B-rep solids on an OpenCASCADE kernel behind a swappable interface. STEP for
    interchange, glTF for the browser viewer.

- __Deterministic__

    A pure executor: the same document always yields the same model. The document is the single
    source of truth.

</div>
