// Motion timeline playback (bucket 6.0): the trajectory player behind the Motion tab (and reused by
// Physics mode). Owns the play/pause + scrub + speed-ladder + loop/bounce controls, the per-frame
// placement apply (showMotionFrame), and the measures / mobility / clash-mark / trace-line panels
// that ride a trajectory.
//
// Extracted from app.js. The playback STATE lives on the shared ViewerState (state.motion,
// state.motionFrame, ...); this module owns the motion DOM elements + the MOTION_SPEEDS ladder.
// Cross-concern pieces are injected by initMotion so this never imports app.js: getViewMode (the
// live view mode - setupMotion is a Motion-tab feature), getModelRoot (trace lines parent to it,
// reassigned on load), renderRobotTree (a Physics-mode fn resetMotion clears), the shared
// motionSources map (setupMotion records a trajectory's source doc), and apiUrl/log.
//
// Public surface: resetMotion / setupMotion / advanceMotion (animate loop) / showMotionFrame, plus
// loadTrajectory (Physics feeds a joint sweep into the player) and pauseMotion (the dev seekFrame
// handle). Physics reuses this path because a joint sweep has the same {frames:[{driver_value,
// placements}]} shape as a motion trajectory.
import * as THREE from "three";
import { state } from "./viewer_state.js";
import { fmtSpeed, matrixFromRowMajor } from "./utils.js";
import { TRACE_COLORS, PLAY_ICON, PAUSE_ICON, LOOP_ICON, BOUNCE_ICON } from "./constants.js";

// Injected cross-concern dependencies, set once by initMotion.
let getViewMode = null;
let getModelRoot = null;
let renderRobotTree = null;
let motionSources = null;
let apiUrl = null;
let log = null;

// Motion DOM elements, resolved in initMotion (once the page exists).
let motionBar = null, motionPlayBtn = null, motionScrub = null, motionReadout = null;
let motionSlowerBtn = null, motionFasterBtn = null, motionSpeedReadout = null, motionLoopBtn = null;

// PLAYBACK RATE only (how fast you watch the same trajectory); it never re-solves. Solve resolution
// is the motion document's driver `steps` (or `fps`+`duration`). 1x = 30 fps (a 1/30 s frame
// interval); the ladder multiplies that rate. Beyond ~2x the ~60 fps render loop advances several
// frames per tick (advanceMotion's while-loop handles it), so the high multipliers act as fast
// preview/scrub. The [-]/[+] buttons + the "[" / "]" keys step along the ladder; choice persists.
const MOTION_BASE_FRAME_MS = 1000 / 30;   // 1x = 30 fps
const MOTION_SPEEDS = [0.1, 0.25, 0.5, 1, 2, 4, 8, 16, 32, 64, 128];
function motionSpeed() { return MOTION_SPEEDS[state.motionSpeedIdx]; }
function motionFrameMs() { return MOTION_BASE_FRAME_MS / motionSpeed(); }
function renderMotionSpeed() {
  // Only the middle readout shows the number (<n>x); the -/+ buttons stay iconic.
  motionSpeedReadout.textContent = fmtSpeed(motionSpeed());
  motionSlowerBtn.disabled = state.motionSpeedIdx === 0;
  motionFasterBtn.disabled = state.motionSpeedIdx === MOTION_SPEEDS.length - 1;
}
function setMotionSpeedIdx(i) {
  state.motionSpeedIdx = Math.max(0, Math.min(MOTION_SPEEDS.length - 1, i));
  localStorage.setItem("ncad.motionSpeed", String(motionSpeed()));
  renderMotionSpeed();
}

function renderLoopMode() {
  motionLoopBtn.innerHTML = state.motionLoopMode === "bounce" ? BOUNCE_ICON : LOOP_ICON;
  motionLoopBtn.classList.toggle("active", state.motionLoopMode === "bounce");
  motionLoopBtn.title = state.motionLoopMode === "bounce"
    ? "Bounce: forward then reverse ( L )" : "Loop: restart each cycle ( L )";
}
function toggleLoopMode() {
  state.motionLoopMode = state.motionLoopMode === "bounce" ? "loop" : "bounce";
  state.motionDir = 1;   // restart the direction so a fresh bounce goes forward first
  localStorage.setItem("ncad.motionLoop", state.motionLoopMode);
  renderLoopMode();
}

