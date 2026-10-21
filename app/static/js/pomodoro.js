// Grote ronde, zwevende en verplaatsbare Pomodoro-timer (rechtsonder in beeld)
// i.p.v. een vast blok in de sidebar. De server bewaart alleen start-tijd +
// geplande duur, de countdown-ring wordt hier client-side berekend zodat een
// refresh niets verliest. De cirkel blijft verborgen totdat je op "Pomodoro"
// in het menu klikt, of automatisch zichtbaar als er al een sessie loopt
// (bv. na het wisselen van pagina).
document.addEventListener("DOMContentLoaded", () => {
  const float = document.getElementById("pomodoro-float");
  const menuBtn = document.getElementById("pomodoro-menu-btn");
  if (!float || !menuBtn) return; // menuBtn blijft altijd in de DOM (eventueel hidden)

  // Als allereerste koppelen: zelfs als een latere stap van de initialisatie mislukt, blijft
  // de menuknop de timer tonen/verbergen.
  menuBtn.addEventListener("click", () => {
    float.hidden = !float.hidden;
    menuBtn.classList.toggle("active", !float.hidden);
  });

  const RADIUS = 90;
  const CIRCUMFERENCE = 2 * Math.PI * RADIUS;
  const MIN_WORK_MINUTES = 5;
  const MAX_WORK_MINUTES = 180;

  const dragHandle = document.getElementById("pomodoro-drag-handle");
  const closeBtn = document.getElementById("pomodoro-close-btn");
  const ring = document.getElementById("pomodoro-ring-progress");
  const icon = document.getElementById("pomodoro-icon");
  const tagline = document.getElementById("pomodoro-tagline");
  const timeLabel = document.getElementById("pomodoro-time");
  const timeMin = timeLabel.querySelector(".pomodoro-time-min");
  const timeSec = timeLabel.querySelector(".pomodoro-time-sec");
  const resetBtn = document.getElementById("pomodoro-reset-btn");
  const skipBtn = document.getElementById("pomodoro-skip-btn");
  const ticksGroup = document.getElementById("pomodoro-ticks");
  const sideMenuBtn = document.getElementById("sidebar-pomodoro-btn");
  const timeTotalLabel = document.getElementById("pomodoro-time-total");
  const minusBtn = document.getElementById("pomodoro-minus-btn");
  const plusBtn = document.getElementById("pomodoro-plus-btn");
  const toggleBtn = document.getElementById("pomodoro-toggle-btn");
  const presetsContainer = document.getElementById("pomodoro-presets");
  const presetButtons = Array.from(presetsContainer.querySelectorAll(".pomodoro-preset"));
  const taskSelect = document.getElementById("pomodoro-task");

  const DEFAULT_TAGLINE = "Focus vandaag, bereik morgen";

  ring.style.strokeDasharray = String(CIRCUMFERENCE);
  ring.style.strokeDashoffset = "0";

  let currentSession = null;
  let intervalId = null;
  let workMinutes = 25;
  let breakMinutes = 5;
  let defaultWorkMinutes = 25;

  const pad = (n) => String(n).padStart(2, "0");
  function setTime(minutes, seconds) {
    timeMin.textContent = pad(minutes);
    timeSec.textContent = pad(seconds);
  }

  // 60 streepjes rond de timer; elk kwartier (12/3/6/9 uur) oranje en iets langer.
  function buildTicks() {
    const NS = "http://www.w3.org/2000/svg";
    for (let i = 0; i < 60; i++) {
      const major = i % 15 === 0;
      const angle = (i * 6 * Math.PI) / 180;
      const inner = major ? 72 : 76;
      const outer = 82;
      const line = document.createElementNS(NS, "line");
      line.setAttribute("x1", String(100 + inner * Math.sin(angle)));
      line.setAttribute("y1", String(100 - inner * Math.cos(angle)));
      line.setAttribute("x2", String(100 + outer * Math.sin(angle)));
      line.setAttribute("y2", String(100 - outer * Math.cos(angle)));
      line.setAttribute("class", major ? "pomodoro-tick pomodoro-tick-major" : "pomodoro-tick");
      ticksGroup.appendChild(line);
    }
  }
  buildTicks();

  restoreSavedMinutes();
  restoreFloatPosition();
  setupDragging();
  loadTasks();
  loadState();

  closeBtn.addEventListener("click", () => {
    float.hidden = true;
    menuBtn.classList.remove("active");
  });

  minusBtn.addEventListener("click", () => {
    if (currentSession) return;
    setWorkMinutes(workMinutes - 5);
  });

  plusBtn.addEventListener("click", () => {
    if (currentSession) return;
    setWorkMinutes(workMinutes + 5);
  });

  presetsContainer.addEventListener("click", (event) => {
    if (currentSession) return;
    const btn = event.target.closest(".pomodoro-preset");
    if (!btn) return;
    setWorkMinutes(parseInt(btn.dataset.minutes, 10));
  });

  toggleBtn.addEventListener("click", async () => {
    if (currentSession) {
      clearInterval(intervalId);
      await fetch(`/pomodoro/${currentSession.id}/cancel`, { method: "POST" });
      currentSession = null;
      showIdle();
    } else {
      saveMinutes();
      startPhase("work", workMinutes, taskSelect.value || null);
    }
  });

  // Resetten: een lopende sessie stoppen, anders terug naar de standaardduur.
  resetBtn.addEventListener("click", async () => {
    if (currentSession) {
      clearInterval(intervalId);
      await fetch(`/pomodoro/${currentSession.id}/cancel`, { method: "POST" });
      currentSession = null;
      showIdle();
    } else {
      setWorkMinutes(defaultWorkMinutes);
    }
  });

  // Overslaan: tijdens een sessie naar de volgende fase (focus -> pauze -> klaar); zonder
  // sessie het volgende voorgestelde tijdblok (25 -> 5 -> 15 min).
  skipBtn.addEventListener("click", async () => {
    if (currentSession) {
      clearInterval(intervalId);
      await handlePhaseComplete();
    } else {
      const options = presetButtons.map((b) => parseInt(b.dataset.minutes, 10));
      const next = options[(options.indexOf(workMinutes) + 1) % options.length];
      setWorkMinutes(next);
    }
  });

  // Het menu kan verborgen zijn (of de menuknop ontbreken in de nav): ook via de ◷-knop
  // naast de ☰ linksboven is de timer te openen.
  if (sideMenuBtn) sideMenuBtn.addEventListener("click", () => menuBtn.click());

  // ---- Pomodoro direct starten vanaf een taak (taaklijst/-bewerkpagina) ----
  document.addEventListener("click", (event) => {
    const btn = event.target.closest(".pomodoro-focus-btn");
    if (!btn) return;
    event.preventDefault();
    startFocusForTask(btn.dataset.taskId, btn.dataset.taskTitle);
  });

  function startFocusForTask(taskId, taskTitle) {
    float.hidden = false;
    menuBtn.classList.add("active");

    if (currentSession) {
      alert(`Er loopt al een pomodoro-sessie. Stop deze eerst om te focussen op "${taskTitle}".`);
      return;
    }

    if ([...taskSelect.options].some((o) => o.value === taskId)) {
      taskSelect.value = taskId;
    }
    saveMinutes();
    startPhase("work", workMinutes, taskId);
  }

  async function loadState() {
    const response = await fetch("/pomodoro/state");
    const data = await response.json();
    defaultWorkMinutes = data.default_work_minutes;
    if (!hasSavedMinutes()) {
      workMinutes = data.default_work_minutes;
      breakMinutes = data.default_break_minutes;
    }

    if (data.active) {
      currentSession = data.active;
      showActive();
      startTicking();
      float.hidden = false;
      menuBtn.classList.add("active");
    } else {
      showIdle();
    }
  }

  async function loadTasks() {
    try {
      const response = await fetch("/pomodoro/tasks");
      const tasks = await response.json();
      for (const task of tasks) {
        const option = document.createElement("option");
        option.value = String(task.id);
        option.textContent = task.title;
        taskSelect.appendChild(option);
      }
    } catch (err) {
      // Taken-selectie is optioneel; bij een fout blijft alleen "Geen taak" over.
    }
  }

  // Een mislukte servercall (verlopen sessie, serverfout) mag niet stil blijven: toon wat er
  // misging in plaats van dat de timer "gewoon niet start".
  async function callApi(url, options) {
    let response;
    try {
      response = await fetch(url, options);
    } catch (err) {
      alert("Pomodoro: de server is niet bereikbaar.");
      throw err;
    }
    if (response.redirected && response.url.includes("/login")) {
      alert("Pomodoro: je sessie is verlopen. Log opnieuw in.");
      throw new Error("sessie verlopen");
    }
    if (!response.ok) {
      let detail = response.statusText;
      try {
        detail = (await response.json()).detail || detail;
      } catch (err) {
        /* geen JSON in het antwoord */
      }
      alert(`Pomodoro: starten mislukt (${response.status}: ${detail}).`);
      throw new Error(`HTTP ${response.status}`);
    }
    return response;
  }

  async function startPhase(phase, minutes, taskId) {
    const body = new URLSearchParams({ phase, minutes: String(minutes) });
    if (taskId) body.set("task_id", taskId);

    const response = await callApi("/pomodoro/start", { method: "POST", body });
    currentSession = await response.json();
    showActive();
    startTicking();
  }

  function startTicking() {
    clearInterval(intervalId);
    tick();
    intervalId = setInterval(tick, 1000);
  }

  function tick() {
    const startedAtMs = new Date(currentSession.started_at + "Z").getTime();
    const totalSeconds = currentSession.planned_minutes * 60;
    const elapsed = (Date.now() - startedAtMs) / 1000;
    const remaining = Math.max(0, totalSeconds - elapsed);

    const fraction = totalSeconds > 0 ? elapsed / totalSeconds : 1;
    ring.style.strokeDashoffset = String(CIRCUMFERENCE * Math.min(1, fraction));

    const minutes = Math.floor(remaining / 60);
    const seconds = Math.floor(remaining % 60);
    setTime(minutes, seconds);

    if (remaining <= 0) {
      clearInterval(intervalId);
      handlePhaseComplete();
    }
  }

  async function handlePhaseComplete() {
    const finishedPhase = currentSession.phase;
    const taskId = currentSession.task_id;
    await fetch(`/pomodoro/${currentSession.id}/finish`, { method: "POST" });

    if (finishedPhase === "work") {
      await startPhase("break", breakMinutes, taskId);
    } else {
      currentSession = null;
      showIdle();
    }
  }

  function setWorkMinutes(minutes) {
    workMinutes = Math.max(MIN_WORK_MINUTES, Math.min(MAX_WORK_MINUTES, minutes));
    saveMinutes();
    renderIdleTime();
    highlightPreset();
  }

  function renderIdleTime() {
    setTime(workMinutes, 0);
    timeTotalLabel.textContent = `van ${workMinutes} min`;
  }

  function highlightPreset() {
    for (const btn of presetButtons) {
      btn.classList.toggle("active", parseInt(btn.dataset.minutes, 10) === workMinutes);
    }
  }

  function setControlsEnabled(enabled) {
    minusBtn.disabled = !enabled;
    plusBtn.disabled = !enabled;
    taskSelect.disabled = !enabled;
    for (const btn of presetButtons) btn.disabled = !enabled;
  }

  function showIdle() {
    float.classList.remove("pomodoro-active", "pomodoro-break");
    icon.textContent = "🍅";
    tagline.textContent = DEFAULT_TAGLINE;
    toggleBtn.textContent = "▶";
    toggleBtn.title = "Start";
    setControlsEnabled(true);
    ring.style.strokeDashoffset = "0"; // in rust: volle ring (de resterende tijd is nog 100%)
    renderIdleTime();
    highlightPreset();
  }

  function showActive() {
    float.classList.add("pomodoro-active");
    float.classList.toggle("pomodoro-break", currentSession.phase === "break");
    icon.textContent = currentSession.phase === "work" ? "🍅" : "☕";
    tagline.textContent = currentSession.phase === "work" ? "Focus loopt..." : "Pauze";
    timeTotalLabel.textContent = `van ${currentSession.planned_minutes} min`;
    toggleBtn.textContent = "⏹";
    toggleBtn.title = "Stop";
    setControlsEnabled(false);
  }

  function saveMinutes() {
    try {
      localStorage.setItem("pomodoro-work-minutes", String(workMinutes));
      localStorage.setItem("pomodoro-break-minutes", String(breakMinutes));
    } catch (err) {
      // localStorage kan geblokkeerd zijn; timer werkt dan gewoon met de defaults.
    }
  }

  function hasSavedMinutes() {
    try {
      return localStorage.getItem("pomodoro-work-minutes") !== null;
    } catch (err) {
      return false;
    }
  }

  function restoreSavedMinutes() {
    try {
      const savedWork = localStorage.getItem("pomodoro-work-minutes");
      const savedBreak = localStorage.getItem("pomodoro-break-minutes");
      if (savedWork) workMinutes = parseInt(savedWork, 10) || workMinutes;
      if (savedBreak) breakMinutes = parseInt(savedBreak, 10) || breakMinutes;
    } catch (err) {
      // Geen probleem, defaults blijven staan.
    }
  }

  // ---- Verplaatsbaarheid ----

  function setupDragging() {
    let dragging = false;
    let offsetX = 0;
    let offsetY = 0;

    dragHandle.addEventListener("mousedown", (event) => {
      dragging = true;
      const rect = float.getBoundingClientRect();
      offsetX = event.clientX - rect.left;
      offsetY = event.clientY - rect.top;
      float.style.right = "auto";
      float.style.bottom = "auto";
      float.style.left = `${rect.left}px`;
      float.style.top = `${rect.top}px`;
      event.preventDefault();
    });

    document.addEventListener("mousemove", (event) => {
      if (!dragging) return;
      const maxLeft = window.innerWidth - float.offsetWidth;
      const maxTop = window.innerHeight - float.offsetHeight;
      const left = Math.max(0, Math.min(maxLeft, event.clientX - offsetX));
      const top = Math.max(0, Math.min(maxTop, event.clientY - offsetY));
      float.style.left = `${left}px`;
      float.style.top = `${top}px`;
    });

    document.addEventListener("mouseup", () => {
      if (!dragging) return;
      dragging = false;
      saveFloatPosition();
    });
  }

  function saveFloatPosition() {
    try {
      localStorage.setItem("pomodoro-float-left", float.style.left);
      localStorage.setItem("pomodoro-float-top", float.style.top);
    } catch (err) {
      // Geen probleem, paneel start dan gewoon weer rechtsonder.
    }
  }

  function restoreFloatPosition() {
    try {
      const left = localStorage.getItem("pomodoro-float-left");
      const top = localStorage.getItem("pomodoro-float-top");
      if (left && top) {
        // Een positie uit een groter venster kan nu buiten beeld vallen: binnen het scherm houden,
        // anders lijkt de timer "niet te openen".
        const size = 304;
        const x = Math.max(0, Math.min(window.innerWidth - size, parseFloat(left) || 0));
        const y = Math.max(0, Math.min(window.innerHeight - size, parseFloat(top) || 0));
        float.style.left = `${x}px`;
        float.style.top = `${y}px`;
        float.style.right = "auto";
        float.style.bottom = "auto";
      }
    } catch (err) {
      // Geen probleem, paneel start dan gewoon weer rechtsonder.
    }
  }
});
