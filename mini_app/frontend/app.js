const tg = window.Telegram?.WebApp;
const MAX_VISIBLE_DATES = 6;

if (tg) {
  tg.ready();
}

const state = {
  dates: [],
  durations: [],
  slots: [],
  selectedDate: null,
  selectedDuration: null,
  selectedSlot: null,
  datePage: 0,
};

const elements = {
  status: document.querySelector("#status"),
  dates: document.querySelector("#dates"),
  dateControls: document.querySelector("#dateControls"),
  durations: document.querySelector("#durations"),
  slots: document.querySelector("#slots"),
  summary: document.querySelector("#summary"),
  form: document.querySelector("#bookingForm"),
  submit: document.querySelector("#submitButton"),
  email: document.querySelector("#email"),
  description: document.querySelector("#description"),
  bookingView: document.querySelector("#bookingView"),
  requestsView: document.querySelector("#requestsView"),
  requests: document.querySelector("#requests"),
};

function initData() {
  return tg?.initData || "";
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      "X-Telegram-Init-Data": initData(),
      ...(options.headers || {}),
    },
  });

  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.detail || "Запрос не выполнен.");
  }
  return data;
}

function setStatus(message, type = "") {
  elements.status.textContent = message;
  elements.status.className = `status ${type}`.trim();
  elements.status.classList.toggle("hidden", !message);
}

function formatDate(value) {
  return new Date(`${value}T00:00:00`).toLocaleDateString("ru-RU", {
    day: "2-digit",
    month: "short",
    weekday: "short",
  });
}

function renderDates() {
  elements.dates.innerHTML = "";
  elements.dateControls.innerHTML = "";

  const startIndex = state.datePage * MAX_VISIBLE_DATES;
  const pageDates = state.dates.slice(startIndex, startIndex + MAX_VISIBLE_DATES);

  pageDates.forEach((date) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = `chip ${state.selectedDate === date ? "active" : ""}`;
    button.textContent = formatDate(date);
    button.addEventListener("click", () => {
      state.selectedDate = date;
      state.selectedSlot = null;
      renderDates();
      loadSlots();
      updateSummary();
    });
    elements.dates.append(button);
  });

  const pageCount = Math.ceil(state.dates.length / MAX_VISIBLE_DATES);
  if (pageCount <= 1) {
    return;
  }

  const prevButton = document.createElement("button");
  prevButton.type = "button";
  prevButton.className = "date-nav-button";
  prevButton.textContent = "Назад";
  prevButton.disabled = state.datePage === 0;
  prevButton.addEventListener("click", () => {
    state.datePage -= 1;
    renderDates();
  });

  const nextButton = document.createElement("button");
  nextButton.type = "button";
  nextButton.className = "date-nav-button";
  nextButton.textContent = "Дальше";
  nextButton.disabled = state.datePage >= pageCount - 1;
  nextButton.addEventListener("click", () => {
    state.datePage += 1;
    renderDates();
  });

  elements.dateControls.append(prevButton, nextButton);
}

function renderDurations() {
  elements.durations.innerHTML = "";
  state.durations.forEach((duration) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = `chip ${state.selectedDuration === duration ? "active" : ""}`;
    button.textContent = `${duration} мин`;
    button.addEventListener("click", () => {
      state.selectedDuration = duration;
      state.selectedSlot = null;
      renderDurations();
      loadSlots();
      updateSummary();
    });
    elements.durations.append(button);
  });
}

function renderSlots() {
  elements.slots.innerHTML = "";
  if (!state.selectedDate || !state.selectedDuration) {
    elements.slots.className = "slot-grid muted-text";
    elements.slots.textContent = "Выберите дату и длительность.";
    return;
  }
  if (!state.slots.length) {
    elements.slots.className = "slot-grid muted-text";
    elements.slots.textContent = "Свободных слотов нет.";
    return;
  }

  elements.slots.className = "slot-grid";
  state.slots.forEach((slot) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = `slot-button ${state.selectedSlot?.start === slot.start ? "active" : ""}`;
    button.textContent = slot.start;
    button.addEventListener("click", () => {
      state.selectedSlot = slot;
      renderSlots();
      updateSummary();
    });
    elements.slots.append(button);
  });
}

