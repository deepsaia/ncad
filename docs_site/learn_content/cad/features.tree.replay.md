**Replay** is how a parametric model rebuilds: to produce the current geometry, the engine
re-executes the feature tree from the top (or from the first changed feature), each op consuming the
prior op's output. Editing a parameter does not patch the geometry, it changes an input and replays
the affected suffix of the tree.

## Deterministic rebuild

Replay is a pure function: the same feature tree always yields the same geometry, against a fixed
geometry kernel. This determinism is what makes the document, not the geometry, the source of truth,
the model can be regenerated from the text at any time, and two builds of the same document are bit
comparable (by topology signature, not raw bytes).

## Incremental replay

A naive rebuild re-runs everything; a good engine rebuilds only the **dirty suffix**. Features form
a dependency graph (each references specific upstream results and named topology). When a parameter
changes, only the features downstream of it re-execute; unaffected features are served from a cache
keyed on their inputs. This is what keeps editing a large part responsive: change a late fillet's
radius and only that fillet recomputes.

Replay is also why **persistent naming** matters: a feature that references "the top face of the
boss" must find that same face on every rebuild even after upstream edits renumber the topology.
Without stable references, replay would silently attach a feature to the wrong face.
