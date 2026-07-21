**Speed** and **feed** are the two primary cutting parameters, and they are chosen from the *material's* physics, not the machine's dials. The starting point is the **cutting speed** \(v_c\), the tangential surface velocity between the cutting edge and the workpiece. It is a property of the tool material, workpiece material, and coolant; each combination has a recommended \(v_c\) range that keeps the cutting-zone temperature in a regime where the tool wears slowly. Speed does not directly become an RPM until the tool diameter is known.

The conversion from surface speed to **spindle speed** \(n\) is purely geometric. A point on the tool periphery of diameter \(D\) travels \(\pi D\) per revolution, so

\[ v_c = \pi D\, n \quad\Longrightarrow\quad n = \frac{v_c}{\pi D} = \frac{1000\, v_c}{\pi D}, \]

where the right-hand form gives \(n\) in rev/min when \(v_c\) is in m/min and \(D\) in mm. The immediate consequence is that a small tool must spin far faster than a large one to reach the same surface speed, and a ball nose running near its tip has effectively zero surface speed there, which is why tilting the tool or leaving finish stock for a smaller effective diameter matters.

The **feed rate** \(v_f\), the linear velocity of the tool along the path, is built up from the per-tooth chip load. With feed per tooth \(f_z\) and \(z\) flutes,

\[ v_f = f_z\, z\, n , \]

so feed rate rises with both spindle speed and tooth count. The quantity that actually governs cutting mechanics is \(f_z\) (the material removed per edge per revolution); \(v_f\) is merely how that intention is expressed to the controller. Hole-making and threading instead use **feed per revolution** \(f = f_z z\), and tapping fixes \(f\) to the thread pitch.

The reason \(v_c\) cannot simply be maximized is captured by **tool life**. Taylor's equation relates cutting speed to the time \(T\) the edge lasts,

\[ v_c\, T^{\,n} = C, \]

with exponent \(n\) and constant \(C\) empirical for the tool-work pair. Because \(n\) is small (often 0.1 to 0.3 for typical tooling), tool life is *very* sensitive to speed: modest overspeed collapses edge life, while running below the sweet spot wastes throughput. Feeds and speeds selection is therefore a constrained optimization: pick \(v_c\) for acceptable tool life, convert to \(n\) via diameter, then choose \(f_z\) for the desired chip load subject to spindle-power, torque, deflection, and finish limits, and finally express the result as \(n\) and \(v_f\) for the program.
