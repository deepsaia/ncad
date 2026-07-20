# ncad Documentation: Design & Information Architecture (v2)

This document specifies **how ncad's documentation is designed, structured, and
maintained**. It is a design spec for the docs, not the docs themselves. The site is built in
**two parts**:

- **(A) Learn** - a general, **product-neutral reference and course** on the engineering
  subjects ncad touches: **Foundations** (math/geometry), **Geometric & Solid Modeling (CAD)**,
  **Manufacturing (CAM)**, **Electronic Design (PCB/ECAD)**, **Kinematics & Mechanisms**,
  **Multibody Dynamics**, **Robotics & Physics-Engine Simulation**, **Engineering Analysis &
  Simulation (CAE)** (statics, kinematics, dynamics, structural/thermal FEA, CFD, 1D frame,
  pipe-network/hydraulics, fluid-power), and **Interchange & Standards**. Every concept is
  taught to professional depth **whether or not ncad implements it**, and each carries an
  honest "In ncad" status box and authoritative source citations.
- **(B) ncad** - a separate, **exhaustive ncad reference + tutorial + user guide**: how to
  actually use the engine.

The two parts are cross-linked: a Learn concept's "In ncad" box links into the ncad section,
and every ncad page links back to the Learn concept it realizes.

---

## 1. Principles (non-negotiable)

1. **Truth over completeness.** The docs describe only what ncad can actually do today. If a
   capability is not implemented, the docs say so explicitly rather than implying it works. No
   hallucinated features, no aspirational verbs in the present tense. The source of truth for
   "what's real" is the **op registry** (`src/ncad/ops/op_registry.py`), the **schema**
   (`schema/part_schema.hocon`), and the **shipped examples** (`examples/*`, each a building,
   validating artifact).
2. **Domain-general, product-neutral.** The Learn material describes each field - the
   operations, workflows, and concepts the discipline supports - **without naming or
   benchmarking specific commercial systems**. The reader learns what a fillet, a kinematic
   joint, a copper pour, a contact model *are*, in general engineering terms. ncad's
   implementation is presented against that neutral backdrop.
3. **Comprehensive but not duplicated.** Cover all concepts of all subjects, but each fact
   lives in exactly one place and is cross-linked, never restated. Shared math (transforms,
   screw theory, continuity, numerics) lives once in **Foundations**; shared file formats live
   once in **Interchange**; disciplines cross-link them.
4. **Status-tagged everywhere.** Every ncad capability carries an explicit, machine-checkable
   status from a fixed five-value vocabulary: **`Available`**, **`Partial`** (with the exact
   limits), **`WIP`** (actively under construction this phase/bucket), **`Planned`** (in the
   roadmap, not buildable today), **`Not-in-scope`** (a deliberate non-goal, with the reason).
   This is the mechanism that keeps principle #1 enforceable.
5. **Reflects "what and how to build."** For every available op the docs show the exact
   authored-document fields, the option enums, and a copy-pasteable example that actually
   builds. Documentation is validated against the real schema and examples (see §7).
6. **Content is data.** All Learn conceptual content is authored as **JSON** (the taxonomy +
   per-node metadata) plus adjacent **MDX** bodies, validated against a schema, then consumed
   by the Docusaurus build. The docs mirror ncad's own document-as-truth philosophy: the pages
   are a projection of structured data, not hand-maintained prose.
7. **Every concept is sourced.** Each concept ends with citations to authoritative resources
   (canonical textbooks, official docs, ratified standards, peer-reviewed papers). A concept
   without at least one primary-tier source is incomplete and fails the citation lint (§7).
8. **Teach the field, not just the product.** Learn explains each concept in full professional
   depth even where ncad's status is `Planned` or `Not-in-scope`. Depth of teaching is
   independent of ncad's implementation state.

---

## 2. Relationship to the existing `docs/`

After the Great Cleanup, the contributor-facing docs are deliberately minimal: the **code is
the source of truth** (the op registry, the schemas, and the shipped examples), and this file
plus `docs/feature-ordering.md` are the only standing design docs. The site serves a different
audience and links to what remains:

| Existing doc | Audience | Role vs. the docs site |
|---|---|---|
| `docs/documentation-design.md` (this file) | contributors | The docs-site information architecture + node schema + citation model. Not user-facing content. |
| `docs/feature-ordering.md` | contributors + advanced users | Op-composition rules (safe order + failure mode per op). Surfaced in the "authoring a feature tree" how-to. |
| the code | everyone | `src/ncad/ops/op_registry.py`, `schema/*.hocon`, and `examples/*` are the authority for what is real; the site is validated against them (§7). |

