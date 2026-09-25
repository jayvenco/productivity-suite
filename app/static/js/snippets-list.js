// Klik op een snippet-titel opent de code in een bijna-volledig-scherm paneel (i.p.v.
// inline uit te klappen in de kaart) -- beter leesbaar voor langere snippets. De
// broncode blijft (verborgen) in de kaart staan als bron; hier wordt er telkens een
// verse kloon van gemaakt zodat regelnummers niet dubbel worden toegepast bij een
// tweede keer openen van dezelfde snippet.
document.addEventListener("DOMContentLoaded", () => {
  const backdrop = document.getElementById("snippet-fullscreen-backdrop");
  const modal = document.getElementById("snippet-fullscreen-modal");
  const titleEl = document.getElementById("snippet-fullscreen-title");
  const bodyEl = document.getElementById("snippet-fullscreen-body");
  const closeBtn = document.getElementById("snippet-fullscreen-close");
  if (!backdrop || !modal) return;

  function closeModal() {
    backdrop.hidden = true;
    modal.hidden = true;
    bodyEl.innerHTML = "";
  }

  function openModal(snippetId, title) {
    const source = document.getElementById(`snippet-files-${snippetId}`);
    if (!source) return;

    const clone = source.cloneNode(true);
    clone.hidden = false;
    clone.removeAttribute("id");
    bodyEl.innerHTML = "";
    bodyEl.appendChild(clone);
    titleEl.textContent = title;

    clone.querySelectorAll("pre code").forEach((codeEl) => {
      if (window.hljs && window.hljs.lineNumbersBlock) {
        window.hljs.lineNumbersBlock(codeEl);
      }
    });

    backdrop.hidden = false;
    modal.hidden = false;
  }

  document.addEventListener("click", (event) => {
    const toggle = event.target.closest(".snippet-toggle");
    if (!toggle) return;
    const title = toggle.querySelector(".snippet-card-title-text").textContent;
    openModal(toggle.dataset.snippetId, title);
  });

  closeBtn.addEventListener("click", closeModal);
  backdrop.addEventListener("click", closeModal);
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && !modal.hidden) closeModal();
  });
});
