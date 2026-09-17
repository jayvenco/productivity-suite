// Dynamisch bestanden toevoegen/verwijderen in het snippet-formulier. Kloont een
// bestaand bestand-blok (i.p.v. de talenlijst te dupliceren in JS) en maakt het leeg.
document.addEventListener("DOMContentLoaded", () => {
  const container = document.getElementById("snippet-files");
  const addBtn = document.getElementById("add-file-btn");
  if (!container || !addBtn) return;

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
});
