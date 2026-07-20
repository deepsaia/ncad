Beyond arithmetic, parameter expressions can call **registered functions**, named, pure operations
the expression evaluator exposes: trigonometry (`sin`, `cos`, `tan`), `sqrt`, `min`/`max`,
`abs`, `floor`/`ceil`, and domain helpers. A dimension can then read
`${radius * sin(angle)}` or `${max(wall, 2.0)}`.

## Why a registry, not arbitrary code

Functions are drawn from a **fixed registry** of pure, deterministic operations, not arbitrary
evaluated code. This matters for two reasons:

- **Determinism.** Every function is a pure mathematical mapping, so the same document always
  resolves to the same numbers, preserving the rebuild guarantee. A function with hidden state or
  side effects would break reproducibility.
- **Safety.** A closed registry means an authored document (which may come from a human, an agent,
  or a generator) cannot execute unrestricted code through an expression, only the sanctioned
  functions are callable.

Registered functions extend the expressiveness of the parametric layer, computed chamfers,
trigonometric placements, clamped clearances, while keeping expressions a safe, deterministic,
declarative language rather than a general-purpose scripting escape hatch.
