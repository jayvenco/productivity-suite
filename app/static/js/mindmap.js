// Simpele mindmap: componenten (losse tekstblokjes) vrij te verslepen op een
// canvas, met SVG-lijnen als verbindingen. Geen library -- zelfde aanpak als
// de native drag-and-drop in kanban.js, nu met vrije x/y i.p.v. kolommen.
document.addEventListener("DOMContentLoaded", () => {
  const canvas = document.getElementById("mindmap-canvas");
  if (!canvas) return;

  const svg = document.getElementById("mindmap-edges");
  const addBtn = document.getElementById("mindmap-add-node");
  const NS = "http://www.w3.org/2000/svg";

  const nodes = new Map(); // id -> element
  const edges = new Map(); // id -> { fromId, toId, line, hit }

  canvas.querySelectorAll(".mindmap-node").forEach((el) => {
    nodes.set(Number(el.dataset.nodeId), el);
  });

  let linkFromId = null;

  function nodeCenter(el) {
    return {
      x: el.offsetLeft + el.offsetWidth / 2,
      y: el.offsetTop + el.offsetHeight / 2,
    };
  }

  function drawEdge(edgeId, fromId, toId) {
    const fromEl = nodes.get(fromId);
    const toEl = nodes.get(toId);
    if (!fromEl || !toEl) return;

    const hit = document.createElementNS(NS, "line");
    hit.setAttribute("class", "mindmap-edge-hit");
    hit.dataset.edgeId = edgeId;

    const line = document.createElementNS(NS, "line");
    line.setAttribute("class", "mindmap-edge-line");
    line.dataset.edgeId = edgeId;

    svg.appendChild(hit);
    svg.appendChild(line);
    edges.set(edgeId, { fromId, toId, line, hit });
    positionEdge(edgeId);
  }

  function positionEdge(edgeId) {
    const edge = edges.get(edgeId);
    if (!edge) return;
    const fromEl = nodes.get(edge.fromId);
    const toEl = nodes.get(edge.toId);
    if (!fromEl || !toEl) return;
    const a = nodeCenter(fromEl);
    const b = nodeCenter(toEl);
    for (const el of [edge.line, edge.hit]) {
      el.setAttribute("x1", a.x);
      el.setAttribute("y1", a.y);
      el.setAttribute("x2", b.x);
      el.setAttribute("y2", b.y);
    }
  }

  function positionEdgesForNode(nodeId) {
    for (const [edgeId, edge] of edges) {
      if (edge.fromId === nodeId || edge.toId === nodeId) positionEdge(edgeId);
    }
  }

  function removeEdgesForNode(nodeId) {
    for (const [edgeId, edge] of [...edges]) {
      if (edge.fromId === nodeId || edge.toId === nodeId) {
        edge.line.remove();
        edge.hit.remove();
        edges.delete(edgeId);
      }
    }
  }

  async function api(path, data) {
    const response = await fetch(path, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams(data),
    });
    if (!response.ok) throw new Error(`Verzoek mislukt (${response.status})`);
    return response.json();
  }

  function setLinkMode(nodeId) {
    linkFromId = nodeId;
    canvas.querySelectorAll(".mindmap-node").forEach((el) => {
      el.classList.toggle("mindmap-node-link-source", Number(el.dataset.nodeId) === nodeId);
    });
  }

  function clearLinkMode() {
    linkFromId = null;
    canvas.querySelectorAll(".mindmap-node-link-source").forEach((el) => {
      el.classList.remove("mindmap-node-link-source");
    });
  }

  function createNodeElement(id, text, color, x, y) {
    const el = document.createElement("div");
    el.className = "mindmap-node";
    el.dataset.nodeId = id;
    el.style.left = `${x}px`;
    el.style.top = `${y}px`;
    el.style.setProperty("--node-color", color);
    el.innerHTML = `
      <div class="mindmap-node-header">
        <input type="color" class="mindmap-node-color" value="${color}" title="Kleur wijzigen">
        <button type="button" class="mindmap-node-btn mindmap-node-add" title="Verbonden component toevoegen">+</button>
        <button type="button" class="mindmap-node-btn mindmap-node-link" title="Verbinden met een ander component">🔗</button>
        <button type="button" class="mindmap-node-btn mindmap-node-delete" title="Verwijderen">×</button>
      </div>
      <div class="mindmap-node-text" contenteditable="true" spellcheck="false"></div>
    `;
    el.querySelector(".mindmap-node-text").textContent = text;
    canvas.appendChild(el);
    nodes.set(id, el);
    return el;
  }

  // ---- Slepen ----
  let dragging = null; // { id, el, offsetX, offsetY }

  canvas.addEventListener("mousedown", (event) => {
    if (event.target.closest("input, button, [contenteditable]")) return;
    const el = event.target.closest(".mindmap-node");
    if (!el) return;
    const rect = canvas.getBoundingClientRect();
    dragging = {
      id: Number(el.dataset.nodeId),
      el,
      offsetX: event.clientX - rect.left - el.offsetLeft,
      offsetY: event.clientY - rect.top - el.offsetTop,
    };
    el.classList.add("mindmap-node-dragging");
  });

  document.addEventListener("mousemove", (event) => {
    if (!dragging) return;
    const rect = canvas.getBoundingClientRect();
    const x = Math.max(0, event.clientX - rect.left - dragging.offsetX);
    const y = Math.max(0, event.clientY - rect.top - dragging.offsetY);
    dragging.el.style.left = `${x}px`;
    dragging.el.style.top = `${y}px`;
    positionEdgesForNode(dragging.id);
  });

  document.addEventListener("mouseup", () => {
    if (!dragging) return;
    const { id, el } = dragging;
    el.classList.remove("mindmap-node-dragging");
    dragging = null;
    api(`/mindmap/nodes/${id}`, { x: Math.round(el.offsetLeft), y: Math.round(el.offsetTop) }).catch(() => {});
  });

  // ---- Klikken binnen een component (kleur/tekst/knoppen) ----
  canvas.addEventListener("click", (event) => {
    const nodeEl = event.target.closest(".mindmap-node");

    if (event.target.closest(".mindmap-node-delete")) {
      if (!nodeEl) return;
      const id = Number(nodeEl.dataset.nodeId);
      if (!confirm("Component verwijderen?")) return;
      api(`/mindmap/nodes/${id}/delete`, {})
        .then(() => {
          removeEdgesForNode(id);
          nodeEl.remove();
          nodes.delete(id);
          if (linkFromId === id) clearLinkMode();
        })
        .catch(() => {});
      return;
    }

    if (event.target.closest(".mindmap-node-add")) {
      if (!nodeEl) return;
      const parentId = Number(nodeEl.dataset.nodeId);
      const x = nodeEl.offsetLeft + 220;
      const y = nodeEl.offsetTop + 40;
      api("/mindmap/nodes", { text: "Nieuw idee", color: nodeEl.style.getPropertyValue("--node-color") || "#bd93f9", x, y, parent_id: parentId })
        .then((data) => {
          createNodeElement(data.id, data.text, data.color, data.x, data.y);
          if (data.edge) drawEdge(data.edge.id, data.edge.from_node_id, data.edge.to_node_id);
        })
        .catch(() => {});
      return;
    }

    if (event.target.closest(".mindmap-node-link")) {
      if (!nodeEl) return;
      const id = Number(nodeEl.dataset.nodeId);
      if (linkFromId === id) {
        clearLinkMode();
      } else {
        setLinkMode(id);
      }
      return;
    }

    // Klikken op een ander component terwijl link-modus actief is -> verbinden.
    if (linkFromId !== null && nodeEl && Number(nodeEl.dataset.nodeId) !== linkFromId) {
      const toId = Number(nodeEl.dataset.nodeId);
      const fromId = linkFromId;
      clearLinkMode();
      api("/mindmap/edges", { from_node_id: fromId, to_node_id: toId })
        .then((edge) => {
          if (!edges.has(edge.id)) drawEdge(edge.id, edge.from_node_id, edge.to_node_id);
        })
        .catch(() => {});
      return;
    }

    // Klikken op een verbindingslijn -> verwijderen.
    const hit = event.target.closest(".mindmap-edge-hit");
    if (hit) {
      const edgeId = Number(hit.dataset.edgeId);
      if (!confirm("Verbinding verwijderen?")) return;
      api(`/mindmap/edges/${edgeId}/delete`, {})
        .then(() => {
          const edge = edges.get(edgeId);
          if (edge) {
            edge.line.remove();
            edge.hit.remove();
            edges.delete(edgeId);
          }
        })
        .catch(() => {});
    }
  });

  canvas.addEventListener("input", (event) => {
    if (!event.target.classList.contains("mindmap-node-color")) return;
    const nodeEl = event.target.closest(".mindmap-node");
    nodeEl.style.setProperty("--node-color", event.target.value);
  });

  canvas.addEventListener("change", (event) => {
    if (!event.target.classList.contains("mindmap-node-color")) return;
    const nodeEl = event.target.closest(".mindmap-node");
    const id = Number(nodeEl.dataset.nodeId);
    api(`/mindmap/nodes/${id}`, { color: event.target.value }).catch(() => {});
  });

  canvas.addEventListener(
    "blur",
    (event) => {
      if (!event.target.classList.contains("mindmap-node-text")) return;
      const nodeEl = event.target.closest(".mindmap-node");
      const id = Number(nodeEl.dataset.nodeId);
      const text = event.target.textContent.trim();
      if (!text) {
        event.target.textContent = "Nieuw idee";
      }
      api(`/mindmap/nodes/${id}`, { text: text || "Nieuw idee" }).catch(() => {});
    },
    true
  );

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") clearLinkMode();
  });

  if (addBtn) {
    addBtn.addEventListener("click", () => {
      const x = 40 + Math.round(Math.random() * 120);
      const y = 40 + Math.round(Math.random() * 120);
      api("/mindmap/nodes", { text: "Nieuw idee", color: "#bd93f9", x, y })
        .then((data) => createNodeElement(data.id, data.text, data.color, data.x, data.y))
        .catch(() => {});
    });
  }

  // ---- Initiële verbindingen tekenen ----
  const edgesDataEl = document.getElementById("mindmap-edges-data");
  if (edgesDataEl) {
    const initialEdges = JSON.parse(edgesDataEl.textContent || "[]");
    for (const edge of initialEdges) {
      drawEdge(edge.id, edge.from_node_id, edge.to_node_id);
    }
  }
});
