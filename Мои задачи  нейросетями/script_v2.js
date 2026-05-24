const storeKey = "finance-calendar-tasks-v1";
const dayNames = ["Вс", "Пн", "Вт", "Ср", "Чт", "Пт", "Сб"];
const longDayNames = ["Воскресенье", "Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота"];
const typeNames = {
  payments: "Платежи",
  reports: "Отчеты",
  taxes: "Налоги",
  calls: "Звонки",
  meetings: "Встречи",
};
const baseCounterparties = [
  "Уралсувенир",
  "Уралфинанст",
  "Деловой персонал",
];

const state = {
  today: startOfDay(new Date()),
  rangeStart: startOfWeek(new Date()),
  monthDate: startOfMonth(new Date()),
  tasks: loadTasks(),
};

const els = {
  board: document.querySelector("#board"),
  miniCalendar: document.querySelector("#miniCalendar"),
  monthTitle: document.querySelector("#monthTitle"),
  boardTitle: document.querySelector("#boardTitle"),
  progressText: document.querySelector("#progressText"),
  doneCount: document.querySelector("#doneCount"),
  openCount: document.querySelector("#openCount"),
  todayCount: document.querySelector("#todayCount"),
  taskForm: document.querySelector("#taskForm"),
  taskTitle: document.querySelector("#taskTitle"),
  taskCounterparty: document.querySelector("#taskCounterparty"),
  taskDate: document.querySelector("#taskDate"),
  taskTime: document.querySelector("#taskTime"),
  taskType: document.querySelector("#taskType"),
  counterpartyCount: document.querySelector("#counterpartyCount"),
  counterpartyTaskCount: document.querySelector("#counterpartyTaskCount"),
  topCounterparty: document.querySelector("#topCounterparty"),
  analyticsPeriod: document.querySelector("#analyticsPeriod"),
  analyticsCounterparty: document.querySelector("#analyticsCounterparty"),
  counterpartyList: document.querySelector("#counterpartyList"),
  counterpartyTaskTable: document.querySelector("#counterpartyTaskTable"),
  counterpartiesList: document.querySelector("#counterpartiesList"),
  dialog: document.querySelector("#taskDialog"),
  editForm: document.querySelector("#editForm"),
  editId: document.querySelector("#editId"),
  editTitle: document.querySelector("#editTitle"),
  editCounterparty: document.querySelector("#editCounterparty"),
  editDate: document.querySelector("#editDate"),
  editTime: document.querySelector("#editTime"),
  editType: document.querySelector("#editType"),
  editNote: document.querySelector("#editNote"),
  editDone: document.querySelector("#editDone"),
  deleteTask: document.querySelector("#deleteTask"),
};

seedTasksIfEmpty();
setDefaultInputs();
bindEvents();
render();

function bindEvents() {
  document.querySelector("#prevMonth").addEventListener("click", () => {
    state.monthDate = addMonths(state.monthDate, -1);
    renderMiniCalendar();
  });

  document.querySelector("#nextMonth").addEventListener("click", () => {
    state.monthDate = addMonths(state.monthDate, 1);
    renderMiniCalendar();
  });

  document.querySelector("#prevRange").addEventListener("click", () => {
    state.rangeStart = addDays(state.rangeStart, -14);
    state.monthDate = startOfMonth(state.rangeStart);
    render();
  });

  document.querySelector("#nextRange").addEventListener("click", () => {
    state.rangeStart = addDays(state.rangeStart, 14);
    state.monthDate = startOfMonth(state.rangeStart);
    render();
  });

  document.querySelector("#todayButton").addEventListener("click", () => {
    state.rangeStart = startOfWeek(new Date());
    state.monthDate = startOfMonth(new Date());
    setDefaultInputs();
    render();
  });

  els.analyticsCounterparty.addEventListener("change", () => {
    renderCounterpartyStats();
  });

  els.taskForm.addEventListener("submit", (event) => {
    event.preventDefault();
    const taskInfo = parseTaskInput(els.taskTitle.value, els.taskCounterparty.value);
    state.tasks.push({
      id: crypto.randomUUID(),
      title: taskInfo.title,
      counterparty: taskInfo.counterparty,
      date: els.taskDate.value,
      time: els.taskTime.value,
      type: els.taskType.value,
      note: "",
      done: false,
    });
    els.taskTitle.value = "";
    els.taskCounterparty.value = "";
    persistAndRender();
  });

  els.editForm.addEventListener("submit", (event) => {
    event.preventDefault();
    if (event.submitter?.value === "cancel") {
      els.dialog.close();
      return;
    }
    const task = state.tasks.find((item) => item.id === els.editId.value);
    if (!task) return;
    const taskInfo = parseTaskInput(els.editTitle.value, els.editCounterparty.value);
    task.title = taskInfo.title;
    task.counterparty = taskInfo.counterparty;
    task.date = els.editDate.value;
    task.time = els.editTime.value;
    task.type = els.editType.value;
    task.note = els.editNote.value.trim();
    task.done = els.editDone.checked;
    els.dialog.close();
    persistAndRender();
  });

  els.deleteTask.addEventListener("click", () => {
    state.tasks = state.tasks.filter((item) => item.id !== els.editId.value);
    els.dialog.close();
    persistAndRender();
  });
}

