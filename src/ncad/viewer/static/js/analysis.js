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
const _UNITS = { von_mises: "Pa", displacement: "m", temperature: "°C" };
const _LABELS = { von_mises: "von Mises", displacement: "displacement", temperature: "temperature" };

let scene = null;
let apiUrl = null;
let log = null;
let onMeshReady = null;        // app.js hook: (group) => set modelRoot + frame + applyMode
let clearPrevious = null;      // app.js hook: clear the current scene model

let legend = null;
let fieldSelect = null;
let minLabel = null;
let maxLabel = null;
let unitLabel = null;

let currentMesh = null;        // {geometry, material, group}
let currentData = null;        // the fetched {points, triangles, fields, ranges}
let currentField = null;

export function initAnalysis(deps) {
  scene = deps.scene;
  apiUrl = deps.apiUrl;
  log = deps.log;
  onMeshReady = deps.onMeshReady;
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
                       "warn"); clearAnalysis(); });
}

export function clearAnalysis() {
  if (currentMesh) {
    scene.remove(currentMesh.group);
    currentMesh.geometry.dispose();
    currentMesh.material.dispose();
    currentMesh = null;
  }
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
    return;
  }
  currentField = fields.includes("von_mises") ? "von_mises" : fields[0];
  _renderFieldOptions(fields);

  const geometry = new THREE.BufferGeometry();
  const positions = new Float32Array(data.points.length * 3);
  data.points.forEach((p, i) => { positions[i * 3] = p[0]; positions[i * 3 + 1] = p[1];
                                   positions[i * 3 + 2] = p[2]; });
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
  currentMesh = { geometry, material, group };
  scene.add(group);
  _applyField(currentField);
  legend.hidden = false;
  if (onMeshReady) onMeshReady(group);      // let app.js parent it as modelRoot + frame it
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
