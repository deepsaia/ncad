**Revolve** sweeps a planar profile around an axis to create a solid of revolution, the feature for
anything turned: shafts, washers, bottles, pulleys, bosses. The profile is revolved through an angle
(a full $360^\circ$ or a partial sweep) about a sketched or datum axis lying in the profile's plane.

<figure markdown="span">
<svg viewBox="0 0 300 150" width="320" role="img" aria-label="A profile revolved about an axis" xmlns="http://www.w3.org/2000/svg" fill="none" stroke="currentColor" stroke-width="2">
  <line x1="150" y1="15" x2="150" y2="135" stroke-dasharray="6 4"/>
  <text x="156" y="26" fill="currentColor" stroke="none" font-size="11">axis</text>
  <path d="M 60 55 L 110 55 L 110 95 L 60 95 Z"/>
  <ellipse cx="150" cy="75" rx="90" ry="22" opacity="0.4"/>
  <path d="M 150 53 A 90 22 0 0 0 60 55" opacity="0.6"/>
</svg>
<figcaption>The profile (left) revolved about the axis generates a solid of revolution.</figcaption>
</figure>

## Profile and axis

The revolved face is named by the feature's profile reference and returns a standalone solid, which
a boolean union recombines with the running body if it is meant to add to an existing part. The axis
must lie in the sketch plane and must not cross the profile (that would produce a self-intersecting
result). A partial revolve leaves planar end faces; a removing revolve cuts a **groove**.

Revolve and extrude are the two workhorse sketched features: extrude for prismatic shapes, revolve
for axisymmetric ones. Many parts combine both, a revolved hub with extruded arms.