function render() {
  renderCounterpartyOptions();
  renderAnalyticsCounterpartyOptions();
  renderBoard();
  renderMiniCalendar();
  renderStats();
  renderCounterpartyStats();
}

function renderBoard() {
  const days = Array.from({ length: 14 }, (_, index) => addDays(state.rangeStart, index));
  const lastDay = days[days.length - 1];
  els.boardTitle.textContent = `${formatDateShort(days[0])} - ${formatDateShort(lastDay)}`;
  els.board.innerHTML = "";

  days.forEach((date) => {
    const iso = toISODate(date);
    const dayTasks = state.tasks
      .filter((task) => task.date === iso)
      .sort((a, b) => a.time.localeCompare(b.time));

    const column = document.createElement("section");
    column.className = `day-column ${isWeekend(date) ? "weekend" : ""}`;
    column.dataset.date = iso;
    column.innerHTML = `
      <div class="day-head">
        <div>
          <strong>${longDayNames[date.getDay()]}</strong>
          <span>${formatDateShort(date)}</span>
        </div>
        <div class="day-total">${dayTasks.length} задач</div>
      </div>
      <div class="tasks"></div>
    `;

    const taskArea = column.querySelector(".tasks");
    if (dayTasks.length === 0) {
      taskArea.innerHTML = `<div class="empty">Перетащите задачу сюда</div>`;
    } else {
      dayTasks.forEach((task) => taskArea.appendChild(createTaskCard(task)));
    }

    column.addEventListener("dragover", (event) => {
      event.preventDefault();
      column.classList.add("drag-over");
    });
    column.addEventListener("dragleave", () => column.classList.remove("drag-over"));
    column.addEventListener("drop", (event) => {
      event.preventDefault();
      column.classList.remove("drag-over");
      const id = event.dataTransfer.getData("text/plain");
      const task = state.tasks.find((item) => item.id === id);
      if (task) {
        task.date = iso;
        persistAndRender();
      }
    });

    els.board.appendChild(column);
  });
}

function createTaskCard(task) {
  const taskInfo = getTaskInfo(task);
  const card = document.createElement("article");
  card.className = `task-card ${task.type} ${task.done ? "done" : ""}`;
  card.draggable = true;
  card.dataset.id = task.id;
  card.innerHTML = `
    <div class="task-meta">
      <span class="task-time">${task.time}</span>
      <span class="task-time">${typeNames[task.type]}</span>
    </div>
    ${taskInfo.counterparty ? `<div class="task-counterparty">${escapeHTML(taskInfo.counterparty)}</div>` : ""}
    <div class="task-title">${escapeHTML(taskInfo.title)}</div>
    ${task.note ? `<div class="task-note">${escapeHTML(task.note)}</div>` : ""}
    <div class="task-actions">
      <button class="small-button done-toggle" type="button">${task.done ? "Вернуть" : "Готово"}</button>
      <button class="small-button edit-task" type="button">Править</button>
    </div>
  `;

  card.addEventListener("dragstart", (event) => {
    event.dataTransfer.setData("text/plain", task.id);
  });

  card.querySelector(".done-toggle").addEventListener("click", () => {
    task.done = !task.done;
    persistAndRender();
  });

  card.querySelector(".edit-task").addEventListener("click", () => openEditDialog(task));
  card.addEventListener("dblclick", () => openEditDialog(task));
  return card;
}

