"""The viewer single-page app (HTML + Three.js), returned as a string.

Kept as one module whose single function returns the page, so the server module stays
focused on HTTP. Three.js is loaded from a CDN via an import map, so there is no Node/npm
build step; the viewer runs on any machine with a browser.
"""

_PAGE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>ncad 3D viewer</title>
<style>
  :root {
    --bg: #0d1117; --bg-2: #11161f; --panel: #161d29; --panel-2: #1e2735;
    --text: #e8eef5; --muted: #8a97a8; --accent: #5aa0ff; --accent-2: #2bd4a8;
    --border: #283546; --shadow: 0 8px 30px rgba(0,0,0,.45);
  }
  * { box-sizing: border-box; }
  html, body { margin: 0; height: 100%; overflow: hidden;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Inter, sans-serif;
    background: var(--bg); color: var(--text); -webkit-font-smoothing: antialiased; }
  #app { display: flex; height: 100%; }

  /* Sidebar */
  #sidebar { width: 286px; background: linear-gradient(180deg, var(--panel), var(--bg-2));
    border-right: 1px solid var(--border); display: flex; flex-direction: column;
    padding: 20px; gap: 22px; overflow-y: auto; }
  .brand { display: flex; align-items: baseline; gap: 2px; }
  .brand h1 { font-size: 18px; margin: 0; font-weight: 700; letter-spacing: 0.3px; }
  .brand .dot { color: var(--accent-2); font-size: 22px; line-height: 0; }
  .brand .sub { margin-left: auto; font-size: 10px; text-transform: uppercase;
    letter-spacing: 1px; color: var(--muted); padding-top: 4px; }
  .label { font-size: 10.5px; text-transform: uppercase; letter-spacing: 1px;
    color: var(--muted); margin-bottom: 9px; font-weight: 600; }
  select, .btn { font: inherit; font-size: 13px; color: var(--text);
    background: var(--panel-2); border: 1px solid var(--border); border-radius: 9px;
    padding: 9px 11px; width: 100%; transition: border-color .15s, background .15s; }
  select:hover, .btn:hover { border-color: var(--accent); cursor: pointer; }
  .modes { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
  .modes .btn.active { background: var(--accent); border-color: var(--accent);
    color: #04101f; font-weight: 700; box-shadow: 0 2px 12px rgba(90,160,255,.35); }

  .swatches { display: grid; grid-template-columns: repeat(8, 1fr); gap: 6px; }
  .swatch { aspect-ratio: 1; border-radius: 6px; border: 1.5px solid var(--border);
    cursor: pointer; transition: transform .12s, border-color .12s; }
  .swatch:hover { transform: translateY(-2px); }
  .swatch.active { border-color: var(--text); box-shadow: 0 0 0 2px var(--accent); }

  .toggle-row { display: flex; align-items: center; justify-content: space-between;
    font-size: 13px; color: var(--text); padding: 5px 0; }
  .switch { position: relative; width: 40px; height: 22px; }
  .switch input { opacity: 0; width: 0; height: 0; }
  .slider { position: absolute; inset: 0; background: var(--panel-2);
    border: 1px solid var(--border); border-radius: 22px; transition: .2s; }
  .slider:before { content: ""; position: absolute; height: 16px; width: 16px; left: 2px;
    top: 2px; background: var(--muted); border-radius: 50%; transition: .2s; }
  input:checked + .slider { background: var(--accent); border-color: var(--accent); }
  input:checked + .slider:before { transform: translateX(18px); background: #04101f; }
  .spacer { margin-top: auto; }

  /* Stage */
  #stage { flex: 1; position: relative; }
  canvas { display: block; }
  #spinner { position: absolute; inset: 0; display: flex; align-items: center;
    justify-content: center; color: var(--muted); font-size: 14px; pointer-events: none; }
  #hint { position: absolute; bottom: 16px; left: 50%; transform: translateX(-50%);
    font-size: 12px; color: var(--muted); background: rgba(13,17,23,.72);
    padding: 7px 16px; border-radius: 22px; border: 1px solid var(--border);
    backdrop-filter: blur(6px); }

  /* Floating panels container, top-right; stacked, each section collapsible */
  #panels { position: absolute; top: 16px; right: 16px; width: 300px;
    display: flex; flex-direction: column; gap: 12px; }
  .panel { background: rgba(22,29,41,.92); border: 1px solid var(--border);
    border-radius: 12px; box-shadow: var(--shadow); backdrop-filter: blur(10px);
    overflow: hidden; }
  .panel-head { display: flex; align-items: center; gap: 8px; padding: 12px 14px;
    cursor: pointer; user-select: none; }
  .panel-head .title { font-size: 12px; font-weight: 700; text-transform: uppercase;
    letter-spacing: 1px; }
  .panel-head .chev { margin-left: auto; color: var(--muted); transition: transform .2s;
    font-size: 12px; }
  .panel.collapsed .panel-head .chev { transform: rotate(-90deg); }
  .panel-body { padding: 0 14px 14px; max-height: 56vh; overflow: auto; }
  .panel.collapsed .panel-body { display: none; }
  .bom-row { display: flex; justify-content: space-between; align-items: baseline;
    font-size: 13px; padding: 7px 0; border-top: 1px solid var(--border); }
  .bom-row:first-child { border-top: none; }
  .bom-row .k { color: var(--muted); }
  .bom-row .v { font-weight: 600; font-variant-numeric: tabular-nums; }
  .bom-row .u { color: var(--muted); font-weight: 400; font-size: 11px; margin-left: 3px; }
  .panel-empty { font-size: 12px; color: var(--muted); padding: 8px 0; }
  #plan-body { padding: 12px; background: #ffffff; border-radius: 0 0 11px 11px; }
  #plan-body svg { width: 100%; height: auto; display: block; }

  #info { font-size: 12px; color: var(--muted); line-height: 1.8;
    border-top: 1px solid var(--border); padding-top: 14px; }
  #info b { color: var(--text); font-weight: 600; }
