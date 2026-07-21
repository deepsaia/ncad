The **singular value decomposition (SVD)** is the most informative and numerically robust factorization in linear algebra. Every real matrix \(A \in \mathbb{R}^{m\times n}\), of any shape or rank, can be written
\[
A = U\,\Sigma\,V^{\top}, \qquad U^{\top}U = I,\; V^{\top}V = I,\; \Sigma = \operatorname{diag}(\sigma_1 \ge \sigma_2 \ge \dots \ge 0),
\]
where the columns of \(U\) are the left singular vectors, the columns of \(V\) are the right singular vectors, and the \(\sigma_i\) are the non-negative **singular values**. Because no assumption of squareness, symmetry, or full rank is needed, the SVD exists universally, which is why it is the tool of last resort when other decompositions become ill-conditioned or fail.

## Geometric meaning

The factorization says that *any* linear map is a rotation or reflection (\(V^{\top}\)), followed by independent scaling along orthogonal axes (\(\Sigma\)), followed by another rotation or reflection (\(U\)). Applied to the unit sphere, \(A\) produces a hyperellipse whose semi-axis lengths are exactly the singular values and whose axis directions are the columns of \(U\). The largest and smallest singular values therefore bound how much the map can stretch or compress any vector, and their ratio defines the 2-norm **condition number** \(\kappa_2(A) = \sigma_{\max}/\sigma_{\min}\), the single most useful predictor of numerical sensitivity in a linear system.

<svg viewBox="0 0 240 110" width="240" height="110" stroke="currentColor" fill="none" stroke-width="1.5">
  <circle cx="55" cy="55" r="34"/>
  <line x1="110" y1="55" x2="150" y2="55"/>
  <polyline points="142,49 150,55 142,61"/>
  <text x="120" y="46" font-size="10" stroke="none" fill="currentColor">A</text>
  <ellipse cx="195" cy="55" rx="38" ry="20" transform="rotate(-18 195 55)"/>
  <text x="36" y="102" font-size="10" stroke="none" fill="currentColor">unit sphere</text>
  <text x="172" y="102" font-size="10" stroke="none" fill="currentColor">axes = sigma_i</text>
</svg>

## Why it matters

The SVD reveals **numerical rank**: the number of singular values above a tolerance is the practical rank, and the trailing right singular vectors span the (approximate) null space, while the leading left singular vectors span the range. This makes it the reliable way to solve rank-deficient or nearly singular least-squares problems through the Moore-Penrose pseudoinverse \(A^{+} = V\Sigma^{+}U^{\top}\), which returns the minimum-norm solution. The **Eckart-Young theorem** states that truncating to the top \(k\) singular triplets gives the best rank-\(k\) approximation of \(A\) in both the spectral and Frobenius norms, the mathematical basis for principal component analysis, data compression, and denoising.

In geometry and metrology the SVD is the standard engine for best-fit primitives and rigid registration. Fitting a plane or line to a point cloud reduces to taking the singular vectors of the mean-centered coordinate matrix, and aligning two corresponding point sets (the orthogonal Procrustes or Kabsch problem) is solved by an SVD of their cross-covariance, yielding the optimal rotation directly. Because the factors are orthogonal, these solutions are stable even when the input geometry is nearly degenerate, which is exactly the regime where naive normal-equation methods break down.
