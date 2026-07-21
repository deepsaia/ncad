A **kinematic chain** is an assembly of links connected by joints. Its topology can be drawn as a graph in which links are nodes and joints are edges, and the presence or absence of cycles in that graph splits all mechanisms into two fundamental families. An **open (serial) chain** has a tree topology with no closed loops: links are strung one after another, one end anchored to ground and the other free, as in a robot arm or an excavator boom. A **closed chain** contains at least one loop, so a sequence of links and joints returns to its starting link, as in the four-bar linkage or a parallel platform.

The distinction reshapes the DOF calculation. For an open chain there are no loop-closure constraints, so its mobility is simply the sum of the joint freedoms,

\[
M_{\text{open}} = \sum_{i=1}^{j} f_i ,
\]

and its forward kinematics is a straightforward chained product of joint transforms. A closed chain must additionally satisfy **loop-closure equations**: traversing any independent loop and multiplying the successive joint and link transforms must return the identity,

\[
\prod_{k \in \text{loop}} T_k(\mathbf{q}) = I .
\]

These equations couple the joint variables and remove freedoms, which is exactly the constraint bookkeeping the Kutzbach and Grubler criteria perform. Open chains trade this constraint-solving simplicity for lower stiffness and accumulating positional error, while closed chains gain rigidity and load sharing at the cost of a smaller reachable workspace and the need to solve coupled nonlinear constraints.

## Planar, spherical, and spatial chains

Beyond open versus closed, chains are classified by the *geometry of their joint axes*, which determines the manifold their points can move on:

- **Planar chains** confine every point to motion in a set of parallel planes. This requires all revolute axes to be mutually parallel (and perpendicular to the plane of motion) and all prismatic directions to lie in that plane. The four-bar and slider-crank are the archetypes.
- **Spherical chains** confine every point to move on concentric spheres about a single common center, which requires **all joint axes to intersect at one point**. The spherical four-bar and many wrist mechanisms are examples; the concurrent-axis condition is what makes a wrist orient a tool without translating its center.
- **Spatial chains** have general axis orientations, neither all parallel nor all concurrent, and their points trace fully three-dimensional paths. They are the most capable and the most demanding to analyze, and they are governed by the six-DOF (\(d = 6\)) form of the mobility criterion.

This two-axis classification, topology (open/closed) crossed with axis geometry (planar/spherical/spatial), frames essentially every mechanism decision. It sets which mobility formula applies (\(d = 3\) for planar and spherical loops, \(d = 6\) for spatial ones), whether forward kinematics is an explicit product or an implicit constraint solve, and how workspace, stiffness, and singularity behavior will trade off. Recognizing a mechanism's family early tells the analyst which mathematical machinery, planar pole geometry, spherical trigonometry, or full spatial screw theory, is the right tool, before any equations are written.