export function resetMotion() {
  state.motion = null; state.motionNodes = {}; state.motionFrame = 0; state.motionPlaying = false; state.motionAccum = 0;
  motionBar.hidden = true;
  motionPlayBtn.innerHTML = PLAY_ICON;
  // Trace lines are children of modelRoot (cleared with the scene in clearModel); just drop refs.
  state.traceLines = [];
  renderMeasures(null);
  renderClashMarks([], 0);
  // Physics rides the motion state; drop the joint picker + Robot inspector with the scene too.
  const pbar = document.getElementById("physics-bar");
  if (pbar) pbar.hidden = true;
  if (typeof renderRobotTree === "function") renderRobotTree(null);
}

function renderClashMarks(events, frameCount) {
  // Red ticks on the scrubber at interfering frame indices (motion-time interference, 6.3).
  const host = document.getElementById("motion-clash-marks");
  if (!host) return;
  host.innerHTML = "";
  if (!events.length || frameCount < 2) return;
  const seen = new Set();
  for (const ev of events) {
    if (seen.has(ev.frame)) continue;
    seen.add(ev.frame);
    const tick = document.createElement("div");
    tick.className = "clash-tick";
    tick.style.left = (100 * ev.frame / (frameCount - 1)) + "%";
    tick.title = `clash: ${ev.a} <> ${ev.b} (frame ${ev.frame})`;
    host.appendChild(tick);
  }
  log(`motion interference: ${seen.size} frame(s) with contact`, "warn");
}

export function setupMotion(name, instanceNodes) {
  resetMotion();
  // The timeline is a Motion-mode feature; in Assemblies mode a driven assembly still loads, just
  // without playback (that is what the Motion tab is for).
  if (getViewMode() !== "motion") return;
  fetch(apiUrl(`/motion/${encodeURIComponent(name)}`)).then(r => {
    if (!r.ok) return null;   // 404: this assembly has no motion, leave the bar hidden
    return r.json();
  }).then(doc => {
    if (!doc || !(doc.frames || []).length) return;
    // The trajectory records its source .motion.hocon, so Regenerate works after a page reload (the
    // in-memory motionSources map alone would be empty on a fresh page).
    if (doc.source) motionSources[name] = doc.source;
    state.motion = doc; state.motionNodes = instanceNodes;
    motionScrub.max = String(doc.frames.length - 1);
    motionScrub.value = "0";
    motionBar.hidden = false;
    buildTraceLines(doc.traces || []);   // motion outputs (bucket 6.1); no-op if none declared
    renderMeasures(doc.measures || []);
    renderMobility(doc.dof || null);
    renderClashMarks(doc.interference || [], doc.frames.length);   // motion-time interference (6.3)
    showMotionFrame(0);
    log(`motion: ${doc.frames.length} frames, driver ${doc.driver ? doc.driver.joint : "?"}`, "info");
  }).catch(() => { /* state.motion is optional; a fetch error just means no timeline */ });
}

// Load a ready trajectory ({frames, driver}) into the player + reveal the bar. Physics mode feeds a
// selected joint's precomputed sweep here so the scrubber/play controls drive it exactly like a
// motion trajectory (same frame shape). The caller supplies the per-instance placement nodes.
export function loadTrajectory(trajectory, instanceNodes) {
  state.motion = trajectory;
  state.motionNodes = instanceNodes;
  motionScrub.max = String(trajectory.frames.length - 1);
  motionScrub.value = "0";
  motionBar.hidden = false;
  showMotionFrame(0);
}

export function showMotionFrame(i) {
  if (!state.motion) return;
  const frames = state.motion.frames;
  state.motionFrame = ((i % frames.length) + frames.length) % frames.length;
  const frame = frames[state.motionFrame];
  for (const id in frame.placements) {
    const node = state.motionNodes[id];
    if (!node) continue;
    node.matrix.copy(matrixFromRowMajor(frame.placements[id]));
    node.matrix.decompose(node.position, node.quaternion, node.scale);
    node.updateMatrixWorld(true);
  }
  motionScrub.value = String(state.motionFrame);
  const unit = degreesLikelyDriver() ? "°" : "";
  motionReadout.textContent = `${(+frame.driver_value).toFixed(1)}${unit}`;
  updateMeasureValues(state.motionFrame);
}