function renderMiniCalendar() {
  const title = new Intl.DateTimeFormat("ru-RU", { month: "long", year: "numeric" }).format(state.monthDate);
  els.monthTitle.textContent = title.charAt(0).toUpperCase() + title.slice(1);
  els.miniCalendar.innerHTML = "";

  const first = startOfMonth(state.monthDate);
  const offset = (first.getDay() + 6) % 7;
  const gridStart = addDays(first, -offset);
  const activeDates = new Set(state.tasks.map((task) => task.date));
  const rangeEnd = addDays(state.rangeStart, 13);

  for (let index = 0; index < 42; index += 1) {
    const date = addDays(gridStart, index);
    const iso = toISODate(date);
    const button = document.createElement("button");
    button.type = "button";
    button.className = "mini-day";
    button.textContent = date.getDate();
    if (date.getMonth() !== state.monthDate.getMonth()) button.classList.add("outside");
    if (activeDates.has(iso)) button.classList.add("has-tasks");
    if (date >= state.rangeStart && date <= rangeEnd) button.classList.add("active");
    button.addEventListener("click", () => {
      state.rangeStart = startOfWeek(date);
      state.monthDate = startOfMonth(date);
      els.taskDate.value = iso;
      render();
    });
    els.miniCalendar.appendChild(button);
  }
}

function renderStats() {
  const rangeEnd = addDays(state.rangeStart, 13);
  const rangeTasks = state.tasks.filter((task) => {
    const date = parseISODate(task.date);
    return date >= state.rangeStart && date <= rangeEnd;
  });
  const done = rangeTasks.filter((task) => task.done).length;
  const open = rangeTasks.length - done;
  const percent = rangeTasks.length ? Math.round((done / rangeTasks.length) * 100) : 0;

  els.progressText.textContent = `${percent}%`;
  els.doneCount.textContent = done;
  els.openCount.textContent = open;
  els.todayCount.textContent = state.tasks.filter((task) => task.date === toISODate(new Date())).length;
}

