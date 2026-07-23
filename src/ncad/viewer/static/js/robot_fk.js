// Forward kinematics for the Physics tab's live joint posing. Given a robot tree (from
// <name>.robot.json: base link + joints with parent/child/axis/parent-relative origin/limits) and a
// pose (one value per actuated joint), it computes each link's world placement by walking the tree
// - T_world(child) = T_world(parent) . translate(origin) . motion(axis, q) - the standard URDF FK.
//
// This REPLACES the per-joint mechanism sweep for open-chain robots: holding ALL joint values at
// once and re-solving the whole chain keeps every link rigidly attached to its parent (so a gripper
// jaw never drifts off the hand) and lets each joint be clamped to its own limit. Pure THREE matrix
// math, no scene/DOM state - the panel in app.js owns the sliders and applies the result to nodes.
import * as THREE from "three";

// Build the FK chain from a robot tree. Returns {baseLink, joints (in tree order), childToJoint,
// restOrigin per link, actuated joint list with limits}. restOrigin is the link's frame origin at
// rest (all q=0): the cumulative parent-relative joint origins down the tree, which equals where the
// in-place-authored geometry expects its link frame to sit.
export function buildFkChain(tree) {
  const joints = (tree.joints || []).filter(j => !j.loop_closure);
  const childToJoint = {};
  for (const j of joints) childToJoint[j.child] = j;
  // Topological order: a joint can be solved once its parent link's transform is known. The base
  // link is the root; repeatedly emit joints whose parent is already reachable.
  const ordered = [];
  const reachable = new Set([tree.base_link]);
  let guard = joints.length + 1;
  while (ordered.length < joints.length && guard-- > 0) {
    for (const j of joints) {
      if (!ordered.includes(j) && reachable.has(j.parent)) {
        ordered.push(j); reachable.add(j.child);
      }
    }
  }
  // Rest frame origins: cumulative parent-relative origins from the base (base = world origin).
  const restOrigin = { [tree.base_link]: new THREE.Vector3(0, 0, 0) };
  for (const j of ordered) {
    const o = j.origin || [0, 0, 0];
    restOrigin[j.child] = restOrigin[j.parent].clone().add(new THREE.Vector3(o[0], o[1], o[2]));
  }
  return { baseLink: tree.base_link, ordered, childToJoint, restOrigin, joints };
}

// The actuated joints (the ones that get a slider), each with its type + limit + a display unit.
// Revolute limits are radians (shown as degrees); prismatic limits are metres (shown as mm).
export function actuatedJoints(tree) {
  return (tree.joints || [])
    .filter(j => j.actuated && !j.loop_closure)
    .map(j => ({
      name: j.name, type: j.type,
      lower: (j.limit && j.limit[0] != null) ? j.limit[0] : defaultLower(j),
      upper: (j.limit && j.limit[1] != null) ? j.limit[1] : defaultUpper(j),
    }));
}

function defaultLower(joint) { return joint.type === "prismatic" ? 0 : -Math.PI; }
function defaultUpper(joint) { return joint.type === "prismatic" ? 0.1 : Math.PI; }

// Solve FK for a pose ({jointName: value}, radians for revolute / metres for prismatic). Returns
// {link: THREE.Matrix4} where each matrix is the NODE placement: it maps the link's rest-world
// geometry to its posed world position (identity at rest), so app.js can assign it to the instance
// node's matrix exactly like a motion frame does.
export function solveFk(chain, pose) {
  const worldByLink = { [chain.baseLink]: new THREE.Matrix4() };   // base at identity
  for (const j of chain.ordered) {
    const parentWorld = worldByLink[j.parent] || new THREE.Matrix4();
    const o = j.origin || [0, 0, 0];
    const offset = new THREE.Matrix4().makeTranslation(o[0], o[1], o[2]);
    const q = pose[j.name] || 0;
    const motion = jointMotion(j, q);
    // T_world(child) = T_world(parent) . translate(origin) . motion(q)
    worldByLink[j.child] = parentWorld.clone().multiply(offset).multiply(motion);
  }
  // Node matrix = T_world(link) . translate(-restOrigin): the authored geometry lives at world
  // coordinates (link-local = world - restOrigin at rest), so this repositions it under the pose.
  const nodes = {};
  for (const link in worldByLink) {
    const r = chain.restOrigin[link] || new THREE.Vector3();
    const back = new THREE.Matrix4().makeTranslation(-r.x, -r.y, -r.z);
    nodes[link] = worldByLink[link].clone().multiply(back);
  }
  return nodes;
}

// One joint's local motion transform for value q (about/along its axis, at the joint origin).
function jointMotion(joint, q) {
  const a = joint.axis || [0, 0, 1];
  const axis = new THREE.Vector3(a[0], a[1], a[2]).normalize();
  if (joint.type === "prismatic") {
    return new THREE.Matrix4().makeTranslation(axis.x * q, axis.y * q, axis.z * q);
  }
  // revolute / continuous: rotate q radians about the axis (through the joint origin).
  return new THREE.Matrix4().makeRotationAxis(axis, q);
}
