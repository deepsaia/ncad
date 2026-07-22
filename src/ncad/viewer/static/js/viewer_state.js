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
  }
}

// The process-wide singleton every viewer module shares.
export const state = new ViewerState();