// Build a THREE.Line for each declared trace polyline (world metres), added to modelRoot so it
// clears with the scene and rides the model's framing shift. Colored from the trace palette,
// visibility follows the Traces toggle. No-op when no traces are declared.
function buildTraceLines(traces) {
  state.traceLines = [];
  const modelRoot = getModelRoot();
  traces.forEach((t, i) => {
    const pts = (t.polyline || []).map(p => new THREE.Vector3(p[0], p[1], p[2]));
    if (pts.length < 2) return;
    const line = new THREE.Line(
      new THREE.BufferGeometry().setFromPoints(pts),
      new THREE.LineBasicMaterial({ color: TRACE_COLORS[i % TRACE_COLORS.length] }));
    line.userData.isGizmo = true;   // excluded from picking/bbox like the other overlays
    line.visible = state.showTraces;
    if (modelRoot) modelRoot.add(line);
    state.traceLines.push(line);
  });
}

// Render the measures panel (a compact numeric readout, one row per measure). Called on load
// (measures list) and reset (null clears it). The per-frame live value is filled by
// updateMeasureValues.
function renderMeasures(measures) {
  const panel = document.getElementById("measures-body");
  if (!panel) return;
  if (!measures || !measures.length) {
    panel.innerHTML = '<div class="panel-empty">no measures</div>';
    document.getElementById("tab-measures-btn").hidden = !measures;
    return;
  }
  document.getElementById("tab-measures-btn").hidden = false;
  panel.innerHTML = "";
  for (const m of measures) {
    const row = document.createElement("div");
    row.className = "measure-row";
    const extra = m.value != null ? ` &middot; total ${(+m.value).toFixed(2)} ${m.unit}` : "";
    row.innerHTML =
      `<span class="measure-id">${m.id}</span>` +
      `<span class="measure-val" data-measure="${m.id}">-</span>` +
      `<span class="measure-range">[${(+m.min).toFixed(1)} .. ${(+m.max).toFixed(1)}] ${m.unit}${extra}</span>`;
    panel.appendChild(row);
  }
}

// Add a mobility (DoF) line to the hierarchy panel, next to the static solve-status line: the
// planar Gruebler mobility + the rest-pose solver DoF. Green when mobile, amber when locked.
// Prepended to the hierarchy body (which renderInstanceTree filled from the assembly scene).
function renderMobility(dof) {
  const existing = document.getElementById("mobility-line");
  if (existing) existing.remove();
  if (!dof) return;
  const body = document.getElementById("hierarchy-body");
  if (!body) return;
  const line = document.createElement("div");
  line.id = "mobility-line";
  line.className = "mate-status " + (dof.status === "mobile" ? "mate-status-ok" : "mate-status-warn");
  line.textContent = `mobility: ${dof.gruebler} DoF (planar Gruebler ${dof.gruebler}, ` +
    `rest solve ${dof.solver})`;
  line.title = "Mechanism mobility from the joint graph (Gruebler) next to the static rest-pose " +
    "free DoF (0 for a well-constrained rest).";
  body.insertBefore(line, body.firstChild);
}

// Fill each measure row's live value from the current frame's series entry.
function updateMeasureValues(frameIdx) {
  if (!state.motion || !state.motion.measures) return;
  for (const m of state.motion.measures) {
    const el = document.querySelector(`.measure-val[data-measure="${m.id}"]`);
    if (!el) continue;
    const v = (m.series || [])[frameIdx];
    el.textContent = v == null ? "-" : `${(+v).toFixed(2)} ${m.unit}`;
  }
}

function degreesLikelyDriver() {
  // A rotation driver reads in degrees; a slider in mm. We do not carry the joint type in the
  // sidecar, so infer: a range that spans a full turn (>= 360 total) is almost certainly degrees.
  if (!state.motion || !state.motion.frames.length) return true;
  const span = Math.abs(state.motion.frames[state.motion.frames.length - 1].driver_value
                        - state.motion.frames[0].driver_value);
  return span >= 180;
}

export function toggleMotionPlay() {
  if (!state.motion) return;
  state.motionPlaying = !state.motionPlaying;
  motionPlayBtn.innerHTML = state.motionPlaying ? PAUSE_ICON : PLAY_ICON;
}

// Pause playback + reset the play button to the Play glyph (no frame change). Used by the dev
// seekFrame handle and any caller that wants a clean paused state before scrubbing.
export function pauseMotion() {
  state.motionPlaying = false;
  motionPlayBtn.innerHTML = PLAY_ICON;
}

