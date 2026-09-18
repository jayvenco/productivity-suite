// Mini-kalender in de sidebar: maandoverzicht met rode stipjes op dagen met
// een taak-deadline of afspraak. Klik op een dag opent een klein inline
// formulier om direct een taak met die deadline aan te maken (verschijnt
// meteen ook in de takenlijst, want het is gewoon een normale Task).
document.addEventListener("DOMContentLoaded", () => {
  const widget = document.getElementById("mini-calendar-widget");
  if (!widget) return;

  const label = document.getElementById("mini-calendar-label");
  const weekdaysEl = document.getElementById("mini-calendar-weekdays");
  const gridEl = document.getElementById("mini-calendar-grid");
  const prevBtn = document.getElementById("mini-calendar-prev");
  const nextBtn = document.getElementById("mini-calendar-next");
  const quickadd = document.getElementById("mini-calendar-quickadd");
  const quickaddDate = document.getElementById("mini-calendar-quickadd-date");
  const quickaddTitle = document.getElementById("mini-calendar-quickadd-title");
  const quickaddCancel = document.getElementById("mini-calendar-quickadd-cancel");

  let selectedDate = null;

  async function loadMonth(year, month) {
    const params = new URLSearchParams();
    if (year) params.set("year", year);
    if (month) params.set("month", month);

    const response = await fetch(`/calendar/widget?${params.toString()}`);
    const data = await response.json();
    render(data);
  }

  function render(data) {
    label.textContent = data.label;

    weekdaysEl.innerHTML = "";
    for (const dayLabel of data.day_labels) {
      const el = document.createElement("span");
      el.textContent = dayLabel;
      weekdaysEl.appendChild(el);
    }

    gridEl.innerHTML = "";
    for (const week of data.weeks) {
      for (const day of week) {
        const cell = document.createElement("button");
        cell.type = "button";
        cell.className = "mini-calendar-day";
        if (!day.in_month) cell.classList.add("mini-calendar-day-other-month");
        if (day.is_today) cell.classList.add("mini-calendar-day-today");
        cell.dataset.date = day.date;
        cell.innerHTML = `${day.day}${day.has_items ? '<span class="mini-calendar-dot"></span>' : ""}`;
        gridEl.appendChild(cell);
      }
    }

    prevBtn.onclick = () => loadMonth(data.prev.year, data.prev.month);
    nextBtn.onclick = () => loadMonth(data.next.year, data.next.month);
  }

  gridEl.addEventListener("click", (event) => {
    const cell = event.target.closest(".mini-calendar-day");
    if (!cell) return;
    openQuickAdd(cell.dataset.date, cell);
  });

  function openQuickAdd(isoDate, cell) {
    selectedDate = isoDate;
    quickaddDate.textContent = new Date(isoDate + "T00:00:00").toLocaleDateString("nl-NL", {
      weekday: "long",
      day: "numeric",
      month: "long",
    });
    quickadd.hidden = false;
    quickaddTitle.value = "";
    quickaddTitle.focus();
    gridEl.querySelectorAll(".mini-calendar-day-selected").forEach((el) => el.classList.remove("mini-calendar-day-selected"));
    if (cell) cell.classList.add("mini-calendar-day-selected");
  }

  function closeQuickAdd() {
    quickadd.hidden = true;
    selectedDate = null;
    gridEl.querySelectorAll(".mini-calendar-day-selected").forEach((el) => el.classList.remove("mini-calendar-day-selected"));
  }

  quickaddCancel.addEventListener("click", closeQuickAdd);

  quickadd.addEventListener("submit", async (event) => {
    event.preventDefault();
    const title = quickaddTitle.value.trim();
    if (!title || !selectedDate) return;

    const response = await fetch("/tasks/quick", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams({ title, deadline: selectedDate }),
    });
    if (!response.ok) return;

    const cell = gridEl.querySelector(`[data-date="${selectedDate}"]`);
    if (cell && !cell.querySelector(".mini-calendar-dot")) {
      cell.insertAdjacentHTML("beforeend", '<span class="mini-calendar-dot"></span>');
    }
    closeQuickAdd();

    // De "Komende deadlines"-widget kan nu ook deze nieuwe taak bevatten.
    document.dispatchEvent(new Event("deadlines:refresh"));
  });

  loadMonth();
});
