Kane's method (also called Lagrange's form of d'Alembert's principle) derives equations of motion that are minimal in number yet built from ordinary vectors of velocity and force, avoiding both the symbolic differentiation of energy functions and the appearance of ideal-constraint reactions. Its distinctive idea is to describe motion with **generalized speeds** \(u_1,\dots,u_n\), chosen independently of the coordinate rates \(\dot q\) and related to them by linear kinematic differential equations \(\dot q = \mathbf{Y}(q,t)\,u + \mathbf{z}(q,t)\). Freedom in this choice, for example picking \(u\) as physical angular-velocity components rather than Euler-angle rates, often yields dramatically simpler final equations.

## Partial velocities and the two generalized forces

Because every point velocity \(\mathbf{v}_i\) and body angular velocity \(\boldsymbol{\omega}_i\) are linear in the generalized speeds, they decompose as

\[ \mathbf{v}_i = \sum_{r=1}^{n} \mathbf{v}_r^{(i)}\,u_r + \mathbf{v}_t^{(i)}, \qquad \boldsymbol{\omega}_i = \sum_{r=1}^{n} \boldsymbol{\omega}_r^{(i)}\,u_r + \boldsymbol{\omega}_t^{(i)}, \]

where \(\mathbf{v}_r^{(i)} = \partial\mathbf{v}_i/\partial u_r\) and \(\boldsymbol{\omega}_r^{(i)} = \partial\boldsymbol{\omega}_i/\partial u_r\) are the **partial velocities** and **partial angular velocities**. These act as projection directions. For each generalized speed \(u_r\) one forms a generalized active force \(F_r\) from applied loads and a generalized inertia force \(F_r^{*}\) from the mass-times-acceleration terms:

\[ F_r = \sum_i \big(\mathbf{v}_r^{(i)}\!\cdot\mathbf{R}_i + \boldsymbol{\omega}_r^{(i)}\!\cdot\mathbf{T}_i\big), \qquad F_r^{*} = \sum_i \Big(\mathbf{v}_r^{(i)}\!\cdot(-m_i\mathbf{a}_i) + \boldsymbol{\omega}_r^{(i)}\!\cdot\big(-\mathbf{I}_i\boldsymbol{\alpha}_i - \boldsymbol{\omega}_i\times\mathbf{I}_i\boldsymbol{\omega}_i\big)\Big). \]

## Kane's equations

The equations of motion are simply the statement that, projected onto each admissible direction, active and inertia forces balance:

\[ F_r + F_r^{*} = 0, \qquad r = 1,\dots,n. \]

This gives exactly \(n\) equations for the \(n\) generalized speeds. Projecting onto the partial velocities is what annihilates the workless constraint forces, so joint reactions never appear unless one deliberately introduces them (which Kane's method can also do, by adding auxiliary generalized speeds that expose a chosen reaction). For systems with nonholonomic constraints, one keeps only the independent generalized speeds and their partial velocities, and the correct minimal set of equations emerges directly, without Lagrange multipliers.

The method sits between the two classical extremes: like the Newton-Euler approach it works with vectors, accelerations, and the gyroscopic term \(\boldsymbol{\omega}\times\mathbf{I}\boldsymbol{\omega}\), but like the Lagrangian approach it produces a minimal, reaction-free set of equations. That combination, together with its systematic, algorithmic bookkeeping, makes it a favored formulation for automatically generating efficient equations of motion for complex spacecraft, vehicle, and multibody models, particularly nonholonomic ones where multiplier-based methods are cumbersome.
