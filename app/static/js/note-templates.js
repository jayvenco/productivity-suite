// Sjablonen: herhaalbare rijen in het invulformulier en de module-editor.
document.addEventListener("DOMContentLoaded", () => {
  // ---- Invulformulier: rijen toevoegen/verwijderen ----
  document.addEventListener("click", (event) => {
    const add = event.target.closest("[data-add-row]");
    if (add) {
      const module = add.closest(".tpl-module");
      const rows = module.querySelector("[data-rows]");
      const tpl = module.querySelector("template[data-row-template]");
      const next = parseInt(rows.dataset.next, 10);
      rows.dataset.next = String(next + 1);
      const holder = document.createElement("div");
      holder.innerHTML = tpl.innerHTML.replaceAll("__R__", String(next));
      rows.appendChild(holder.firstElementChild);
      return;
    }
    const remove = event.target.closest("[data-remove-row]");
    if (remove) {
      const row = remove.closest("[data-row]");
      const rows = row.parentElement;
      if (rows.querySelectorAll("[data-row]").length > 1) row.remove();
      else row.querySelectorAll("input,select,textarea").forEach((el) => (el.type === "checkbox" ? (el.checked = false) : (el.value = "")));
    }
  });

  // ---- Sjabloon-editor ----
  const dataEl = document.getElementById("tpl-data");
  if (!dataEl) return;
  const { library, modules } = JSON.parse(dataEl.textContent);
  const list = document.getElementById("tpl-modules");
  const select = document.getElementById("tpl-library");
  const form = document.getElementById("tpl-edit-form");
  library.forEach((m) => {
    const opt = document.createElement("option");
    opt.value = m.id;
    opt.textContent = m.name;
    select.appendChild(opt);
  });
  const byId = new Map(library.map((m) => [m.id, m]));

  function addModule(item) {
    const meta = byId.get(item.module_id);
    const li = document.createElement("li");
    li.className = "tpl-module-item";
    li.dataset.moduleId = item.module_id;
    li.innerHTML = `
      <div class="tpl-module-head">
        <strong></strong>
        <span class="tpl-module-actions">
          <button type="button" data-up title="Omhoog">↑</button>
          <button type="button" data-down title="Omlaag">↓</button>
          <button type="button" data-remove title="Verwijderen">×</button>
        </span>
      </div>
      <input type="text" data-title placeholder="Sectietitel (leeg = naam van de module)">
      <label class="tpl-opt"><input type="checkbox" data-optional class="round-checkbox"> Optioneel (kan bij gebruik uitgevinkt worden)</label>
      <textarea data-default rows="2" placeholder="Hint/standaardtekst (optioneel, mag {{date}} e.d. bevatten)"></textarea>
      <details ${meta.kind === "fields" ? "open" : ""}><summary>Geavanceerd: configuratie (JSON)</summary>
        <textarea data-config rows="6" placeholder='{"fields":[{"name":"deelnemers","label":"Deelnemers","type":"textarea"}]}'></textarea>
        <small class="tpl-hint">Voor "Velden": veldtypes text, textarea, number, date, checkbox, select (met "options"), url, task; optioneel placeholder, default, required, description.</small>
      </details>`;
    li.querySelector("strong").textContent = meta.name;
    li.querySelector("[data-title]").value = item.title || "";
    li.querySelector("[data-optional]").checked = !!item.optional;
    li.querySelector("[data-default]").value = item.default_content || "";
    li.querySelector("[data-config]").value = item.config || "";
    list.appendChild(li);
  }

  modules.forEach(addModule);

  list.addEventListener("click", (event) => {
    const li = event.target.closest(".tpl-module-item");
    if (!li) return;
    if (event.target.closest("[data-up]") && li.previousElementSibling) list.insertBefore(li, li.previousElementSibling);
    else if (event.target.closest("[data-down]") && li.nextElementSibling) list.insertBefore(li.nextElementSibling, li);
    else if (event.target.closest("[data-remove]")) li.remove();
  });

  document.getElementById("tpl-add").addEventListener("click", () => {
    if (select.value) addModule({ module_id: parseInt(select.value, 10) });
  });

  function serialize() {
    return JSON.stringify(
      [...list.children].map((li) => ({
        module_id: parseInt(li.dataset.moduleId, 10),
        title: li.querySelector("[data-title]").value,
        optional: li.querySelector("[data-optional]").checked,
        default_content: li.querySelector("[data-default]").value,
        config: li.querySelector("[data-config]").value,
      }))
    );
  }

  form.addEventListener("submit", () => {
    document.getElementById("modules_json").value = serialize();
  });

  document.getElementById("tpl-preview-btn").addEventListener("click", async () => {
    const panel = document.getElementById("tpl-preview-panel");
    const body = new URLSearchParams({ name: document.getElementById("name").value, modules_json: serialize() });
    const response = await fetch("/notes/templates/preview", { method: "POST", body });
    panel.innerHTML = response.ok ? await response.text() : `<p>Voorbeeld mislukt: ${(await response.json()).detail}</p>`;
    panel.hidden = false;
  });
});
