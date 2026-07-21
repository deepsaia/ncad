**Legged robots** locomote through intermittent contacts at discrete footholds rather than continuous rolling. This lets them cross gaps, climb steps, and traverse rough or cluttered terrain that defeats wheels, at the cost of mechanical and control complexity: legs are heavy, articulated, and must alternately support the body and swing forward. Configurations range from **bipeds** and **humanoids** (two legs, an anthropomorphic torso and arms) through **quadrupeds** to **hexapods**, with stability generally easier as the number of legs rises.

## Static versus dynamic stability

A legged machine is **statically stable** when its center of mass projects vertically inside the **support polygon** (the convex hull of the ground contacts); it can then halt at any instant without falling. Statically stable gaits keep enough feet down that this always holds, which is slow but robust. Faster **dynamic** gaits (running, and most bipedal walking) spend time statically unstable, relying on momentum and the timing of future footfalls to remain upright, so balance becomes a feedback problem rather than a geometric guarantee.

## The Zero Moment Point and reduced models

For gaits with flat-footed contact the key criterion is the **Zero Moment Point (ZMP)**: the point on the ground where the net horizontal moment of inertial and gravitational forces vanishes. Contact stays sustainable (the foot does not roll about an edge) only while the ZMP lies strictly inside the foot support region. Under the **Linear Inverted Pendulum Model**, which lumps the body as a point mass at constant height \(z_c\), the ZMP reduces to a simple relation between the mass position and its horizontal acceleration:

\[ x_{\text{zmp}} = x - \frac{z_c}{g}\,\ddot{x}. \]

This linear form lets a controller plan a center-of-mass trajectory whose ZMP tracks a reference walking through the footprints, which is the backbone of many walking-pattern generators. Because bipeds are underactuated (no actuator directly commands the body's fall about the foot edge), they require continuous balance control, and dynamic walkers are often analyzed via the closely related capture point or divergent-component-of-motion, which quantifies where a foot must be placed to arrest a fall.

## Gaits and energetics

A **gait** is the cyclic pattern of lifting and placing feet; it is characterized by duty factor (fraction of the cycle each foot is on the ground) and phase relationships between legs. Well-tuned dynamic gaits can approach the efficiency of passive-dynamic walkers, which descend a shallow slope with no actuation at all, showing that some of a leg's motion can be powered by gravity and elastic recoil rather than continuous actuation. Legged robots therefore balance three coupled objectives: terrain capability, energetic economy, and the robustness of balance under disturbance.
