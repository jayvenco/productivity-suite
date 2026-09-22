// Simpele, dependency-vrije force-directed graph (canvas 2D) -- net als
// Obsidian's graph-view, maar dan getagde taken/notities/kanban-kaarten/
// mindmaps die een tag delen, gegroepeerd rond een knooppunt vóór die tag
// (een bipartiete taggraaf i.p.v. losse item-naar-item-links, want dit
// project heeft geen [[wiki-links]] tussen items -- alleen gedeelde tags).
document.addEventListener("DOMContentLoaded", async () => {
  const canvas = document.getElementById("graph-canvas");
  const emptyMsg = document.getElementById("graph-empty");
  const wrap = canvas ? canvas.closest(".graph-wrap") : null;
  if (!canvas || !wrap) return;

  const COLORS = {
    task: "#8be9fd",
    note: "#ffb86c",
    kanban: "#bd93f9",
    mindmap: "#50fa7b",
    tag: "#6c7086",
  };

  const ctx = canvas.getContext("2d");
  let width = 0;
  let height = 480;

  function resize() {
    width = wrap.clientWidth;
    canvas.width = width * devicePixelRatio;
    canvas.height = height * devicePixelRatio;
    canvas.style.width = `${width}px`;
    canvas.style.height = `${height}px`;
    ctx.setTransform(devicePixelRatio, 0, 0, devicePixelRatio, 0, 0);
  }

  let response;
  try {
    response = await fetch("/graph/data");
  } catch (err) {
    return;
  }
  const data = await response.json();

  if (!data.nodes.length) {
    canvas.hidden = true;
    emptyMsg.hidden = false;
    return;
  }

  resize();
  window.addEventListener("resize", resize);

  const edgeCount = {};
  for (const edge of data.edges) {
    edgeCount[edge.source] = (edgeCount[edge.source] || 0) + 1;
    edgeCount[edge.target] = (edgeCount[edge.target] || 0) + 1;
  }

  const nodes = data.nodes.map((n, i) => {
    const angle = (i / data.nodes.length) * Math.PI * 2;
    const degree = edgeCount[n.id] || 0;
    return {
      ...n,
      x: width / 2 + Math.cos(angle) * 80,
      y: height / 2 + Math.sin(angle) * 80,
      vx: 0,
      vy: 0,
      radius: n.type === "tag" ? 8 + Math.min(14, degree * 1.5) : 6,
      fixed: false,
    };
  });
  const nodeById = new Map(nodes.map((n) => [n.id, n]));
  const edges = data.edges
    .map((e) => ({ source: nodeById.get(e.source), target: nodeById.get(e.target) }))
    .filter((e) => e.source && e.target);

  const textColor = getComputedStyle(document.body).color || "#e5e5e5";
  const edgeColor = getComputedStyle(document.body).getPropertyValue("--border") || "#444";

  function step() {
    // Afstoting tussen alle knooppuntparen.
    for (let i = 0; i < nodes.length; i++) {
      for (let j = i + 1; j < nodes.length; j++) {
        const a = nodes[i];
        const b = nodes[j];
        let dx = a.x - b.x;
        let dy = a.y - b.y;
        let distSq = dx * dx + dy * dy;
        if (distSq < 1) distSq = 1;
        const dist = Math.sqrt(distSq);
        const force = 900 / distSq;
        const fx = (dx / dist) * force;
        const fy = (dy / dist) * force;
        a.vx += fx;
        a.vy += fy;
        b.vx -= fx;
        b.vy -= fy;
      }
    }

    // Aantrekking langs edges (veer naar gewenste lengte).
    for (const edge of edges) {
      const dx = edge.target.x - edge.source.x;
      const dy = edge.target.y - edge.source.y;
      const dist = Math.sqrt(dx * dx + dy * dy) || 1;
      const targetLen = 70;
      const force = (dist - targetLen) * 0.02;
      const fx = (dx / dist) * force;
      const fy = (dy / dist) * force;
      edge.source.vx += fx;
      edge.source.vy += fy;
      edge.target.vx -= fx;
      edge.target.vy -= fy;
    }

    // Zachte trek naar het midden, zodat alles binnen beeld blijft.
    for (const node of nodes) {
      node.vx += (width / 2 - node.x) * 0.002;
      node.vy += (height / 2 - node.y) * 0.002;
    }

    for (const node of nodes) {
      if (node.fixed) continue;
      node.vx *= 0.82;
      node.vy *= 0.82;
      node.x += node.vx;
      node.y += node.vy;
      node.x = Math.max(node.radius, Math.min(width - node.radius, node.x));
      node.y = Math.max(node.radius, Math.min(height - node.radius, node.y));
    }
  }

  function draw() {
    ctx.clearRect(0, 0, width, height);

    ctx.strokeStyle = edgeColor.trim() || "rgba(255,255,255,0.15)";
    ctx.lineWidth = 1;
    for (const edge of edges) {
      ctx.beginPath();
      ctx.moveTo(edge.source.x, edge.source.y);
      ctx.lineTo(edge.target.x, edge.target.y);
      ctx.stroke();
    }

    for (const node of nodes) {
      ctx.beginPath();
      ctx.arc(node.x, node.y, node.radius, 0, Math.PI * 2);
      ctx.fillStyle = COLORS[node.type] || "#999";
      ctx.fill();

      ctx.font = node.type === "tag" ? "bold 11px sans-serif" : "10px sans-serif";
      ctx.fillStyle = textColor;
      ctx.textAlign = "center";
      ctx.fillText(truncate(node.label, node.type === "tag" ? 20 : 16), node.x, node.y - node.radius - 4);
    }
  }

  function truncate(text, max) {
    return text.length > max ? `${text.slice(0, max)}…` : text;
  }

  function loop() {
    step();
    draw();
    requestAnimationFrame(loop);
  }
  loop();

  // ---- Slepen + klikken ----
  let dragging = null;
  let dragMoved = false;

  function nodeAt(x, y) {
    for (let i = nodes.length - 1; i >= 0; i--) {
      const node = nodes[i];
      const dx = node.x - x;
      const dy = node.y - y;
      if (dx * dx + dy * dy <= (node.radius + 4) * (node.radius + 4)) return node;
    }
    return null;
  }

  function canvasPoint(event) {
    const rect = canvas.getBoundingClientRect();
    return { x: event.clientX - rect.left, y: event.clientY - rect.top };
  }

  canvas.addEventListener("mousedown", (event) => {
    const { x, y } = canvasPoint(event);
    const node = nodeAt(x, y);
    if (!node) return;
    dragging = node;
    dragMoved = false;
    node.fixed = true;
  });

  document.addEventListener("mousemove", (event) => {
    if (!dragging) return;
    const { x, y } = canvasPoint(event);
    dragging.x = x;
    dragging.y = y;
    dragging.vx = 0;
    dragging.vy = 0;
    dragMoved = true;
  });

  document.addEventListener("mouseup", () => {
    if (!dragging) return;
    dragging.fixed = false;
    if (!dragMoved && dragging.url) {
      window.location = dragging.url;
    }
    dragging = null;
  });

  canvas.addEventListener("mouseleave", () => {
    canvas.style.cursor = "default";
  });

  canvas.addEventListener("mousemove", (event) => {
    if (dragging) return;
    const { x, y } = canvasPoint(event);
    canvas.style.cursor = nodeAt(x, y) ? "pointer" : "default";
  });
});
