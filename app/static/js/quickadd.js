// Quick-add-wiel: klik op de ronde hub-knop rechtsonder om een semi-transparant
// rond menu met 5 snelkoppelingen te openen (Notities/Kanban/Snippets/Taken/
// Mindmap), elk een gewone link naar de bijbehorende aanmaakpagina -- geen los
// formulier, gewoon navigeren zoals een klik op de sidebar.
document.addEventListener("DOMContentLoaded", () => {
  const wrap = document.getElementById("quickadd-wheel-wrap");
  const hub = document.getElementById("quickadd-hub");
  const wheel = document.getElementById("quickadd-wheel");
  if (!wrap || !hub || !wheel) return;

  function closeWheel() {
    wrap.classList.remove("open");
    wheel.hidden = true;
  }

  function openWheel() {
    wrap.classList.add("open");
    wheel.hidden = false;
  }

  hub.addEventListener("click", () => {
    if (wheel.hidden) {
      openWheel();
    } else {
      closeWheel();
    }
  });

  document.addEventListener("click", (event) => {
    if (wrap.contains(event.target)) return;
    closeWheel();
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") closeWheel();
  });
});
