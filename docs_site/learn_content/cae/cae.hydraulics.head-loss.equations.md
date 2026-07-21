Pressurized-pipe hydraulics rests on two conservation laws applied to steady, essentially incompressible flow. **Mass conservation** (continuity) states that for a control volume with no storage the volumetric inflow equals the outflow, so for a single conduit \( A_1 V_1 = A_2 V_2 \) and at any junction \( \sum Q_{\text{in}} = \sum Q_{\text{out}} \). **Energy conservation** is expressed as the extended Bernoulli (energy) equation between an upstream station 1 and a downstream station 2, written in units of head (energy per unit weight):

\[ \frac{p_1}{\gamma} + z_1 + \frac{V_1^2}{2g} + h_p = \frac{p_2}{\gamma} + z_2 + \frac{V_2^2}{2g} + h_t + h_L \]

Here \( p/\gamma \) is pressure head, \( z \) elevation head, \( V^2/2g \) velocity head, \( h_p \) and \( h_t \) the head added by a pump and extracted by a turbine, and \( h_L \) the total head loss. Every hydraulic analysis is ultimately a bookkeeping of these terms; the entire difficulty is estimating \( h_L \), which is dissipated irreversibly as heat by wall friction and by fittings.

## Darcy-Weisbach

The Darcy-Weisbach equation is the dimensionally rigorous, physics-based expression for **frictional (major) head loss** in a straight run of pipe:

\[ h_f = f \, \frac{L}{D} \, \frac{V^2}{2g} \]

where \( f \) is the dimensionless Darcy friction factor, \( L \) the length, \( D \) the inside diameter, and \( V \) the mean velocity. It applies to any Newtonian fluid, any temperature, and laminar or turbulent flow, which is why it is the reference method in fluid mechanics. The friction factor is a function of the Reynolds number \( Re = \rho V D / \mu \) and the relative roughness \( \varepsilon/D \). In laminar flow \( (Re < \sim 2300) \) it is exact: \( f = 64/Re \). In turbulent flow it is given implicitly by the Colebrook-White equation,

\[ \frac{1}{\sqrt{f}} = -2\log_{10}\!\left( \frac{\varepsilon/D}{3.7} + \frac{2.51}{Re\,\sqrt{f}} \right), \]

which is what the Moody chart plots graphically and which numerous explicit approximations (Swamee-Jain, Haaland) fit to avoid iteration. **Minor (local) losses** at bends, valves, contractions, and fittings are added as \( h_m = K\,V^2/2g \), with tabulated loss coefficients \( K \), or as an equivalent added length.

## Hazen-Williams

The Hazen-Williams formula is an **empirical** correlation developed specifically for water flowing turbulently in the temperature range of ordinary municipal systems. In SI form the head loss over a length \( L \) is

\[ h_f = \frac{10.67\, L\, Q^{1.852}}{C^{1.852}\, D^{4.87}}, \]

with \( Q \) in m³/s, \( D \) and \( L \) in metres, and \( C \) a roughness coefficient (roughly 130-150 for new plastic or lined pipe, dropping toward 100 or below for old tuberculated metal). Its appeal is that \( C \) depends only on pipe material and condition, not on velocity or fluid properties, so no Reynolds number or iterative friction factor is needed. That convenience is also its limitation: because the exponents and constant are curve-fits, the formula is only valid for water near 15-20 °C and degrades badly outside typical distribution velocities or for other fluids. Engineering practice therefore prefers Darcy-Weisbach for rigor and wide validity, and reserves Hazen-Williams for rapid water-distribution sizing where its assumptions hold.

The non-integer exponent on \( Q \) matters downstream: any pipe head loss can be written compactly as \( h_L = r\,Q^{n} \), where the resistance \( r \) folds in geometry and roughness. Darcy-Weisbach gives \( n = 2 \) (loss varies with the square of flow) while Hazen-Williams gives \( n = 1.852 \). This \( h_L = r Q^n \) form is the building block that network solvers assemble into loop and node equations.
