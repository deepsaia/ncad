**Parameters** are named values a document defines once and reuses everywhere through
**references**. Instead of scattering the number `60` across a dozen dimensions, an author declares
`width = 60` and writes `${width}` wherever it applies. Change the parameter and every reference
updates on rebuild.

## Expressions

A reference is not limited to a bare value; it can be an **expression** combining parameters and
arithmetic: `${width}`, `${width / 2}`, `${2 * hole_spacing + margin}`. Expressions are resolved
*before* the geometry builds, each `${...}` is evaluated to a concrete number and substituted, so
downstream schema validation and feature ops see plain values.

## Why parameters make a family

Parameters turn a single document into a **design family**: one set of named inputs generates a
whole range of parts. A parametric bracket with `width`, `height`, and `thickness` parameters
becomes any bracket in that family by changing three numbers. This is the core of the
document-as-truth model, the design intent lives in named, referenceable inputs, and the geometry is
a deterministic function of them.

References also express *relationships*: a boss diameter defined as `${shaft_dia + 4}` stays 4 mm
larger than the shaft no matter how the shaft changes. That relational intent is exactly what a
parametric model exists to preserve.
