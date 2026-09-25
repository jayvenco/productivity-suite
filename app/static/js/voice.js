// Voice-notitie: neemt audio op via MediaRecorder, laat 'm transcriberen door de
// zelf-gehoste Whisper-container (server-side, zie app/routers/voice.py), en
// slaat het (door de gebruiker gecontroleerde/aangepaste) transcript op als
// gewone notitie via de bestaande /notes-route. Er zit bewust geen automatische
// interpretatie (taak/kanban/...) in -- dat is een latere uitbreiding; dit is de
// eerste stap: spreken -> transcript -> zelf controleren -> opslaan.
document.addEventListener("DOMContentLoaded", () => {
  const spokeBtn = document.getElementById("voice-spoke-btn");
  const backdrop = document.getElementById("voice-modal-backdrop");
  const panel = document.getElementById("voice-recorder-panel");
  const closeBtn = document.getElementById("voice-recorder-close");
  const statusEl = document.getElementById("voice-recorder-status");
  const recordBtn = document.getElementById("voice-recorder-record-btn");
  const recordIcon = document.getElementById("voice-recorder-record-icon");
  const timerEl = document.getElementById("voice-recorder-timer");
  const resultEl = document.getElementById("voice-recorder-result");
  const titleInput = document.getElementById("voice-recorder-title");
  const transcriptInput = document.getElementById("voice-recorder-transcript");
  const saveBtn = document.getElementById("voice-recorder-save-btn");
  const retryBtn = document.getElementById("voice-recorder-retry-btn");
  const languageSelect = document.getElementById("voice-recorder-language");
  if (!spokeBtn || !panel) return;

  const LANGUAGE_STORAGE_KEY = "voice-recorder-language";
  if (languageSelect) {
    try {
      const savedLanguage = localStorage.getItem(LANGUAGE_STORAGE_KEY);
      if (savedLanguage !== null) languageSelect.value = savedLanguage;
    } catch (err) {
      // localStorage kan geblokkeerd zijn; werkt dan gewoon met de default (auto).
    }
    languageSelect.addEventListener("change", () => {
      try {
        localStorage.setItem(LANGUAGE_STORAGE_KEY, languageSelect.value);
      } catch (err) {
        // Zie hierboven.
      }
    });
  }

  let mediaRecorder = null;
  let audioChunks = [];
  let timerInterval = null;
  let secondsElapsed = 0;

  function formatTime(totalSeconds) {
    const m = String(Math.floor(totalSeconds / 60)).padStart(2, "0");
    const s = String(totalSeconds % 60).padStart(2, "0");
    return `${m}:${s}`;
  }

  function resetPanel() {
    statusEl.textContent = "Druk op opnemen en spreek je notitie in.";
    statusEl.classList.remove("voice-recorder-status-error");
    recordBtn.disabled = false;
    recordBtn.classList.remove("recording");
    recordIcon.textContent = "⏺";
    timerEl.hidden = true;
    timerEl.textContent = "00:00";
    resultEl.hidden = true;
    titleInput.value = "";
    transcriptInput.value = "";
    secondsElapsed = 0;
    clearInterval(timerInterval);
  }

  function openPanel() {
    resetPanel();
    backdrop.hidden = false;
    panel.hidden = false;
  }

  function closePanel() {
    if (mediaRecorder && mediaRecorder.state !== "inactive") {
      mediaRecorder.stop();
    }
    backdrop.hidden = true;
    panel.hidden = true;
  }

  spokeBtn.addEventListener("click", openPanel);
  closeBtn.addEventListener("click", closePanel);
  backdrop.addEventListener("click", closePanel);
  retryBtn.addEventListener("click", resetPanel);

  async function startRecording() {
    let stream;
    try {
      stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch (err) {
      statusEl.textContent = "Kon geen toegang krijgen tot de microfoon.";
      statusEl.classList.add("voice-recorder-status-error");
      return;
    }

    audioChunks = [];
    mediaRecorder = new MediaRecorder(stream);
    mediaRecorder.addEventListener("dataavailable", (event) => {
      if (event.data.size > 0) audioChunks.push(event.data);
    });
    mediaRecorder.addEventListener("stop", () => {
      stream.getTracks().forEach((track) => track.stop());
      clearInterval(timerInterval);
      transcribeRecording();
    });

    mediaRecorder.start();
    recordBtn.classList.add("recording");
    recordIcon.textContent = "⏹";
    statusEl.textContent = "Bezig met opnemen...";
    timerEl.hidden = false;
    secondsElapsed = 0;
    timerEl.textContent = formatTime(0);
    timerInterval = setInterval(() => {
      secondsElapsed += 1;
      timerEl.textContent = formatTime(secondsElapsed);
    }, 1000);
  }

  function stopRecording() {
    if (mediaRecorder && mediaRecorder.state !== "inactive") {
      mediaRecorder.stop();
    }
  }

  recordBtn.addEventListener("click", () => {
    if (mediaRecorder && mediaRecorder.state === "recording") {
      stopRecording();
    } else {
      startRecording();
    }
  });

  async function transcribeRecording() {
    recordBtn.disabled = true;
    recordBtn.classList.remove("recording");
    recordIcon.textContent = "⏺";
    statusEl.textContent = "Bezig met transcriberen...";

    const blob = new Blob(audioChunks, { type: "audio/webm" });
    const formData = new FormData();
    formData.append("audio", blob, "opname.webm");
    if (languageSelect && languageSelect.value) {
      formData.append("language", languageSelect.value);
    }

    try {
      const response = await fetch("/voice/transcribe", { method: "POST", body: formData });
      if (!response.ok) {
        const errorBody = await response.json().catch(() => ({}));
        throw new Error(errorBody.detail || "Transcriberen mislukt.");
      }
      const data = await response.json();
      recordBtn.disabled = false;
      if (!data.text) {
        statusEl.textContent = "Geen tekst herkend -- probeer het opnieuw.";
        statusEl.classList.add("voice-recorder-status-error");
        return;
      }
      statusEl.textContent = "Controleer het transcript en sla op.";
      transcriptInput.value = data.text;
      titleInput.value = data.text.slice(0, 60);
      resultEl.hidden = false;
    } catch (err) {
      recordBtn.disabled = false;
      statusEl.textContent = err.message || "Transcriberen mislukt.";
      statusEl.classList.add("voice-recorder-status-error");
    }
  }

  saveBtn.addEventListener("click", async () => {
    const title = titleInput.value.trim() || "Voice-notitie";
    const content = `<p>${transcriptInput.value.trim().replace(/\n/g, "<br>")}</p>`;

    saveBtn.disabled = true;
    saveBtn.textContent = "Opslaan...";
    try {
      await fetch("/notes", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: new URLSearchParams({ title, content, tags: "" }),
      });
      closePanel();
      window.location.href = "/notes";
    } catch (err) {
      statusEl.textContent = "Opslaan mislukt, probeer het opnieuw.";
      statusEl.classList.add("voice-recorder-status-error");
      saveBtn.disabled = false;
      saveBtn.textContent = "Opslaan als notitie";
    }
  });
});
