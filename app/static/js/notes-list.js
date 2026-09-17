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
});
