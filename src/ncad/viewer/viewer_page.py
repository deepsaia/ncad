"""The viewer single-page app (HTML + Three.js), returned as a string.

Kept as one module whose single function returns the page, so the server module stays
focused on HTTP. Three.js is loaded from a CDN via an import map, so there is no Node/npm
build step — the viewer runs on any machine with a browser.
"""

_PAGE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>ncad — 3D viewer</title>
<style>
  :root {
    --bg: #0f1419; --panel: #1a2230; --panel-2: #222d3d; --text: #e6edf3;
    --muted: #8b98a9; --accent: #4f9cf9; --accent-2: #2bd4a8; --border: #2c3a4f;
  }
  * { box-sizing: border-box; }
  html, body { margin: 0; height: 100%; overflow: hidden;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    background: var(--bg); color: var(--text); }
  #app { display: flex; height: 100%; }
  #sidebar { width: 270px; background: var(--panel); border-right: 1px solid var(--border);
    display: flex; flex-direction: column; padding: 18px; gap: 18px; overflow-y: auto; }
  #stage { flex: 1; position: relative; }
  canvas { display: block; }
  h1 { font-size: 16px; margin: 0; letter-spacing: 0.5px; }
  h1 .dot { color: var(--accent-2); }
  .label { font-size: 11px; text-transform: uppercase; letter-spacing: 0.8px;
    color: var(--muted); margin-bottom: 8px; }
  select, button { font: inherit; color: var(--text); background: var(--panel-2);
    border: 1px solid var(--border); border-radius: 8px; padding: 8px 10px; width: 100%; }
  select:hover, button:hover { border-color: var(--accent); cursor: pointer; }
  .modes { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
  .modes button.active { background: var(--accent); border-color: var(--accent);
    color: #051018; font-weight: 600; }
  .toggle-row { display: flex; align-items: center; justify-content: space-between;
    font-size: 13px; color: var(--muted); padding: 4px 0; }
  .switch { position: relative; width: 38px; height: 20px; }
  .switch input { opacity: 0; width: 0; height: 0; }
  .slider { position: absolute; inset: 0; background: var(--panel-2);
    border: 1px solid var(--border); border-radius: 20px; transition: .2s; }
  .slider:before { content: ""; position: absolute; height: 14px; width: 14px; left: 2px;
    top: 2px; background: var(--muted); border-radius: 50%; transition: .2s; }
  input:checked + .slider { background: var(--accent); }
  input:checked + .slider:before { transform: translateX(18px); background: #051018; }
  #info { font-size: 12px; color: var(--muted); line-height: 1.7;
    border-top: 1px solid var(--border); padding-top: 12px; margin-top: auto; }
  #info b { color: var(--text); font-weight: 600; }
  #hint { position: absolute; bottom: 14px; left: 50%; transform: translateX(-50%);
    font-size: 12px; color: var(--muted); background: rgba(15,20,25,.7);
    padding: 6px 14px; border-radius: 20px; border: 1px solid var(--border); }
  #spinner { position: absolute; inset: 0; display: flex; align-items: center;
    justify-content: center; color: var(--muted); font-size: 14px; }
</style>
</head>
<body>
<div id="app">
  <aside id="sidebar">
    <h1>ncad<span class="dot">.</span>viewer</h1>
    <div>
      <div class="label">Model</div>
      <select id="model-select"></select>
    </div>
    <div>
      <div class="label">Display mode</div>
      <div class="modes" id="modes">
        <button data-mode="solid" class="active">Solid</button>
        <button data-mode="material">Material</button>
        <button data-mode="wireframe">Wireframe</button>
        <button data-mode="xray">X-ray</button>
      </div>
    </div>
    <div>
      <div class="label">Scene</div>
      <label class="toggle-row">Edges
        <span class="switch"><input type="checkbox" id="t-edges" checked><span class="slider"></span></span>
      </label>
      <label class="toggle-row">Grid
        <span class="switch"><input type="checkbox" id="t-grid" checked><span class="slider"></span></span>
      </label>
      <label class="toggle-row">Auto-rotate
        <span class="switch"><input type="checkbox" id="t-rotate"><span class="slider"></span></span>
      </label>
    </div>
    <button id="reset-view">Reset view</button>
    <div id="info">
      <div><b>Size</b> <span id="i-size">—</span></div>
      <div><b>Triangles</b> <span id="i-tris">—</span></div>
      <div><b>Meshes</b> <span id="i-meshes">—</span></div>
    </div>
  </aside>
  <main id="stage">
    <div id="spinner">loading…</div>
    <div id="hint">drag to orbit · scroll to zoom · right-drag to pan</div>
  </main>
</div>

<script type="importmap">
{ "imports": {
  "three": "https://unpkg.com/three@0.160.0/build/three.module.js",
  "three/addons/": "https://unpkg.com/three@0.160.0/examples/jsm/"
}}
</script>

<script type="module">
import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";

const stage = document.getElementById("stage");
const spinner = document.getElementById("spinner");

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x0f1419);

const camera = new THREE.PerspectiveCamera(45, stage.clientWidth / stage.clientHeight, 0.01, 1000);
const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setPixelRatio(window.devicePixelRatio);
renderer.setSize(stage.clientWidth, stage.clientHeight);
stage.appendChild(renderer.domElement);

