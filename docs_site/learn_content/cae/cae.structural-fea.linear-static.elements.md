An element formulation is the recipe that turns a patch of material into a stiffness contribution: it fixes how displacement varies inside the element (the shape functions), which strains and stresses it represents, and how many degrees of freedom each node carries. Choosing the right family is the single most consequential modeling decision in structural analysis, because it encodes the assumed mechanics of the part before any load is applied. The families form a hierarchy of dimensional reduction, trading generality for efficiency wherever a structure is slender or thin.

## The element families

**Bar / truss** elements carry only axial force along their axis; each node has translational degrees of freedom and the axial stress is constant, making them ideal for pin-jointed frameworks and reinforcement. **Beam** elements add bending, transverse shear, and torsion, with both translations and rotations at each node. Two theories compete: Euler-Bernoulli beams neglect transverse shear (plane sections stay normal to the axis, cubic Hermite interpolation) and suit slender members, while Timoshenko beams retain shear deformation and are correct for stubby members and higher vibration modes. **Plate** elements model flat panels loaded out of plane; Kirchhoff (thin-plate) theory ignores transverse shear, whereas Mindlin-Reissner (thick-plate) theory includes it. **Shell** elements generalize plates to curved surfaces and couple membrane and bending action, which is what makes them the standard tool for thin-walled structures such as bodywork, tanks, and casings. **Solid (continuum)** elements carry the full three-dimensional stress state with translational degrees of freedom only, in tetrahedral or hexahedral shapes, and are the fallback whenever no dimensional reduction is justified.

## Interpolation order and integration

Within the isoparametric framework the same shape functions map geometry and interpolate displacement. Linear (first-order) elements have nodes only at corners and represent constant strain; quadratic (second-order) elements add mid-edge nodes, capture linear strain gradients, and follow curved boundaries far better, at higher cost per element. Element integrals such as \(\mathbf{K}^e=\int \mathbf{B}^{\mathsf T}\mathbf{D}\,\mathbf{B}\,d\Omega\) are evaluated at a small set of Gauss points; the number of points chosen (full versus reduced integration) directly affects both accuracy and the pathologies described below.

## Locking and its remedies

Low-order elements can be far too stiff in regimes their kinematics cannot represent. **Shear locking** afflicts fully integrated linear elements under bending: spurious shear strain absorbs energy that should go into flexure, so a coarsely meshed beam or plate barely deflects. **Volumetric locking** appears in nearly incompressible materials (rubber, saturated soil, metal plasticity) where the element cannot deform at constant volume. Reduced or selective integration relieves locking but can admit zero-energy hourglass modes that require stabilization; more robust cures include enhanced assumed strain, assumed natural strain, and \(\bar{\mathbf{B}}\) (mean-dilatation) formulations. Awareness of these effects, and of which element uses which cure, is what separates a trustworthy mesh from a misleadingly stiff one.

<svg viewBox="0 0 240 90" role="img" aria-label="Beam element with two nodes, each carrying a translation and a rotation">
  <line x1="30" y1="55" x2="210" y2="55" stroke="currentColor" fill="none"/>
  <circle cx="30" cy="55" r="4" stroke="currentColor" fill="none"/>
  <circle cx="210" cy="55" r="4" stroke="currentColor" fill="none"/>
  <line x1="30" y1="55" x2="30" y2="30" stroke="currentColor" fill="none"/>
  <line x1="210" y1="55" x2="210" y2="30" stroke="currentColor" fill="none"/>
  <path d="M22 38 A 12 12 0 0 1 38 38" stroke="currentColor" fill="none"/>
  <path d="M202 38 A 12 12 0 0 1 218 38" stroke="currentColor" fill="none"/>
  <text x="18" y="78" font-size="10" fill="currentColor">node i</text>
  <text x="196" y="78" font-size="10" fill="currentColor">node j</text>
</svg>
