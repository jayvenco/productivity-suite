// Account-pagina: "Sleutel testen"-knop voor de OpenAI API-sleutel. Stuurt de waarde die
// nu in het veld staat (ook als die nog niet is opgeslagen) naar de server, die 'm tegen
// de OpenAI API test -- zo weet je vóór het opslaan al of een sleutel werkt.
document.addEventListener("DOMContentLoaded", () => {
  const testBtn = document.getElementById("openai-key-test-btn");
  const input = document.getElementById("openai_api_key");
  const resultEl = document.getElementById("openai-key-test-result");
  if (!testBtn || !input || !resultEl) return;

  testBtn.addEventListener("click", async () => {
    testBtn.disabled = true;
    testBtn.textContent = "Testen...";
    resultEl.textContent = "";
    resultEl.style.color = "";

    try {
      const response = await fetch("/account/openai-key/test", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: new URLSearchParams({ openai_api_key: input.value }),
      });
      const data = await response.json();
      resultEl.textContent = data.message;
      resultEl.style.color = data.valid ? "var(--success)" : "var(--danger)";
    } catch (err) {
      resultEl.textContent = "Testen mislukt, probeer het opnieuw.";
      resultEl.style.color = "var(--danger)";
    } finally {
      testBtn.disabled = false;
      testBtn.textContent = "Sleutel testen";
    }
  });
});
