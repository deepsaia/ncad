// Analysis mode (S7 FEA): loads a part's boundary field mesh (.analysis.mesh.json) and colors it
// by a chosen scalar (von Mises / displacement / temperature) via a jet-style colormap, with a
// bottom-center legend (field selector + gradient bar + min/max). The field mesh is a single
// vertex-colored surface; app.js parents it as modelRoot and frames it, so this module owns only
// the geometry build + coloring + legend. Injected deps keep it from importing app.js.

import * as THREE from "three";

// A perceptual-ish blue->cyan->green->yellow->red ramp (matplotlib "coolwarm"-adjacent stops),
// matching the CSS gradient in #analysis-gradient so the legend reads the same as the mesh.
const _RAMP = [
  [0.231, 0.298, 0.753], [0.427, 0.690, 0.937], [0.624, 0.851, 0.561],
  [0.953, 0.890, 0.353], [0.937, 0.541, 0.227], [0.706, 0.016, 0.149],
];
const _MM_TO_M = 0.001;   // the kernel meshes in mm; the viewer scene is metre-scale (glTF convention)
const _UNITS = { von_mises: "Pa", displacement: "m", temperature: "°C" };
const _LABELS = { von_mises: "von Mises", displacement: "displacement", temperature: "temperature" };

let scene = null;
let apiUrl = null;
let log = null;
let onMeshReady = null;        // app.js hook: (group) => set modelRoot + frame + applyMode
let onDone = null;             // app.js hook: () => hide the spinner (also on an empty/failed load)
let clearPrevious = null;      // app.js hook: clear the current scene model

let legend = null;
let fieldSelect = null;
let minLabel = null;
let maxLabel = null;
let unitLabel = null;

let currentMesh = null;        // {geometry, material, group}
let currentData = null;        // the fetched {points, triangles, fields, ranges}
let currentField = null;
let group_labels = [];         // glyph label sprite textures, disposed on clear

export function initAnalysis(deps) {
  scene = deps.scene;
  apiUrl = deps.apiUrl;
  log = deps.log;
  onMeshReady = deps.onMeshReady;
  onDone = deps.onDone;
  clearPrevious = deps.clearPrevious;

  legend = document.getElementById("analysis-legend");
  fieldSelect = document.getElementById("analysis-field");
  minLabel = document.getElementById("analysis-min");
  maxLabel = document.getElementById("analysis-max");
  unitLabel = document.getElementById("analysis-unit");

  fieldSelect.addEventListener("change", () => setField(fieldSelect.value));
}

export function loadAnalysis(name) {
  fetch(apiUrl(`/analysis-mesh/${encodeURIComponent(name)}`))
    .then(r => (r.ok ? r.json() : Promise.reject(new Error("no analysis mesh"))))
    .then(data => _renderMesh(data))
    .catch(() => { log(`analysis: no field mesh for ${name} (run a solve with ncad[fea] + ccx)`,
                       "warn"); clearAnalysis(); if (onDone) onDone(); });
}

export function clearAnalysis() {
  if (currentMesh) {
    scene.remove(currentMesh.group);
    currentMesh.geometry.dispose();
    currentMesh.material.dispose();
    currentMesh = null;
  }
  group_labels.forEach(l => l.texture.dispose());
  group_labels = [];
  currentData = null;
  if (legend) legend.hidden = true;
}

