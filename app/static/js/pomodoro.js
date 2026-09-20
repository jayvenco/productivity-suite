// Zwevend, verplaatsbaar Pomodoro-paneel (rechtsonder in beeld) i.p.v. een vast
// blok in de sidebar. De server bewaart alleen start-tijd + geplande duur, de
// countdown-ring wordt hier client-side berekend zodat een refresh niets verliest.
// Het paneel blijft verborgen totdat je op "Pomodoro" in het menu klikt, of
// automatisch zichtbaar als er al een sessie loopt (bv. na het wisselen van pagina).
document.addEventListener("DOMContentLoaded", () => {
  const float = document.getElementById("pomodoro-float");
  const menuBtn = document.getElementById("pomodoro-menu-btn");
  if (!float || !menuBtn) return;

  const RADIUS = 26;
  const CIRCUMFERENCE = 2 * Math.PI * RADIUS;

  const dragHandle = document.getElementById("pomodoro-drag-handle");
  const closeBtn = document.getElementById("pomodoro-close-btn");
  const ring = document.getElementById("pomodoro-ring-progress");
  const timeLabel = document.getElementById("pomodoro-time");
  const phaseLabel = document.getElementById("pomodoro-phase");
  const idleControls = document.getElementById("pomodoro-idle-controls");
  const activeControls = document.getElementById("pomodoro-active-controls");
  const taskSelect = document.getElementById("pomodoro-task");
  const workMinutesInput = document.getElementById("pomodoro-work-minutes");
  const breakMinutesInput = document.getElementById("pomodoro-break-minutes");
  const startBtn = document.getElementById("pomodoro-start-btn");
  const stopBtn = document.getElementById("pomodoro-stop-btn");

  ring.style.strokeDasharray = String(CIRCUMFERENCE);
  ring.style.strokeDashoffset = "0";

  let currentSession = null;
  let intervalId = null;

  restoreSavedMinutes();
  restoreFloatPosition();
  setupDragging();
  loadTasks();
  loadState();

  menuBtn.addEventListener("click", () => {
    float.hidden = !float.hidden;
    menuBtn.classList.toggle("active", !float.hidden);
  });

  closeBtn.addEventListener("click", () => {
    float.hidden = true;
    menuBtn.classList.remove("active");
  });

  startBtn.addEventListener("click", () => {
    const minutes = parseInt(workMinutesInput.value, 10) || 25;
    saveMinutes();
    startPhase("work", minutes, taskSelect.value || null);
  });

  stopBtn.addEventListener("click", async () => {
    if (!currentSession) return;
    clearInterval(intervalId);
    await fetch(`/pomodoro/${currentSession.id}/cancel`, { method: "POST" });
    currentSession = null;
    showIdle();
  });

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
    const minutes = parseInt(workMinutesInput.value, 10) || 25;
    saveMinutes();
    startPhase("work", minutes, taskId);
  }

  async function loadState() {
    const response = await fetch("/pomodoro/state");
    const data = await response.json();
    workMinutesInput.value = workMinutesInput.value || data.default_work_minutes;
    breakMinutesInput.value = breakMinutesInput.value || data.default_break_minutes;

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

  async function startPhase(phase, minutes, taskId) {
    const body = new URLSearchParams({ phase, minutes: String(minutes) });
    if (taskId) body.set("task_id", taskId);

    const response = await fetch("/pomodoro/start", { method: "POST", body });
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
    timeLabel.textContent = `${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;

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
      const breakMinutes = parseInt(breakMinutesInput.value, 10) || 5;
      await startPhase("break", breakMinutes, taskId);
    } else {
      currentSession = null;
      showIdle();
    }
  }

  function showIdle() {
    idleControls.hidden = false;
    activeControls.hidden = true;
    phaseLabel.textContent = "Pomodoro";
    ring.style.strokeDashoffset = "0";
    const minutes = parseInt(workMinutesInput.value, 10) || 25;
    timeLabel.textContent = `${String(minutes).padStart(2, "0")}:00`;
  }

  function showActive() {
    idleControls.hidden = true;
    activeControls.hidden = false;
    phaseLabel.textContent = currentSession.phase === "work" ? "Focus" : "Pauze";
    float.classList.toggle("pomodoro-break", currentSession.phase === "break");
  }

  function saveMinutes() {
    try {
      localStorage.setItem("pomodoro-work-minutes", workMinutesInput.value);
      localStorage.setItem("pomodoro-break-minutes", breakMinutesInput.value);
    } catch (err) {
      // localStorage kan geblokkeerd zijn; timer werkt dan gewoon met de defaults.
    }
  }

  function restoreSavedMinutes() {
    try {
      const savedWork = localStorage.getItem("pomodoro-work-minutes");
      const savedBreak = localStorage.getItem("pomodoro-break-minutes");
      if (savedWork) workMinutesInput.value = savedWork;
      if (savedBreak) breakMinutesInput.value = savedBreak;
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
        float.style.left = left;
        float.style.top = top;
        float.style.right = "auto";
        float.style.bottom = "auto";
      }
    } catch (err) {
      // Geen probleem, paneel start dan gewoon weer rechtsonder.
    }
  }
});
