// Inbox: snel-invoervenster (Alt+I of de +-knop in het menu) en het aantal-label in het menu.
// Het venster staat op elke pagina; opslaan gaat via fetch, dus je blijft waar je was.
document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("inbox-capture");
  const backdrop = document.getElementById("inbox-capture-backdrop");
  const text = document.getElementById("inbox-capture-text");
  const cancel = document.getElementById("inbox-capture-cancel");
  const quickBtn = document.getElementById("inbox-quick-btn");
  const badge = document.getElementById("inbox-badge");
  if (!form || !backdrop || !text) return;

  function setCount(count) {
    if (!badge) return;
    badge.textContent = String(count);
    badge.hidden = !count;
  }

  fetch("/inbox/count")
    .then((r) => (r.ok ? r.json() : null))
    .then((data) => data && setCount(data.count))
    .catch(() => {});

  function openCapture() {
    form.hidden = false;
    backdrop.hidden = false;
    text.focus();
  }

  function closeCapture() {
    form.hidden = true;
    backdrop.hidden = true;
  }

  if (quickBtn) quickBtn.addEventListener("click", openCapture);
  cancel.addEventListener("click", closeCapture);
  backdrop.addEventListener("click", closeCapture);

  document.addEventListener("keydown", (event) => {
    if (event.altKey && !event.ctrlKey && !event.metaKey && event.code === "KeyI") {
      event.preventDefault();
      form.hidden ? openCapture() : closeCapture();
    } else if (event.key === "Escape" && !form.hidden) {
      closeCapture();
    }
  });

  async function save() {
    const value = text.value.trim();
    if (!value) return;
    const response = await fetch("/inbox", {
      method: "POST",
      headers: { "X-Requested-With": "fetch" },
      body: new URLSearchParams({ text: value }),
    });
    if (!response.ok) {
      alert("Opslaan in de inbox is mislukt.");
      return;
    }
    const data = await response.json();
    setCount(data.count);
    text.value = "";
    closeCapture();
    // Staan we op de inbox-pagina zelf, dan meteen de nieuwe lijst tonen.
    if (location.pathname === "/inbox") location.reload();
  }

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    save();
  });

  text.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && (event.metaKey || event.ctrlKey)) {
      event.preventDefault();
      save();
    }
  });
});
