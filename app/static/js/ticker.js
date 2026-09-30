// Nieuws-ticker onderin: laat alle nog niet afgeronde taken langzaam van rechts naar links
// over het scherm glijden, zoals een nieuwsband onder een tv-uitzending. Data komt via
// GET /tasks/ticker (zelfde "los JSON-endpoint, elke pagina kan het tonen"-patroon als
// het deadlines-widgetje, zie deadlines.js). De inhoud staat twee keer achter elkaar
// (#task-ticker-content + de "-dup"-kopie) en de animatie schuift precies 50% van de totale
// breedte op -- zo loopt de eerste kopie er net af op het moment dat de tweede (identieke)
// kopie op dezelfde plek verschijnt, wat een naadloze, oneindige lus geeft zonder sprong.
document.addEventListener("DOMContentLoaded", () => {
  const ticker = document.getElementById("task-ticker");
  const track = document.getElementById("task-ticker-track");
  const content = document.getElementById("task-ticker-content");
  const contentDup = document.getElementById("task-ticker-content-dup");
  const closeBtn = document.getElementById("task-ticker-close");
  if (!ticker || !content) return;

  const DISMISSED_KEY = "task-ticker-dismissed";

  function isDismissed() {
    try {
      return localStorage.getItem(DISMISSED_KEY) === "1";
    } catch (err) {
      return false;
    }
  }

  function setDismissed(value) {
    try {
      localStorage.setItem(DISMISSED_KEY, value ? "1" : "0");
    } catch (err) {
      // localStorage kan geblokkeerd zijn; de ticker blijft dan gewoon zichtbaar tot de
      // volgende page load i.p.v. de voorkeur te onthouden.
    }
  }

  function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
  }

  function buildItemsHtml(tasks) {
    return tasks
      .map((task) => {
        const star = task.priority ? '<span class="task-ticker-item-priority">★</span> ' : "";
        return `<a class="task-ticker-item" href="/tasks/${task.id}/edit">${star}${escapeHtml(task.title)}</a>`;
      })
      .join("");
  }

  async function loadTicker() {
    if (isDismissed()) return;

    try {
      const response = await fetch("/tasks/ticker");
      const tasks = await response.json();
      if (!Array.isArray(tasks) || tasks.length === 0) return;

      const itemsHtml = buildItemsHtml(tasks);
      content.innerHTML = itemsHtml;
      contentDup.innerHTML = itemsHtml;

      // Snelheid meeschalen met het aantal taken -- bij weinig taken anders zou de band
      // ofwel te snel voorbijflitsen (vaste korte duur) ofwel eeuwig duren om één keer rond
      // te komen (vaste lange duur) als er heel veel taken zijn.
      const duration = Math.max(20, Math.min(120, tasks.length * 4));
      track.style.animationDuration = `${duration}s`;

      ticker.hidden = false;
    } catch (err) {
      // Stil falen -- de ticker is een leuk extraatje, geen kernfunctie; de rest van de
      // pagina moet gewoon blijven werken als deze feed een keer niet laadt.
    }
  }

  if (closeBtn) {
    closeBtn.addEventListener("click", () => {
      ticker.hidden = true;
      setDismissed(true);
    });
  }

  loadTicker();
});
