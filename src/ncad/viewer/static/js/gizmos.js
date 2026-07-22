// 3D gizmo + glyph builders: the axis gizmo, the ViewCube face label texture, and the joint-freedom
// glyphs (rotation arc / translation arrow). All are pure builders - they take arguments (+ THREE)
// and return fresh THREE objects, holding no module state - so they are a safe slice out of app.js.
// Each function keeps its original comment(s). Imported by app.js.
import * as THREE from "three";

export function cubeLabelTexture(text) {
  const c = document.createElement("canvas"); c.width = c.height = 128;
  const ctx = c.getContext("2d");
  ctx.fillStyle = "#e9eef4"; ctx.fillRect(0, 0, 128, 128);
  ctx.strokeStyle = "#9aa6b4"; ctx.lineWidth = 5; ctx.strokeRect(4, 4, 120, 120);
  ctx.fillStyle = "#33414f"; ctx.font = "bold 22px sans-serif";
  ctx.textAlign = "center"; ctx.textBaseline = "middle";
  ctx.fillText(text, 64, 66);
  const tex = new THREE.CanvasTexture(c); tex.anisotropy = 4;
  return tex;
}

// A small poly axis gizmo: three thin colored cylinders (X red / Y green / Z blue) + a center
// sphere. Poly meshes take real thickness and do NOT z-fight like GL LINES (AxesHelper), fixing the
// world-origin stutter. `size` is the axis length; opts.radius scales the shaft thickness. Reused
// for the world origin, instance origins, connector triads, and joint-glyph bases (DRY).
export function buildAxisGizmo(size, opts) {
  opts = opts || {};
  const r = opts.radius != null ? opts.radius : size * 0.04;
  const g = new THREE.Group();
  g.userData.isGizmo = true;
  const axes = [
    { color: 0xff5555, rot: [0, 0, -Math.PI / 2], off: [size / 2, 0, 0] },  // +X
    { color: 0x55ff55, rot: [0, 0, 0], off: [0, size / 2, 0] },             // +Y
    { color: 0x5599ff, rot: [Math.PI / 2, 0, 0], off: [0, 0, size / 2] },   // +Z
  ];
  for (const a of axes) {
    const m = new THREE.Mesh(new THREE.CylinderGeometry(r, r, size, 12),
                             new THREE.MeshBasicMaterial({ color: a.color }));
    m.rotation.set(a.rot[0], a.rot[1], a.rot[2]);
    m.position.set(a.off[0], a.off[1], a.off[2]);
    g.add(m);
  }
  g.add(new THREE.Mesh(new THREE.SphereGeometry(r * 1.6, 12, 12),
                       new THREE.MeshBasicMaterial({ color: 0xdddddd })));
  return g;
}

// True if the object is inside a gizmo group (so it is excluded from the pick raycast set).
export function _inGizmo(o) {
  for (let p = o; p; p = p.parent) if (p.userData && p.userData.isGizmo) return true;
  return false;
}

// A thin arc line in the plane perpendicular to `dir` (a rotation-freedom marker). Color-coded.
export function _rotArc(dir, size, color) {
  // Two in-plane basis vectors perpendicular to `dir`, so the arc lies around the rotation axis.
  const up = Math.abs(dir.z) > 0.9 ? new THREE.Vector3(1, 0, 0) : new THREE.Vector3(0, 0, 1);
  const u = new THREE.Vector3().crossVectors(dir, up).normalize();
  const w = new THREE.Vector3().crossVectors(dir, u).normalize();
  const rad = size * 0.6, pts = [];
  for (let i = 0; i <= 32; i++) {
    const t = (i / 32) * Math.PI * 1.5;   // a 270deg arc reads as "turns about this axis"
    pts.push(u.clone().multiplyScalar(Math.cos(t) * rad).add(w.clone().multiplyScalar(Math.sin(t) * rad)));
  }
  return new THREE.Line(new THREE.BufferGeometry().setFromPoints(pts),
                        new THREE.LineBasicMaterial({ color }));
}

// A thin double-headed arrow line along `dir` (a translation-freedom marker). Color-coded.
export function _transArrow(dir, size, color) {
  const h = size * 0.6, head = size * 0.16;
  const tip = dir.clone().multiplyScalar(h), tail = dir.clone().multiplyScalar(-h);
  // A perpendicular for the arrowhead barbs.
  const up = Math.abs(dir.z) > 0.9 ? new THREE.Vector3(1, 0, 0) : new THREE.Vector3(0, 0, 1);
  const perp = new THREE.Vector3().crossVectors(dir, up).normalize().multiplyScalar(head * 0.5);
  const pts = [tail, tip,
    tip, tip.clone().sub(dir.clone().multiplyScalar(head)).add(perp),
    tip, tip.clone().sub(dir.clone().multiplyScalar(head)).sub(perp),
    tail, tail.clone().add(dir.clone().multiplyScalar(head)).add(perp),
    tail, tail.clone().add(dir.clone().multiplyScalar(head)).sub(perp)];
  return new THREE.LineSegments(new THREE.BufferGeometry().setFromPoints(pts),
                               new THREE.LineBasicMaterial({ color }));
}

// A signature-keyed joint glyph at a joint's world connector frame: rotation -> arc about the axis;
// translation -> double arrow along it; cylindrical -> both; ball -> three arcs; screw -> arc+arrow
// on Z; fixed -> a cube. The signature axis "Z"/"X"/"Y" maps to that FRAME's vector (not world), so
// a tilted joint shows its freedom about the tilted axis. `frame` = {origin,x,y,z} (world, metres).
export function buildJointGlyph(joint, frame, size) {
  const g = new THREE.Group();
  g.userData.isGizmo = true;
  const axisVec = { X: frame.x, Y: frame.y, Z: frame.z, line: frame.z };
  const sig = joint.signature || [];
  if (joint.type === "fixed" || sig.length === 0) {
    g.add(new THREE.Mesh(new THREE.BoxGeometry(size * 0.4, size * 0.4, size * 0.4),
                         new THREE.MeshBasicMaterial({ color: 0x999999 })));
  }
  for (const a of sig) {
    const v = axisVec[a.axis] || frame.z;
    const dir = new THREE.Vector3(v[0], v[1], v[2]).normalize();
    if (a.motion === "rotation" || a.motion === "screw") g.add(_rotArc(dir, size, 0xffaa33));
    if (a.motion === "translation" || a.motion === "screw") g.add(_transArrow(dir, size, 0x33ccff));
  }
  g.position.set(frame.origin[0], frame.origin[1], frame.origin[2]);
  return g;
}