const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;

scene.add(new THREE.HemisphereLight(0xffffff, 0x33404f, 0.9));
const key = new THREE.DirectionalLight(0xffffff, 1.6);
key.position.set(6, 12, 8); scene.add(key);
const fill = new THREE.DirectionalLight(0x9fc7ff, 0.5);
fill.position.set(-8, 4, -6); scene.add(fill);

let grid = new THREE.GridHelper(40, 40, 0x2c3a4f, 0x1c2735);
scene.add(grid);

const SOLID = new THREE.MeshStandardMaterial({ color: 0xc6d3e2, metalness: 0.05, roughness: 0.85, flatShading: true });
const MATERIAL = new THREE.MeshStandardMaterial({ color: 0xb98a5a, metalness: 0.1, roughness: 0.6 });
const WIRE = new THREE.MeshBasicMaterial({ color: 0x4f9cf9, wireframe: true });
const XRAY = new THREE.MeshStandardMaterial({ color: 0x4f9cf9, transparent: true, opacity: 0.28, depthWrite: false });

let modelRoot = null;
let edges = [];
let mode = "solid";
let showEdges = true;

const loader = new GLTFLoader();

function clearModel() {
  if (modelRoot) { scene.remove(modelRoot); modelRoot = null; }
  edges.forEach(e => scene.remove(e)); edges = [];
}

function applyMode() {
  if (!modelRoot) return;
  const mat = { solid: SOLID, material: MATERIAL, wireframe: WIRE, xray: XRAY }[mode];
  modelRoot.traverse(o => { if (o.isMesh) o.material = mat; });
  edges.forEach(e => { e.visible = showEdges && mode !== "wireframe"; });
}

function frameModel() {
  const box = new THREE.Box3().setFromObject(modelRoot);
  const size = box.getSize(new THREE.Vector3());
  const center = box.getCenter(new THREE.Vector3());
  modelRoot.position.sub(center);
  edges.forEach(e => e.position.sub(center));
  const radius = Math.max(size.x, size.y, size.z);
  camera.position.set(radius * 1.4, radius * 1.1, radius * 1.6);
  camera.near = radius / 100; camera.far = radius * 50; camera.updateProjectionMatrix();
  controls.target.set(0, 0, 0); controls.update();
  document.getElementById("i-size").textContent =
    `${size.x.toFixed(1)} × ${size.z.toFixed(1)} × ${size.y.toFixed(1)} m`;
}

function loadModel(name) {
  spinner.style.display = "flex";
  loader.load(`/models/${name}`, gltf => {
    clearModel();
    modelRoot = gltf.scene;
    let tris = 0, meshes = 0;
    modelRoot.traverse(o => {
      if (o.isMesh) {
        meshes++;
        const geo = o.geometry;
        tris += (geo.index ? geo.index.count : geo.attributes.position.count) / 3;
        const eg = new THREE.EdgesGeometry(geo, 25);
        const line = new THREE.LineSegments(eg, new THREE.LineBasicMaterial({ color: 0x1a2230 }));
        o.updateWorldMatrix(true, false);
        line.applyMatrix4(o.matrixWorld);
        edges.push(line); scene.add(line);
      }
    });
    scene.add(modelRoot);
    document.getElementById("i-tris").textContent = Math.round(tris).toLocaleString();
    document.getElementById("i-meshes").textContent = meshes;
    applyMode(); frameModel();
    spinner.style.display = "none";
  }, undefined, err => { spinner.textContent = "failed to load model"; console.error(err); });
}

// UI wiring
document.querySelectorAll("#modes button").forEach(btn => {
  btn.addEventListener("click", () => {
    document.querySelectorAll("#modes button").forEach(b => b.classList.remove("active"));
    btn.classList.add("active"); mode = btn.dataset.mode; applyMode();
  });
});
document.getElementById("t-edges").addEventListener("change", e => { showEdges = e.target.checked; applyMode(); });
document.getElementById("t-grid").addEventListener("change", e => { grid.visible = e.target.checked; });
document.getElementById("t-rotate").addEventListener("change", e => { controls.autoRotate = e.target.checked; });
document.getElementById("reset-view").addEventListener("click", () => { if (modelRoot) frameModel(); });

const select = document.getElementById("model-select");
select.addEventListener("change", () => loadModel(select.value));

fetch("/api/models").then(r => r.json()).then(data => {
  if (!data.models.length) { spinner.textContent = "no models in the models directory"; return; }
  data.models.forEach(name => {
    const opt = document.createElement("option"); opt.value = name; opt.textContent = name;
    select.appendChild(opt);
  });
  loadModel(data.models[0]);
});

window.addEventListener("resize", () => {
  camera.aspect = stage.clientWidth / stage.clientHeight; camera.updateProjectionMatrix();
  renderer.setSize(stage.clientWidth, stage.clientHeight);
});

(function animate() {
  requestAnimationFrame(animate);
  controls.update();
  renderer.render(scene, camera);
})();
</script>
</body>
</html>
"""


def render_viewer_page() -> str:
    """Return the viewer single-page app as an HTML string."""
    return _PAGE