export function advanceMotion(dtMs) {
  if (!state.motionPlaying || !state.motion) return;
  state.motionAccum += dtMs;
  const frameMs = motionFrameMs();
  while (state.motionAccum >= frameMs) {
    state.motionAccum -= frameMs;
    stepMotion();
  }
}

function stepMotion() {
  // Loop mode wraps forward (modulo). Bounce mode ping-pongs: step by motionDir and flip direction
  // at either end so the trajectory plays forward then reverse (a there-and-back loop for video).
  const last = state.motion.frames.length - 1;
  if (state.motionLoopMode !== "bounce") { showMotionFrame(state.motionFrame + 1); return; }
  let next = state.motionFrame + state.motionDir;
  if (next > last) { state.motionDir = -1; next = last - 1; }
  else if (next < 0) { state.motionDir = 1; next = 1; }
  if (next < 0) next = 0;   // a single-frame trajectory stays put
  showMotionFrame(next);
}

// Resolve the DOM elements + wire the controls, then boot the speed/loop readouts. Called once by
// app.js after MOTION-related deps exist. `deps` supplies the injected cross-concern accessors.
export function initMotion(deps) {
  getViewMode = deps.getViewMode;
  getModelRoot = deps.getModelRoot;
  renderRobotTree = deps.renderRobotTree;
  motionSources = deps.motionSources;
  apiUrl = deps.apiUrl;
  log = deps.log;

  motionBar = document.getElementById("motion-bar");
  motionPlayBtn = document.getElementById("motion-play");
  motionScrub = document.getElementById("motion-scrub");
  motionReadout = document.getElementById("motion-readout");
  motionSlowerBtn = document.getElementById("motion-slower");
  motionFasterBtn = document.getElementById("motion-faster");
  motionSpeedReadout = document.getElementById("motion-speed-readout");
  motionLoopBtn = document.getElementById("motion-loop");

  // Resolve the persisted playback-rate ladder index now that MOTION_SPEEDS exists (ViewerState
  // seeds it to 0 as a placeholder). Nothing reads state.motionSpeedIdx before this runs.
  state.motionSpeedIdx = (() => {
    const saved = parseFloat(localStorage.getItem("ncad.motionSpeed"));
    const i = MOTION_SPEEDS.indexOf(saved);
    return i >= 0 ? i : MOTION_SPEEDS.indexOf(1);   // default 1x
  })();

  motionSlowerBtn.addEventListener("click", () => setMotionSpeedIdx(state.motionSpeedIdx - 1));
  motionFasterBtn.addEventListener("click", () => setMotionSpeedIdx(state.motionSpeedIdx + 1));
  renderMotionSpeed();

  motionLoopBtn.addEventListener("click", toggleLoopMode);
  renderLoopMode();

  // "[" slower, "]" faster - only when a motion is loaded and the user is not typing in a field.
  document.addEventListener("keydown", ev => {
    if (motionBar.hidden) return;
    const t = ev.target;
    if (t && (t.tagName === "INPUT" || t.tagName === "TEXTAREA" || t.tagName === "SELECT")) return;
    if (ev.key === "[") { setMotionSpeedIdx(state.motionSpeedIdx - 1); ev.preventDefault(); }
    else if (ev.key === "]") { setMotionSpeedIdx(state.motionSpeedIdx + 1); ev.preventDefault(); }
    // P (and the space bar, the media convention) toggles play/pause, matching the widget's button.
    else if (ev.key === "p" || ev.key === "P" || ev.key === " ") {
      toggleMotionPlay(); ev.preventDefault();
    }
    // L toggles the loop mode (loop <-> bounce).
    else if (ev.key === "l" || ev.key === "L") { toggleLoopMode(); ev.preventDefault(); }
    // 0 rewinds to the start frame and pauses (a clean reset before recording a fresh loop).
    else if (ev.key === "0") {
      state.motionPlaying = false; motionPlayBtn.innerHTML = PLAY_ICON;
      state.motionDir = 1; state.motionAccum = 0; showMotionFrame(0);
      ev.preventDefault();
    }
  });

  motionPlayBtn.addEventListener("click", toggleMotionPlay);
  motionScrub.addEventListener("input", () => {
    state.motionPlaying = false; motionPlayBtn.innerHTML = PLAY_ICON;
    showMotionFrame(parseInt(motionScrub.value, 10) || 0);
  });
}
