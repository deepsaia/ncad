# Research notes

Sourced investigations behind the decisions recorded in [`../design.md`](../design.md)
§19 and [`../plan.md`](../plan.md). Each note ends with a confidence level and the
single biggest remaining unknown (which the phase spikes are designed to close).

- [`direct-modeling-occt-ceiling.md`](./direct-modeling-occt-ceiling.md): how far
  history-free face editing goes on OCCT; the narrow well-behaved-only envelope and
  the dual validity gate. *(design §3, §19; plan Phase 4)*
- [`class-a-surfacing-feasibility.md`](./class-a-surfacing-feasibility.md): OCCT's
  G2 ceiling; ship engineering surfacing + analysis, true Class A out of scope.
  *(design §6, §19; plan Phase 9)*
- [`cam-toolpath-kernel.md`](./cam-toolpath-kernel.md): build 2.5D+drilling on
  OCCT sections + Clipper2; opencamlib as the 3D plugin; 5-axis out. *(design §6a,
  §19; plan Phase 15)*
- [`pcb-ecad-ownership.md`](./pcb-ecad-ownership.md): own the board data model +
  geometric DRC + 3D lowering; delegate routing/fab to KiCad. *(design §6b, §19;
  plan Phase 16)*
- [`kernel-choice-2026.md`](./kernel-choice-2026.md): OCCT via build123d validated
  as the only open kernel for the scope; commercial kernels unusable by an open
  project; not switching. *(design §4, §19)*
- [`occt-boolean-robustness.md`](./occt-boolean-robustness.md): solve OCCT's
  boolean/fillet fragility in a robustness layer we own (normalize, fuzzy retry
  ladder, unify, heal-and-retry), not by upstreaming. *(design §4, §19)*
- [`infinigen-transferable-ideas.md`](./infinigen-transferable-ideas.md): a reading
  of Infinigen (procedural generator) against ncad; parametric-by-default authoring,
  a declarative constraint graph split into exact vs. soft, and why ncad's pure build
  is a stronger determinism model. *(comparative study, not a §19 decision;
  design §1, §4a, §5, §18)*
- [`assembly-constraints-3d.md`](./assembly-constraints-3d.md): the 3D assembly
  constraint layer, the 21 element-pair primitives, DoF = 6n-6-rank diagnostics, and
  nested-sparsity screening; py-slvs solves, this is the analysis layer on top.
  *(design §7, §8; plan Phase 5)*
- [`blender-transferable-ideas.md`](./blender-transferable-ideas.md): Blender's
  architecture read against ncad; depsgraph (incremental DAG), modifier stack
  (non-destructive tree), fields (lazy selectors), and library overrides (typed
  deltas). Mesh not B-rep, so patterns not geometry. *(comparative study;
  design §0, §2, §4, §7, §13)*
- [`viewer-tessellation-lod.md`](./viewer-tessellation-lod.md): heavy-mesh rendering
  and axis orientation; adaptive-budget tessellation (not retopology), glTF compression,
  interaction LOD, and a Z-up scene fix; keep three.js, defer WASM tessellation / Nanite.
  *(design §13; plan bucket 2.8a)*

The design-judgment questions (MBD depth, provenance-map budget, building-profile
altitude) were reasoned directly and recorded in design §19 without a separate note.