function renderCounterpartyStats() {
  const monthTasks = getMonthTasks();
  const targetCounterparties = new Set(baseCounterparties);
  const selectedCounterparty = els.analyticsCounterparty.value;
  const allCounterpartyTasks = monthTasks.filter((task) => {
    const taskInfo = getTaskInfo(task);
    if (!targetCounterparties.has(taskInfo.counterparty)) return false;
    return !selectedCounterparty || taskInfo.counterparty === selectedCounterparty;
  });
  const rangeTasks = allCounterpartyTasks;
  const stats = new Map();

  rangeTasks.forEach((task) => {
    const taskInfo = getTaskInfo(task);
    const current = stats.get(taskInfo.counterparty) || { total: 0, meetings: 0, done: 0 };
    current.total += 1;
    if (task.type === "meetings") current.meetings += 1;
    if (task.done) current.done += 1;
    stats.set(taskInfo.counterparty, current);
  });

  const rows = [...stats.entries()].sort((a, b) => b[1].total - a[1].total || a[0].localeCompare(b[0], "ru"));
  const top = rows[0];
  els.analyticsPeriod.textContent = getMonthTitle(state.monthDate);

  els.counterpartyCount.textContent = rows.length;
  els.counterpartyTaskCount.textContent = rangeTasks.length;
  els.topCounterparty.textContent = top ? `${top[0]} (${top[1].total})` : "-";

  if (!rows.length) {
    els.counterpartyList.innerHTML = `<div class="empty compact">Данных нет</div>`;
  } else {
    els.counterpartyList.innerHTML = rows
      .map(([name, item]) => {
        const open = item.total - item.done;
        return `
          <div class="counterparty-row">
            <strong>${escapeHTML(name)}</strong>
            <span>${item.total} задач, ${item.meetings} встреч, ${item.done} выполнено, ${open} в работе</span>
          </div>
        `;
      })
      .join("");
  }

  if (!allCounterpartyTasks.length) {
    els.counterpartyTaskTable.innerHTML = `<div class="empty compact">Данных нет</div>`;
    return;
  }

  const sortedTasks = [...allCounterpartyTasks].sort((a, b) => {
    const firstCounterparty = getTaskInfo(a).counterparty;
    const secondCounterparty = getTaskInfo(b).counterparty;
    const byCounterparty = firstCounterparty.localeCompare(secondCounterparty, "ru");
    if (byCounterparty) return byCounterparty;
    return `${a.date} ${a.time}`.localeCompare(`${b.date} ${b.time}`);
  });

  els.counterpartyTaskTable.innerHTML = `
    <table>
      <thead>
        <tr>
          <th>Организация</th>
          <th>Дата</th>
          <th>Задача</th>
          <th>Статус</th>
        </tr>
      </thead>
      <tbody>
        ${sortedTasks
          .map(
            (task) => {
              const taskInfo = getTaskInfo(task);
              return `
                <tr>
                  <td>${escapeHTML(taskInfo.counterparty)}</td>
                  <td>${formatDateShort(parseISODate(task.date))}</td>
                  <td>${escapeHTML(taskInfo.title)}</td>
                  <td>${task.done ? "Выполнено" : "В работе"}</td>
                </tr>
              `;
            },
          )
          .join("")}
      </tbody>
    </table>
  `;
}

function openEditDialog(task) {
  const taskInfo = getTaskInfo(task);
  els.editId.value = task.id;
  els.editTitle.value = taskInfo.title;
  els.editCounterparty.value = taskInfo.counterparty || "";
  els.editDate.value = task.date;
  els.editTime.value = task.time;
  els.editType.value = task.type;
  els.editNote.value = task.note || "";
  els.editDone.checked = task.done;
  els.dialog.showModal();
}

function persistAndRender() {
  localStorage.setItem(storeKey, JSON.stringify(state.tasks));
  render();
}

function loadTasks() {
  try {
    return JSON.parse(localStorage.getItem(storeKey)) || [];
  } catch {
    return [];
  }
}

function seedTasksIfEmpty() {
  if (state.tasks.length) return;
  const today = toISODate(state.today);
  const tomorrow = toISODate(addDays(state.today, 1));
  state.tasks = [
    {
      id: crypto.randomUUID(),
      title: "Проверить входящие платежи",
      counterparty: "Уралсувенир",
      date: today,
      time: "09:30",
      type: "payments",
      note: "Банк, касса, сверка с реестром",
      done: false,
    },
    {
      id: crypto.randomUUID(),
      title: "Подготовить отчет по ДДС",
      counterparty: "Уралфинанст",
      date: today,
      time: "12:00",
      type: "reports",
      note: "Факт, план, отклонения",
      done: false,
    },
    {
      id: crypto.randomUUID(),
      title: "Уточнить счет и закрывающие документы",
      counterparty: "Деловой персонал",
      date: tomorrow,
      time: "15:30",
      type: "calls",
      note: "",
      done: false,
    },
  ];
  localStorage.setItem(storeKey, JSON.stringify(state.tasks));
}

function setDefaultInputs() {
  els.taskDate.value = toISODate(new Date());
  els.taskTime.value = "09:00";
}

function getRangeTasks() {
  const rangeEnd = addDays(state.rangeStart, 13);
  return state.tasks.filter((task) => {
    const date = parseISODate(task.date);
    return date >= state.rangeStart && date <= rangeEnd;
  });
}

function getMonthTasks() {
  const monthStart = startOfMonth(state.monthDate);
  const nextMonthStart = addMonths(monthStart, 1);
  return state.tasks.filter((task) => {
    const date = parseISODate(task.date);
    return date >= monthStart && date < nextMonthStart;
  });
}

