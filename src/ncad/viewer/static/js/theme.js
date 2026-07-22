// Color theme controller: the light -> system -> dark toggle (persisted), plus the 3D-scene recolor
// that keeps the WebGL scene (background, fog, grid, edges) in sync with the active CSS theme.
//
// Extracted from app.js. The toggle owns its own DOM + choice state; the scene recolor
// (applySceneTheme) is injected the scene-side pieces it needs: `scene` + `grid` (stable consts,
// injected once) and a live `getEdges` accessor (edges is reassigned in app.js on model load).
// initTheme wires the control and applies the saved theme once. Each function/comment is kept
// verbatim except the bare `edges` read becoming the injected accessor.
import { cssColor } from "./utils.js";
import { THEME_ORDER, THEME_ICONS } from "./constants.js";

// Injected scene-side dependencies, set once by initTheme.
let scene = null;
let grid = null;
let getEdges = null;

// Theme DOM + choice, resolved/loaded in initTheme.
let themeBtn = null;
let themeIcon = null;
let darkMedia = null;
let themeChoice = "system";

// Recolor the 3D scene from the current theme's CSS variables. Called on theme change.
function applySceneTheme() {
  const bg = cssColor("--scene-bg");
  scene.background = bg;
  if (scene.fog) scene.fog.color = bg;
  const major = cssColor("--grid-major"), minor = cssColor("--grid-minor");
  const gm = grid.material;
  (Array.isArray(gm) ? gm : [gm]).forEach((m, i) => { m.color = i === 0 ? major : minor; });
  const edgeColor = cssColor("--edge");
  getEdges().forEach(e => { e.material.color = edgeColor; });
}

function resolvedTheme() {
  return themeChoice === "system" ? (darkMedia.matches ? "dark" : "light") : themeChoice;
}
function applyTheme() {
  document.documentElement.setAttribute("data-theme", resolvedTheme());
  themeIcon.innerHTML = THEME_ICONS[themeChoice];
  themeBtn.title = "Theme: " + themeChoice[0].toUpperCase() + themeChoice.slice(1) + " (click to change)";
  applySceneTheme();
}

// Wire the theme toggle + system-theme listener, then apply the saved theme once. `sceneArg`/
// `gridArg` are the scene + grid to recolor; `getEdgesArg` returns the current edge lines (edges is
// reassigned in app.js on each model load).
export function initTheme(sceneArg, gridArg, getEdgesArg) {
  scene = sceneArg;
  grid = gridArg;
  getEdges = getEdgesArg;
  themeBtn = document.getElementById("theme-toggle");
  themeIcon = document.getElementById("theme-icon");
  darkMedia = window.matchMedia("(prefers-color-scheme: dark)");
  themeChoice = localStorage.getItem("ncad.theme") || "system";

  themeBtn.addEventListener("click", () => {
    themeChoice = THEME_ORDER[(THEME_ORDER.indexOf(themeChoice) + 1) % THEME_ORDER.length];
    localStorage.setItem("ncad.theme", themeChoice);
    applyTheme();
  });
  // When following the system and the OS theme flips, update live.
  darkMedia.addEventListener("change", () => { if (themeChoice === "system") applyTheme(); });
  applyTheme();
}
