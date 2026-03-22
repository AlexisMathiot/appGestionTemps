(function () {
  "use strict";

  const STORAGE_KEYS = {
    entryId: "timer_entry_id",
    startTime: "timer_start_time",
    categoryName: "timer_category_name",
    categoryEmoji: "timer_category_emoji",
    categoryColor: "timer_category_color",
    paused: "timer_paused",
    pausedAt: "timer_paused_at",
    totalPausedMs: "timer_total_paused_ms",
  };

  let intervalId = null;

  function formatTime(totalSeconds) {
    const h = Math.floor(totalSeconds / 3600);
    const m = Math.floor((totalSeconds % 3600) / 60);
    const s = totalSeconds % 60;
    return (
      String(h).padStart(2, "0") +
      ":" +
      String(m).padStart(2, "0") +
      ":" +
      String(s).padStart(2, "0")
    );
  }

  function updateDisplay() {
    const startTime = localStorage.getItem(STORAGE_KEYS.startTime);
    if (!startTime) return;

    var elapsed;
    var isPaused = localStorage.getItem(STORAGE_KEYS.paused) === "true";
    var totalPausedMs = parseInt(localStorage.getItem(STORAGE_KEYS.totalPausedMs) || "0", 10);

    if (isPaused) {
      var pausedAt = parseInt(localStorage.getItem(STORAGE_KEYS.pausedAt) || "0", 10);
      elapsed = Math.floor((pausedAt - parseInt(startTime, 10) - totalPausedMs) / 1000);
    } else {
      elapsed = Math.floor((Date.now() - parseInt(startTime, 10) - totalPausedMs) / 1000);
    }

    const timeEl = document.getElementById("timer-time");
    if (timeEl) {
      timeEl.textContent = formatTime(Math.max(0, elapsed));
    }
  }

  function showTimerHeader() {
    const container = document.getElementById("timer-container");
    if (!container) return;

    const name = localStorage.getItem(STORAGE_KEYS.categoryName) || "";
    const emoji = localStorage.getItem(STORAGE_KEYS.categoryEmoji) || "";
    const color = localStorage.getItem(STORAGE_KEYS.categoryColor) || "#6B7280";
    const isPaused = localStorage.getItem(STORAGE_KEYS.paused) === "true";

    container.innerHTML = "";

    var header = document.createElement("div");
    header.id = "timer-header";
    header.className = "sticky top-0 z-50 w-full py-4 px-4 text-center shadow-lg transition-opacity duration-300";
    if (isPaused) {
      header.className += " opacity-60";
    }
    header.style.backgroundColor = color;

    var wrapper = document.createElement("div");
    wrapper.className = "text-white";

    var nameRow = document.createElement("div");
    nameRow.className = "text-2xl mb-1";
    nameRow.textContent = emoji + " " + name;

    var timeRow = document.createElement("div");
    timeRow.id = "timer-time";
    timeRow.className = "font-timer text-5xl font-bold tracking-wider";
    timeRow.textContent = "00:00:00";

    wrapper.appendChild(nameRow);
    wrapper.appendChild(timeRow);

    if (isPaused) {
      var badge = document.createElement("div");
      badge.className = "text-sm opacity-80 mt-1";
      badge.textContent = "En pause";
      wrapper.appendChild(badge);
    }

    var btnRow = document.createElement("div");
    btnRow.className = "mt-2 flex justify-center gap-2";

    var pauseBtn = document.createElement("button");
    pauseBtn.className = "btn btn-sm btn-ghost text-white border-white/30";
    if (isPaused) {
      pauseBtn.textContent = "Reprendre";
      pauseBtn.setAttribute("hx-post", "/api/timer/resume");
    } else {
      pauseBtn.textContent = "Pause";
      pauseBtn.setAttribute("hx-post", "/api/timer/pause");
    }
    pauseBtn.setAttribute("hx-target", "#timer-container");

    var stopBtn = document.createElement("button");
    stopBtn.className = "btn btn-sm btn-disabled opacity-50";
    stopBtn.disabled = true;
    stopBtn.textContent = "Stop";

    btnRow.appendChild(pauseBtn);
    btnRow.appendChild(stopBtn);
    wrapper.appendChild(btnRow);
    header.appendChild(wrapper);
    container.appendChild(header);

    // Process HTMX attributes on dynamically created elements
    if (typeof htmx !== "undefined") {
      htmx.process(pauseBtn);
    }

    updateDisplay();
  }

  function startTimer(data) {
    // Save to localStorage
    localStorage.setItem(STORAGE_KEYS.entryId, data.entryId);
    localStorage.setItem(STORAGE_KEYS.startTime, String(data.startTime));
    localStorage.setItem(STORAGE_KEYS.categoryName, data.categoryName);
    localStorage.setItem(STORAGE_KEYS.categoryEmoji, data.categoryEmoji);
    localStorage.setItem(STORAGE_KEYS.categoryColor, data.categoryColor);

    // Pause state (with defaults for backward compatibility)
    var isPaused = data.isPaused || false;
    var pausedSeconds = data.pausedSeconds || 0;
    var pausedAt = data.pausedAt || null;

    localStorage.setItem(STORAGE_KEYS.paused, isPaused ? "true" : "false");

    if (isPaused && pausedAt) {
      localStorage.setItem(STORAGE_KEYS.pausedAt, String(new Date(pausedAt).getTime()));
    } else {
      localStorage.removeItem(STORAGE_KEYS.pausedAt);
    }

    // Convert server paused_seconds to totalPausedMs
    // If already paused, we don't add current pause duration (it's tracked via pausedAt)
    localStorage.setItem(STORAGE_KEYS.totalPausedMs, String(pausedSeconds * 1000));

    // Show header and start interval
    showTimerHeader();
    if (intervalId) clearInterval(intervalId);
    intervalId = setInterval(updateDisplay, 1000);

    // Vibration on mobile
    if (navigator.vibrate) {
      navigator.vibrate(50);
    }
  }

  function pauseTimer() {
    localStorage.setItem(STORAGE_KEYS.paused, "true");
    localStorage.setItem(STORAGE_KEYS.pausedAt, String(Date.now()));
    showTimerHeader();
  }

  function resumeTimer() {
    var pausedAt = parseInt(localStorage.getItem(STORAGE_KEYS.pausedAt) || "0", 10);
    var totalPausedMs = parseInt(localStorage.getItem(STORAGE_KEYS.totalPausedMs) || "0", 10);
    if (pausedAt > 0) {
      totalPausedMs += Date.now() - pausedAt;
    }
    localStorage.setItem(STORAGE_KEYS.totalPausedMs, String(totalPausedMs));
    localStorage.setItem(STORAGE_KEYS.paused, "false");
    localStorage.removeItem(STORAGE_KEYS.pausedAt);
    showTimerHeader();
  }

  function stopTimerDisplay() {
    Object.values(STORAGE_KEYS).forEach(function (key) {
      localStorage.removeItem(key);
    });
    if (intervalId) {
      clearInterval(intervalId);
      intervalId = null;
    }
    var container = document.getElementById("timer-container");
    if (container) {
      container.innerHTML = "";
    }
  }

  function restoreTimer() {
    var startTime = localStorage.getItem(STORAGE_KEYS.startTime);
    if (!startTime) return;

    var entryId = localStorage.getItem(STORAGE_KEYS.entryId);
    if (!entryId) return;

    showTimerHeader();
    if (intervalId) clearInterval(intervalId);
    intervalId = setInterval(updateDisplay, 1000);
  }

  // Page Visibility API: recalculate on tab focus
  document.addEventListener("visibilitychange", function () {
    if (!document.hidden && localStorage.getItem(STORAGE_KEYS.startTime)) {
      // Only recalculate if not paused (paused timers don't change)
      updateDisplay();
    }
  });

  // Restore timer on page load
  document.addEventListener("DOMContentLoaded", restoreTimer);

  // Also restore after HTMX swaps (navigation)
  document.addEventListener("htmx:afterSettle", function () {
    if (localStorage.getItem(STORAGE_KEYS.startTime)) {
      restoreTimer();
    }
  });

  // Expose globally
  window.timerApp = {
    startTimer: startTimer,
    stopTimerDisplay: stopTimerDisplay,
    restoreTimer: restoreTimer,
    formatTime: formatTime,
    pauseTimer: pauseTimer,
    resumeTimer: resumeTimer,
  };
})();
