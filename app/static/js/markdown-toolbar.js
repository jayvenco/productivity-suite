// Lichte markdown-werkbalk voor plain-text <textarea>s (i.p.v. contenteditable),
// zodat de bestaande checklist-syntax ("- [ ] item") in kanban-kaarten gewoon
// blijft werken -- de inhoud blijft immers platte, regel-gebaseerde tekst.
document.addEventListener("DOMContentLoaded", () => {
  document.addEventListener("click", (event) => {
    const button = event.target.closest(".md-toolbar [data-md]");
    if (!button) return;
    event.preventDefault();

    const textarea = button.closest(".md-editor").querySelector(".md-textarea");
    if (!textarea) return;

    applyMarkdownAction(textarea, button.dataset.md);
  });

  function applyMarkdownAction(textarea, action) {
    switch (action) {
      case "bold":
        wrapSelection(textarea, "**", "**", "vet");
        break;
      case "italic":
        wrapSelection(textarea, "*", "*", "cursief");
        break;
      case "code":
        wrapSelection(textarea, "`", "`", "code");
        break;
      case "heading":
        prefixLines(textarea, "## ");
        break;
      case "bullet":
        prefixLines(textarea, "- ");
        break;
      case "link":
        insertLink(textarea);
        break;
    }
  }

  function wrapSelection(textarea, before, after, placeholder) {
    const { value, selectionStart, selectionEnd } = textarea;
    const selected = value.slice(selectionStart, selectionEnd) || placeholder;

    textarea.value = value.slice(0, selectionStart) + before + selected + after + value.slice(selectionEnd);
    const selStart = selectionStart + before.length;
    focusAndSelect(textarea, selStart, selStart + selected.length);
  }

  function prefixLines(textarea, prefix) {
    const { value, selectionStart, selectionEnd } = textarea;
    const lineStart = value.lastIndexOf("\n", selectionStart - 1) + 1;
    const nextBreak = value.indexOf("\n", selectionEnd);
    const lineEnd = nextBreak === -1 ? value.length : nextBreak;

    const block = value.slice(lineStart, lineEnd);
    const prefixed = block
      .split("\n")
      .map((line) => prefix + line)
      .join("\n");

    textarea.value = value.slice(0, lineStart) + prefixed + value.slice(lineEnd);
    focusAndSelect(textarea, lineStart, lineStart + prefixed.length);
  }

  function insertLink(textarea) {
    const url = window.prompt("Link-URL:", "https://");
    if (!url) return;

    const { value, selectionStart, selectionEnd } = textarea;
    const selected = value.slice(selectionStart, selectionEnd);
    const linkText = selected || window.prompt("Linktekst:", url) || url;
    const markdown = `[${linkText}](${url})`;

    textarea.value = value.slice(0, selectionStart) + markdown + value.slice(selectionEnd);
    const cursor = selectionStart + markdown.length;
    focusAndSelect(textarea, cursor, cursor);
  }

  function focusAndSelect(textarea, start, end) {
    textarea.focus();
    textarea.setSelectionRange(start, end);
  }
});
