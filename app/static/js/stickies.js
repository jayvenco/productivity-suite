// Auto-save: elke wijziging (tekst na verlaten, kleur, tags, temp) wordt direct via fetch
// opgeslagen, zonder pagina-herlaad -- het "Opslaan"-gevoel van echte plakbriefjes.
document.querySelectorAll("[data-sticky-form]").forEach((form) => {
  const save = () => {
    fetch(form.action, {
      method: "POST",
      headers: { "X-Requested-With": "fetch" },
      body: new URLSearchParams(new FormData(form)),
    });
  };

  form.addEventListener("change", (event) => {
    if (event.target.name === "color") {
      form.className = form.className.replace(/sticky-(yellow|pink|blue|green|orange|purple)/, `sticky-${event.target.value}`);
    }
    save();
  });
});
