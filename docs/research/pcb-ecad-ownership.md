# Research: PCB/ECAD ownership line

*Question:* how much of the electrical PCB workflow should ncad own vs. delegate?
*Decision recorded in* `design.md` §6b, §19; plan Phase 16.

## Key findings

1. **The PCB data model is small, stable, standardized in concept.** ~7 primitives:
   numbered net table, logical layers + physical stackup, footprints>>pads,
   tracks/arcs, vias, copper zones/pours, drills + non-electrical graphics.
   `.kicad_pcb`, ODB++, IPC-2581 agree on these objects; the winning pattern is a
   **numbered net table** all copper references by ordinal. Gerber base is per-layer
   image only (X2 adds net/pad attrs, X3 adds components).
2. **DRC splits cleanly: own the geometry, delegate the physics.** Geometric
   (clearance, trace width, annular ring, drill size, hole-to-hole, silk clearance,
   copper-to-edge, courtyard overlap, connectivity) are deterministic distance/
   width/overlap/graph ops (natural for ncad). Physics (voltage-dependent
   clearance (IPC-2221; ~30× by voltage), current-dependent width, impedance (field
   solver), SI/PI, DFM) need simulation/material data >> dedicated tools. DRC scope
   is open-ended (KiCad added creepage/skew as recently as 9.0).
3. **Routing + autoplacement are firmly "delegate."** Steiner routing / QAP
   placement are NP-hard; KiCad *removed* its built-in autorouter and offloads to
   Freerouting via Specctra DSN/SES. The netlist is the canonical handoff.
4. **Text-PCB tools converge on the same line: own logical/netlist, delegate
   physical to KiCad.** pcbdl (netlist>>Allegro), SKiDL (netlist+ERC>>KiCad),
   atopile (`.ato` DSL + constraint solver >> writes `.kicad_pcb`). tscircuit is the
   outlier (owns full stack incl. its own TS autorouter + Gerber).
5. **Exchange seams.** **STEP AP214** is the only format carrying true 3D solids
   (**AP242's electrical scope is wire-harness, not PCB. Don't rely on it**). IDF
   v3 (.emn/.emp) = lightweight board+placement; IDX/ProSTEP EDMD = modern
   change-tracked ECAD↔MCAD; IPC-2581 Rev B/C = open full fab+assembly dataset.
6. **PCB>>3D lowering is plain OCCT, replicable in build123d.** KiCad extrudes the
   `Edge.Cuts` outline (`SHAPE_POLY_SET`>>`BRepPrimAPI_MakePrism`), boolean-cuts
   drills, optionally fuses copper, places each component `.step` as an XCAF
   sub-assembly via `gp_Trsf`, writes with `STEPCAFControl_Writer`. build123d rides
   the same OCCT >> replicate the *algorithm*. KiCad's exporter is **not** a callable
   library (C++ `EXPORTER_STEP`, GPLv3); reuse the technique or shell out to
   `kicad-cli pcb export step`; use `pcbnew` read-only to ingest boards.

## Recommendation (adopted)

**OWN natively (deterministic core):**
- The **board data model**: numbered net table, logical layers + physical stackup,
  footprints/pads, tracks/vias/zones, drills, graphics. Treat zone *fills* as
  authored input or pin one deterministic fill algorithm (main determinism hazard).
- **Geometric validators** (SpecValidator mold): referential integrity + geometric
  DRC (clearance, width, annular ring, drill, courtyard, copper-to-edge,
  connectivity). Consume voltage/current/stackup as *inputs*.
- **PCB>>3D solid lowering**: the OCCT/build123d extrude-drill-place-STEP pipeline.
  ncad's home turf and its differentiator.

**DELEGATE (plugin / external):** schematic capture, autorouting, autoplacement, fab
output (Gerber/drill/pick-place) >> KiCad. Physics DRC >> dedicated tools.

**Priority exchange formats:**
1. **KiCad `.kicad_pcb` s-expr** (read + write): delegation seam to
   placement/routing/DRC/Gerber.
2. **STEP AP214** (export): board+component solids for MCAD.
3. **IDF v3 / IDX** (export, later); IPC-2581 Rev C + Gerber X3 later (delegate to
   `kicad-cli`).

**First slice proves:** text spec >> deterministic board model >> geometric
SpecValidator (clearance + connectivity + annular ring) >> lower to board+component
**STEP AP214** via build123d, with a **`.kicad_pcb` round-trip** so KiCad owns
routing/fab. Regression: golden spec, geometry hash on the lowered solid, golden
validator issues.

**Confidence:** high on the ownership line (data-model boundedness, DRC
geometry/physics split, routing=delegate, netlist handoff, OCCT lowering
replicable). **Biggest unknown:** fidelity of the `.kicad_pcb` **write** round-trip
(net ordinals, layer tokens, zone fills, 3D-model refs surviving re-open + DRC +
KiCad's own STEP export). Secondary: whether AP242 ever gains a real PCB schema
(current evidence: no).