</style>
</head>
<body>
<div id="app">
  <aside id="sidebar">
    <div class="brand"><h1>ncad<span class="dot">.</span></h1><span class="sub">viewer</span></div>
    <div>
      <div class="label">Model</div>
      <select id="model-select"></select>
    </div>
    <div>
      <div class="label">Display mode</div>
      <div class="modes" id="modes">
        <button class="btn active" data-mode="solid">Solid</button>
        <button class="btn" data-mode="material">Material</button>
        <button class="btn" data-mode="wireframe">Wireframe</button>
        <button class="btn" data-mode="xray">X-ray</button>
      </div>
    </div>
    <div id="material-block">
      <div class="label">Material</div>
      <div class="swatches" id="swatches"></div>
    </div>
    <div>
      <div class="label">Lighting</div>
      <select id="light-select">
        <option value="sun">Sun (directional)</option>
        <option value="studio">Studio (3-point)</option>
        <option value="spotlight">Spotlight</option>
        <option value="overcast">Overcast (soft)</option>
      </select>
    </div>
    <div>
      <div class="label">Scene</div>
      <label class="toggle-row">Edges
        <span class="switch"><input type="checkbox" id="t-edges" checked><span class="slider"></span></span>
      </label>
      <label class="toggle-row">Grid
        <span class="switch"><input type="checkbox" id="t-grid" checked><span class="slider"></span></span>
      </label>
      <label class="toggle-row">Shadows
        <span class="switch"><input type="checkbox" id="t-shadow" checked><span class="slider"></span></span>
      </label>
      <label class="toggle-row">Auto-rotate
        <span class="switch"><input type="checkbox" id="t-rotate"><span class="slider"></span></span>
      </label>
    </div>
    <button class="btn" id="reset-view">Reset view</button>
    <div class="spacer"></div>
    <div id="info">
      <div><b>Size</b> <span id="i-size">-</span></div>
      <div><b>Triangles</b> <span id="i-tris">-</span></div>
      <div><b>Meshes</b> <span id="i-meshes">-</span></div>
    </div>
  </aside>

  <main id="stage">
    <div id="spinner">loading…</div>
    <div id="panels">
      <section class="panel" id="bom" data-store="ncad.panel.bom" aria-label="Bill of materials">
        <header class="panel-head"><span class="title">Bill of materials</span><span class="chev">▼</span></header>
        <div class="panel-body" id="bom-body"><div class="panel-empty">select a model</div></div>
      </section>
      <section class="panel" id="plan" data-store="ncad.panel.plan" aria-label="Plan view">
        <header class="panel-head"><span class="title">Plan view</span><span class="chev">▼</span></header>
        <div class="panel-body" id="plan-body"><div class="panel-empty">select a model</div></div>
      </section>
    </div>
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
scene.background = new THREE.Color(0x0d1117);
scene.fog = new THREE.Fog(0x0d1117, 40, 120);

