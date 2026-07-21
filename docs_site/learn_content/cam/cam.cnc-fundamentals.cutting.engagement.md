**Tool engagement** describes how much of the tool is buried in the material, and it is resolved into two orthogonal depths plus an angle. The **radial depth of cut** \(a_e\) (the *stepover*) is how far the tool steps sideways between passes, measured across the tool's radius; the **axial depth of cut** \(a_p\) (the *stepdown*) is how deep it cuts along the spindle axis per level. Together with feed they set the material-removal rate, the cutting force, and, indirectly, tool life and stability.

The **material-removal rate** (MRR) in milling is simply the cross-section of the cut times the feed velocity,

\[ \text{MRR} = a_e\, a_p\, v_f , \]

so any two of \((a_e, a_p, v_f)\) trade against the third at constant throughput. This is the lever behind two opposing roughing philosophies. **Traditional roughing** uses a large radial engagement (up to full-slot \(a_e = D\)) and a modest axial depth. **High-efficiency / dynamic roughing** inverts this: a small radial engagement with a large axial depth (often the full flute length), run at high feed. The latter spreads wear along the whole flute rather than a narrow band, keeps the tool cooler, and exploits the fact that light \(a_e\) permits high feed once chip thinning is accounted for.

The governing quantity that ties engagement to tool health is the **engagement (or wrap) angle** \(\theta\), the arc of the tool in contact with material. For radial engagement \(a_e\) on a tool of diameter \(D\),

\[ \cos\theta = 1 - \frac{2 a_e}{D}, \]

ranging from a thin sliver at light stepover to \(180^\circ\) in a full slot. Sharp increases in engagement angle, which happen precisely at inside corners where a conventional offset path suddenly wraps the tool, spike the cutting force and cause chatter or breakage. This is why **constant-engagement** strategies exist: they morph the toolpath (trochoidal loops, adaptive clearing) so \(\theta\) stays near a set value everywhere, trading a longer path for a controlled, predictable load.

Engagement also sets finish. In finishing, the stepover on a curved or contoured surface leaves a residual **scallop** whose cusp height for a ball tool of radius \(R\) and stepover \(s\) on a locally flat region is

\[ h \approx \frac{s^{2}}{8R}. \]

So halving the stepover quarters the cusp, at double the passes. Finally, engagement couples back to chip load: at light radial engagement the average chip thins (radial chip thinning), so feed must be raised to keep the edge cutting rather than rubbing. A coherent operation sets \(a_e\) and \(a_p\) first for the intended strategy and stability, then chooses feed to deliver the target chip thickness at the resulting engagement.
