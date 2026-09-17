// Live markdown-preview: rendert server-side (dezelfde renderer als bij het opslaan)
// via een klein debounced fetch-verzoek, zodat er geen aparte markdown-parser in
// de browser nodig is.
document.addEventListener("DOMContentLoaded", () => {
  const textarea = document.getElementById("content");
  const preview = document.getElementById("note-preview");
  if (!textarea || !preview) return;

  let debounceTimer = null;

  textarea.addEventListener("input", () => {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(async () => {
      const response = await fetch("/notes/preview", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: new URLSearchParams({ content: textarea.value }),
      });
      preview.innerHTML = await response.text();
    }, 250);
  });
});
