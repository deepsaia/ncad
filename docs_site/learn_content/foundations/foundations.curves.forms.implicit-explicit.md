Besides the parametric form, a curve can be described by an equation that its points must satisfy rather than by a rule that generates them. The two classical variants are the **explicit** and **implicit** forms, and each answers a different geometric question.

The **explicit form** expresses one coordinate as a direct function of the other,

\[ y = f(x), \]

for example \(y = x^2\) or \(y = \sqrt{r^2 - x^2}\). It is the most elementary description and is convenient for tabulation, integration, and elementary calculus. Its limitation is structural: a function returns a single value, so an explicit curve can never have a vertical tangent, close on itself, or pass a given \(x\) more than once. A full circle, for instance, requires two explicit branches. For this reason the explicit form is best regarded as a special, restricted case rather than a general modeling tool.

## The implicit form

The **implicit form** describes a plane curve as the zero set of a function of both coordinates,

\[ F(x, y) = 0, \]

such as \(x^2 + y^2 - r^2 = 0\) for a circle. In three dimensions a single equation \(F(x,y,z)=0\) defines a surface, so a space curve is expressed as the intersection of two implicit surfaces. When \(F\) is a polynomial the result is an **algebraic curve**, and \(F\) can equally be read as a **level set** of a scalar field, the viewpoint underlying signed-distance and level-set methods. The gradient \(\nabla F\) is orthogonal to the curve, so the tangent direction and normal follow immediately from partial derivatives, and the sign of \(F\) partitions the plane into inside and outside regions.

The implicit and parametric forms have **complementary strengths**, a duality that is central to how solid modelers are built. Given a query point, the implicit form answers point membership in constant time by evaluating and testing the sign of \(F\); the parametric form cannot do this without solving an inversion problem. Conversely, to generate an ordered sequence of points on the curve the parametric form is trivial to evaluate, while the implicit form requires numerically solving \(F = 0\). The practical rule of thumb is: parametric forms are easy to **draw** and hard to **test**, implicit forms are easy to **test** and hard to **draw**.

Because of this trade-off, real systems keep both descriptions and convert between them. Turning a parametric curve into an implicit equation is called **implicitization** and, for rational curves, can always be done in principle by eliminating the parameter (via resultants or Groebner bases), though the resulting algebraic degree grows quickly. Going the other way, tracing a parametric path along an implicit curve, is a root-finding and continuation problem. Understanding which representation a downstream operation prefers, membership classification versus rendering and sampling, is a recurring design decision in geometric computing.
