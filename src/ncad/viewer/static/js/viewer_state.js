// Shared viewer state: a single mutable object that the viewer's controllers read and write.
//
// app.js grew a large set of module-scope `let`s that its event-wired controllers close over
// (scene overlays, selection, motion, the active mode, ...). ES module imports are read-only
// bindings, so a controller cannot be lifted into its own module while it reassigns a bare
// module-scope variable. Holding that state on one shared object whose PROPERTIES are reassigned
// (state.foo = ...) removes the barrier: any module can `import { state }` and mutate it. This is
// the seam that lets the remaining big controllers move out of app.js one cluster at a time.
//
// Migration is incremental. Each field is moved from a bare `let` in app.js onto ViewerState in its
// own step (references rewritten bare -> state.field), so this class grows cluster by cluster. It is
// deliberately a plain state holder (single responsibility: hold shared viewer state); behavior
// stays in the controllers.
export class ViewerState {
  constructor() {
    // Assembly origin gizmos + their toggle state (per-instance origin axes, toggled by Origins).
    this.originGizmos = [];
    this.showOrigins = localStorage.getItem("ncad.origins") === "1";
    // Mate connector triads (bucket 5.1): per-connector frame markers, toggled by Connectors.
    this.connectorGizmos = [];
    this.showConnectors = localStorage.getItem("ncad.connectors") === "1";
    // Joint-freedom glyphs (bucket 5.5): per-joint free-axis markers + dashed coupling links,
    // toggled by Joints.
    this.jointGizmos = [];
    this.showJoints = localStorage.getItem("ncad.joints") === "1";
    // Motion trace curves (bucket 6.1): a THREE.Line per declared trace, added to modelRoot (world
    // path), toggled by Traces. Default on (localStorage null -> on).
    this.traceLines = [];
    this.showTraces = localStorage.getItem("ncad.traces") !== "0";
    // Assembly selection / highlight / isolate (bucket 5.5). instanceMeshMap: instanceId -> [meshes],
    // published by loadAssembly once all glbs load.
    this.instanceMeshMap = {};
    this.selectedInstances = [];
    this.isolateOn = localStorage.getItem("ncad.isolate") === "1";
    // Motion timeline playback (bucket 6.0): the active trajectory + per-frame cursor + play state,
    // advanced in the animate() loop.
    this.motion = null;         // {frames, driver} or null when no motion
    this.motionNodes = {};      // instanceId -> node for the active motion
    this.motionFrame = 0;       // current frame index
    this.motionPlaying = false;
    this.motionAccum = 0;       // ms accumulated toward the next frame
    // Loop mode: "loop" restarts at frame 0 each cycle (the default); "bounce" ping-pongs forward then
    // reverse, so a one-way stroke (a rack sliding, a follower rising) reads as a seamless there-and-
    // back loop in the recorded video. `motionDir` is the current step direction under bounce.
    this.motionLoopMode = localStorage.getItem("ncad.motionLoop") || "loop";
    this.motionDir = 1;
    // Playback-rate ladder index. The real value (ncad.motionSpeed matched against MOTION_SPEEDS) is
    // resolved in app.js where MOTION_SPEEDS lives; 0 is a safe placeholder until that runs (nothing
    // reads it before then).
    this.motionSpeedIdx = 0;
    // Physics mode poses the robot by live FORWARD KINEMATICS: the arm's actuated joints each get a
    // slider, and moving any slider re-solves the whole chain (link nodes below) so descendants stay
    // rigidly attached and each joint is clamped to its limit. Replaces the old per-joint sweep.
    this.robotChain = null;     // the FK chain (buildFkChain output) for the active robot, or null
    this.robotPose = {};        // {jointName: value} radians (revolute) / metres (prismatic)
    this.robotNodes = {};       // instanceId (== link) -> THREE.Group node to place via FK
    // Keyframe animation (bucket: robot poses). Each keyframe is {time (s), pose {joint: value}} - a
    // full pose snapshot captured from the FK sliders. They compile into a motion-shaped trajectory
    // the Motion widget plays; persisted to out/<robot>.keyframes.json.
    this.robotKeyframes = [];
  }
}

// The process-wide singleton every viewer module shares.
export const state = new ViewerState();
