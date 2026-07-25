# Showcase

Live 3D scenes built by ncad from text documents. Each one is a shipped example under
`examples/`: a feature-tree part per body, composed into an assembly, and (for the mechanisms)
driven by a kinematic motion study. Drag to orbit, scroll to zoom. The moving scenes replay the
solved trajectory frame by frame, the same data the browser viewer plays.

<div class="ncad-showcase-grid" markdown>

<div>
<div class="ncad-viewer" data-ncad-model="../../assets/models/crank_slider" data-ncad-motion="true"></div>
<p class="ncad-caption"><strong>Crank-slider</strong> A flywheel drives a connecting rod that pushes
a piston in a block: rotation to reciprocating translation, one closed loop.</p>
</div>

<div>
<div class="ncad-viewer" data-ncad-model="../../assets/models/peaucellier" data-ncad-motion="true"></div>
<p class="ncad-caption"><strong>Peaucellier-Lipkin linkage</strong> Eight bars, ten revolute joints;
the driven crank makes the output point trace an exact straight line.</p>
</div>

<div>
<div class="ncad-viewer" data-ncad-model="../../assets/models/geneva" data-ncad-motion="true"></div>
<p class="ncad-caption"><strong>Geneva drive</strong> A continuously turning crank indexes a slotted
wheel in intermittent steps: the classic film-advance mechanism.</p>
</div>

<div>
<div class="ncad-viewer" data-ncad-model="../../assets/models/four_bar" data-ncad-motion="true"></div>
<p class="ncad-caption"><strong>Four-bar linkage</strong> The fundamental planar mechanism: a driven
crank, a coupler, and a rocker on a fixed ground link, one closed loop.</p>
</div>

<div>
<div class="ncad-viewer" data-ncad-model="../../assets/models/cam_follower" data-ncad-motion="true"></div>
<p class="ncad-caption"><strong>Cam and follower</strong> A rotating cam profile lifts a spring-return
follower along its prescribed dwell-rise-return law: rotation to timed linear motion.</p>
</div>

<div>
<div class="ncad-viewer" data-ncad-model="../../assets/models/gear_pair" data-ncad-motion="true"></div>
<p class="ncad-caption"><strong>Gear pair</strong> A meshing involute pinion and gear: the driven
pinion turns the gear at the tooth-count ratio, real involute tooth geometry.</p>
</div>

<div>
<div class="ncad-viewer" data-ncad-model="../../assets/models/l_house"></div>
<p class="ncad-caption"><strong>L-house</strong> A multi-part building assembly (walls, floor bands,
roof, stair, balcony, glazing): the same engine, an architectural model.</p>
</div>

</div>

Every scene here is reproducible from the repository: `ncad build examples/07-motion/geneva.motion.hocon`
(or any example) regenerates the exact geometry and trajectory shown above.
