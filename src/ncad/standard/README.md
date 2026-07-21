# Standard parts

Native generators for standard mechanical parts. Each family is a **versioned dimension table**
(`standard_tables/*.json`, keyed by a real standard designation) plus a **generator** that turns a
size into a buildable ncad part document. No network and no third-party CAD import: geometry is
generated from the dimensions.

Every family is generatable two ways (see `StandardLibrary`):

- **by designation** (table lookup): `ncad spgen <family> <designation>` , e.g. `ncad spgen pipe DN50`
- **by custom dimensions**: `ncad spgen <family> --dim key=value ...`, e.g.
  `ncad spgen pipe --dim outer_diameter=60.3 --dim wall_thickness=3.6 --dim length=300`

## Families and their standards

| Family    | Table                          | Designation scheme        | Simplification |
|-----------|--------------------------------|---------------------------|----------------|
| `washer`  | `iso_7089_washers.json`        | ISO 7089 (M3..M20)        | flat annulus |
| `hex_nut` | `iso_4032_hex_nuts.json`       | ISO 4032 (M3..M20)        | plain bore, no thread |
| `pipe`    | `en_10220_pipes.json`          | EN 10220 (DN15..DN150)    | one wall per size |
| `flange`  | `asme_b16_5_flanges.json`      | ASME B16.5 class 150 (NPS)| bored disk + bolt circle, no raised face/hub |
| `gasket`  | `asme_b16_21_gaskets.json`     | ASME B16.21 (NPS)         | thin flat full-face ring |
| `bearing` | `iso_15_bearings.json`         | ISO 15 (6000/6200/6300)   | solid ring envelope, no races/balls |
| `i_beam`  | `euronorm_ipe_beams.json`      | Euronorm IPE (IPE80..300) | sharp corners, no root fillet |

## Data provenance and bulk expansion

The dimension VALUES are physical facts (a bolt's size is a measurement), transcribed into our own
JSON schema, with a `source` field on every table citing the standard. The shipped tables are
representative subsets covering common sizes. To bulk-expand a family to its full size range, import
from a freely-available, permissively-licensed machine-readable source and emit our
`standard_tables/*.json` schema (a one-off offline importer, not shipped), citing the source here:

- **Fasteners (washers, nuts, bolts, screws):** FreeCAD Fasteners workbench (LGPL) and the BOLTS
  library (Open Library of Technical Specifications) carry ISO/DIN/ASME fastener tables.
- **Bearings:** cq-warehouse (Apache-2.0) ships deep-groove and other bearing boundary dimensions.
- **Structural steel:** the AISC Shapes Database is distributed free as CSV (US W/HSS shapes);
  Euronorm IPE/HEA tables are widely published as CSV/JSON.
- **Pipe/flange pressure classes:** the full ASME B16.x tables are largely paywalled; keep these to
  a hand-verified representative subset unless a clearly-licensed source is found.

Clean-room rule: transcribe VALUES (facts) and cite the source; never copy a copyrighted document's
formatted table file into the repo.
