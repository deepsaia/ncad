// Hierarchy tree builder: the feature-tree DOM node factory + its icon mapping. All pure DOM
// builders - they take a plain tree node (from the /hierarchy sidecar) and return fresh DOM,
// holding no module state - so they are a safe slice out of app.js. Each function/table keeps its
// original comment(s). Imported by app.js (loadHierarchy fetches the tree, then calls treeNode).

// Icons are Google Material Symbols (referenced by glyph name, drawn by the font), chosen
// per node kind and, for features, per OP CATEGORY (additive / subtractive / dress-up /
// boolean / placement / sketch). An unknown op falls back to the generic `feature` glyph.
export const TREE_ICONS = {
  part: "deployed_code",             // a 3D cube = the part
  feature: "settings",               // generic op
  element: "check_box_outline_blank",// a sketch primitive (empty square)
  sketch: "draw",                    // a sketch
  additive: "add_box",               // extrude/revolve/loft/sweep/rib/wrap (add material)
  subtractive: "indeterminate_check_box",  // pocket/hole/groove (remove material)
  dressup: "rounded_corner",         // fillet/chamfer/draft/shell (edge/wall treatment)
  boolean: "join",                   // boolean/split (combine/divide bodies)
  placement: "grid_view",            // pattern/mirror/transform (place copies)
  group: "folder",                   // the Bodies folder
  body: "deployed_code",             // a built body (cube)
};
export const OP_CATEGORY = {
  sketch: "sketch",
  extrude: "additive", revolve: "additive", loft: "additive", sweep: "additive",
  rib: "additive", wrap: "additive",
  pocket: "subtractive", hole: "subtractive", groove: "subtractive",
  fillet: "dressup", chamfer: "dressup", draft: "dressup", shell: "dressup",
  boolean: "boolean", split: "boolean",
  pattern: "placement", mirror: "placement", transform: "placement",
};
export function iconKey(node) {
  if (node.kind === "part") return "part";
  if (node.kind === "element") return "element";
  if (node.kind === "group") return "group";   // the Bodies folder
  if (node.kind === "body") return "body";      // a built body (cube)
  return OP_CATEGORY[node.op] || "feature";  // feature: category by op, else generic gear
}

// Build one tree node (and its subtree). The twist toggles a node's children; leaves
// hide the twist. Names/ops carry a class so the label toggle can hide them.
export function treeNode(node) {
  const wrap = document.createElement("div");
  wrap.className = "tree-node";
  const row = document.createElement("div");
  row.className = "tree-row";
  const kids = node.children || [];
  const twist = document.createElement("span");
  twist.className = "tree-twist" + (kids.length ? "" : " leaf");
  twist.textContent = "▼";
  const key = iconKey(node);
  const ico = document.createElement("span");
  ico.className = "tree-ico material-symbols-rounded " + node.kind + " " + key;
  ico.textContent = TREE_ICONS[key] || TREE_ICONS.feature;
  const label = node.name || node.id || "?";
  row.innerHTML = "";
  row.appendChild(twist);
  row.appendChild(ico);
  const nameEl = document.createElement("span");
  nameEl.className = "tree-name"; nameEl.textContent = label;
  row.appendChild(nameEl);
  if (node.op) {
    const opEl = document.createElement("span");
    opEl.className = "tree-op"; opEl.textContent = node.op;
    row.appendChild(opEl);
  }
  // A sketch feature shows its constraint status inline: a colored dot (green/amber/red),
  // plus a muted "dof N" label that reveals on row hover (a native title as a fallback), so
  // the constraint state is easy to read. Replaces the old separate status box.
  if (node.status) {
    const fail = (node.failing_ids && node.failing_ids.length)
      ? ` [${node.failing_ids.join(", ")}]` : "";
    const dot = document.createElement("span");
    dot.className = "status-dot tree-status " + node.status;
    row.appendChild(dot);
    const dof = document.createElement("span");
    dof.className = "tree-dof";
    dof.textContent = `${node.status}, dof ${node.dof}${fail}`;
    row.appendChild(dof);
    row.title = dof.textContent;
  }
  // A material chip (part default or a feature override) rides at the row's end.
  if (node.material) {
    const mat = document.createElement("span");
    mat.className = "tree-mat"; mat.textContent = node.material;
    mat.title = "material: " + node.material;
    row.appendChild(mat);
  }
  wrap.appendChild(row);
  if (kids.length) {
    const childWrap = document.createElement("div");
    childWrap.className = "tree-children";
    kids.forEach(c => childWrap.appendChild(treeNode(c)));
    wrap.appendChild(childWrap);
    twist.addEventListener("click", () => {
      const collapsed = wrap.classList.toggle("tree-collapsed");
      twist.textContent = collapsed ? "▶" : "▼";
    });
  }
  return wrap;
}
