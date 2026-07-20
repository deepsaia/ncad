A **multibody** part contains more than one disjoint solid body in a single document. Bodies arise
from a non-merging pattern, a split, an unfused boolean, or simply modeling several lumps before
joining them. Each body has a stable **identity** so features and later operations can refer to a
specific one.

## Why identity matters

In a multibody part, "operate on the running solid" is ambiguous, which body? Body identity
resolves that: each body carries a persistent id (derived from its provenance, the op and role that
created it), so an operation can name `row/body/2` or `spoke_hub` and mean exactly that solid across
rebuilds. Without stable identity, a pattern that reorders its copies would scramble every per-body
reference.

Body identity is the multibody analogue of persistent face naming: it is what lets a fillet target
one body, a boolean union two named bodies, a material assignment apply per body, and a mass roll-up
attribute mass to the right lump. Multibody modeling is common as an intermediate state (build parts
separately, then fuse) and as a final form (a part legitimately made of several disconnected
solids), and stable identity is what keeps it editable rather than a bag of anonymous volumes.
