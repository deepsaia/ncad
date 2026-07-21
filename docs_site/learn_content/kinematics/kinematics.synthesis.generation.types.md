Kinematic synthesis is the inverse of kinematic analysis: instead of computing what a given mechanism does, it designs the mechanism (its link lengths, pivot locations, and joint types) so that it performs a prescribed task. For linkages the tasks fall into three classical categories, and naming the category correctly is the first design decision because it fixes which quantities are constrained and how many free parameters remain.

**Function generation** coordinates an input variable with an output variable, so that output angle (or slide) tracks a desired function of the input angle, \( \psi = f(\phi) \). The mechanism becomes a mechanical computer or a coordinating link between two shafts. **Path generation** requires a single traced point on a moving link to pass through a set of prescribed points in the plane; if the timing (which input angle corresponds to which point) is also specified it is *path generation with prescribed timing*, otherwise the timing is free. **Motion generation** (also called rigid-body guidance) prescribes not just a point but the full pose of a moving body: a set of positions **and** orientations that a coupler must be guided through, as when a bucket or a door must reach several placements at a specified attitude.

## The governing algebra

For the planar four-bar the workhorse relation is Freudenstein's equation, which links the input angle \( \theta_2 \) and output angle \( \theta_4 \) through three dimensionless ratios of the frame, input, coupler, and output lengths \( r_1, r_2, r_3, r_4 \):

\[ K_1\cos\theta_4 - K_2\cos\theta_2 + K_3 = \cos(\theta_2 - \theta_4), \]

\[ K_1=\frac{r_1}{r_2},\quad K_2=\frac{r_1}{r_4},\quad K_3=\frac{r_2^{2}-r_3^{2}+r_4^{2}+r_1^{2}}{2\,r_2 r_4}. \]

Because the equation is linear in \( K_1, K_2, K_3 \), specifying three input/output angle pairs (three *precision points*) gives three linear equations that solve directly for the ratios, from which the link lengths follow. This is the essence of *precision-point synthesis*: the mechanism is forced to match the target exactly at a finite number of points, and it interpolates elsewhere.

## Precision points, structural error, and point placement

The number of precision points a task can enforce is bounded by the number of independent design parameters. A four-bar function generator can satisfy up to five precision points, path generation up to nine, and motion generation up to five prescribed poses. Between the precision points the mechanism deviates from the ideal task; this deviation is the *structural error*. It is not eliminated by choosing more points blindly, and it depends strongly on *where* the points are placed. Spacing them by the Chebyshev rule minimizes the peak structural error over the range \([x_0, x_f]\):

\[ x_j = \tfrac12(x_0 + x_f) - \tfrac12(x_f - x_0)\cos\frac{(2j-1)\pi}{2n},\quad j = 1,\dots,n. \]

Motion generation has its own geometric theory: given up to five prescribed coupler poses, the admissible fixed pivots (center points) and moving pivots (circle points) lie on two cubic curves, the Burmester center-point and circle-point curves. Four poses leave a one-parameter family of solutions along those curves; five poses reduce the set to a finite number of Burmester points. When exact precision-point synthesis cannot meet enough conditions, or when the resulting linkage is defective (branch, order, or circuit faults, or a poor transmission angle), designers switch to *approximate* or *optimization-based* synthesis that minimizes error over the whole cycle rather than nailing isolated points.
