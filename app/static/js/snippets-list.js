// Klik op een snippet-titel opent de code in een bijna-volledig-scherm paneel (i.p.v.
// inline uit te klappen in de kaart) -- beter leesbaar voor langere snippets. De
// broncode blijft (verborgen) in de kaart staan als bron; hier wordt er telkens een
// verse kloon van gemaakt zodat regelnummers niet dubbel worden toegepast bij een
// tweede keer openen van dezelfde snippet. Vanuit datzelfde paneel is de code ook direct
// te bewerken (los van het volledige bewerkformulier, dat titel/tags/bestandenlijst
// beheert -- hier gaat het puur om de inhoud van bestaande bestanden).
document.addEventListener("DOMContentLoaded", () => {
  const backdrop = document.getElementById("snippet-fullscreen-backdrop");
  const modal = document.getElementById("snippet-fullscreen-modal");
  const titleEl = document.getElementById("snippet-fullscreen-title");
  const bodyEl = document.getElementById("snippet-fullscreen-body");
  const closeBtn = document.getElementById("snippet-fullscreen-close");
  const editBtn = document.getElementById("snippet-fullscreen-edit-btn");
  const saveBtn = document.getElementById("snippet-fullscreen-save-btn");
  const cancelBtn = document.getElementById("snippet-fullscreen-cancel-btn");
  if (!backdrop || !modal) return;

  let currentSnippetId = null;
  let currentTitle = "";
  let isEditing = false;

  function applyHighlighting(clone) {
    clone.querySelectorAll("pre code").forEach((codeEl) => {
      // Regelnummers herstructureren de inhoud in een <table> per regel, waarbij de
      // originele "\n"-tekens verdwijnen (regeleinden worden dan tabelrijen i.p.v.
      // tekens) -- de platte tekst moet dus vóór het toepassen ervan bewaard blijven,
      // anders raakt bewerken (die op codeEl.textContent leunt) de regeleindes kwijt.
      codeEl.dataset.rawContent = codeEl.textContent;
      if (window.hljs && window.hljs.lineNumbersBlock) {
        window.hljs.lineNumbersBlock(codeEl);
      }
    });
  }

  function renderView(snippetId) {
    const source = document.getElementById(`snippet-files-${snippetId}`);
    if (!source) return;

    const clone = source.cloneNode(true);
    clone.hidden = false;
    clone.removeAttribute("id");
    // In de kaart zelf staat alleen het eerste bestand open (ByteStash-achtige preview,
    // zie app/templates/snippets/list.html) -- de overige bestanden hebben daar het
    // `hidden`-attribuut, dat hier weer verwijderd moet worden zodat het volledige-
    // scherm-paneel wél alle bestanden toont.
    clone.querySelectorAll(".snippet-file[hidden]").forEach((file) => file.removeAttribute("hidden"));
    bodyEl.innerHTML = "";
    bodyEl.appendChild(clone);
    applyHighlighting(clone);
  }

  function openModal(snippetId, title) {
    currentSnippetId = snippetId;
    currentTitle = title;
    isEditing = false;
    titleEl.textContent = title;
    renderView(snippetId);

    editBtn.hidden = false;
    saveBtn.hidden = true;
    cancelBtn.hidden = true;

    backdrop.hidden = false;
    modal.hidden = false;
  }

  function closeModal() {
    if (isEditing && !confirm("Niet-opgeslagen wijzigingen weggooien?")) return;
    backdrop.hidden = true;
    modal.hidden = true;
    bodyEl.innerHTML = "";
    currentSnippetId = null;
    isEditing = false;
  }

  function enterEditMode() {
    isEditing = true;
    bodyEl.querySelectorAll(".snippet-file").forEach((fileBlock) => {
      const codeEl = fileBlock.querySelector("pre code");
      const rawContent = codeEl ? codeEl.dataset.rawContent ?? codeEl.textContent : "";
      const pre = fileBlock.querySelector("pre");
      const textarea = document.createElement("textarea");
      textarea.className = "snippet-edit-textarea";
      textarea.value = rawContent;
      textarea.spellcheck = false;
      pre.replaceWith(textarea);
    });

    editBtn.hidden = true;
    saveBtn.hidden = false;
    cancelBtn.hidden = false;
  }

  async function saveEdits() {
    const fileBlocks = [...bodyEl.querySelectorAll(".snippet-file")];
    saveBtn.disabled = true;
    saveBtn.textContent = "Opslaan...";

    try {
      await Promise.all(
        fileBlocks.map((fileBlock) => {
          const fileId = fileBlock.dataset.fileId;
          const textarea = fileBlock.querySelector(".snippet-edit-textarea");
          if (!fileId || !textarea) return Promise.resolve();
          return fetch(`/snippets/${currentSnippetId}/files/${fileId}/content`, {
            method: "POST",
            headers: { "Content-Type": "application/x-www-form-urlencoded" },
            body: new URLSearchParams({ content: textarea.value }),
          });
        })
      );
      window.location.reload();
    } catch (err) {
      saveBtn.disabled = false;
      saveBtn.textContent = "Opslaan";
      alert("Opslaan is mislukt, probeer het opnieuw.");
    }
  }

  function cancelEdits() {
    isEditing = false;
    renderView(currentSnippetId);
    editBtn.hidden = false;
    saveBtn.hidden = true;
    cancelBtn.hidden = true;
  }

  document.addEventListener("click", (event) => {
    const toggle = event.target.closest(".snippet-toggle");
    if (!toggle) return;
    openModal(toggle.dataset.snippetId, toggle.dataset.snippetTitle || "");
  });

  // Kopieer-icoontje op de code-preview in de kaart (ByteStash-achtig) -- kopieert de
  // rauwe tekst van het bijbehorende <code>-element, ongeacht de <span>-tags die
  // hljs.highlightAll() erin gezet heeft voor de syntax-kleuring (textContent negeert
  // die sowieso, dus geen aparte "rauwe" kopie nodig zoals bij de bewerk-modus hierboven).
  document.addEventListener("click", (event) => {
    const copyBtn = event.target.closest(".snippet-copy-btn");
    if (!copyBtn) return;
    const codeEl = document.getElementById(copyBtn.dataset.copyTarget);
    if (!codeEl || !navigator.clipboard) return;

    navigator.clipboard.writeText(codeEl.textContent).then(() => {
      const original = copyBtn.textContent;
      copyBtn.textContent = "✓";
      setTimeout(() => {
        copyBtn.textContent = original;
      }, 1200);
    });
  });

  editBtn.addEventListener("click", enterEditMode);
  saveBtn.addEventListener("click", saveEdits);
  cancelBtn.addEventListener("click", cancelEdits);
  closeBtn.addEventListener("click", closeModal);
  backdrop.addEventListener("click", closeModal);
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && !modal.hidden) closeModal();
  });

  // Meerdere snippets tegelijk selecteren en verwijderen (zelfde patroon als notities).
  const bulkForm = document.getElementById("snippets-bulk-form");
  const bulkBar = document.getElementById("snippets-bulk-bar");
  const bulkCount = document.getElementById("snippets-bulk-count");
  if (bulkForm && bulkBar && bulkCount) {
    bulkForm.addEventListener("change", (event) => {
      if (!event.target.classList.contains("snippet-select")) return;
      const checked = bulkForm.querySelectorAll(".snippet-select:checked").length;
      bulkBar.hidden = checked === 0;
      bulkCount.textContent = `${checked} geselecteerd`;
    });
  }
});
