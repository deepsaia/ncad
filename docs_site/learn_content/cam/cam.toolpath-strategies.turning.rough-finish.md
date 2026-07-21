Turning strategies for roughing, finishing, and facing are the lathe counterparts of the milling toolpaths, but the kinematics are inverted: the **workpiece rotates** about the spindle axis and a single-point tool moves in the tool plane, typically the two axes \(Z\) (along the axis) and \(X\) (radially, the diameter). The cutting speed is set by the rotating part, and the tool sweeps profiles to reduce a cylindrical or bar blank toward the target contour.

**Roughing** removes the bulk of the stock in a series of parallel passes. The most common pattern is a set of straight cuts parallel to the spindle axis (longitudinal turning), each stepping in by a depth of cut \(a_p\) until the profile is approached, leaving a uniform finish allowance for the finishing pass. Alternatives run passes parallel to the contour (profile roughing) or radially (for face-dominant shapes). The material removal rate for a turning cut is

\[ \text{MRR} = v_c \, f \, a_p, \qquad v_c = \pi D N, \]

where \(v_c\) is cutting speed, \(f\) is feed per revolution, \(a_p\) is depth of cut, \(D\) is the instantaneous diameter, and \(N\) is spindle speed. Note that because \(v_c\) depends on the current diameter, a **constant-surface-speed** control raises \(N\) as the tool cuts toward the axis to hold \(v_c\) fixed, which keeps finish and tool load uniform across the radius.

**Finishing** takes a single (or few) light pass along the final contour to meet dimensional tolerance and surface finish. The dominant driver of turned surface roughness is the interaction of the feed \(f\) with the tool **nose radius** \(r_\varepsilon\); the theoretical peak-to-valley roughness left by the nose is

\[ R_{\text{th}} \approx \frac{f^2}{8\,r_\varepsilon}, \]

so a larger nose radius or a finer feed gives a smoother finish (at the cost of higher radial force and possible chatter with too large a nose). This closed-form relation is why feed and nose radius, not spindle speed, are the primary finish parameters on a lathe.

## Facing

**Facing** cuts perpendicular to the spindle axis to produce a flat end face, feeding the tool radially in \(X\) at a fixed \(Z\). Because the diameter passes through zero at the center, constant surface speed cannot be maintained all the way in (spindle speed would diverge), so the control clamps to a maximum \(N\) near the center and a small witness or dwell may remain at the axis. Facing establishes the length datum and a clean reference face for subsequent operations. Together, rough-finish-face form the backbone of turned-part programming: rough to near-net leaving stock, face to length and datum, then finish to size, with each stage governed by the speed, feed, depth, and nose-radius relations above.