function _renderMesh(data) {
  clearAnalysis();
  if (clearPrevious) clearPrevious();       // drop any part/robot scene before the field mesh
  currentData = data;
  const fields = Object.keys(data.fields || {});
  if (!fields.length || !data.points.length) {
    log("analysis: field mesh has no data", "warn");
    if (onDone) onDone();
    return;
  }
  currentField = fields.includes("von_mises") ? "von_mises" : fields[0];
  _renderFieldOptions(fields);

  const geometry = new THREE.BufferGeometry();
  const positions = new Float32Array(data.points.length * 3);
  // The mesh JSON is in the kernel's millimetres; the rest of the viewer is metre-scale (the glTF
  // export divides mm->m). Scale here so the field mesh sits in the same scene as everything else.
  data.points.forEach((p, i) => { positions[i * 3] = p[0] * _MM_TO_M;
                                   positions[i * 3 + 1] = p[1] * _MM_TO_M;
                                   positions[i * 3 + 2] = p[2] * _MM_TO_M; });
  geometry.setAttribute("position", new THREE.BufferAttribute(positions, 3));
  geometry.setAttribute("color", new THREE.BufferAttribute(
    new Float32Array(data.points.length * 3), 3));
  geometry.setIndex(data.triangles.flat());
  geometry.computeVertexNormals();

  const material = new THREE.MeshStandardMaterial({
    vertexColors: true, metalness: 0.1, roughness: 0.75, side: THREE.DoubleSide });
  const mesh = new THREE.Mesh(geometry, material);
  mesh.userData.fieldMesh = true;           // applyMode must NOT re-materialize this mesh
  mesh.castShadow = true; mesh.receiveShadow = true;
  const group = new THREE.Group();
  group.add(mesh);
  // Load glyphs: arrows for force/pressure/gravity/flux, a pinned marker for a fixed support, so
  // the user sees WHAT acts on the model. Sized to the model extent so they read at any scale.
  const extent = _meshExtent(data.points) * _MM_TO_M;
  for (const glyph of data.loads || []) _addGlyph(group, glyph, extent);
  currentMesh = { geometry, material, group };
  scene.add(group);
  _applyField(currentField);
  legend.hidden = false;
  if (onMeshReady) onMeshReady(group);      // let app.js parent it as modelRoot + frame it
}

// The largest bounding-box extent of the point cloud (mm), for sizing the glyphs proportionally.
function _meshExtent(points) {
  const lo = [Infinity, Infinity, Infinity];
  const hi = [-Infinity, -Infinity, -Infinity];
  for (const p of points) {
    for (let a = 0; a < 3; a += 1) { lo[a] = Math.min(lo[a], p[a]); hi[a] = Math.max(hi[a], p[a]); }
  }
  return Math.max(hi[0] - lo[0], hi[1] - lo[1], hi[2] - lo[2]) || 1;
}

const _GLYPH_COLORS = {
  fixed: 0x9aa6b4, force: 0xef8a3a, pressure: 0xef4b3a, gravity: 0x6db0ef,
  flux: 0xf3b73a, film: 0xf3e35a, radiation: 0xef6a3a, temperature: 0xb40426,
};

// Add one glyph to the group: an arrow (loads) or a small octahedron marker (a fixed support), at
// the glyph's anchor (mm->m) pointing along its direction, plus a floating text label so the user
// knows what each colored arrow/marker is. Length is a fraction of the model.
function _addGlyph(group, glyph, extent) {
  const at = new THREE.Vector3(glyph.at[0], glyph.at[1], glyph.at[2]).multiplyScalar(_MM_TO_M);
  const dir = new THREE.Vector3(glyph.dir[0], glyph.dir[1], glyph.dir[2]);
  const color = _GLYPH_COLORS[glyph.kind] || 0xffffff;
  let tip;   // where the label floats: the arrow tip, or just above a fixed marker
  if (glyph.kind === "fixed" || dir.lengthSq() < 1e-9) {
    const marker = new THREE.Mesh(
      new THREE.OctahedronGeometry(extent * 0.05),
      new THREE.MeshBasicMaterial({ color, transparent: true, opacity: 0.9 }));
    marker.position.copy(at);
    marker.userData.fieldMesh = true;        // applyMode must not re-materialize glyphs
    group.add(marker);
    tip = at.clone().add(new THREE.Vector3(0, 0, extent * 0.09));
  } else {
    const arrow = new THREE.ArrowHelper(dir.clone().normalize(), at, extent * 0.4, color,
                                        extent * 0.12, extent * 0.07);
    arrow.traverse(o => { o.userData.fieldMesh = true; });
    group.add(arrow);
    tip = at.clone().add(dir.clone().normalize().multiplyScalar(extent * 0.44));
  }
  group.add(_makeLabel(`${glyph.name}: ${glyph.kind}`, tip, color, extent));
}

