# ncad Documentation: Design & Information Architecture

This document specifies **how ncad's documentation is designed, structured, and
maintained**. It is a design spec for the docs, not the docs themselves. The goal is a
professional-grade documentation site that is (a) a **general reference on CAD / CAM / CAE
/ PCB** as engineering domains and (b) an **accurate manual for ncad**, fused so that every
domain concept is followed by ncad's honest status on it.

---

## 1. Principles (non-negotiable)

1. **Truth over completeness.** The docs describe only what ncad can actually do today. If a
   capability is not implemented, the docs say so explicitly ("Not available in ncad today")
   rather than implying it works. No hallucinated features, no aspirational verbs written in
   the present tense. The single source of truth for "what's real" is the **implemented op
   registry** (`src/ncad/ops/op_registry.py`), the **schema** (`schema/part_schema.hocon`),
   and the **gate examples** (`examples/gate-*`, each one is a tested, building artifact).
2. **Domain-general, product-neutral.** The conceptual material describes CAD/CAM/CAE/PCB as
   *fields* - the operations, workflows, and concepts the discipline supports - **without
   naming or benchmarking specific commercial systems**. The reader learns "what a fillet is
   and why," "what a kinematic joint is," "what a copper pour is," in general engineering
   terms. ncad's implementation is then presented against that neutral backdrop.
3. **Comprehensive but not duplicated.** Cover all concepts and aspects of all four domains,
   but each fact lives in exactly one place and is cross-linked, never restated. The domain
   concept is explained once; feature pages link to it rather than re-explaining it.
4. **Status-tagged everywhere.** Every ncad feature carries an explicit, machine-checkable
   **status badge**: `Available`, `Partial` (with the exact limits), or `Planned` (not yet
   buildable). This is the mechanism that keeps principle #1 enforceable.
5. **Reflects "what and how to build."** For every available op the docs show the exact
   authored-document fields, the option enums, and a copy-pasteable example that actually
   builds. Documentation is validated against the real schema and examples (see §7).

---

## 2. Relationship to the existing `docs/`

The docs site does **not** replace or duplicate the existing repository documents; it serves
a different audience and links to them:

| Existing doc | Audience | Role vs. the docs site |
|---|---|---|
| `docs/design.md` | contributors | *Why* the engine is shaped this way (architecture, decisions). The site's "Explanation" tier links here, does not restate it. |
| `docs/plan.md` | contributors | *What to build, in what order* (roadmap/backlog). Feeds the `Planned` status badges; the site does not copy the tracker. |
| `docs/research/*` | contributors | Sourced decisions (kernel, robustness, etc.). Deep-linked from Explanation pages where a "why" needs a citation. |
| `docs/feature-ordering.md` | contributors + advanced users | The op-composition rules. Surfaced (adapted) in the "authoring a feature tree" how-to. |

Rule: **design/plan/research are the contributor-facing source of truth; the docs site is
the user-facing, accuracy-gated projection of it.** When they disagree, the code wins, then
design.md, then the site is corrected.

---

## 3. Information architecture: Diataxis + a domain axis

The site uses the **Diataxis** framework (four modes, each serving a distinct need) crossed
with the **four engineering domains**. Diataxis is the industry-standard structure precisely
because it stops the classic failure of docs that mix teaching, doing, and reference into one
unusable blob.

**The four Diataxis modes:**

- **Tutorials** (learning-oriented): a beginner follows steps to a guaranteed result. "Build
  your first part." Success = the reader completes it and feels capable.
- **How-to guides** (task-oriented): recipes for a user who knows what they want. "How to cut
  a counterbored hole," "How to constrain a sketch fully." Goal-indexed.
- **Reference** (information-oriented): dry, exhaustive, accurate. Every op, every field,
  every enum, every limit. This is where the capability inventory lives and where the
  accuracy gate bites hardest.
- **Explanation** (understanding-oriented): the domain concepts and ncad's design rationale.
  "What is a B-rep and why exact geometry," "What the topological naming problem is," "Why
  ncad has no authoring GUI." Links out to `design.md`/`research`.

