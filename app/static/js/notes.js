// Lichte rich-text editor op basis van contenteditable + document.execCommand --
// geen zware WYSIWYG-library nodig voor een basis tools set (vet, cursief, koppen,
// lijsten, links, code). De opgeslagen inhoud is HTML, geen markdown.
document.addEventListener("DOMContentLoaded", () => {
  const editor = document.getElementById("note-editor");
  const toolbar = document.getElementById("rich-toolbar");
  const form = document.getElementById("note-form");
  const hiddenContent = document.getElementById("content");
  if (!editor || !toolbar || !form) return;

  toolbar.addEventListener("click", (event) => {
    const button = event.target.closest("button[data-cmd]");
    if (!button) return;
    event.preventDefault();
    editor.focus();

    const cmd = button.dataset.cmd;
    if (cmd === "createLink") {
      const url = window.prompt("Link-URL:", "https://");
      if (url) document.execCommand("createLink", false, url);
    } else if (cmd === "code") {
      wrapSelectionInCode();
    } else {
      document.execCommand(cmd, false, null);
    }
  });

  toolbar.querySelector("select[data-cmd='formatBlock']").addEventListener("change", (event) => {
    editor.focus();
    document.execCommand("formatBlock", false, event.target.value);
  });

  function wrapSelectionInCode() {
    const selection = window.getSelection();
    if (!selection.rangeCount) return;
    const range = selection.getRangeAt(0);
    if (range.collapsed) return;

    const code = document.createElement("code");
    code.textContent = range.toString();
    range.deleteContents();
    range.insertNode(code);
    selection.removeAllRanges();
  }

  form.addEventListener("submit", () => {
    hiddenContent.value = editor.innerHTML;
  });
});
