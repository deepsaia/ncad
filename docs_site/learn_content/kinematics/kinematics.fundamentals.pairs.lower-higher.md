A **kinematic pair** is the connection between two links that permits some relative motions while blocking others. Following Reuleaux's classical scheme, pairs are divided by the *nature of their contact* into **lower pairs**, which mate over a shared surface (area contact), and **higher pairs**, which touch along a line or at a point. This distinction is not merely descriptive: it governs how load is transmitted, how contact stress develops, and how the constraint is modeled analytically.

There are exactly **six lower pairs**, because there are only six ways two rigid surfaces can remain in continuous area contact while sliding on one another. Each corresponds to a subgroup of the rigid-motion group \(SE(3)\):

| Lower pair | Symbol | Relative freedoms \(f\) | Motion permitted |
|---|---|---|---|
| Revolute | R | 1 | rotation about one axis |
| Prismatic | P | 1 | translation along one axis |
| Helical (screw) | H | 1 | coupled rotation + translation (fixed pitch) |
| Cylindrical | C | 2 | independent rotation and translation about one axis |
| Spherical | S | 3 | rotation about a point (ball joint) |
| Planar (flat) | E | 3 | two translations + one rotation in a plane |

**Higher pairs** encompass everything else: meshing gear teeth, a cam pushing a follower, a wheel rolling on a rail, a ball rolling in a bearing race. Because their contact is confined to a line or point, higher pairs typically allow a combination of rolling and sliding and are described not by a fixed subgroup but by a **contact constraint** that depends on the local surface geometry and can change as the point of contact migrates.

## Why the distinction is more than taxonomy

The contact type dictates the mechanics. A lower pair spreads its transmitted force over a finite bearing area, so contact pressure stays low, wear is gradual, and lubrication films are easy to maintain, which is why virtually all robot and machine joints are lower pairs. A higher pair concentrates the same force onto a line or point, producing intense **Hertzian contact stress** that scales unfavorably with load; for point contact the peak pressure grows roughly as \(p_{\max} \propto P^{1/3}\) with normal force \(P\), and the contact patch is vanishingly small. This is why cams, gears, and rolling-element bearings demand hardened, precisely finished surfaces and careful lubrication, and why they are the usual sites of pitting and fatigue failure.

For kinematic modeling, lower pairs are attractive because each maps to a clean, geometry-independent joint constraint with a constant freedom count \(f\), feeding directly into the mobility formulas. Higher pairs earn their place when a lower-pair chain cannot produce the required motion profile, such as an arbitrary displacement-versus-input curve from a cam, or the constant-velocity-ratio conjugate action of gear teeth. A common analytical trick is to replace a higher pair with a *kinematically equivalent* chain of lower pairs and extra links for the purpose of instantaneous mobility and velocity analysis, capturing the same freedoms while keeping the model uniform. Choosing lower versus higher pairs is therefore a coupled kinematic and tribological decision: it sets both what motions are possible and how long the joint will survive under load.