**The domain axis** (CAD / CAM / CAE / PCB) organizes the *content within* Reference and
Explanation. Each domain gets a concept overview (product-neutral) and a capability matrix
mapping domain features to ncad status.

### Top-level site structure

```
Home  (what ncad is, the one-way document>>build>>view model, honest status banner)
│
├── Getting Started            [Tutorials]
│     ├── Install & run (uv, ncad build, ncad view)
│     ├── Your first part (rectangle >> extrude >> view)     [maps to gate-0.1]
│     ├── A parametric part (expressions, a hole, a fillet)  [maps to gate-0.2]
│     └── Editing & rebuilding (change a param, delete a feature)
│
├── How-to Guides              [How-to]
│     ├── Authoring
│     │     ├── Write a feature-tree document
│     │     ├── Use parameters & expressions
│     │     └── Reference geometry (semantic / generative / selector refs)
│     ├── Sketching  (constraints, dimensions, project/offset, sketch-modify)
│     ├── Modeling   (one how-to per available op family)
│     └── Export & view  (STEP, glTF, the viewer, pick-by-id)
│
├── Concepts                   [Explanation]   <-- the DOMAIN-GENERAL material
│     ├── What is CAD/CAM/CAE/PCB (the four domains, product-neutral)
│     ├── CAD concepts    (B-rep vs mesh, feature tree, parametric vs direct,
│     │                    sketches & constraints, references/TNP, assemblies,
│     │                    surfacing, sheet metal, mold, drafting, PMI)
│     ├── CAE concepts    (kinematics: joints/DoF/FK/IK/motion; MBD; the FEA/CFD line)
│     ├── CAM concepts    (stock, setups, toolpath strategies, post/G-code)
│     ├── PCB/ECAD concepts (nets, stackup, footprints, DRC, board>>solid lowering)
│     └── Why ncad is shaped this way (document-as-truth, determinism, no GUI)
│
├── Reference                  [Reference]   <-- the ACCURACY-GATED capability surface
│     ├── The document schema (blocks, units, schema_version, profile)
│     ├── Operations reference (one page per op, uniform template - see §5)
│     ├── Sketch entities & constraints (exhaustive lists)
│     ├── References & selectors (grammar, attribute model, what's wired)
│     ├── Expressions & functions (syntax + registered-function catalogue)
│     ├── Export formats & CLI
│     └── Capability matrix  (the master domain>>status table - see §6)
│
└── About  (status legend, versioning policy, how to read these docs, contributing)
```

---

## 4. The domain-general + ncad-status pattern (the core device)

This is how principle #2 (product-neutral) and #1 (truth) combine on a single page. Every
**Concepts** page follows this shape:

