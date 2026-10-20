// Snippets: raster/lijst-weergave (onthouden in localStorage) en alle kaarten in de rasterweergave
// even hoog maken als de hoogste kaart.
document.addEventListener("DOMContentLoaded", () => {
  const VIEW_KEY = "snippets-view";
  const toggle = document.getElementById("snippets-view-toggle");
  const lists = () => document.querySelectorAll(".snippets-list");
  const cards = () => document.querySelectorAll(".snippet-card");
  let view = "grid";
  try {
    view = localStorage.getItem(VIEW_KEY) || "grid";
  } catch (err) {
    /* localStorage geblokkeerd: standaard raster */
  }

  function equalizeHeights() {
    cards().forEach((card) => (card.style.minHeight = ""));
    if (view !== "grid") return;
    let tallest = 0;
    cards().forEach((card) => {
      tallest = Math.max(tallest, card.getBoundingClientRect().height);
    });
    if (tallest) cards().forEach((card) => (card.style.minHeight = `${Math.ceil(tallest)}px`));
  }

  function applyView(next) {
    view = next;
    lists().forEach((list) => list.classList.toggle("view-list", view === "list"));
    if (toggle) toggle.querySelectorAll(".notes-view-btn").forEach((b) => b.classList.toggle("active", b.dataset.view === view));
    equalizeHeights();
  }

  if (toggle) {
    toggle.addEventListener("click", (event) => {
      const btn = event.target.closest(".notes-view-btn");
      if (!btn) return;
      applyView(btn.dataset.view);
      try {
        localStorage.setItem(VIEW_KEY, view);
      } catch (err) {
        /* zie hierboven */
      }
    });
  }

  applyView(view);
  // highlight.js en lettertypen veranderen de hoogte na het laden; daarna nog eens meten.
  window.addEventListener("load", equalizeHeights);
  let timer = null;
  window.addEventListener("resize", () => {
    clearTimeout(timer);
    timer = setTimeout(equalizeHeights, 150);
  });
});
