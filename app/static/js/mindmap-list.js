// Mindmap-lijst: hele kaart is klikbaar om de mindmap te openen, behalve
// tags/links/knoppen/velden en de "Bewerken"-details (die moet gewoon
// open-/dichtklappen zonder meteen weg te navigeren).
document.addEventListener("DOMContentLoaded", () => {
  const grid = document.querySelector(".notes-grid");
  if (!grid) return;

  grid.addEventListener("click", (event) => {
    if (event.target.closest(".tag, a, button, input, details, summary")) return;
    const card = event.target.closest(".note-card");
    if (card) window.location = card.dataset.href;
  });
});
