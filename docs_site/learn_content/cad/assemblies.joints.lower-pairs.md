A **joint** is a named kinematic relationship between two parts that permits specific motion. The
classical **lower pairs** are the six joints with surface contact, each leaving a defined set of
degrees of freedom:

| Joint | DoF | Motion |
|---|---|---|
| Fixed | 0 | rigidly locked |
| Revolute | 1 | rotation about an axis (a hinge) |
| Prismatic / slider | 1 | translation along an axis |
| Cylindrical | 2 | rotate + slide on one axis |
| Planar | 3 | slide in a plane + rotate about its normal |
| Spherical / ball | 3 | rotation about a point |

<figure markdown="span">
<svg viewBox="0 0 300 90" width="300" role="img" aria-label="Revolute and prismatic joints" xmlns="http://www.w3.org/2000/svg" fill="none" stroke="currentColor" stroke-width="2">
  <circle cx="55" cy="45" r="22"/><circle cx="55" cy="45" r="4" fill="currentColor"/>
  <path d="M 55 45 A 22 22 0 0 1 77 45" stroke-dasharray="3 3"/>
  <text x="35" y="85" fill="currentColor" stroke="none" font-size="11">revolute (1 DoF)</text>
  <rect x="190" y="35" width="80" height="20"/><line x1="180" y1="45" x2="285" y2="45" stroke-dasharray="4 3"/>
  <text x="185" y="85" fill="currentColor" stroke="none" font-size="11">slider (1 DoF)</text>
</svg>
<figcaption>A revolute joint permits one rotation; a slider permits one translation.</figcaption>
</figure>

## Joints versus mates

A joint is a higher-level statement than a set of mates: it directly declares "these parts form a
hinge" with a defined axis and freedom, and it lowers to the primitive constraints (plus a recorded
free-axis signature) that leave exactly that DoF. Joints are what motion drives, a revolute becomes
a rotating input, a slider a linear one, and what a mechanism's mobility is computed from. Point-on-
line and slot joints extend the set for higher-pair contacts. A valued joint pins its freedom to a
number (a fixed angle); a free joint leaves it for motion or the solver.
