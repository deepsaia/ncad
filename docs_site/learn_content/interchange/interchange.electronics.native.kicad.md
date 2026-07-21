The `.kicad_pcb` file is the native board format of the KiCad EDA suite, and it is built on **S-expressions** -- the parenthesized, nested-list notation borrowed from the Lisp family. The entire board is one big list whose head token is `kicad_pcb`, containing child lists for the format version, the generating application, the general settings, the layer table, design rules, nets, footprints, copper tracks, vias, filled zones, and graphic items. Its sibling files (`.kicad_sch` for schematics, `.kicad_sym` for symbol libraries, `.kicad_mod` for footprints) share the same grammar. Because it is plain, line-oriented UTF-8 text rather than a binary blob, it is human-readable, greppable, and produces meaningful diffs under version control.

## Shape of the format

Every element is a token followed by its attributes, nested to arbitrary depth. Coordinates are absolute and expressed in millimetres, and objects carry a `uuid` so that identity survives edits. A stripped-down excerpt looks like:

```
(kicad_pcb
  (version 20240108)
  (generator "pcbnew")
  (layers (0 "F.Cu" signal) (31 "B.Cu" signal))
  (net 0 "")
  (net 1 "GND")
  (segment (start 10 20) (end 40 20) (width 0.25)
           (layer "F.Cu") (net 1) (uuid "a1b2..."))
  (via (at 40 20) (size 0.8) (drill 0.4)
       (layers "F.Cu" "B.Cu") (net 1))
)
```

The grammar itself is tiny and can be stated as a recursive rule where an element is either an atom (a symbol, number, or quoted string) or a list of elements:

\[ \textit{sexpr} \;\to\; \textit{atom} \;\mid\; \texttt{(}\; \textit{token}\; \textit{sexpr}^{*}\; \texttt{)} \]

This regularity is what makes the format straightforward to parse with a single generic reader and to emit with a single generic writer, independent of how many distinct object types the schema defines.

## What round-trip means

*Round-trip* is the property that a tool can read a `.kicad_pcb` file into its own object model and write it back out **without losing or corrupting information** -- ideally producing a file that a downstream reader treats as equivalent to the original. This is stronger than merely parsing. Faithful round-tripping requires several disciplines: honoring the `version` token so that the reader interprets tokens with the right generation's semantics; **preserving tokens the reader does not recognize** so that data written by a newer or different generator is not silently dropped; carrying `uuid`/timestamp identifiers through unchanged so cross-references (nets, footprint fields, DRC exclusions) stay valid; and preserving coordinate precision and net numbering exactly.

Deterministic, canonical serialization is the other half of the contract. If a writer emits child elements in a stable order and with stable numeric formatting, then a semantically null round-trip yields a byte-for-byte identical file, and any real change shows up as a small, reviewable diff. That determinism is precisely what allows a board to live in a version-control system as a first-class source artifact, where meaningful merges and history are possible rather than treating the design as an opaque export.

## Why it matters

A readable, losslessly round-trippable native format is what lets an external program participate as a *peer* in the design flow rather than a one-way exporter. A generator or script can synthesize or transform a board and hand it back to the interactive editor with hand-authored data intact; automated checks can operate on the same file engineers edit; and continuous-integration pipelines can regenerate, diff, and validate boards mechanically. The cost of this openness is the obligation to track the format's evolving grammar and to preserve unfamiliar constructs faithfully, which is why round-trip fidelity -- not just import -- is the meaningful engineering bar.