// A camera-facing text sprite (canvas texture) for a glyph label, colored to match its glyph.
function _makeLabel(text, position, color, extent) {
  const pad = 8;
  const font = 40;
  const measure = document.createElement("canvas").getContext("2d");
  measure.font = `${font}px sans-serif`;
  const w = Math.ceil(measure.measureText(text).width) + pad * 2;
  const h = font + pad * 2;
  const canvas = document.createElement("canvas");
  canvas.width = w; canvas.height = h;
  const ctx = canvas.getContext("2d");
  ctx.font = `${font}px sans-serif`;
  ctx.fillStyle = "rgba(20,22,28,0.72)";
  ctx.fillRect(0, 0, w, h);
  ctx.fillStyle = "#" + color.toString(16).padStart(6, "0");
  ctx.textBaseline = "middle";
  ctx.fillText(text, pad, h / 2);
  const texture = new THREE.CanvasTexture(canvas);
  texture.minFilter = THREE.LinearFilter;
  const sprite = new THREE.Sprite(new THREE.SpriteMaterial({ map: texture, transparent: true,
                                                             depthTest: false }));
  sprite.position.copy(position);
  // A small, readable label: a fraction of the model extent, capped so it never dominates.
  const scale = Math.min(extent * 0.09, 0.02);
  sprite.scale.set(scale * (w / h), scale, 1);
  sprite.userData.fieldMesh = true;        // applyMode must not touch glyph labels
  group_labels.push({ texture });          // tracked for disposal on clear
  return sprite;
}

export function setField(name) {
  if (!currentData || !currentData.fields[name]) return;
  currentField = name;
  _applyField(name);
}

function _applyField(name) {
  const values = currentData.fields[name];
  const [lo, hi] = currentData.ranges[name] || [0, 1];
  const span = hi - lo || 1;
  const colors = currentMesh.geometry.getAttribute("color");
  for (let i = 0; i < values.length; i += 1) {
    const t = (values[i] - lo) / span;
    const [r, g, b] = _colormap(t);
    colors.setXYZ(i, r, g, b);
  }
  colors.needsUpdate = true;
  _renderLegend(name, lo, hi);
}

function _renderLegend(name, lo, hi) {
  minLabel.textContent = _fmt(lo);
  maxLabel.textContent = _fmt(hi);
  unitLabel.textContent = _UNITS[name] || "";
  if (fieldSelect.value !== name) fieldSelect.value = name;
}

function _renderFieldOptions(fields) {
  fieldSelect.innerHTML = "";
  for (const name of fields) {
    const opt = document.createElement("option");
    opt.value = name;
    opt.textContent = _LABELS[name] || name;
    fieldSelect.appendChild(opt);
  }
  fieldSelect.value = currentField;
}

// Map a normalized t in [0,1] to an [r,g,b] triple by linear interpolation over the ramp stops.
function _colormap(t) {
  const x = Math.max(0, Math.min(1, t)) * (_RAMP.length - 1);
  const i = Math.min(_RAMP.length - 2, Math.floor(x));
  const f = x - i;
  const a = _RAMP[i];
  const b = _RAMP[i + 1];
  return [a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f, a[2] + (b[2] - a[2]) * f];
}

// A compact numeric label for the legend ends (3 significant figures, sci notation for big/small).
function _fmt(v) {
  const abs = Math.abs(v);
  if (abs !== 0 && (abs >= 1e5 || abs < 1e-3)) return v.toExponential(2);
  return Number(v.toPrecision(3)).toString();
}
