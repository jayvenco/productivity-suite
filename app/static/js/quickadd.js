// Zwevende quick-add-knop: klik op de + opent een pizza-achtig menu met
// sneltoetsen voor Taak (T), Kanban (K), Snippet (S) en Notitie (N). Klik op
// een van die knoppen toont een klein tekstveld dat direct naar de
// bijbehorende /quick-route post, zonder de pagina te verlaten.
document.addEventListener("DOMContentLoaded", () => {
  const float = document.getElementById("quickadd-float");
  if (!float) return;

  const mainBtn = document.getElementById("quickadd-main-btn");
  const menu = document.getElementById("quickadd-menu");
  const form = document.getElementById("quickadd-input-form");
  const input = document.getElementById("quickadd-input");
  const cancelBtn = document.getElementById("quickadd-cancel");

  const QUICK_ROUTES = {
    task: { url: "/tasks/quick", field: "title", placeholder: "Nieuwe taak..." },
    kanban: { url: "/kanban/cards/quick", field: "title", placeholder: "Nieuwe kanban-kaart..." },
    snippet: { url: "/snippets/quick", field: "title", placeholder: "Nieuwe snippet..." },
    note: { url: "/notes/quick", field: "title", placeholder: "Nieuwe notitie..." },
  };

  let activeType = null;

  function closeMenu() {
    float.classList.remove("quickadd-open");
    menu.hidden = true;
  }

  function closeForm() {
    form.hidden = true;
    activeType = null;
    input.value = "";
  }

  mainBtn.addEventListener("click", () => {
    if (!form.hidden) {
      closeForm();
      return;
    }
    const opening = menu.hidden;
    if (opening) {
      menu.hidden = false;
      float.classList.add("quickadd-open");
    } else {
      closeMenu();
    }
  });

  menu.addEventListener("click", (event) => {
    const btn = event.target.closest(".quickadd-option");
    if (!btn) return;
    activeType = btn.dataset.type;
    const config = QUICK_ROUTES[activeType];
    input.placeholder = config.placeholder;
    closeMenu();
    form.hidden = false;
    input.focus();
  });

  cancelBtn.addEventListener("click", () => closeForm());

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!activeType) return;
    const config = QUICK_ROUTES[activeType];
    const title = input.value.trim();
    if (!title) return;

    try {
      const response = await fetch(config.url, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: new URLSearchParams({ [config.field]: title }),
      });
      if (!response.ok) throw new Error(`Verzoek mislukt (${response.status})`);
      closeForm();
    } catch (err) {
      alert("Aanmaken is mislukt. Probeer het opnieuw.");
    }
  });

  document.addEventListener("click", (event) => {
    if (float.contains(event.target)) return;
    closeMenu();
    if (!form.hidden) closeForm();
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      closeMenu();
      closeForm();
    }
  });
});
