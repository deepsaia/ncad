// Pure viewer helpers: formatting, small DOM builders, CSS-var reads, and the row-major -> THREE
// matrix conversion. These take all inputs as arguments and hold no module state, so they are the
// first, safest slice carved out of app.js. Each function keeps its original comment. Imported by
// app.js (and future viewer modules).
import * as THREE from "three";

// Read a resolved CSS variable (so the 3D scene shares the same palette as the DOM).
export function cssVar(name) { return getComputedStyle(document.documentElement).getPropertyValue(name).trim(); }
export function cssColor(name) { return new THREE.Color(cssVar(name)); }

// Format a duration (milliseconds) as 00h00m00.0s, dropping leading zero units: seconds-only reads
// "3.7s", minutes "1m04.2s", hours "1h02m03.4s". A starting point for profiling (build vs render).
export function fmtDuration(ms) {
  const totalS = ms / 1000;
  const h = Math.floor(totalS / 3600);
  const m = Math.floor((totalS % 3600) / 60);
  const s = totalS % 60;
  const pad2 = n => String(n).padStart(2, "0");
  // Seconds keep one decimal; pad the whole "S.s" to width 4 so a single-digit second reads "04.2".
  const secs = s.toFixed(1).padStart(4, "0");
  if (h > 0) return `${h}h${pad2(m)}m${secs}s`;
  if (m > 0) return `${m}m${secs}s`;
  return `${s.toFixed(1)}s`;
}

export function fmtSpeed(s) { return (s < 1 ? s : String(s)) + "x"; }

// Escape text destined for innerHTML (robot ids come from an ncad doc, so this is belt-and-braces).
export function escapeHtml(s) {
  return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

export function iconButton(tip, svg, extraClass) {
  const b = document.createElement("button");
  b.className = "icon-btn" + (extraClass ? " " + extraClass : "");
  b.title = tip; b.setAttribute("aria-label", tip); b.innerHTML = svg;
  return b;
}

// Scroll the list so the active row is visible (nearest edge, no animation), rather than
// leaving it scrolled to the top. Safe when nothing is active (no-op).
export function scrollActiveIntoView(list) {
  const active = list.querySelector(".model-row.active");
  if (active) active.scrollIntoView({ block: "nearest" });
}

// The sidecar placement is a ROW-MAJOR 4x4 already in the glb's unit (metres): the AssemblyBuilder
// bakes the document-unit-to-metres conversion, so the viewer is unit-agnostic (like single-part
// glbs). three.js Matrix4.set takes row-major args with the translation in the last column.
export function matrixFromRowMajor(m) {
  // ncad placements are ROW-VECTOR convention (p_world = p_local . M): the 3x3 rotation block holds
  // the images of the basis vectors as ROWS (i.e. it is R-transpose). three.js applies transforms
  // column-vector (M . p), so the rotation must be TRANSPOSED here (rows->columns); the translation
  // stays m[3] -> the 4th column. Without the transpose, rotations render inverted (parts spin the
  // wrong way / flip), which is invisible while every static placement is identity but shows up the
  // moment a motion frame carries real rotation.
  const M = new THREE.Matrix4();
  M.set(m[0][0], m[1][0], m[2][0], m[3][0],
        m[0][1], m[1][1], m[2][1], m[3][1],
        m[0][2], m[1][2], m[2][2], m[3][2],
        0, 0, 0, 1);
  return M;
}
