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
    } else if (cmd === "insertImage") {
      savedRange = currentRange();
      imageInput.click();
    } else {
      document.execCommand(cmd, false, null);
    }
  });

  toolbar.querySelector("select[data-cmd='formatBlock']").addEventListener("change", (event) => {
    editor.focus();
    document.execCommand("formatBlock", false, event.target.value);
  });

  // Afbeeldingen (plakken, slepen of via de knop) worden als data-URI in de notitie-HTML
  // opgeslagen. Grote afbeeldingen schalen we eerst terug (max. 1600px breed), anders wordt
  // de notitie onnodig zwaar.
  const MAX_IMAGE_WIDTH = 1600;
  const imageInput = document.getElementById("note-image-input");
  let savedRange = null;

  function currentRange() {
    const selection = window.getSelection();
    return selection.rangeCount && editor.contains(selection.anchorNode) ? selection.getRangeAt(0).cloneRange() : null;
  }

  function fileToDataUrl(file) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onerror = reject;
      reader.onload = () => {
        const original = reader.result;
        if (file.type === "image/gif" || file.type === "image/svg+xml") return resolve(original);
        const img = new Image();
        img.onerror = () => resolve(original);
        img.onload = () => {
          if (img.width <= MAX_IMAGE_WIDTH) return resolve(original);
          const canvas = document.createElement("canvas");
          canvas.width = MAX_IMAGE_WIDTH;
          canvas.height = Math.round((img.height * MAX_IMAGE_WIDTH) / img.width);
          canvas.getContext("2d").drawImage(img, 0, 0, canvas.width, canvas.height);
          const type = file.type === "image/png" || file.type === "image/webp" ? file.type : "image/jpeg";
          resolve(canvas.toDataURL(type, 0.9));
        };
        img.src = original;
      };
      reader.readAsDataURL(file);
    });
  }

  async function insertImageFiles(files, range) {
    editor.focus();
    if (range) {
      const selection = window.getSelection();
      selection.removeAllRanges();
      selection.addRange(range);
    }
    for (const file of files) {
      const dataUrl = await fileToDataUrl(file);
      document.execCommand("insertImage", false, dataUrl);
    }
  }

  const imageFiles = (list) => Array.from(list || []).filter((f) => f.type.startsWith("image/"));

  editor.addEventListener("paste", (event) => {
    const files = imageFiles(event.clipboardData && event.clipboardData.files);
    if (!files.length) return; // gewone tekst-paste: standaardgedrag laten gebeuren
    event.preventDefault();
    insertImageFiles(files, null);
  });

  editor.addEventListener("dragover", (event) => {
    if (imageFiles(event.dataTransfer && event.dataTransfer.files).length || (event.dataTransfer && [...event.dataTransfer.types].includes("Files"))) {
      event.preventDefault();
    }
  });

  editor.addEventListener("drop", (event) => {
    const files = imageFiles(event.dataTransfer && event.dataTransfer.files);
    if (!files.length) return;
    event.preventDefault();
    insertImageFiles(files, null);
  });

  imageInput.addEventListener("change", () => {
    const files = imageFiles(imageInput.files);
    imageInput.value = "";
    if (files.length) insertImageFiles(files, savedRange);
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
