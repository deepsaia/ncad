**Determinism** is the guarantee that the same document, built with the same kernel, always
produces the same model, and that reproducibility is what makes a text document a trustworthy source
of truth.

## Why it is the foundation

A parametric engine is a pure function `build(document) -> model`. Determinism means that function
has no hidden inputs: no randomness, no wall-clock, no global state, no order-dependent iteration
that changes the result. Given that, a design can be regenerated from its text at any time, two
builds are comparable, and an edit's effect is exactly the replayed difference.

## How it is verified and where it is bounded

Determinism is a *tested* property, not a hope. Two builds of the same document are compared not by
raw B-rep bytes (which can differ harmlessly) but by a **topology signature plus toleranced
measures**, a canonical fingerprint that ignores insignificant floating-point noise while catching
any real geometric change. Golden tests pin these signatures.

The guarantee is bounded by the **kernel**: geometry equality and cache keys are only meaningful
against a fixed geometry-kernel version, so a kernel bump invalidates cached geometry wholesale
(re-execute) even though the document is unchanged. Within a pinned kernel, determinism is what
underpins incremental rebuild, reproducible viewer output, and the whole document-as-truth model,
authored by a human, an agent, or a generator, and always rebuildable to the same result.
