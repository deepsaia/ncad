// Robot keyframe animation: compile a list of captured poses into a motion-shaped trajectory the
// existing Motion widget plays. A keyframe is {time (s), pose {joint: value}} - a full pose snapshot
// taken from the FK sliders. Playback interpolates each joint linearly between consecutive keyframes
// (by time), runs forward kinematics per interpolated pose, and emits per-link placements in the
// {frames:[{driver_value, placements}]} shape motion.js consumes - so play/pause/scrub/speed/loop
// are reused wholesale (no separate transport). Pure client math; no server, no kernel.
import { solveFk } from "./robot_fk.js";
import { matrixToRowMajor } from "./utils.js";

// Frames per second the keyframe animation is sampled at (playback SPEED is the Motion widget's
// ladder; this is just the interpolation resolution, matching the motion path's 30 fps default).
const _FPS = 30;

// Compile keyframes into a trajectory for the Motion player. `keyframes` is [{time, pose}] sorted by
// time; `chain` is the FK chain (buildFkChain). Returns {frames:[{driver_value, placements}]} where
// each placement is a row-major 4x4 (metres) per link, or null if fewer than 2 keyframes (nothing
// to interpolate). driver_value carries the frame's time (s) so the readout shows elapsed time.
export function compileKeyframes(keyframes, chain) {
  const sorted = [...keyframes].sort((a, b) => a.time - b.time);
  if (sorted.length < 2) return null;
  const jointNames = _jointNames(sorted);
  const start = sorted[0].time, end = sorted[sorted.length - 1].time;
  const span = end - start;
  if (span <= 0) return null;
  const frameCount = Math.max(2, Math.round(span * _FPS) + 1);
  const frames = [];
  for (let i = 0; i < frameCount; i++) {
    const t = start + (span * i) / (frameCount - 1);
    const pose = _poseAt(sorted, jointNames, t);
    frames.push({ driver_value: t, status: "solved", placements: _placements(chain, pose) });
  }
  return { frames, driver: { joint: "keyframes" } };
}

// The union of joint names across all keyframes (a joint missing from a keyframe holds 0 there).
function _jointNames(keyframes) {
  const names = new Set();
  for (const kf of keyframes) for (const name in (kf.pose || {})) names.add(name);
  return [...names];
}

// Linearly interpolate every joint's value at time `t` between the bracketing keyframes.
function _poseAt(sorted, jointNames, t) {
  let hi = sorted.findIndex(kf => kf.time >= t);
  if (hi <= 0) hi = 1;   // clamp to the first segment for t at/below the start
  const a = sorted[hi - 1], b = sorted[hi];
  const dt = b.time - a.time;
  const u = dt > 0 ? (t - a.time) / dt : 0;
  const pose = {};
  for (const name of jointNames) {
    const va = (a.pose && a.pose[name]) || 0;
    const vb = (b.pose && b.pose[name]) || 0;
    pose[name] = va + (vb - va) * u;
  }
  return pose;
}

// FK-solve a pose to per-link row-major placements (metres), the motion-frame shape.
function _placements(chain, pose) {
  const nodes = solveFk(chain, pose);   // link -> THREE.Matrix4
  const placements = {};
  for (const link in nodes) placements[link] = matrixToRowMajor(nodes[link]);
  return placements;
}
