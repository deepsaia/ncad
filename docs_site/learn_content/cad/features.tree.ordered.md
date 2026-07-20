A parametric part is an **ordered feature tree**: a sequence of operations, each consuming the
previous result and producing the next. The first feature mints a base solid (a sketched extrude, a
primitive, an import); every later feature adds material, removes it, or modifies the running body.

<figure markdown="span">
<svg viewBox="0 0 340 90" width="360" role="img" aria-label="A feature tree as an ordered pipeline" xmlns="http://www.w3.org/2000/svg" font-size="11">
  <g fill="none" stroke="currentColor" stroke-width="2">
    <rect x="10" y="30" width="60" height="30" rx="4"/>
    <rect x="100" y="30" width="60" height="30" rx="4"/>
    <rect x="190" y="30" width="60" height="30" rx="4"/>
    <rect x="280" y="30" width="55" height="30" rx="4"/>
    <line x1="70" y1="45" x2="100" y2="45"/><line x1="160" y1="45" x2="190" y2="45"/>
    <line x1="250" y1="45" x2="280" y2="45"/>
    <polygon points="100,45 92,41 92,49" fill="currentColor"/>
    <polygon points="190,45 182,41 182,49" fill="currentColor"/>
    <polygon points="280,45 272,41 272,49" fill="currentColor"/>
  </g>
  <g fill="currentColor" stroke="none" text-anchor="middle" font-size="10">
    <text x="40" y="49">sketch</text><text x="130" y="49">extrude</text>
    <text x="220" y="49">hole</text><text x="307" y="49">fillet</text>
  </g>
</svg>
<figcaption>Each feature consumes the previous solid and its topology, like a modifier stack.</figcaption>
</figure>

## Why order is meaning, not detail

The same set of features in a different order can produce a different shape, an invalid B-rep, or a
kernel crash: a fillet applied before a boolean rounds different edges than one applied after; a
shell late in a complex part can self-intersect. Order *is* part of the model's definition. This is
the same discipline as a modifier stack in mesh tools, but on exact B-rep, where the geometry kernel
is order-sensitive.

The tree is also what makes the model editable and legible: each feature is a named, revisitable
step with its own parameters and references. Editing a feature's parameter, or reordering the tree,
re-runs the pipeline from that point forward.
