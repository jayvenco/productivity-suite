// Pomodoro-widget in de sidebar: server bewaart alleen start-tijd + geplande duur,
// de countdown-ring wordt hier client-side berekend zodat een refresh niets verliest.
document.addEventListener("DOMContentLoaded", () => {
  const widget = document.getElementById("pomodoro-widget");
  if (!widget) return;

  const RADIUS = 26;
  const CIRCUMFERENCE = 2 * Math.PI * RADIUS;

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
  loadTasks();
  loadState();

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

  async function loadState() {
    const response = await fetch("/pomodoro/state");
    const data = await response.json();
    workMinutesInput.value = workMinutesInput.value || data.default_work_minutes;
    breakMinutesInput.value = breakMinutesInput.value || data.default_break_minutes;

    if (data.active) {
      currentSession = data.active;
      showActive();
      startTicking();
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
    widget.classList.toggle("pomodoro-break", currentSession.phase === "break");
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
});
