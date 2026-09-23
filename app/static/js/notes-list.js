// Notitielijst: hele kaart is klikbaar om te bewerken (behalve de checkbox/tags,
// die hun eigen gedrag hebben), plus een selectie-balk voor bulk-acties.
document.addEventListener("DOMContentLoaded", () => {
  const grid = document.querySelector(".notes-grid");
  const bulkBar = document.getElementById("notes-bulk-bar");
  const bulkCount = document.getElementById("notes-bulk-count");
  if (!grid) return;

  grid.addEventListener("click", (event) => {
    if (event.target.closest(".note-select, .tag, a, button, input")) return;
    const card = event.target.closest(".note-card");
    if (card) window.location = card.dataset.href;
  });

  grid.addEventListener("change", (event) => {
    if (!event.target.classList.contains("note-select")) return;
    updateBulkBar();
  });

  function updateBulkBar() {
    const checked = grid.querySelectorAll(".note-select:checked").length;
    bulkBar.hidden = checked === 0;
    bulkCount.textContent = `${checked} geselecteerd`;
  }

  // Raster/lijst-weergave: puur client-side (geen data, dus geen page reload nodig),
  // onthouden in localStorage zodat de keuze blijft staan bij een volgend bezoek.
  const VIEW_STORAGE_KEY = "notes-view";
  const toggle = document.getElementById("notes-view-toggle");
  if (toggle) {
    const buttons = toggle.querySelectorAll(".notes-view-btn");

    function applyView(view) {
      grid.classList.toggle("view-list", view === "list");
      buttons.forEach((btn) => btn.classList.toggle("active", btn.dataset.view === view));
    }

    let savedView = "grid";
    try {
      savedView = localStorage.getItem(VIEW_STORAGE_KEY) || "grid";
    } catch (err) {
      // localStorage kan geblokkeerd zijn; werkt dan gewoon met de default (raster).
    }
    applyView(savedView);

    toggle.addEventListener("click", (event) => {
      const btn = event.target.closest(".notes-view-btn");
      if (!btn) return;
      applyView(btn.dataset.view);
      try {
        localStorage.setItem(VIEW_STORAGE_KEY, btn.dataset.view);
      } catch (err) {
        // Zie hierboven.
      }
    });
  }
});
