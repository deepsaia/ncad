A **universal joint** (Cardan or Hooke joint) transmits rotary motion between two shafts whose axes intersect at an angle \(\beta\). Two yokes are connected by a rigid cross (spider) with two mutually perpendicular pin axes; each yoke pivots on one pin axis. Kinematically the device is a **spherical four-bar linkage**: all four revolute axes pass through a single point, the center of the cross, so the mechanism is analyzed with spherical trigonometry. Its virtue is simplicity and the ability to accommodate large, varying bend angles; its defining limitation is that it does *not* transmit rotation at a constant speed.

## The Cardan speed fluctuation

With the input shaft turned through \(\theta_1\) and the output through \(\theta_2\), the geometry of the cross forces

\[ \tan\theta_1 = \cos\beta \, \tan\theta_2 . \]

Differentiating gives the instantaneous velocity ratio as a function of input position:

\[ \frac{\omega_2}{\omega_1} = \frac{\cos\beta}{\,1-\sin^2\beta\,\cos^2\theta_1\,}. \]

The ratio oscillates between \(\cos\beta\) and \(1/\cos\beta\), completing **two full cycles per input revolution**. Even though the shafts share the same *average* speed, the output leads and lags the input within each turn. This cyclic non-uniformity injects a second-order torsional excitation that grows rapidly with \(\beta\): at \(\beta = 30^\circ\) the speed already swings by roughly \(\pm 15\%\). The result is vibration, noise, accelerated wear, and fatigue loading of downstream components, which is why a single Cardan joint is acceptable only at small angles or where the fluctuation is tolerable (for example, some steering columns).

## Cancelling the error: double-Cardan

Two universal joints in series can cancel the fluctuation. If the two joints operate at **equal bend angles**, the yokes on the intermediate shaft are aligned (in phase), and the input and output shafts lie in a common plane, the lead introduced by the first joint is exactly undone by the second. The intermediate shaft still runs unevenly, but the input and output turn in lockstep. This **double-Cardan** arrangement is the classic near-constant-velocity solution for driveshafts and steering shafts; it is only truly homokinetic when the equal-angle condition is met.

## Constant-velocity joints and the bisecting-plane principle

A **constant-velocity (CV) joint** delivers \(\omega_2/\omega_1 = 1\) at every instant and every angle. The governing geometric idea is the **homokinetic (bisecting) plane**: the torque-transmitting contact points must always lie in the plane that bisects the angle between the input and output axes. On that plane the effective radius arm to each shaft is equal, so equal angular increments are transferred and the velocity ratio stays unity.

<svg viewBox="0 0 260 140" width="260" height="140" stroke="currentColor" fill="none" stroke-width="1.5">
  <line x1="20" y1="70" x2="130" y2="70"/>
  <line x1="130" y1="70" x2="235" y2="22"/>
  <line x1="130" y1="20" x2="130" y2="120" stroke-dasharray="4 3"/>
  <circle cx="130" cy="70" r="4" fill="currentColor"/>
  <circle cx="130" cy="46" r="3"/>
  <text x="22" y="88" font-size="11" stroke="none" fill="currentColor">input axis</text>
  <text x="165" y="18" font-size="11" stroke="none" fill="currentColor">output axis</text>
  <text x="136" y="128" font-size="11" stroke="none" fill="currentColor">bisecting plane</text>
</svg>

Practical CV joints realize this principle in different ways. **Rzeppa** (ball-type) joints hold torque-carrying balls in an inner/outer race and use a cage to force the ball centers into the bisecting plane; they suit the large, articulating outboard positions of driven, steered wheels. **Tripod** joints use three rollers on a spider running in a tulip housing and additionally allow axial **plunge** to absorb suspension travel, common at inboard positions. **Double-Cardan** and **Weiss/fixed-ball** joints serve other duty cycles. Because they combine constant speed with substantial articulation, CV joints are indispensable in front-wheel and independent-suspension driveshafts, robotics, and any drivetrain that must deliver smooth torque through a moving, angled path.
