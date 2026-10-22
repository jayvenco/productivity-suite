// Herbruikbare rich-text-editor. Elke <textarea data-rich-editor> wordt automatisch een
// WYSIWYG-editor (contenteditable + werkbalk); de textarea blijft verborgen en bevat de HTML, dus
// formulieren werken ongewijzigd. Gebruikt voor notities, taken, kanban-kaarten en de inbox.
//
// Werkbalk: vet, cursief, onderstrepen, doorhalen, koppen, lijsten, afvinkbare checklist,
// citaat, link, code, afbeelding (knop, plakken of slepen), ongedaan maken, opmaak wissen.
// Oudere inhoud in platte tekst/markdown wordt bij het openen omgezet naar HTML.
// API per editor: textarea.richEditor = { editor, getHTML, setHTML, isEmpty, focus, clear }.
(function () {
  const MAX_IMAGE_WIDTH = 1600;
  const HTML_HINT = /<(p|div|br|ul|ol|li|h[1-6]|blockquote|pre|strong|b|em|i|u|s|a|img|hr)\b/i;

  const esc = (s) => s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

  function inlineMarkdown(s) {
    return esc(s)
      .replace(/`([^`]+)`/g, "<code>$1</code>")
      .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
      .replace(/(^|[^*])\*([^*\s][^*]*)\*/g, "$1<em>$2</em>");
  }

  // Platte tekst/markdown (van vóór de editor) -> HTML, inclusief "- [ ]"-checklists.
  function legacyToHtml(text) {
    const out = [];
    let open = null;
    const close = () => {
      if (open) out.push(`</${open}>`);
      open = null;
    };
    const start = (tag, cls) => {
      const key = tag + (cls || "");
      if (open === key) return;
      close();
      out.push(cls ? `<${tag} class="${cls}">` : `<${tag}>`);
      open = key;
    };
    for (const line of text.replace(/\r/g, "").split("\n")) {
      let m;
      if ((m = line.match(/^\s*[-*]\s*\[([ xX])\]\s*(.*)$/))) {
        start("ul", "rt-checklist");
        out.push(`<li data-checked="${m[1] === " " ? 0 : 1}">${inlineMarkdown(m[2])}</li>`);
      } else if ((m = line.match(/^\s*[-*]\s+(.*)$/))) {
        start("ul");
        out.push(`<li>${inlineMarkdown(m[1])}</li>`);
      } else if ((m = line.match(/^\s*\d+[.)]\s+(.*)$/))) {
        start("ol");
        out.push(`<li>${inlineMarkdown(m[1])}</li>`);
      } else if ((m = line.match(/^#{1,3}\s+(.*)$/))) {
        close();
        out.push(`<h2>${inlineMarkdown(m[1])}</h2>`);
      } else if (line.trim() === "") {
        close();
      } else {
        close();
        out.push(`<p>${inlineMarkdown(line)}</p>`);
      }
    }
    close();
    return out.join("");
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

  const TOOLBAR = `
    <button type="button" data-cmd="bold" title="Vet (Cmd/Ctrl+B)"><b>V</b></button>
    <button type="button" data-cmd="italic" title="Cursief (Cmd/Ctrl+I)"><i>C</i></button>
    <button type="button" data-cmd="underline" title="Onderstrepen (Cmd/Ctrl+U)"><u>O</u></button>
    <button type="button" data-cmd="strikeThrough" title="Doorhalen"><s>D</s></button>
    <select data-cmd="formatBlock" title="Kop">
      <option value="p">Normale tekst</option>
      <option value="h2">Kop 1</option>
      <option value="h3">Kop 2</option>
    </select>
    <button type="button" data-cmd="insertUnorderedList" title="Opsomming">• Lijst</button>
    <button type="button" data-cmd="insertOrderedList" title="Genummerde lijst">1. Lijst</button>
    <button type="button" data-cmd="checklist" title="Afvinkbare checklist">☑ Checklist</button>
    <button type="button" data-cmd="blockquote" title="Citaat">❝</button>
    <button type="button" data-cmd="createLink" title="Link invoegen">Link</button>
    <button type="button" data-cmd="code" title="Code">&lt;/&gt;</button>
    <button type="button" data-cmd="insertImage" title="Afbeelding invoegen (of plak/sleep er een)">🖼</button>
    <button type="button" data-cmd="undo" title="Ongedaan maken">↶</button>
    <button type="button" data-cmd="redo" title="Opnieuw">↷</button>
    <button type="button" data-cmd="removeFormat" title="Opmaak wissen">Wissen</button>`;

  function create(textarea) {
    if (textarea.richEditor) return textarea.richEditor;

    const wrap = document.createElement("div");
    wrap.className = "rich-wrap";
    const toolbar = document.createElement("div");
    toolbar.className = "rich-toolbar";
    toolbar.innerHTML = TOOLBAR;
    const editor = document.createElement("div");
    editor.className = "rich-editor";
    editor.contentEditable = "true";
    editor.setAttribute("role", "textbox");
    editor.setAttribute("aria-multiline", "true");
    if (textarea.placeholder) editor.dataset.placeholder = textarea.placeholder;
    const fileInput = document.createElement("input");
    fileInput.type = "file";
    fileInput.accept = "image/*";
    fileInput.hidden = true;

    wrap.append(toolbar, editor, fileInput);
    textarea.parentNode.insertBefore(wrap, textarea);
    textarea.hidden = true;
    textarea.removeAttribute("required"); // een verborgen verplicht veld blokkeert het versturen

    const initial = textarea.value || "";
    editor.innerHTML = (HTML_HINT.test(initial) ? initial : legacyToHtml(initial)) || "<p><br></p>";
    // Elke regel een <p> (anders maakt Chrome kale tekst + <div>'s, wat "eerste regel = titel" breekt).
    try {
      document.execCommand("defaultParagraphSeparator", false, "p");
    } catch (err) {
      /* niet ondersteund: dan blijft het browsergedrag */
    }
    let savedRange = null;

    const isEmpty = () => !editor.querySelector("img") && editor.textContent.trim() === "" && !editor.querySelector("li[data-checked]");

    function refresh() {
      editor.classList.toggle("is-empty", isEmpty());
    }

    function normalizeChecklists() {
      editor.querySelectorAll("ul.rt-checklist > li").forEach((li) => {
        if (!li.hasAttribute("data-checked")) li.setAttribute("data-checked", "0");
      });
    }

    function getHTML() {
      normalizeChecklists();
      return isEmpty() ? "" : editor.innerHTML;
    }

    function sync() {
      textarea.value = getHTML();
      refresh();
    }

    function currentRange() {
      const sel = window.getSelection();
      return sel.rangeCount && editor.contains(sel.anchorNode) ? sel.getRangeAt(0).cloneRange() : null;
    }

    function closestFromSelection(selector) {
      const sel = window.getSelection();
      let node = sel.anchorNode;
      if (!node || !editor.contains(node)) return null;
      if (node.nodeType === 3) node = node.parentNode;
      return node.closest(selector);
    }

    function toggleChecklist() {
      editor.focus();
      if (closestFromSelection("ul.rt-checklist")) {
        document.execCommand("insertUnorderedList"); // lijst helemaal uitzetten
        return;
      }
      if (!closestFromSelection("ul")) document.execCommand("insertUnorderedList");
      const ul = closestFromSelection("ul");
      if (ul) {
        ul.classList.add("rt-checklist");
        ul.querySelectorAll(":scope > li").forEach((li) => li.setAttribute("data-checked", li.getAttribute("data-checked") || "0"));
      }
    }

    function wrapSelectionInCode() {
      const sel = window.getSelection();
      if (!sel.rangeCount) return;
      const range = sel.getRangeAt(0);
      if (range.collapsed) return;
      const code = document.createElement("code");
      code.textContent = range.toString();
      range.deleteContents();
      range.insertNode(code);
      sel.removeAllRanges();
    }

    async function insertImageFiles(files, range) {
      editor.focus();
      if (range) {
        const sel = window.getSelection();
        sel.removeAllRanges();
        sel.addRange(range);
      }
      for (const file of files) {
        document.execCommand("insertImage", false, await fileToDataUrl(file));
      }
      sync();
    }

    const imageFiles = (list) => Array.from(list || []).filter((f) => f.type.startsWith("image/"));

    // Werkbalk: mousedown niet laten stelen van de selectie in de editor.
    toolbar.addEventListener("mousedown", (event) => {
      if (event.target.closest("button")) event.preventDefault();
    });

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
      } else if (cmd === "checklist") {
        toggleChecklist();
      } else if (cmd === "blockquote") {
        document.execCommand("formatBlock", false, closestFromSelection("blockquote") ? "p" : "blockquote");
      } else if (cmd === "insertImage") {
        savedRange = currentRange();
        fileInput.click();
      } else {
        document.execCommand(cmd, false, null);
      }
      sync();
    });

    toolbar.querySelector("select[data-cmd='formatBlock']").addEventListener("change", (event) => {
      editor.focus();
      document.execCommand("formatBlock", false, event.target.value);
      sync();
    });

    fileInput.addEventListener("change", () => {
      const files = imageFiles(fileInput.files);
      fileInput.value = "";
      if (files.length) insertImageFiles(files, savedRange);
    });

    editor.addEventListener("paste", (event) => {
      const files = imageFiles(event.clipboardData && event.clipboardData.files);
      if (!files.length) return; // gewone tekst-paste: standaardgedrag
      event.preventDefault();
      insertImageFiles(files, null);
    });

    editor.addEventListener("dragover", (event) => {
      if (event.dataTransfer && [...event.dataTransfer.types].includes("Files")) event.preventDefault();
    });

    editor.addEventListener("drop", (event) => {
      const files = imageFiles(event.dataTransfer && event.dataTransfer.files);
      if (!files.length) return;
      event.preventDefault();
      insertImageFiles(files, null);
    });

    // Klikken op het vakje van een checklist-item vinkt het af (de ::before-ruimte links).
    editor.addEventListener("click", (event) => {
      const li = event.target.closest && event.target.closest("ul.rt-checklist > li");
      if (!li || !editor.contains(li)) return;
      if (event.clientX - li.getBoundingClientRect().left <= 26) {
        li.setAttribute("data-checked", li.getAttribute("data-checked") === "1" ? "0" : "1");
        sync();
      }
    });

    // Een nieuw item na Enter in een afgevinkt item begint niet afgevinkt.
    editor.addEventListener("keyup", (event) => {
      if (event.key !== "Enter") return;
      const li = closestFromSelection("ul.rt-checklist > li");
      if (li && li.textContent.trim() === "") li.setAttribute("data-checked", "0");
    });

    editor.addEventListener("input", sync);
    editor.addEventListener("blur", sync);
    if (textarea.form) textarea.form.addEventListener("submit", sync);
    sync();

    const api = {
      editor,
      getHTML,
      isEmpty,
      focus: () => editor.focus(),
      setHTML(html) {
        editor.innerHTML = (HTML_HINT.test(html || "") ? html : legacyToHtml(html || "")) || "<p><br></p>";
        sync();
      },
      clear() {
        editor.innerHTML = "<p><br></p>";
        sync();
      },
    };
    textarea.richEditor = api;
    return api;
  }

  window.RichEditor = { create, legacyToHtml };

  document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll("textarea[data-rich-editor]").forEach(create);
  });
})();
