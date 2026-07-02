# Research: geometry-kernel choice (validated 2026)

*Question:* is OCCT via build123d still the best kernel for ncad, or should we
switch? *Decision recorded in* `design.md` §4, §19.

**Verdict:** stay on **OCCT**, keep **build123d** (reach through it into OCP for
advanced modules). The choice is effectively forced by ncad's open/public/GPL
intent, and the 2026 landscape confirms it. Confidence: high.

## Open side: OCCT is the only production-viable open B-rep kernel

- OCCT (latest major **8.0.0**, May 2026) is maintained in the open on GitHub by
  Open Cascade SAS. It has everything the scope needs: STEP AP203/214 + **AP242
  with PMI/GD&T** (partial), full XCAF/XDE assemblies + colors, IGES, **HLR** for
  drawings, glTF 2.0 r/w. License: LGPL-2.1 + the "Open CASCADE exception."
- **Every open alternative is dead, immature, or wrong-paradigm:**
  - **Fornjot (Rust)**, the most-watched open-kernel attempt, was **shut down and
    archived June 2026**; never shipped working booleans/fillets/STEP. Author: would
    need "another 2-3 years just to lay the foundation."
  - **truck (Rust)**, most capable native-Rust kernel (booleans + NURBS + partial
    STEP), but **no fillets/chamfers, no PMI/drawings, pre-1.0**, no release since
    2024-09. Years from production. The 2023-24 Rust-CAD wave (CADmium, ISOtope)
    was archived 2025. The pragmatic "Rust CAD" path is `opencascade-rs`, a wrapper
    around C++ OCCT, not a new kernel.
  - **Manifold / manifold3d**: guaranteed-manifold *mesh* booleans (ncad already
    uses it for convergent modeling); no B-rep, NURBS, fillets, or STEP.
  - CGAL (GPL/commercial; algorithm toolbox, not a NURBS B-rep kernel), libfive
    (implicit/F-rep), OpenNURBS (NURBS eval + 3DM I/O only) each replace a slice, not
    the kernel.

## Commercial side: better, but unusable by an open project

Parasolid (Siemens), 3D ACIS (Spatial/Dassault), CGM (Dassault), C3D (C3D Labs),
SMLib (defunct, absorbed by NVIDIA 2022) are all **closed-binary, per-seat/royalty
licensed**. Parasolid is the acknowledged robustness/ecosystem leader (SolidWorks,
NX, Onshape, Shapr3D, Plasticity), but:

- An open/public/GPL project **cannot redistribute** a closed kernel, and no user
  could build from source without their own paid, NDA'd license. There is **zero
  precedent** for an OSS CAD tool shipping one.
- Adopting a commercial kernel *is* the move associated with going proprietary
  (Shapr3D switched off OCCT to Parasolid and is closed). FreeCAD, OpenSCAD (CGAL),
  KiCad all stay on open kernels for this reason.
- Only C3D publishes pricing (academic ~$5k/yr, commercial base + 2-7% royalty), and
  it carries Russia-sanctions/procurement risk. Others are quote-only OEM programs.

**If the open constraint were ever relaxed** (a separate closed distribution):
Parasolid is the best target on robustness/ecosystem (high, unpublished OEM cost);
C3D the most transparent/affordable; ACIS a solid #2. Not a near-term path.

## Binding

Stay on **build123d** (v0.11.x, very active), which sits on **OCP /
cadquery-ocp**. build123d surfaces only STEP/STL/SVG; for XCAF/AP242 PMI, HLR,
defeaturing, and draft, `import OCP.*` directly alongside it. pythonocc-core is an
equally complete alternative binding but redundant once on OCP. occwl is stale.

## Biggest risk of staying (and the hedge)

Single-vendor concentration + documented **boolean/fillet robustness gaps** + Python
bindings version-locked to OCCT (OCP lagged 8.0.0 by weeks). Mitigation is not a
replacement kernel (none exists) but a **robustness layer we own** (see
[`occt-boolean-robustness.md`](./occt-boolean-robustness.md)), plus keeping the
swappable `Kernel` seam (design §16) as the architectural hedge.

*Uncertainty flags:* the static-linking freedom often read into the OCCT exception
exceeds its literal wording (irrelevant to us, since we are GPL); commercial-kernel
pricing is quote-only except C3D.
