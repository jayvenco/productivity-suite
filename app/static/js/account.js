// Account-pagina: "testen"-knoppen voor de OpenAI API-sleutel en de Whisper/Speaches-
// verbinding. Sturen telkens de waarde die nu in het veld staat (ook als die nog niet is
// opgeslagen) naar de server, die 'm test -- zo weet je vóór het opslaan al of het werkt.
document.addEventListener("DOMContentLoaded", () => {
  function wireTestButton({ buttonId, resultId, url, buildBody, idleLabel }) {
    const btn = document.getElementById(buttonId);
    const resultEl = document.getElementById(resultId);
    if (!btn || !resultEl) return;

    btn.addEventListener("click", async () => {
      btn.disabled = true;
      btn.textContent = "Testen...";
      resultEl.textContent = "";
      resultEl.style.color = "";

      try {
        const response = await fetch(url, {
          method: "POST",
          headers: { "Content-Type": "application/x-www-form-urlencoded" },
          body: buildBody(),
        });
        const data = await response.json();
        resultEl.textContent = data.message;
        resultEl.style.color = data.valid ? "var(--success)" : "var(--danger)";
      } catch (err) {
        resultEl.textContent = "Testen mislukt, probeer het opnieuw.";
        resultEl.style.color = "var(--danger)";
      } finally {
        btn.disabled = false;
        btn.textContent = idleLabel;
      }
    });
  }

  wireTestButton({
    buttonId: "openai-key-test-btn",
    resultId: "openai-key-test-result",
    url: "/account/openai-key/test",
    idleLabel: "Sleutel testen",
    buildBody: () =>
      new URLSearchParams({ openai_api_key: document.getElementById("openai_api_key").value }),
  });

  wireTestButton({
    buttonId: "whisper-test-btn",
    resultId: "whisper-test-result",
    url: "/voice/test-connection",
    idleLabel: "Verbinding testen",
    buildBody: () =>
      new URLSearchParams({
        whisper_service_url: document.getElementById("whisper_service_url").value,
        whisper_model: document.getElementById("whisper_model").value,
      }),
  });
});
