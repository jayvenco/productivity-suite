// Taakgroepen (bij "Groeperen op tag") in-/uitklappen. Zelfde patroon als de
// kanban-swimlanes: puur client-side, status per groepsnaam in localStorage.
document.addEventListener("DOMContentLoaded", () => {
  const STORAGE_KEY = "tasks-collapsed-groups";

  function loadCollapsed() {
    try {
      return new Set(JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]"));
    } catch {
      return new Set();
    }
  }

  function saveCollapsed(set) {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify([...set]));
    } catch {
      /* privénavigatie of volle opslag: dan onthoudt de sessie het gewoon niet */
    }
  }

  const collapsed = loadCollapsed();

  function applyCollapsed(name, isCollapsed) {
    const toggle = document.querySelector(`[data-group-toggle="${CSS.escape(name)}"]`);
    const table = document.querySelector(`[data-group-block="${CSS.escape(name)}"]`);
    if (!toggle || !table) return;
    table.hidden = isCollapsed;
    const arrow = toggle.querySelector(".task-group-toggle-arrow");
    if (arrow) arrow.textContent = isCollapsed ? "▸" : "▾";
  }

  document.querySelectorAll("[data-group-toggle]").forEach((toggle) => {
    applyCollapsed(toggle.dataset.groupToggle, collapsed.has(toggle.dataset.groupToggle));
  });

  document.addEventListener("click", (event) => {
    const toggle = event.target.closest("[data-group-toggle]");
    if (!toggle) return;
    const name = toggle.dataset.groupToggle;
    const isCollapsed = !collapsed.has(name);
    if (isCollapsed) {
      collapsed.add(name);
    } else {
      collapsed.delete(name);
    }
    saveCollapsed(collapsed);
    applyCollapsed(name, isCollapsed);
  });
});
