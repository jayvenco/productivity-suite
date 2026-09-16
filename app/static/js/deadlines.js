// Vult het "Komende deadlines"-widgetje in de sidebar via een kleine JSON-feed,
// zodat elke pagina dit kan tonen zonder dat elke route de data hoeft op te halen.
document.addEventListener("DOMContentLoaded", async () => {
  const list = document.getElementById("deadlines-list");
  if (!list) return;

  try {
    const response = await fetch("/tasks/upcoming");
    const tasks = await response.json();

    list.innerHTML = "";
    if (tasks.length === 0) {
      list.innerHTML = '<li class="deadlines-empty">Geen deadlines gepland</li>';
      return;
    }

    for (const task of tasks) {
      const li = document.createElement("li");
      li.className = "deadlines-item";
      const badgeClass = task.overdue ? "badge-danger" : task.warning ? "badge-warning" : "";
      li.innerHTML = `
        <a href="/tasks/${task.id}/edit">${escapeHtml(task.title)}</a>
        <span class="deadlines-date ${badgeClass}">${task.deadline}</span>
      `;
      list.appendChild(li);
    }
  } catch (err) {
    list.innerHTML = '<li class="deadlines-empty">Kon deadlines niet laden</li>';
  }
});

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}
