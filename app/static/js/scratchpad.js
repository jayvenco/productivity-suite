// Scratchpad: automatisch opslaan van de grote rich-text-editor (debounce na typen, direct bij
// verlaten van de pagina) en een statusregel. De editor zelf komt uit rich-editor.js.
document.addEventListener("DOMContentLoaded", () => {
  const textarea = document.getElementById("scratchpad-text");
  const status = document.getElementById("scratchpad-status");
  const clearBtn = document.getElementById("scratchpad-clear");
  if (!textarea || !textarea.richEditor) return;

  const rich = textarea.richEditor;
  let timer = null;
  let dirty = false;
  let lastSaved = rich.getHTML();

  const setStatus = (text, cls) => {
    status.textContent = text;
    status.className = "scratchpad-status" + (cls ? ` ${cls}` : "");
  };

  async function save() {
    clearTimeout(timer);
    const html = rich.getHTML();
    if (!dirty && html === lastSaved) return;
    setStatus("Opslaan...");
    try {
      const response = await fetch("/scratchpad", { method: "POST", body: new URLSearchParams({ content: html }) });
      if (!response.ok) throw new Error(String(response.status));
      lastSaved = html;
      dirty = rich.getHTML() !== html;
      setStatus(dirty ? "Niet-opgeslagen wijzigingen" : `Opgeslagen ${new Date().toLocaleTimeString("nl-NL", { hour: "2-digit", minute: "2-digit" })}`);
    } catch (err) {
      setStatus("Opslaan mislukt - nieuwe poging bij de volgende wijziging", "error");
    }
  }

  rich.editor.addEventListener("input", () => {
    dirty = true;
    setStatus("Niet-opgeslagen wijzigingen");
    clearTimeout(timer);
    timer = setTimeout(save, 800);
  });

  document.addEventListener("keydown", (event) => {
    if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "s") {
      event.preventDefault();
      save();
    }
  });

  // Bij verlaten van de pagina nog wat openstaat meteen wegschrijven (sendBeacon overleeft het sluiten).
  const flush = () => {
    const html = rich.getHTML();
    if (html !== lastSaved) {
      navigator.sendBeacon("/scratchpad", new URLSearchParams({ content: html }));
      lastSaved = html;
    }
  };
  window.addEventListener("pagehide", flush);
  document.addEventListener("visibilitychange", () => document.visibilityState === "hidden" && flush());

  clearBtn.addEventListener("click", () => {
    if (rich.isEmpty() || !confirm("Het hele scratchpad leegmaken? Dit kan niet ongedaan gemaakt worden.")) return;
    rich.clear();
    dirty = true;
    save();
  });

  rich.focus();
});
