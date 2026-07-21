The cutting curves are only part of a toolpath; they must be connected to rapid moves and to one another by carefully shaped transition geometry. **Lead-in/out** brings the cutter into and out of engagement smoothly; **ramping and helical entry** get the tool down to depth without plunging straight into material; and **linking moves** reposition the tool between disjoint segments while staying clear of the part. These moves do not remove design-critical material, but they govern surface finish, tool life, and the majority of non-productive cycle time.

## Lead-in/out geometry

Entering a profile by driving straight at the wall leaves a witness (dwell) mark and shock-loads the tool. A **tangential arc lead** instead meets the contour tangentially, so the feed direction is continuous (\(G^1\)) at the junction and cutter load ramps up gradually. For an arc lead-in of radius \(R\) blending onto the profile, the arc's endpoint tangent equals the profile's start tangent by construction; a straight tangential lead is the degenerate large-radius case. Leads are also where cutter-radius compensation is switched on and off, since the control needs a compensation-free move to establish the offset before the tool reaches the finished surface.

<svg viewBox="0 0 240 120" width="240" height="120" stroke="currentColor" fill="none" stroke-width="2">
  <path d="M20 100 L220 100" />
  <path d="M120 100 A 40 40 0 0 1 160 60" stroke-dasharray="5 4" />
  <circle cx="120" cy="100" r="3" fill="currentColor" />
  <text x="126" y="94" font-size="11" stroke="none" fill="currentColor">tangent point</text>
  <text x="150" y="40" font-size="11" stroke="none" fill="currentColor">arc lead-in (radius R)</text>
</svg>

## Ramping and helical entry

Most end mills cut poorly straight down because the tool center has zero surface speed and chips cannot evacuate. Instead the tool descends while moving laterally. A linear **ramp** at angle \(\alpha\) that must gain axial depth \(d\) requires horizontal travel

\[ L = \frac{d}{\tan\alpha}, \]

and a **helical** entry of pitch \(p\) on a circle of radius \(\rho\) descends along a helix whose lead angle is

\[ \theta = \arctan\!\left(\frac{p}{2\pi\rho}\right). \]

Ramp angle and helix pitch are chosen to keep axial engagement within the tool's plunge capability while still evacuating chips.

## Linking and travel optimization

Linking chooses how to get from the end of one cutting move to the start of the next: a direct link at cutting or clearance height when the straight path is provably collision-free, a link that follows the surface to avoid a full retract, or a retract to a safe clearance plane when neither is safe. Because air-cutting can dominate cycle time on parts with many pockets or islands, the order in which regions are visited is a travel-minimization problem close to a traveling-salesman tour, and the choice between clearance distance and full retract distance trades safety margin against time. The governing constraints are the same collision checks used for the cutting moves, applied now to the whole non-cutting excursion.