const camera = new THREE.PerspectiveCamera(45, stage.clientWidth / stage.clientHeight, 0.01, 1000);
const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setPixelRatio(window.devicePixelRatio);
renderer.setSize(stage.clientWidth, stage.clientHeight);
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
stage.appendChild(renderer.domElement);

const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.dampingFactor = 0.08;

// Ambient base, always on; the rig below provides the directional/spot character.
const ambient = new THREE.HemisphereLight(0xffffff, 0x2a3340, 0.45);
scene.add(ambient);

// A swappable light rig. Each preset clears and rebuilds `lightRig`.
const lightRig = new THREE.Group();
scene.add(lightRig);

function makeShadowCaster(light) {
  light.castShadow = true;
  light.shadow.mapSize.set(2048, 2048);
  light.shadow.bias = -0.0004;
  const c = light.shadow.camera;
  c.near = 0.5; c.far = 160; c.left = -40; c.right = 40; c.top = 40; c.bottom = -40;
  return light;
}

const LIGHT_PRESETS = {
  sun() {
    ambient.intensity = 0.45;
    const key = makeShadowCaster(new THREE.DirectionalLight(0xfff4e6, 2.2));
    key.position.set(12, 20, 8);
    const fill = new THREE.DirectionalLight(0x9fc7ff, 0.45); fill.position.set(-10, 6, -8);
    return [key, fill];
  },
  studio() {
    ambient.intensity = 0.5;
    const key = makeShadowCaster(new THREE.DirectionalLight(0xffffff, 1.5)); key.position.set(10, 14, 12);
    const fill = new THREE.DirectionalLight(0xcfe0ff, 0.9); fill.position.set(-12, 8, 6);
    const rim = new THREE.DirectionalLight(0xffffff, 1.1); rim.position.set(0, 10, -14);
    return [key, fill, rim];
  },
  spotlight() {
    ambient.intensity = 0.2;
    const spot = makeShadowCaster(new THREE.SpotLight(0xffffff, 900, 0, Math.PI / 6, 0.4, 1.4));
    spot.position.set(6, 26, 10);
    return [spot];
  },
  overcast() {
    ambient.intensity = 1.0;
    const soft = makeShadowCaster(new THREE.DirectionalLight(0xeaf0f6, 0.6));
    soft.position.set(4, 24, 6);
    return [soft];
  },
};

function setLighting(name) {
  lightRig.clear();
  const preset = LIGHT_PRESETS[name] || LIGHT_PRESETS.sun;
  preset().forEach(l => { lightRig.add(l); if (l.target) lightRig.add(l.target); });
  localStorage.setItem("ncad.light", name);
}

const ground = new THREE.Mesh(
  new THREE.PlaneGeometry(400, 400),
  new THREE.ShadowMaterial({ opacity: 0.32 })
);
ground.rotation.x = -Math.PI / 2; ground.receiveShadow = true; scene.add(ground);

let grid = new THREE.GridHelper(80, 80, 0x33455c, 0x1b2533);
scene.add(grid);

// Material presets for "Material" mode.
const MATERIALS = [
  { name: "Concrete",  color: 0xb8bdc4, metalness: 0.05, roughness: 0.9 },
  { name: "Brick",     color: 0xa8533a, metalness: 0.0,  roughness: 0.85 },
  { name: "Red brick", color: 0x8c3b2b, metalness: 0.0,  roughness: 0.9 },
  { name: "Timber",    color: 0xb9824f, metalness: 0.05, roughness: 0.6 },
  { name: "Oak",       color: 0x9c6b3f, metalness: 0.05, roughness: 0.55 },
  { name: "Sandstone", color: 0xd8c9a3, metalness: 0.0,  roughness: 0.8 },
  { name: "Plaster",   color: 0xeae6dd, metalness: 0.0,  roughness: 0.95 },
  { name: "Stucco",    color: 0xc9b79a, metalness: 0.0,  roughness: 0.85 },
  { name: "Steel",     color: 0x9aa6b4, metalness: 0.85, roughness: 0.35 },
  { name: "Copper",    color: 0xb87333, metalness: 0.9,  roughness: 0.4 },
  { name: "Glass",     color: 0x8fb8d8, metalness: 0.1,  roughness: 0.05, opacity: 0.45 },
  { name: "Slate",     color: 0x4a525c, metalness: 0.1,  roughness: 0.7 },
  { name: "Marble",    color: 0xe8e8ea, metalness: 0.05, roughness: 0.3 },
  { name: "Terracotta",color: 0xc06a4b, metalness: 0.0,  roughness: 0.8 },
  { name: "Graphite",  color: 0x2f3640, metalness: 0.3,  roughness: 0.6 },
  { name: "Mint",      color: 0x8fd4bf, metalness: 0.05, roughness: 0.55 },
];
let materialIndex = parseInt(localStorage.getItem("ncad.material") || "0", 10) || 0;

