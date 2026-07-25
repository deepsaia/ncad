# Getting Started

ncad turns a **text document** into exact-geometry CAD. You write a part as a declarative feature
tree (HOCON or JSON); a pure executor replays it against an OpenCASCADE kernel and produces a solid,
an assembly, or a solved motion. There is no authoring GUI: the document is the single source of
truth, and the same document rebuilds deterministically whether a human, an agent, or a generator
wrote it.

This tutorial takes you from an install to a moving mechanism in four short steps:

1. [Build your first part](first-part.md) - a feature tree to a viewable solid.
2. [Compose an assembly](first-assembly.md) - place two parts and join them.
3. [Drive a motion study](first-motion.md) - sweep a joint and watch the trajectory.

## Install

ncad needs Python 3.13, managed with [`uv`](https://docs.astral.sh/uv/). One dependency
(`pyondsel`, the multibody solver used for motion) is a side-by-side checkout; clone it next to this
repo before syncing.

```bash
git clone https://github.com/deepsaia/pyondsel ../pyondsel   # motion solver (side-by-side)
uv sync                        # install ncad + deps into .venv
uv run pytest -m "not slow"    # fast suite (no geometry kernel import)
```

The `ncad` command is the single entry point and runs from anywhere inside the project:

```bash
ncad build <document>    # build a feature-tree part to glTF (+ sidecars)
ncad view                # browser 3D viewer + model manager over ./out
ncad serve               # the full HTTP service (JSON API + viewer + Swagger)
```

See the [CLI reference](../reference/cli.md) for every command and flag.

## The shape of an ncad document

Every part document is a `parts {}` block of named parts, each an **ordered feature tree**. A
feature consumes the previous result and its topology, like a modifier stack:

```properties
units = mm
parts {
  bracket {
    profile = solid
    features = [
      { id = sk,   op = sketch,  plane = XY, elements = [ { id = r, type = rectangle, w = 60, h = 40 } ] }
      { id = body, op = extrude, profile = sk, distance = 8 }
      { id = soft, op = fillet,  edges = vertical, radius = 5 }
    ]
  }
}
```

Order is part of the model's meaning. The next page builds a real part this way, step by step.