1. **The concept, generically.** What the operation/feature *is* in the discipline, why it
   exists, when an engineer uses it - in neutral terms, no product names. (E.g. "A *fillet*
   rounds a sharp edge with a constant- or variable-radius blend, to relieve stress
   concentrations and ease manufacture.")
2. **The general capability space.** What the field as a whole supports (constant / variable
   / face / full-round fillets; setback corners; conic/G2 rounds). This is the "what all
   other systems can do" coverage, phrased as domain capability, not as any product's menu.
3. **ncad status.** An explicit, tagged statement of where ncad sits against that space, with
   a link to the Reference page for the exact fields. (E.g. "**ncad:** constant-radius and
   two-distance/distance-angle chamfers are `Available`; variable-radius, face, and
   full-round fillets are `Planned`.")

This lets the docs be a genuine general CAD/CAM/CAE/PCB reference while never overstating
ncad. A reader learning the field gets the whole picture; a reader evaluating ncad gets the
truth.

---

## 5. The Operations Reference template (uniform, per-op)

Every implemented op gets one Reference page from a fixed template, so the surface is
predictable and the accuracy gate can check it:

```
# <op name>            [status badge: Available | Partial]
> One-line: what it does, in domain terms. Links to the Concept page.

## Signature
The authored fields (name · type · required? · default · allowed values/enum).
Generated straight from the schema + the *_params.py validator - not hand-written.

## Options
Each enum value explained (e.g. extrude end: blind / symmetric / two_side /
through_all / to_next / to_face / to_surface), with what each produces.

## Example
A minimal HOCON snippet that ACTUALLY BUILDS (drawn from or verified against a
gate example). Shown with the resulting render where useful.

## Limits & notes
Every documented limitation, verbatim from the code's own notes (e.g. "guide curves
are accepted but approximate a plain sweep in this release"; "distance-angle picks
the first adjacent face"). This section is mandatory and must not be empty if the
code has a limit.

## See also
Concept page (domain), related ops, feature-ordering rule if any.
```

The initial op set to document (the current `Available` surface, 15 ops): **sketch, extrude,
pocket, revolve, groove, sweep, loft, rib, hole, fillet, chamfer, shell, draft, boolean,
wrap**. Each with its real fields/enums/limits from the code.

---

## 6. The Capability Matrix (the honesty centerpiece)

A single master table (and per-domain sub-tables) mapping the **general domain capability**
to **ncad status**. This is the page a decision-maker reads to know exactly what ncad can and
cannot do, at a glance, without reading prose. Columns:

| Domain capability (product-neutral) | ncad status | Notes / limits | Ref |
|---|---|---|---|
| Sketched extrude (blind/symmetric/2-side/through/to-face) | Available | to-surface via face target | [op] |
| Revolve / groove | Available | axis X/Y/Z or point+dir; datum-axis Planned | [op] |
| Sweep (single path) | Available | guides approximate a plain sweep | [op] |
| Variable-radius / face / full-round fillet | Planned | - | [plan] |
| Assemblies / joints / motion | Planned | design-complete, unbuilt (Phase 5-6) | [concept] |
| CAM toolpaths / G-code | Planned | seam designed, built late (Phase 15) | [concept] |
| PCB board model / DRC | Planned | seam designed, built late (Phase 16) | [concept] |
| FEA / CFD | Not in scope | export/integration concern, never a solver we write | [concept] |

Status vocabulary (exactly four, no others):
- **Available** - implemented, tested, has a gate example.
- **Partial** - implemented with stated limits (the limits are mandatory, not optional).
- **Planned** - in the roadmap (`plan.md`), not buildable today.
- **Not in scope** - a deliberate non-goal (e.g. FEA/CFD solver), with the reason.

The matrix is **generated/validated from code**, not hand-maintained (see §7), so it can
never drift into a lie.

---

## 7. Accuracy enforcement (how principle #1 stays true)

Documentation accuracy is a *tested property*, not a promise:

- **Op coverage check.** A test asserts every op in `op_registry.py` has a Reference page,
  and every Reference page names a real op. A new op with no doc (or a doc for a removed op)
  fails CI.
- **Example builds.** Every HOCON snippet shown in the docs is either a gate example or is
  built by the doc-check in the test suite (reusing the `test_gate_examples` machinery), so a
  shown example that no longer builds fails CI. This directly serves "must truly reflect what
  can be built."
- **Status source of truth.** `Available` is derived from the registry + a gate example;
  `Planned` is derived from `plan.md`. The capability matrix is generated from these sources
  so a feature cannot be marked `Available` unless it actually is.
- **No-hallucination lint.** A doc author checklist (and ideally a lint) forbids present-tense
  capability claims on `Planned`/`Not in scope` items; those must use the status badge and
  "not available today" phrasing.

---

## 8. Tooling: Docusaurus on GitHub Pages

**Docusaurus** (React/MDX static-site generator) hosted on **GitHub Pages**, chosen because it
gives Markdown authoring, a category/sidebar structure that maps cleanly onto the Diataxis +
domain IA, Algolia search, MDX (for the interactive status badges and capability matrix), and
first-class GitHub Pages deployment.

**Layout** (docs live in the repo, so they version with the code):

```
repo/
├── docs/                         # existing contributor docs (design/plan/research) - unchanged
└── website/                      # Docusaurus root
    ├── docusaurus.config.js      # url, baseUrl, organizationName, projectName, trailingSlash
    ├── sidebars.js               # the §3 IA as sidebar categories
    ├── docs/                     # the site content (getting-started/ how-to/ concepts/ reference/)
    ├── src/                      # custom React (StatusBadge, CapabilityMatrix components)
    └── static/                   # images/renders, .nojekyll, CNAME (if custom domain)
```

**GitHub Pages config** (project site `deepsaia/ncad` -> `https://deepsaia.github.io/ncad/`):
- `url: 'https://deepsaia.github.io'`, `baseUrl: '/ncad/'`, `organizationName: 'deepsaia'`,
  `projectName: 'ncad'`, `trailingSlash: false`.
- `.nojekyll` in `static/` (GitHub Pages/Jekyll drops `_`-prefixed files otherwise).

**Deployment:** a GitHub Actions workflow (`.github/workflows/deploy-docs.yml`) on push to
`main`: build the site, publish with `actions/deploy-pages` (permissions `pages: write`,
`id-token: write`); a `test-deploy.yml` on PRs runs a build-only check. Publishing source set
to "GitHub Actions."

**Versioning:** Docusaurus doc-versioning is **not** enabled initially - the docs track a
single evolving pre-1.0 engine, and snapshot versioning is recommended only for high-traffic,
rapidly-diverging release lines. Revisit at the first stable release. Until then, the docs
always describe `main`, and the status badges carry the "as of" truth.

**Custom React components** (the accuracy machinery made visible):
- `<StatusBadge status="available|partial|planned|not-in-scope" />` - the ubiquitous tag.
- `<CapabilityMatrix domain="cad|cam|cae|pcb" />` - renders the §6 table from a data file
  that the accuracy tests validate against the registry.

---

## 9. Authoring conventions

- **One concept, one home.** A concept is explained in exactly one Concepts page; everything
  else links to it. No re-explaining what a fillet is on the fillet op page - link.
- **Neutral voice in Concepts, imperative in How-to, terse in Reference.** Match the Diataxis
  mode's register.
- **No product names** in Concepts/Reference domain material (principle #2). Describe the
  capability, not a vendor's menu.
- **Every limit is documented.** If the code refuses or approximates something, the Reference
  "Limits & notes" says so, in the code's own words.
- **Examples build.** Never show HOCON that isn't validated (§7).
- **Link to `design.md`/`research`** for the deep "why"; do not copy their content.

---

## 10. Build order for the docs (thin slices, so it ships useful early)

1. **Scaffold**: Docusaurus + GH-Pages deploy workflow + the §3 sidebar skeleton +
   `StatusBadge`/`CapabilityMatrix` components. Ships an empty-but-live site.
2. **Reference first** (highest accuracy value): the schema page + the 15 op pages from the
   §5 template, generated against code; the capability matrix; the accuracy tests (§7).
3. **Getting Started**: the three tutorials mapped to gate-0.1/0.2 and the edit-rebuild loop.
4. **Concepts (CAD)**: the domain-general CAD material with ncad-status, the biggest writing
   effort; then CAE, CAM, PCB concept overviews (mostly `Planned`/seam status today, but the
   domain explanation is real and valuable).
5. **How-to guides**: fill in task recipes as the common questions surface.
6. **Polish**: search, cross-links, renders/images, the About/versioning pages.

Each step leaves a deployable, honest site; none blocks on a later one.

---

## Summary

The docs are a **product-neutral CAD/CAM/CAE/PCB reference fused with an accuracy-gated ncad
manual**, structured by **Diataxis** (tutorials / how-to / reference / explanation) crossed
with the **four domains**, built in **Docusaurus** on **GitHub Pages**. The defining
mechanism is the **status badge + code-validated capability matrix**: every capability the
field offers is described generically, and ncad's real position on it is stated honestly as
`Available` / `Partial` / `Planned` / `Not in scope` - enforced by tests so the documentation
can never claim something ncad cannot do.