function getCounterparties() {
  return [...baseCounterparties].sort((a, b) => a.localeCompare(b, "ru"));
}

function renderCounterpartyOptions() {
  els.counterpartiesList.innerHTML = getCounterparties()
    .map((name) => `<option value="${escapeHTML(name)}"></option>`)
    .join("");
}

function renderAnalyticsCounterpartyOptions() {
  const currentValue = els.analyticsCounterparty.value;
  els.analyticsCounterparty.innerHTML = `
    <option value="">Все контрагенты</option>
    ${getCounterparties().map((name) => `<option value="${escapeHTML(name)}">${escapeHTML(name)}</option>`).join("")}
  `;
  if (getCounterparties().includes(currentValue)) {
    els.analyticsCounterparty.value = currentValue;
  }
}

function normalizeCounterparty(value) {
  return value.trim().replace(/\s+/g, " ");
}

function parseTaskInput(titleValue, counterpartyValue) {
  const explicitCounterparty = normalizeCounterparty(counterpartyValue);
  const parsed = parseCounterpartyFromTitle(titleValue);
  return {
    title: explicitCounterparty ? stripCounterpartyFromTitle(titleValue, explicitCounterparty) : parsed.title,
    counterparty: explicitCounterparty || parsed.counterparty,
  };
}

function getTaskInfo(task) {
  const parsed = parseCounterpartyFromTitle(task.title);
  return {
    title: task.counterparty ? stripCounterpartyFromTitle(task.title, task.counterparty) : parsed.title,
    counterparty: task.counterparty || parsed.counterparty,
  };
}

function parseCounterpartyFromTitle(titleValue) {
  const title = titleValue.trim();
  const counterparty = baseCounterparties.find((name) => title.toLowerCase().startsWith(name.toLowerCase()));
  if (!counterparty) return { title, counterparty: "" };
  const cleanedTitle = title
    .slice(counterparty.length)
    .replace(/^[\s:;,.–—-]+/, "")
    .trim();
  return {
    title: cleanedTitle || title,
    counterparty,
  };
}

function stripCounterpartyFromTitle(titleValue, counterparty) {
  const title = titleValue.trim();
  if (!title.toLowerCase().startsWith(counterparty.toLowerCase())) return title;
  return title
    .slice(counterparty.length)
    .replace(/^[\s:;,.–—-]+/, "")
    .trim() || title;
}

function getMonthTitle(date) {
  const title = new Intl.DateTimeFormat("ru-RU", { month: "long", year: "numeric" }).format(date);
  return title.charAt(0).toUpperCase() + title.slice(1);
}

function startOfDay(date) {
  const result = new Date(date);
  result.setHours(0, 0, 0, 0);
  return result;
}

function startOfMonth(date) {
  return new Date(date.getFullYear(), date.getMonth(), 1);
}

function startOfWeek(date) {
  const day = startOfDay(date);
  const offset = (day.getDay() + 6) % 7;
  return addDays(day, -offset);
}

function isWeekend(date) {
  return date.getDay() === 0 || date.getDay() === 6;
}

function addDays(date, days) {
  const result = new Date(date);
  result.setDate(result.getDate() + days);
  return startOfDay(result);
}

function addMonths(date, months) {
  return new Date(date.getFullYear(), date.getMonth() + months, 1);
}

function toISODate(date) {
  const local = new Date(date);
  local.setMinutes(local.getMinutes() - local.getTimezoneOffset());
  return local.toISOString().slice(0, 10);
}

function parseISODate(value) {
  const [year, month, day] = value.split("-").map(Number);
  return new Date(year, month - 1, day);
}

function formatDateShort(date) {
  return new Intl.DateTimeFormat("ru-RU", { day: "2-digit", month: "short" }).format(date).replace(".", "");
}

function escapeHTML(value) {
  return value.replace(/[&<>"']/g, (char) => {
    const map = { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;" };
    return map[char];
  });
}
