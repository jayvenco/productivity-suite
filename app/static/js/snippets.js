// Dynamisch bestanden toevoegen/verwijderen in het snippet-formulier. Kloont een
// bestaand bestand-blok (i.p.v. de talenlijst te dupliceren in JS) en maakt het leeg.
// Daarnaast: taal automatisch afleiden uit de bestandsextensie.
document.addEventListener("DOMContentLoaded", () => {
  const container = document.getElementById("snippet-files");
  const addBtn = document.getElementById("add-file-btn");
  if (!container || !addBtn) return;

  const EXTENSION_TO_LANGUAGE = {
    py: "python",
    js: "javascript",
    mjs: "javascript",
    cjs: "javascript",
    jsx: "javascript",
    ts: "typescript",
    tsx: "typescript",
    sh: "bash",
    bash: "bash",
    zsh: "bash",
    html: "html",
    htm: "html",
    css: "css",
    scss: "css",
    json: "json",
    yml: "yaml",
    yaml: "yaml",
    sql: "sql",
    md: "markdown",
    markdown: "markdown",
    go: "go",
    rs: "rust",
    java: "java",
    cs: "csharp",
    php: "php",
    rb: "ruby",
    c: "c",
    h: "c",
    cpp: "cpp",
    cc: "cpp",
    cxx: "cpp",
    hpp: "cpp",
  };

  function languageForFilename(filename) {
    const dotIndex = filename.lastIndexOf(".");
    if (dotIndex === -1) return null;
    const extension = filename.slice(dotIndex + 1).toLowerCase();
    return EXTENSION_TO_LANGUAGE[extension] || null;
  }

  addBtn.addEventListener("click", () => {
    const blocks = container.querySelectorAll(".snippet-file-block");
    const clone = blocks[blocks.length - 1].cloneNode(true);
    clone.querySelector('input[name="filename"]').value = "";
    clone.querySelector('select[name="language"]').value = "plaintext";
    clone.querySelector('textarea[name="content"]').value = "";
    container.appendChild(clone);
  });

  container.addEventListener("click", (event) => {
    const removeBtn = event.target.closest(".remove-file-btn");
    if (!removeBtn) return;
    const blocks = container.querySelectorAll(".snippet-file-block");
    if (blocks.length <= 1) return; // altijd minstens één bestand laten staan
    removeBtn.closest(".snippet-file-block").remove();
  });

  // Zodra er een herkende extensie getypt is, zet de taal-select automatisch mee --
  // scheelt handmatig kiezen voor de meest voorkomende bestandstypes. Blijft
  // gewoon aanpasbaar via de select zelf als de herkenning een keer misgokt.
  container.addEventListener("input", (event) => {
    const filenameInput = event.target.closest('input[name="filename"]');
    if (!filenameInput) return;

    const language = languageForFilename(filenameInput.value.trim());
    if (!language) return;

    const select = filenameInput.closest(".snippet-file-block").querySelector('select[name="language"]');
    select.value = language;
  });
});
