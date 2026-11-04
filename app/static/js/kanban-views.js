// Kanban-weergaven: Lijst (standaard), Lanes (één swimlane tegelijk als bord) en Swimlanes (alle
// swimlanes onder elkaar, het oorspronkelijke bord). De keuze (en de actieve lane) worden in
// localStorage onthouden. De lijst gebruikt dezelfde bewerk-/toevoeg-formulieren als het bord: een
// klik op een rij opent de bestaande kaart-editor, "+ Kaart" opent het toevoegformulier.
document.addEventListener("DOMContentLoaded", () => {
  const root = document.getElementById("kanban-root");
  const toggle = document.getElementById("kanban-view-toggle");
  if (!root || !toggle) return;

  const VIEW_KEY = "kanban-view";
  const LANE_KEY = "kanban-active-lane";
  const VIEWS = ["list", "lanes", "swimlanes"];
  const tabs = [...document.querySelectorAll(".kanban-lane-tab")];
  const blocks = [...document.querySelectorAll("[data-swimlane-block]")];

  const read = (key) => {
    try {
      return localStorage.getItem(key);
    } catch (err) {
      return null;
    }
  };
  const write = (key, value) => {
    try {
      localStorage.setItem(key, value);
    } catch (err) {
      /* localStorage geblokkeerd: de keuze geldt dan alleen voor deze pagina */
    }
  };

  function showLane(id) {
    const known = blocks.some((b) => b.dataset.swimlaneBlock === id);
    const active = known ? id : blocks[0] && blocks[0].dataset.swimlaneBlock;
    blocks.forEach((b) => b.classList.toggle("lane-active", b.dataset.swimlaneBlock === active));
    tabs.forEach((t) => t.classList.toggle("active", t.dataset.lane === active));
    if (active) write(LANE_KEY, active);
  }

  // "Lanes standaard ingeklapt" bepaalt alleen de swimlanes-weergave.
  const collapseLabel = document.querySelector(".kanban-collapse-default");

  function applyView(view) {
    if (!VIEWS.includes(view)) view = "list";
    root.dataset.view = view;
    if (collapseLabel) collapseLabel.style.display = view === "swimlanes" ? "" : "none";
    toggle.querySelectorAll(".notes-view-btn").forEach((b) => b.classList.toggle("active", b.dataset.view === view));
    write(VIEW_KEY, view);
  }

  toggle.addEventListener("click", (event) => {
    const btn = event.target.closest(".notes-view-btn");
    if (btn) applyView(btn.dataset.view);
  });

  tabs.forEach((tab) => tab.addEventListener("click", () => showLane(tab.dataset.lane)));

  applyView(read(VIEW_KEY) || "list");
  showLane(read(LANE_KEY));

  // ---- Lijstweergave ----
  const list = document.getElementById("kanban-list-view");
  if (!list) return;

  list.addEventListener("click", (event) => {
    if (event.target.closest("select, a, button, input")) {
      const add = event.target.closest(".kl-add");
      if (add) {
        const block = document.querySelector(`[data-swimlane-block="${add.dataset.swimlaneId}"]`);
        const summary = block && block.querySelector(".add-card-details summary");
        if (summary) summary.click(); // opent het schermvullende "nieuwe kaart"-formulier
      }
      return;
    }
    const row = event.target.closest(".kl-row");
    if (!row) return;
    const edit = document.querySelector(`.card-edit-toggle[data-card-id="${row.dataset.cardId}"]`);
    if (edit) edit.click(); // opent de bestaande kaart-editor (modal)
  });

  // Kolom wijzigen in de lijst = de kaart verplaatsen (onderaan de nieuwe kolom).
  list.addEventListener("change", async (event) => {
    const select = event.target.closest(".kl-column");
    if (!select) return;
    select.disabled = true;
    await fetch(`/kanban/cards/${select.dataset.cardId}/move`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams({
        column_id: select.value,
        swimlane_id: select.dataset.swimlaneId,
        position: "9999",
      }),
    });
    location.reload();
  });

  const filter = document.getElementById("kanban-list-filter");
  filter.addEventListener("input", () => {
    const needle = filter.value.trim().toLowerCase();
    list.querySelectorAll(".kl-row").forEach((row) => {
      row.hidden = needle !== "" && !row.dataset.search.includes(needle);
    });
  });
});
