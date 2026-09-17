// Snippet-kaarten staan standaard ingeklapt (alleen titel + tags + bestandsnamen);
// klik op de titel om de code te tonen/verbergen.
document.addEventListener("DOMContentLoaded", () => {
  document.addEventListener("click", (event) => {
    const toggle = event.target.closest(".snippet-toggle");
    if (!toggle) return;

    const files = document.getElementById(`snippet-files-${toggle.dataset.snippetId}`);
    if (!files) return;

    files.hidden = !files.hidden;
    toggle.querySelector(".snippet-toggle-arrow").textContent = files.hidden ? "▸" : "▾";
  });
});
