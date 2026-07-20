A **coupled joint** ties the motion of one joint to another by a relationship, so driving one moves
the other according to a law. The classic couplings are **gear** (two revolutes at a fixed speed
ratio), **belt/pulley** (same, same sign), **rack-and-pinion** (a revolute driving a slider),
**screw** (rotation coupled to translation by a pitch), and higher pairs like **cam** and **slot**
(a profile-defined relation).

## Ratio, sign, and enforcement

A coupling declares which joints it relates and the law: a gear ratio (with sign, external meshes
reverse direction), a rack's travel-per-radian, a screw's pitch, or a cam/geneva profile. It is a
**derived** relationship, not an extra rigid constraint: one joint (the primary) is driven, and the
coupling computes the secondary's motion from it.

## Where couplings live

Couplings are declared on the assembly but **enforced during motion**: the static assembly solve
places the parts, and when a driver sweeps the primary joint, the coupling prescribes the secondary
joint's value at each step (a gear turns its mate, a cam lifts its follower). Because a general
solver has no built-in gear/cam constraint, each coupling is realized as a prescribed secondary
motion co-solved with the driver. This is how a mechanism, gear train, cam-follower, rack-pinion,
intermittent Geneva, animates correctly from a single input.
