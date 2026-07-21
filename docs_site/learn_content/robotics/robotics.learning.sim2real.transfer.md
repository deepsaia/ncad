A controller learned or tuned in simulation almost never behaves identically on physical hardware. The discrepancy is called the **reality gap**, and it arises because a simulator is an approximation: mass and inertia estimates are imperfect, friction and contact are notoriously hard to model, actuators have unmodeled dynamics and saturation, sensors add noise and latency, and the numerical integrator introduces its own error. **Sim-to-real transfer** is the collection of techniques that make behavior developed in simulation survive deployment on the real system, and it is essential precisely because training on hardware is slow, expensive, and often unsafe, while simulation is fast, parallel, and resettable.

## System identification: shrink the gap by fitting the model

The classical response is **system identification**: estimate the simulator's physical parameters from real measurements so the model matches the plant. Given a parameterized dynamics model and a dataset of observed inputs \(u_t\) and outputs \(y_t\) from the real system, one chooses parameters \(\theta\) that minimize prediction error,

\[ \hat{\theta} = \arg\min_{\theta} \sum_{t} \big\| y_t - \hat{y}_t(\theta) \big\|^2, \]

where \(\hat{y}_t(\theta)\) is the model's predicted output. The parameters may be inertial properties, joint friction and damping coefficients, motor constants, or sensor biases. Good identification requires **persistently exciting** inputs, motions rich enough in frequency content to reveal each parameter, and it is limited by structural model error: no amount of fitting recovers dynamics the model has no term for. This is why identification is usually paired with, rather than replaced by, the robustness methods below.

## Domain randomization: transfer by training over a distribution

Rather than pin down one "true" model, **domain randomization** deliberately varies simulation parameters (masses, friction, latencies, visual textures, sensor noise) across a wide distribution during training, so the policy must succeed across a whole family of environments. The idea is that if the real system looks like just one more sample from that distribution, the policy generalizes to it without ever having seen it. Formally the objective becomes an expectation over a distribution \(p(\xi)\) of environment parameters,

\[ \max_{\pi} \; \mathbb{E}_{\xi \sim p(\xi)} \big[\, \mathbb{E}_{\pi}\, G \mid \xi \,\big], \]

which trades some peak performance on any single model for **robustness** across all of them. The randomization ranges are themselves a design choice: too narrow and the real system falls outside the training support, too wide and the policy becomes needlessly conservative or fails to learn at all.

## Closing the loop and where it matters

System identification and domain randomization are complementary: identification centers the randomization distribution on realistic values, and randomization covers the residual uncertainty and unmodeled effects that identification cannot capture. More adaptive schemes close the loop, using small amounts of real-world data to update the parameter distribution (sometimes called adaptive or automatic domain randomization), fine-tune the policy on hardware, or learn a residual model that corrects the simulator's error term. Throughout, the transfer only works to the extent the simulated environment captures the phenomena that matter for the task; contact-rich manipulation and dynamic locomotion, where friction and impact dominate, are far harder to transfer than smooth free-space motion. In every case the discipline is the same: quantify the gap on held-out real trajectories, not just simulated returns, before trusting a transferred controller on hardware.
