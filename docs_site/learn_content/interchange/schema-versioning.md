**Schema versioning** manages the evolution of a document format over time. As a modeling engine
gains features, its document schema changes, new fields, new ops, changed defaults. Versioning is
how documents authored under an older schema are recognized, and (when needed) migrated forward.

## Version tag and migration

The classic approach tags each document with a schema version and provides **migration
converters**: a chain of small transforms that upgrade a document from version $n$ to $n+1$, so an
old file loads under the current engine. A tool may prompt "upgrade this design?" and apply the
converters.

## Versioning versus determinism

Schema versioning is distinct from the *determinism* guarantee: determinism says the same document
plus the same kernel yields the same geometry; versioning says an *older* document can still be
understood. The two meet at reproducibility, to reproduce an old build faithfully you may need both
the old schema (to read it) and the pinned kernel (to build it identically).

A related evolution concern is the **attribute model** behind selectors and references: when the set
of queryable attributes changes, old selectors must keep their meaning, so the attribute schema is
versioned alongside the document. Versioning is a cross-cutting interchange concern, kept minimal and
tested, so the format can grow without stranding existing documents.
