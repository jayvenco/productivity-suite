// Lichte drag-and-drop implementatie op basis van de native HTML5 Drag & Drop API --
// geen extra library nodig. Kaarten kunnen tussen kolommen én swimlanes verslepen.
document.addEventListener("DOMContentLoaded", () => {
  const board = document.querySelector(".board-grid");
  if (!board) return;

  let draggedCard = null;

  board.addEventListener("dragstart", (event) => {
    const card = event.target.closest(".kanban-card");
    if (!card) return;
    draggedCard = card;
    card.classList.add("dragging");
    event.dataTransfer.effectAllowed = "move";
  });

  board.addEventListener("dragend", (event) => {
    const card = event.target.closest(".kanban-card");
    if (card) card.classList.remove("dragging");
  });

  board.querySelectorAll(".card-list").forEach((list) => {
    list.addEventListener("dragover", (event) => {
      event.preventDefault();
      const afterElement = getDragAfterElement(list, event.clientY);
      if (!draggedCard) return;
      if (afterElement == null) {
        list.appendChild(draggedCard);
      } else {
        list.insertBefore(draggedCard, afterElement);
      }
    });

    list.addEventListener("drop", async (event) => {
      event.preventDefault();
      if (!draggedCard) return;

      const columnId = list.dataset.columnId;
      const swimlaneId = list.dataset.swimlaneId;
      const cardId = draggedCard.dataset.cardId;
      const position = Array.from(list.children).indexOf(draggedCard);

      await fetch(`/kanban/cards/${cardId}/move`, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: new URLSearchParams({
          column_id: columnId,
          swimlane_id: swimlaneId,
          position: String(position),
        }),
      });
    });
  });

  // Checklist-items in kaartbeschrijvingen: klik op checkbox -> toggle op de server,
  // optimistisch bijgewerkt in de UI zonder page reload.
  board.addEventListener("change", async (event) => {
    const checkbox = event.target.closest(".checklist-item input[type=checkbox]");
    if (!checkbox) return;

    const cardId = checkbox.dataset.cardId;
    const lineIndex = checkbox.dataset.lineIndex;
    checkbox.closest(".checklist-item").classList.toggle("done", checkbox.checked);

    await fetch(`/kanban/cards/${cardId}/checklist-toggle`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams({ line_index: lineIndex }),
    });
  });

  function getDragAfterElement(container, y) {
    const cards = [...container.querySelectorAll(".kanban-card:not(.dragging)")];
    return cards.reduce(
      (closest, child) => {
        const box = child.getBoundingClientRect();
        const offset = y - box.top - box.height / 2;
        if (offset < 0 && offset > closest.offset) {
          return { offset, element: child };
        }
        return closest;
      },
      { offset: Number.NEGATIVE_INFINITY, element: null }
    ).element;
  }
});
