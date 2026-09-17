// Lichte drag-and-drop implementatie op basis van de native HTML5 Drag & Drop API --
// geen extra library nodig. Kaarten kunnen tussen kolommen én swimlanes verslepen.
document.addEventListener("DOMContentLoaded", () => {
  const board = document.querySelector(".board-swimlanes");
  if (!board) return;

  let draggedCard = null;

  board.addEventListener("dragstart", (event) => {
    // Niet slepen als de gebruiker in het bewerk-formulier (of de modal eromheen)
    // aan het typen/klikken is.
    if (event.target.closest("input, textarea, button, select, label, .card-edit-form")) {
      event.preventDefault();
      return;
    }
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

  // "Bewerken"-knop op een kaart opent het bewerk-formulier als modal (met backdrop).
  const backdrop = document.getElementById("kanban-modal-backdrop");

  function openCardEditModal(form) {
    form.hidden = false;
    backdrop.hidden = false;
  }

  function closeCardEditModal(form) {
    form.hidden = true;
    backdrop.hidden = true;
  }

  board.addEventListener("click", (event) => {
    const toggle = event.target.closest(".card-edit-toggle");
    if (!toggle) return;
    const form = document.getElementById(`card-edit-${toggle.dataset.cardId}`);
    if (form) openCardEditModal(form);
  });

  board.addEventListener("click", (event) => {
    const cancelBtn = event.target.closest(".card-edit-cancel");
    if (!cancelBtn) return;
    closeCardEditModal(cancelBtn.closest(".card-edit-form"));
  });

  backdrop.addEventListener("click", () => {
    const openForm = document.querySelector(".card-edit-form:not([hidden])");
    if (openForm) closeCardEditModal(openForm);
  });

  // "+ Checklist-item": voegt een lege "- [ ] "-regel toe aan de beschrijving,
  // zodat je de markdown-syntax niet zelf hoeft te typen.
  board.addEventListener("click", (event) => {
    const button = event.target.closest(".add-checklist-item-btn");
    if (!button) return;
    event.preventDefault();

    const textarea = button.closest("form").querySelector("textarea[name=description]");
    if (!textarea) return;

    const needsNewline = textarea.value.length > 0 && !textarea.value.endsWith("\n");
    textarea.value += (needsNewline ? "\n" : "") + "- [ ] ";
    textarea.focus();
    textarea.setSelectionRange(textarea.value.length, textarea.value.length);
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

  // Swimlanes in-/uitklappen. Status per bord onthouden in localStorage (per
  // swimlane-id), zodat een dichtgeklapte lane dat blijft na een refresh --
  // puur weergave, geen serverstate nodig voor een enkele gebruiker.
  const collapseKey = `kanban-collapsed-lanes-${board.dataset.boardId || "default"}`;

  function loadCollapsed() {
    try {
      return new Set(JSON.parse(localStorage.getItem(collapseKey) || "[]"));
    } catch {
      return new Set();
    }
  }

  function saveCollapsed(set) {
    try {
      localStorage.setItem(collapseKey, JSON.stringify([...set]));
    } catch {
      /* privénavigatie of volle opslag: dan onthoudt de sessie het gewoon niet */
    }
  }

  const collapsed = loadCollapsed();

  function applyCollapsed(block, isCollapsed) {
    block.classList.toggle("swimlane-collapsed", isCollapsed);
    const row = block.querySelector(".board-row");
    if (row) row.hidden = isCollapsed;
    const arrow = block.querySelector(".swimlane-toggle-arrow");
    if (arrow) arrow.textContent = isCollapsed ? "▸" : "▾";
  }

  board.querySelectorAll("[data-swimlane-block]").forEach((block) => {
    applyCollapsed(block, collapsed.has(block.dataset.swimlaneBlock));
  });

  board.addEventListener("click", (event) => {
    const toggle = event.target.closest("[data-swimlane-toggle]");
    if (!toggle) return;
    const id = toggle.dataset.swimlaneToggle;
    const block = toggle.closest("[data-swimlane-block]");
    if (!block) return;
    const isCollapsed = !collapsed.has(id);
    if (isCollapsed) {
      collapsed.add(id);
    } else {
      collapsed.delete(id);
    }
    saveCollapsed(collapsed);
    applyCollapsed(block, isCollapsed);
  });
});