const SOLID = new THREE.MeshStandardMaterial({ color: 0xc6d3e2, metalness: 0.05, roughness: 0.85, flatShading: true });
const WIRE = new THREE.MeshBasicMaterial({ color: 0x5aa0ff, wireframe: true });
const XRAY = new THREE.MeshStandardMaterial({ color: 0x5aa0ff, transparent: true, opacity: 0.26, depthWrite: false });
function materialMat() {
  const m = MATERIALS[materialIndex];
  return new THREE.MeshStandardMaterial({ color: m.color, metalness: m.metalness, roughness: m.roughness });
}

let modelRoot = null, edges = [], mode = "solid", showEdges = true, castShadows = true;
const loader = new GLTFLoader();

function clearModel() {
  if (modelRoot) { scene.remove(modelRoot); modelRoot = null; }
  edges.forEach(e => scene.remove(e)); edges = [];
}

function applyMode() {
  if (!modelRoot) return;
  const mat = { solid: SOLID, material: materialMat(), wireframe: WIRE, xray: XRAY }[mode];
  modelRoot.traverse(o => { if (o.isMesh) { o.material = mat; o.castShadow = castShadows && mode !== "wireframe"; } });
  edges.forEach(e => { e.visible = showEdges && mode !== "wireframe"; });
}

function syncMaterialBlock() {
  // Material swatches stay hidden until the user picks "Material" display mode.
  document.getElementById("material-block").style.display = mode === "material" ? "" : "none";
}

function frameModel() {
  const box = new THREE.Box3().setFromObject(modelRoot);
  const size = box.getSize(new THREE.Vector3());
  const center = box.getCenter(new THREE.Vector3());
  modelRoot.position.sub(center);
  edges.forEach(e => e.position.sub(center));
  // Drop the model onto the ground plane (y=0 at its base).
  const half = size.y / 2;
  modelRoot.position.y += half; edges.forEach(e => e.position.y += half);
  const radius = Math.max(size.x, size.y, size.z);
  camera.position.set(radius * 1.4, radius * 1.05, radius * 1.6);
  camera.near = radius / 100; camera.far = radius * 50; camera.updateProjectionMatrix();
  controls.target.set(0, half, 0); controls.update();
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
        const line = new THREE.LineSegments(
          new THREE.EdgesGeometry(geo, 25),
          new THREE.LineBasicMaterial({ color: 0x0d1117 }));
        o.updateWorldMatrix(true, false); line.applyMatrix4(o.matrixWorld);
        edges.push(line); scene.add(line);
      }
    });
    scene.add(modelRoot);
    document.getElementById("i-tris").textContent = Math.round(tris).toLocaleString();
    document.getElementById("i-meshes").textContent = meshes;
    applyMode(); frameModel();
    spinner.style.display = "none";
  }, undefined, err => { spinner.textContent = "failed to load model"; console.error(err); });
  loadBom(name);
  loadPlan(name);
}

// ---- Bill of materials panel ----
const BOM_FIELDS = [
  { key: "floor_area", label: "Floor area", unit: "m²", digits: 1 },
  { key: "roof_area", label: "Roof area", unit: "m²", digits: 1 },
  { key: "wall_volume", label: "Wall volume", unit: "m³", digits: 2 },
  { key: "wall_face_area", label: "Wall face area", unit: "m²", digits: 1 },
  { key: "door_count", label: "Doors", unit: "", digits: 0 },
  { key: "window_count", label: "Windows", unit: "", digits: 0 },
];

function loadBom(name) {
  const body = document.getElementById("bom-body");
  fetch(`/api/bom/${name}`).then(r => r.ok ? r.json() : Promise.reject()).then(bom => {
    body.innerHTML = "";
    BOM_FIELDS.forEach(f => {
      if (!(f.key in bom)) return;
      const row = document.createElement("div"); row.className = "bom-row";
      const v = Number(bom[f.key]).toFixed(f.digits);
      row.innerHTML = `<span class="k">${f.label}</span>` +
        `<span class="v">${v}<span class="u">${f.unit}</span></span>`;
      body.appendChild(row);
    });
  }).catch(() => { body.innerHTML = '<div class="panel-empty">no BOM for this model</div>'; });
}

