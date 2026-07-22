// By-material coloring: the global material->color model, the "what materials exist" queries, and
// the per-material color panel + the By-Material mode button glue.
//
// Extracted from app.js. The material-color STATE (matColors + its localStorage key + the
// "(no material)" bucket) is fully self-contained here. The scene-side pieces it needs are injected
// by initMaterials so nothing static-imports app.js: `isAssemblyScene` (a predicate over the live
// view mode), `getAssemblyMaterials`/`getElementMap` (both reassigned in app.js as models load, so
// read live), `getMode` (the current display mode, reassigned by setMode), and the `applyMode`/
// `setMode` callbacks (a color edit or a material-availability change re-applies the mode). applyMode
// itself stays in app.js: it renders ALL modes, and its By-Material branch calls colorFor (exported
// here). Each function/comment is kept verbatim except bare cross-concern reads becoming injected
// accessor calls.
import { paletteColor } from "./utils.js";

// Injected scene-side dependencies, set once by initMaterials.
let isAssemblyScene = null;
let getAssemblyMaterials = null;
let getElementMap = null;
let getMode = null;
let applyMode = null;
let setMode = null;

// The mapping is GLOBAL by material name and lives in localStorage, so a material means the
// same color across every model. "__none__" is the reserved bucket for bodies with no material.
const MAT_COLORS_KEY = "ncad.materialColors";
const NO_MATERIAL = "__none__";
let matColors = (() => {
  try { return JSON.parse(localStorage.getItem(MAT_COLORS_KEY)) || {}; }
  catch (e) { return {}; }
})();
// Resolution order: user-assigned (localStorage) > authored appearance color > stable palette.
// Unassigned bodies default to the neutral solid gray until the user colors the "(no material)".
export function colorFor(name, appearanceColor) {
  const key = name || NO_MATERIAL;
  if (matColors[key]) return matColors[key];
  if (name && appearanceColor) return appearanceColor;
  if (!name) return "#c6d3e2";
  return paletteColor(name);
}

function hasMaterials() {
  if (isAssemblyScene()) {
    return Object.values(getAssemblyMaterials()).some(m => m.material);
  }
  const elementMap = getElementMap();
  const els = (elementMap && elementMap.elements) || [];
  return els.some(e => e.material);
}

// Materials present in the loaded model, first-seen order, plus a trailing "(no material)"
// entry when any face/instance is unassigned. Each entry carries the appearance color (if any).
// In Assemblies mode the source is the per-instance materials; in Parts mode the element map.
function distinctMaterials() {
  const seen = new Map();
  let hasNone = false;
  const elementMap = getElementMap();
  const entries = isAssemblyScene()
    ? Object.values(getAssemblyMaterials()).map(m => ({material: m.material,
                                                  appearance_color: m.appearance_color}))
    : ((elementMap && elementMap.elements) || []);
  entries.forEach(e => {
    if (e.material) { if (!seen.has(e.material)) seen.set(e.material, e.appearance_color); }
    else hasNone = true;
  });
  const out = [...seen.entries()].map(([name, appearance]) => ({ name, appearance }));
  if (hasNone) out.push({ name: null, appearance: null });
  return out;
}

// Show/hide the By-Material mode button by whether the current model (part OR assembly) has
// materials; drop out of the mode if it no longer applies. Shared by the part + assembly paths.
export function updateByMaterialButton() {
  const byBtn = document.querySelector('#vc-modes .vc-btn[data-mode="bymaterial"]');
  if (byBtn) byBtn.hidden = !hasMaterials();
  if (getMode() === "bymaterial" && !hasMaterials()) { setMode("solid"); return; }
  syncMaterialBlock();
  applyMode();
}

function renderMaterialColors() {
  const wrap = document.getElementById("material-colors");
  wrap.innerHTML = "";
  distinctMaterials().forEach(m => {
    const key = m.name || NO_MATERIAL;
    const row = document.createElement("label");
    row.className = "matrow";
    const dot = document.createElement("span");
    dot.className = "dot"; dot.style.background = colorFor(m.name, m.appearance);
    const label = document.createElement("span");
    label.className = "mname"; label.textContent = m.name || "(no material)";
    const input = document.createElement("input");
    input.type = "color"; input.value = colorFor(m.name, m.appearance);
    input.addEventListener("input", () => {
      matColors[key] = input.value;
      localStorage.setItem(MAT_COLORS_KEY, JSON.stringify(matColors));
      dot.style.background = input.value;
      if (getMode() === "bymaterial") applyMode();   // live recolor
    });
    row.appendChild(dot); row.appendChild(label); row.appendChild(input);
    wrap.appendChild(row);
  });
}

export function syncMaterialBlock() {
  // The 16-preset appearance panel shows in "material" mode; the per-material color panel
  // shows in "bymaterial" mode.
  document.getElementById("vc-material").hidden = getMode() !== "material";
  const byPanel = document.getElementById("vc-bymaterial");
  byPanel.hidden = getMode() !== "bymaterial";
  if (getMode() === "bymaterial") renderMaterialColors();
}

// Called when the element map arrives (a separate promise from the glb): reveal the
// By-material mode only if this model has materials, re-render the panel, and re-apply the
// mode so a by-material recolor now has both the meshes and the material data.
export function onElementMapReady() {
  updateByMaterialButton();
}

// Wire the injected scene-side dependencies. Called once by app.js after applyMode/setMode +
// the accessors exist.
export function initMaterials(deps) {
  isAssemblyScene = deps.isAssemblyScene;
  getAssemblyMaterials = deps.getAssemblyMaterials;
  getElementMap = deps.getElementMap;
  getMode = deps.getMode;
  applyMode = deps.applyMode;
  setMode = deps.setMode;
}