Rule: **the code is the contributor-facing source of truth; the docs site is the user-facing,
accuracy-gated projection.** When they disagree, the code wins and the site is corrected. (The
prior design.md / plan.md / research notes were removed in the Great Cleanup; their durable
conclusions live in the code and its inline decision comments.)

---

## 2a. The two-part document model (the core structure)

| | **Part A - Learn (Engineering Reference)** | **Part B - ncad (the Manual)** |
|---|---|---|
| Audience | anyone learning the field | ncad users / evaluators |
| Neutrality | product-neutral | ncad-specific |
| Authoring | JSON (schema-validated) + MDX bodies | MDX + generated-from-code |
| Structure | subject -> topic -> sub-topic -> concept | Diataxis (4 modes) |
| Status device | per-concept "In ncad" box | status badges + Capability Matrix |
| Depth rule | full depth regardless of ncad status | only what ncad does today |

**The bridge.** Part A's per-concept "In ncad" box is the *only* place general concepts and
ncad meet. Part B never re-teaches a concept - it links back to the Learn node. This preserves
principle #3 across both parts: **the concept lives in Learn; the capability lives in ncad.**

---

## 3. Information architecture

### Part A - Learn (product-neutral course), organized by discipline

Nine subjects, each a **subject -> topic -> sub-topic -> concept** tree (the full taxonomy is
in the companion `docs/documentation-structure.json`; §8a). Two of the nine - **Foundations**
and **Interchange** - are shared homes that exist to enforce no-duplication (principle #3).

```
Learn
├── S0  Foundations              math, geometry, screw theory, numerics, units/determinism
├── S1  Geometric & Solid Modeling (CAD)
├── S2  Manufacturing & CAM
├── S3  Electronic Design (PCB / ECAD)
├── S4  Kinematics & Mechanisms
├── S5  Multibody Dynamics
├── S6  Robotics & Physics-Engine Simulation      (MuJoCo = ncad's first-class backend)
├── S7  Engineering Analysis & Simulation (CAE)   (statics/FEA/thermal/CFD/hydraulics/…)
└── S8  Interchange, Standards & Data Exchange     (STEP/glTF/URDF/Gerber/IFC/G-code/…)
```

### Part B - ncad (the product), Diataxis

```
ncad
├── Getting Started   [Tutorials]   install & run; first part (a sketched block); a
│                                    parametric part; editing & rebuilding
├── How-to Guides     [How-to]      authoring (feature tree, expressions, references);
│                                    sketching; modeling (per op family); export & view
├── Reference         [Reference]   the schema; operations reference (per-op template, §5);
│                                    sketch entities & constraints; references & selectors;
│                                    expressions & functions; export & CLI; Capability Matrix
└── ncad Explained    [Explanation] ncad design rationale (document-as-truth, determinism,
                                     no authoring GUI, the TNP); the feature-ordering rules
```

Migration from v1: v1's **Concepts** tier is promoted and expanded into **Learn**; v1's
ncad-specific rationale moves to **ncad Explained**. This resolves the v1 ambiguity where
domain concepts and ncad rationale shared one tier.

---

## 4. The concept page shape (Learn) - domain-general + ncad status

Every Learn **concept** page has three parts, rendered from its JSON node + MDX body:

1. **The concept, in full depth (product-neutral).** What it is, why it exists, the governing
   math (KaTeX), the general capability space the field supports - regardless of ncad's status.
2. **"In ncad" box** (`<NcadBox>`): the status badge (`Available` / `Partial` / `WIP` /
   `Planned` / `Not-in-scope`), an honest note, cross-links into the ncad Reference, and (for
   delegated domains) the intended external engine. Rendered from the node's `ncad` object.
3. **"Sources" box** (`<Sources>`): the tiered typed citations (§8b), rendered from `sources[]`.

**Rule:** the "In ncad" box is the concept's only ncad content; **teaching depth does not
scale with ncad status** (principle #8). A `Not-in-scope` concept (e.g. CFD turbulence models)
still gets full professional treatment.

---

## 5. The Operations Reference template (ncad, uniform per-op)

Every implemented op gets one ncad Reference page from a fixed template:

```
# <op name>            [status badge: Available | Partial]
> One-line: what it does. Links to the Learn concept it realizes.

## Signature   fields (name · type · required? · default · allowed values), generated
               from the schema + the *_params.py validator, not hand-written.
## Options     each enum value explained (e.g. extrude end: blind/symmetric/two_side/
               through_all/to_next/to_face/to_surface).
## Example     a minimal HOCON snippet that ACTUALLY BUILDS (from/verified against a gate
               example), with the resulting render where useful.
## Limits & notes   every documented limitation, verbatim from the code's notes. Mandatory
               and non-empty if the code has a limit.
## See also    the Learn concept id it realizes (reverse of the "In ncad" link), related ops,
               feature-ordering rule if any.
```

Op set (the current `Available` surface, from `op_registry.py`): **sketch, extrude, pocket,
revolve, groove, sweep, loft, rib, hole, fillet, chamfer, shell, draft, boolean, wrap, thread,
primitive, pattern, mirror, transform, split, offset, defeature, move_face, relate,
reposition_hole, feature_mirror, feature_pattern, import, datum_plane, datum_axis**. The list is
generated from the registry (§7), not hand-maintained, so it never drifts.

---

## 6. The Capability Matrix (the honesty centerpiece)

A master table (and per-subject sub-tables) mapping **general domain capability** to **ncad
status**, extended in v2 to the full subject axis and with a **delegated-engine** column:

| Domain capability (product-neutral) | ncad status | Engine / delegated-to | Notes / limits | Ref |
|---|---|---|---|---|
| Sketched extrude (blind/symmetric/2-side/through/to-face) | Available | (native) | to-surface via face target | [op] |
| Fillet - variable-radius / face / full-round | Planned | (native) | constant-radius fillet is Available | [op] |
| Assemblies / mates / joints | Available | py-slvs | 8-mate + 7 lower-pair joints | [op] |
| Kinematics / motion | Available | OndselSolver (FK) | drivers + gear/cam/slot couplings | [op] |
| Rigid-body dynamics (MBD) | Planned | physics engine | deferred; not on the FK solver | [concept] |
| Robotics / contact simulation | Planned | **MuJoCo** | first-class force-driven backend | [concept] |
| Structural / thermal FEA | Planned | CalculiX / Elmer / Z88 | export seam | [concept] |
| 1D frame / beam | Planned | frame3dd / PyNite | export seam | [concept] |
| CFD | Planned | Elmer | export seam | [concept] |
| Pipe-network flow (hydraulics) | Planned | EPANET | fed by piping profile | [concept] |
| CAM toolpaths / G-code | Planned | (native + opencamlib) | process profile | [concept] |
| PCB board model / DRC | Planned | (native + KiCad round-trip) | board data-model profile | [concept] |

The matrix is **generated/validated from code** (the op registry + shipped examples; §7), so it
can never drift into a lie. The "Engine" column records the owned-vs-delegated
map.

---

## 7. Accuracy enforcement (how principle #1 stays true)

Documentation accuracy is a *tested property*, not a promise:

- **Op coverage check.** Every op in `op_registry.py` has an ncad Reference page, and every
  Reference page names a real op. Drift fails CI.
- **Example builds.** Every HOCON snippet in the ncad section is one of the shipped examples
  under `examples/`, or is built by the doc-check at build time. A shown example that no longer
  builds fails CI.
- **JSON-schema validation.** Every Learn content node validates against
  `content-node.schema.json`; a malformed node fails CI.
- **Status-source validation.** Each `ncad.status` must match its derivation source:
  `Available`/`Partial` from the op registry + a shipped example; `WIP`/`Planned` from a
  documented roadmap direction; `Not-in-scope` from a stated non-goal. A node claiming
  `Available` for an op not in the registry fails CI.
- **Citation lint.** Every concept has >=1 `sources[]` entry of tier `primary`; every source
  has its required fields and a shape-valid URL. A non-blocking nightly job link-checks URLs
  (third-party link rot must not break the build).

---

## 8. Tooling: Docusaurus on GitHub Pages

**Docusaurus** (React/MDX) on **GitHub Pages**: Markdown/MDX authoring, a category/sidebar
structure matching the two-part IA, Algolia search, and first-class GH-Pages deploy.

**Layout** (docs live in the repo, versioned with the code):

```
repo/
├── docs/                              # contributor docs (design/plan/research) + this spec
│   └── documentation-structure.json   # the Learn taxonomy (companion to this doc, §8a)
└── website/                           # Docusaurus root
    ├── docusaurus.config.js           # url, baseUrl, org/project, trailingSlash, KaTeX
    ├── sidebars.js                    # the two-part IA (generated for Learn from the JSON)
    ├── content/                       # Learn JSON (one file per subject) + MDX bodies
    ├── schema/content-node.schema.json
    ├── docs/                          # ncad section (Getting Started / How-to / Reference / Explained)
    ├── src/components/                # NcadBox, Sources, Equation, CapabilityMatrix, StatusBadge
    ├── scripts/gen-reference.mjs      # JSON -> Learn MDX pages + Learn sidebar
    └── static/                        # images/renders, .nojekyll, CNAME (if custom domain)
```

**GitHub Pages config** (`deepsaia/ncad` -> `https://deepsaia.github.io/ncad/`):
`url: 'https://deepsaia.github.io'`, `baseUrl: '/ncad/'`, `organizationName: 'deepsaia'`,
`projectName: 'ncad'`, `trailingSlash: false`; `.nojekyll` in `static/`.

**KaTeX math:** enable `remark-math` + `rehype-katex` in `docusaurus.config.js` and load the
KaTeX stylesheet. Math is authored as LaTeX in MDX bodies (inline `$…$`, display `$$…$$`) and
in a node's `math[]` field for numbered display equations (rendered by `<Equation>`).

**JSON -> pages pipeline:** Learn content lives in `website/content/*.json`. A pre-build
script (`gen-reference.mjs`) validates each file against the schema and **generates the Learn
MDX pages (with embedded `<NcadBox>`/`<Sources>`) + the Learn sidebar**. Generated MDX (not
runtime rendering) is chosen for search/SEO. ncad-section pages are authored MDX + generated
op pages.

**Deployment:** GitHub Actions `deploy-docs.yml` on push to `main` (build + `actions/deploy-
pages`, permissions `pages: write` / `id-token: write`); a `test-deploy.yml` build-only check
on PRs. Versioning stays **off** pre-1.0 (revisit at first stable release); the docs describe
`main` and the status badges carry the "as of" truth.

### 8a. The JSON authoring model & node schema

The Learn taxonomy is the file **`docs/documentation-structure.json`** (the deliverable
companion to this design). One recursive node type serves all four levels; `level`
disambiguates. `concept` nodes require `body` + `ncad` + `sources` (>=1 primary);
`subject`/`topic`/`subtopic` require `title` + `summary`. A fact lives in exactly one node;
others use `see_also`. Node shape:

```jsonc
{
  "id": "cad.solid-modeling.brep.euler-operators",  // stable, dotted, unique, encodes ancestry
  "level": "concept",              // subject | topic | subtopic | concept
  "title": "Euler Operators",
  "slug": "euler-operators",
  "order": 30,
  "summary": "Topology-preserving primitives maintaining the Euler-Poincare invariant.",
  "body": "./cad/solid-modeling/brep/euler-operators.mdx",   // MDX; KaTeX math inside
  "math": [ { "id": "euler-poincare", "tex": "V - E + F = 2(s - h) + r", "caption": "..." } ],
  "figures": [ { "src": "/img/...", "alt": "...", "caption": "..." } ],
  "ncad": {                        // REQUIRED on concept nodes - the "In ncad" box
    "status": "partial",           // available | partial | wip | planned | not-in-scope
    "notes": "B-rep via OCCT; Euler ops are kernel-internal, not authored.",
    "refs": ["/ncad/reference/ops/shell"],   // cross-links INTO the ncad section
    "phase": "P2",                 // roadmap phase backing wip/planned (optional)
    "engine": null                 // delegated domains: "MuJoCo" | "CalculiX" | ...
  },
  "sources": [                     // REQUIRED on concept nodes: >=1 tier "primary"
    { "type": "textbook", "tier": "primary", "title": "Geometric Modeling",
      "authors": "Mortenson, M. E.", "year": 2006, "edition": "3rd",
      "locator": "Ch. 10", "url": "https://..." }
  ],
  "see_also": ["foundations.geometry.continuity"],   // id-refs, NOT restatement
  "tags": ["topology", "b-rep"],
  "children": [ /* nested nodes for subject/topic/subtopic */ ]
}
```

### 8b. The citation model & discipline

- **Tiers.** `primary` = canonical textbook, official docs, ratified standard, or peer-reviewed
  paper. `secondary` = reputable encyclopedic/vendor material - allowed only *in addition to* a
  primary source.
- **Types & required locators.** `textbook` (edition + chapter/§), `standard` (designation +
  clause, e.g. "IPC-2221B §6.3"), `paper` (DOI), `official-docs` (versioned page URL),
  `reference` (encyclopedic).
- **Seed anchors per subject** (the discipline, seeded - not exhaustive; authoring adds more):
  - S0/S1 CAD: Mortenson *Geometric Modeling*; Piegl & Tiller *The NURBS Book*; Shah & Mantyla
    *Parametric and Feature-Based CAD/CAM*; OpenCASCADE docs; Wikipedia B-rep (secondary).
  - S2 CAM: LinuxCNC G-code docs; NIST RS274/NGC (Kramer et al.); PyCAM.
  - S3 PCB: KiCad docs; IPC-2221 / IPC-2581 / IPC-D-356; Gerber (Ucamco RS-274X) spec.
  - S4/S5 Kinematics/MBD: Featherstone *Rigid Body Dynamics Algorithms*; Uicker et al.
    mechanism theory.
  - S6 Robotics: Lynch & Park *Modern Robotics* (free PDF + NxRLab code); Craig *Introduction
    to Robotics*; MuJoCo docs (mujoco.readthedocs.io) + google-deepmind/mujoco; ROS URDF spec.
  - S7 CAE: Zienkiewicz & Taylor *The FEM*; Hughes; Bathe; CalculiX docs; Elmer docs; EPANET
    manual; OpenModelica docs.
  - S8 Interchange: ISO 10303 (STEP incl. AP242); glTF spec; IFC (buildingSMART); each format's
    canonical spec.

---

## 9. Authoring conventions

- **One concept, one home.** A concept is explained in exactly one Learn node; everything else
  cross-links. Shared math -> Foundations; shared formats -> Interchange.
- **Register per mode.** Neutral/academic in Learn; imperative in ncad How-to; terse in ncad
  Reference; rationale in ncad Explained.
- **No product names** in Learn (principle #2). Describe the capability, not a vendor's menu.
- **Every limit documented** (ncad Reference "Limits & notes"), in the code's own words.
- **Examples build** (§7). Never show HOCON that isn't validated.
- **Depth is independent of status** (principle #8). Teach `Planned`/`Not-in-scope` concepts
  fully.

---

## 10. Build order (thin slices; each ships a deployable, honest site)

1. **Scaffold:** Docusaurus + GH-Pages workflow + KaTeX + the JSON pipeline
   (`gen-reference.mjs`) + `content-node.schema.json` + the `NcadBox`/`Sources`/`Equation`/
   `CapabilityMatrix` components, with one sample subject. Empty-but-live.
2. **ncad Reference** (accuracy-critical): schema page + the 15 op pages from the §5 template,
   generated against code; the Capability Matrix; the accuracy tests (§7).
3. **Learn: Foundations + CAD** (highest reuse; ncad's strongest area, so most `Available` "In
   ncad" boxes).
4. **Learn: Kinematics / MBD / Robotics** (maps to Phases 5/6/14/17; mix of `Available` /
   `WIP` / `Planned`, with the MuJoCo/Ondsel engine notes).
5. **Learn: CAM / PCB / CAE** (mostly `Planned` / `Not-in-scope`, but full-depth teaching +
   delegated-engine notes).
6. **Learn: Interchange**; then **ncad Getting Started / How-to / Explained**; then polish
   (search, cross-links, renders, About/versioning pages).

---

## Summary

v2 is a **two-part site**: **Learn**, a product-neutral, professional-depth course across nine
subjects (Foundations, CAD, CAM, PCB, Kinematics, MBD, Robotics/MuJoCo, CAE, Interchange), each
concept sourced and carrying an honest "In ncad" status box; and **ncad**, a separate
exhaustive manual (Diataxis). Learn content is **data** (a JSON taxonomy + MDX bodies, in
`docs/documentation-structure.json`), math is **KaTeX**, and accuracy is a **tested property**
(status validated against the op registry, examples must build). The defining
discipline is unchanged from v1 and strengthened: **teach the whole field honestly; never
claim a capability ncad lacks.**
