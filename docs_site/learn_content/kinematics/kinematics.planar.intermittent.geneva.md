The Geneva mechanism (also called the Maltese cross) is the classic device for converting continuous rotation of a driver into precise **intermittent** indexing of a driven wheel, alternating between periods of motion and stationary **dwell**. It is widely used wherever a part must be advanced by an exact step and then held still, such as film advance, rotary indexing tables, assembly transfer stations, and older watch and instrument mechanisms.

## How it works

The driving member carries a single **pin** (roller) on a crank of radius \(a\), plus a raised circular **locking disk**. The driven Geneva wheel has \(n\) radial **slots** and matching concave locking arcs. During most of the driver's revolution the pin is disengaged and the locking disk sits in a concave arc, positively holding the Geneva wheel stationary (the dwell). Once per revolution the pin enters a slot, sweeps the wheel forward by one slot pitch, and exits, after which the locking disk again captures the wheel. For an *external* Geneva the two wheels turn in opposite senses; each driver revolution advances the driven wheel by one increment of

\[ \Delta = \frac{2\pi}{n}. \]

## The tangency (smooth-entry) condition

The defining kinematic requirement is that the pin enter and leave each slot **without shock**. The pin moves on a circle of radius \(a\) about the driver center, so its velocity is perpendicular to the crank. For that velocity to be directed *along* the slot at the instant of engagement, the crank must be perpendicular to the slot centerline at that moment. Geometrically this makes the triangle formed by the driver center \(O_1\), driven center \(O_2\), and pin a right triangle with the right angle at the pin, giving the sizing relation

\[ a = c\,\sin\!\left(\frac{\pi}{n}\right), \]

where \(c\) is the center distance. As a consequence the driver rotates through an angle of \(\pi + 2\pi/n\) during indexing and dwells for the remainder of the turn, so more slots give a smaller index angle but a longer dwell fraction. The instantaneous angular displacement of the Geneva wheel while the pin is engaged is

\[ \psi(\alpha) = \arctan\!\left(\frac{\sin\alpha}{\,c/a - \cos\alpha\,}\right), \]

with \(\alpha\) the driver crank angle measured from the line of centers.

The great merit of the Geneva is that it combines indexing with **positive self-locking**: the locking disk mechanically prevents the driven wheel from creeping or overrunning during dwell, without a separate brake. Its limitation is dynamic: although velocity is zero at entry and exit, the *acceleration* is finite and non-zero there and peaks sharply inside the stroke, so at high indexing rates the inertia loads and the resulting jerk restrict speed. Fewer slots aggravate the peak acceleration, so very fine indexing (large \(n\)) runs more smoothly, while for demanding high-speed indexing designers turn to cam-driven indexers with fully controlled acceleration profiles.
