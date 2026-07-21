Forward kinematics answers one direct question: given the value of every driven input in a mechanism (an angle at each revolute pair, a displacement at each prismatic pair), where does each downstream body end up, and in particular what is the pose of a chosen output frame? It is the single-valued map

\[ f : \mathcal{Q} \to SE(3), \qquad \theta \mapsto X = f(\theta), \]

from the configuration (or joint) space \(\mathcal{Q}\) into the group of rigid-body displacements \(SE(3)\). Because rigid transforms compose by multiplication, evaluating \(f\) is deterministic and cheap: exactly one output pose exists for each set of inputs. That determinism is why forward kinematics is the backbone of every mechanism rebuild, animation frame, and simulation step.

## Two standard formalisms

The Denavit-Hartenberg (DH) convention attaches a frame to each link and encodes the transform between consecutive frames with four parameters (link length, link twist, joint offset, and the joint variable), so the output pose is the ordered product \(T = A_1(\theta_1)\,A_2(\theta_2)\cdots A_n(\theta_n)\). The product-of-exponentials (PoE) form instead describes each joint by a screw axis \(\mathcal{S}_i\) and writes

\[ X(\theta) = e^{[\mathcal{S}_1]\theta_1}\,e^{[\mathcal{S}_2]\theta_2}\cdots e^{[\mathcal{S}_n]\theta_n}\,M, \]

where \(M\) is the output frame at the zero configuration and \([\mathcal{S}_i]\) is the \(4\times4\) matrix form of the screw twist. PoE needs no intermediate link frames, exposes each axis direction and location directly, and differentiates cleanly, which is convenient for chains that mix revolute and prismatic joints and for building the Jacobian.

## Inputs must match mobility

The output pose is only well posed when the count of independent driven inputs equals the mechanism's degree of freedom. The Grübler-Kutzbach criterion gives that mobility from the link and joint counts; for a spatial mechanism of \(n\) links (ground included) connected by \(j\) joints,

\[ M = 6(n-1) - \sum_{i=1}^{j}\left(6 - f_i\right), \]

where \(f_i\) is the number of freedoms permitted by joint \(i\) (the planar version replaces 6 with 3). When \(M\) driven inputs are specified, forward kinematics propagates them through the structure to fix every remaining body. For an open serial chain that propagation is a straight sequence of multiplications; for a closed loop it requires solving the loop-closure equation \(A_1 A_2 \cdots A_k = I\), which reintroduces the multivalued behaviour treated under inverse kinematics.

In practice forward kinematics is the evaluation half of a parametric model: it drives collision and interference checks, samples the reachable set, produces the frame-by-frame poses of an animation, and supplies the operating point at which the velocity Jacobian and statics are linearized. Its speed and single-valuedness are exactly what make an interactive, deterministic rebuild possible.