// Each floating panel collapses independently; state persists per panel in localStorage.
// Open/close is entirely the user's choice.
document.querySelectorAll(".panel").forEach(panel => {
  const storeKey = panel.dataset.store + ".collapsed";
  if (localStorage.getItem(storeKey) === "1") panel.classList.add("collapsed");
  panel.querySelector(".panel-head").addEventListener("click", () => {
    panel.classList.toggle("collapsed");
    localStorage.setItem(storeKey, panel.classList.contains("collapsed") ? "1" : "0");
  });
});

function loadPlan(name) {
  const body = document.getElementById("plan-body");
  fetch(`/api/plan/${name}`).then(r => r.ok ? r.text() : Promise.reject()).then(svg => {
    body.innerHTML = svg;
  }).catch(() => { body.innerHTML = '<div class="panel-empty">no plan for this model</div>'; });
}

// ---- swatches ----
const swatchWrap = document.getElementById("swatches");
MATERIALS.forEach((m, i) => {
  const s = document.createElement("div");
  s.className = "swatch" + (i === materialIndex ? " active" : "");
  s.style.background = "#" + m.color.toString(16).padStart(6, "0");
  s.title = m.name;
  s.addEventListener("click", () => {
    materialIndex = i; localStorage.setItem("ncad.material", String(i));
    document.querySelectorAll(".swatch").forEach(e => e.classList.remove("active"));
    s.classList.add("active");
    if (mode !== "material") { setMode("material"); } else { applyMode(); }
  });
  swatchWrap.appendChild(s);
});

// ---- mode + toggles (all persisted to localStorage) ----
function setMode(next) {
  mode = next;
  localStorage.setItem("ncad.mode", next);
  document.querySelectorAll("#modes .btn").forEach(b =>
    b.classList.toggle("active", b.dataset.mode === next));
  syncMaterialBlock();
  applyMode();
}
document.querySelectorAll("#modes .btn").forEach(btn =>
  btn.addEventListener("click", () => setMode(btn.dataset.mode)));

// A persisted boolean scene toggle: restores the saved state, applies it, and saves changes.
function bindToggle(id, key, apply) {
  const el = document.getElementById(id);
  const saved = localStorage.getItem(key);
  if (saved !== null) el.checked = saved === "1";
  apply(el.checked);
  el.addEventListener("change", e => {
    localStorage.setItem(key, e.target.checked ? "1" : "0");
    apply(e.target.checked);
  });
}
bindToggle("t-edges", "ncad.edges", v => { showEdges = v; applyMode(); });
bindToggle("t-grid", "ncad.grid", v => { grid.visible = v; });
bindToggle("t-shadow", "ncad.shadow", v => { castShadows = v; applyMode(); });
bindToggle("t-rotate", "ncad.rotate", v => { controls.autoRotate = v; });
document.getElementById("reset-view").addEventListener("click", () => { if (modelRoot) frameModel(); });

// Restore the saved display mode (default solid). Buttons reflect it; applyMode on load.
setMode(localStorage.getItem("ncad.mode") || "solid");

// Lighting selector (persisted).
const lightSelect = document.getElementById("light-select");
const savedLight = localStorage.getItem("ncad.light") || "sun";
lightSelect.value = savedLight;
setLighting(savedLight);
lightSelect.addEventListener("change", () => setLighting(lightSelect.value));

// Material swatches start hidden (solid is the default mode).
syncMaterialBlock();

const select = document.getElementById("model-select");
// Selecting a model updates the URL path so it can be shared/deep-linked.
select.addEventListener("change", () => {
  loadModel(select.value);
  history.replaceState(null, "", "/" + select.value);
});

fetch("/api/models").then(r => r.json()).then(data => {
  if (!data.models.length) { spinner.textContent = "no models in the models directory"; return; }
  data.models.forEach(name => {
    const opt = document.createElement("option"); opt.value = name; opt.textContent = name;
    select.appendChild(opt);
  });
  // Deep link: /<model>.glb in the URL preselects that model; else the first one.
  const requested = decodeURIComponent(location.pathname.replace(/^\//, ""));
  const initial = data.models.includes(requested) ? requested : data.models[0];
  select.value = initial;
  loadModel(initial);
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