function updateSummary() {
  if (!state.selectedDate || !state.selectedDuration || !state.selectedSlot) {
    elements.summary.textContent = "Заполните дату, длительность и время.";
    elements.summary.classList.add("muted-text");
    elements.submit.disabled = true;
    return;
  }

  elements.summary.classList.remove("muted-text");
  elements.summary.textContent = `Дата: ${state.selectedDate}, время: ${state.selectedSlot.start}, длительность: ${state.selectedDuration} минут.`;
  elements.submit.disabled = false;
}

async function loadInitialData() {
  setStatus("");
  const [datesData, durationsData] = await Promise.all([
    api("/api/booking/dates"),
    api("/api/booking/durations"),
  ]);
  state.dates = datesData.dates;
  state.durations = durationsData.durations;
  state.selectedDate = state.dates[0] || null;
  state.selectedDuration = state.durations[0] || null;
  state.datePage = 0;
  renderDates();
  renderDurations();
  await loadSlots();
  updateSummary();
}

async function loadSlots() {
  if (!state.selectedDate || !state.selectedDuration) {
    renderSlots();
    return;
  }
  const data = await api(
    `/api/booking/slots?target_date=${state.selectedDate}&duration=${state.selectedDuration}`,
  );
  state.slots = data.slots;
  renderSlots();
}

async function submitBooking(event) {
  event.preventDefault();
  if (!state.selectedDate || !state.selectedDuration || !state.selectedSlot) {
    return;
  }

  elements.submit.disabled = true;
  try {
    await api("/api/booking/requests", {
      method: "POST",
      body: JSON.stringify({
        date: state.selectedDate,
        time: state.selectedSlot.start,
        duration_minutes: state.selectedDuration,
        email: elements.email.value,
        description: elements.description.value,
      }),
    });
    setStatus("Заявка отправлена на согласование.", "success");
    elements.form.reset();
    await loadRequests();
    tg?.HapticFeedback?.notificationOccurred("success");
  } catch (error) {
    setStatus(error.message, "error");
    tg?.HapticFeedback?.notificationOccurred("error");
  } finally {
    updateSummary();
  }
}

async function loadRequests() {
  const data = await api("/api/booking/my-requests");
  elements.requests.innerHTML = "";
  if (!data.requests.length) {
    elements.requests.innerHTML = '<p class="muted-text">Заявок пока нет.</p>';
    return;
  }

  data.requests.forEach((request) => {
    const card = document.createElement("article");
    card.className = "request-card";
    card.innerHTML = `
      <strong>${request.date} ${request.time}</strong>
      <span class="request-meta">${request.duration_minutes} минут · ${request.status_label}</span>
      <span>${request.description}</span>
      <span class="request-meta">${request.email}</span>
    `;
    elements.requests.append(card);
  });
}

function switchView(view) {
  document.querySelectorAll(".tab").forEach((tab) => {
    tab.classList.toggle("active", tab.dataset.view === view);
  });
  elements.bookingView.classList.toggle("hidden", view !== "booking");
  elements.requestsView.classList.toggle("hidden", view !== "requests");
  if (view === "requests") {
    loadRequests().catch((error) => setStatus(error.message, "error"));
  }
}

document.querySelectorAll(".tab").forEach((tab) => {
  tab.addEventListener("click", () => switchView(tab.dataset.view));
});
document.querySelector("#reloadButton").addEventListener("click", () => {
  loadInitialData().catch((error) => setStatus(error.message, "error"));
});
document.querySelector("#refreshRequestsButton").addEventListener("click", () => {
  loadRequests().catch((error) => setStatus(error.message, "error"));
});
elements.form.addEventListener("submit", submitBooking);

loadInitialData().catch((error) => setStatus(error.message, "error"));
