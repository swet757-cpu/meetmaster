const stages = [
  { id: "profile", title: "Профиль", range: [1, 6] },
  { id: "money", title: "Деньги", range: [7, 11] },
  { id: "profit", title: "Прибыль", range: [12, 16] },
  { id: "reports", title: "Отчеты", range: [17, 20] },
  { id: "readiness", title: "Готовность", range: [21, 26] },
];

const revenueMap = {
  "До 1 млн": 750000,
  "1-5 млн": 3000000,
  "5-15 млн": 10000000,
  "Более 15 млн": 20000000,
};

const maxRiskScore = 52;

const questions = [
  q(1, "profile", "Какая сфера бизнеса?", ["Производство", "Строительство", "Услуги", "Торговля", "IT и Digital", "Другое"]),
  q(2, "profile", "Примерная выручка в месяц", Object.keys(revenueMap)),
  q(3, "profile", "Сколько юридических лиц или ИП используется?", scored(["1", 0], ["2", 1], ["3 и более", 2])),
  q(4, "profile", "Сколько направлений, проектов или объектов нужно видеть отдельно?", scored(["1", 0], ["2-3", 1], ["Более 3", 2])),
  q(5, "profile", "Сколько сотрудников в бизнесе?", scored(["До 10", 0], ["10-50", 1], ["Более 50", 2])),
  q(6, "profile", "Что собственник хочет получить в первую очередь?", ["Контроль денег", "Понимать прибыль", "Убрать хаос", "Контролировать платежи", "Принимать решения"]),

  q(7, "money", "Понимаете ли вы, сколько денег будет на расчетном счете через 7-14 дней?", scored(["Да", 0], ["Примерно", 1], ["Нет", 2])),
  q(8, "money", "Бывают ли кассовые разрывы или задержки оплат?", scored(["Часто", 2], ["Иногда", 1], ["Редко", 1], ["Нет", 0])),
  q(9, "money", "Есть ли платежный календарь?", scored(["Да, ведется регулярно", 0], ["Есть, но неактуальный", 1], ["Нет", 2])),
  q(10, "money", "Кто контролирует налоги, зарплату, аренду, кредиты и крупные платежи?", scored(["Финансист", 0], ["Бухгалтер", 1], ["Собственник", 1], ["Никто системно", 2])),
  q(11, "money", "Есть ли общий график дебиторской и кредиторской задолженности?", scored(["Да", 0], ["Частично", 1], ["Нет", 2])),

  q(12, "profit", "Понимаете ли вы, сколько бизнес реально зарабатывает в месяц?", scored(["Да", 0], ["Примерно", 1], ["Нет", 2])),
  q(13, "profit", "Считаете ли вы прибыль по направлениям, клиентам, проектам или объектам?", scored(["Да", 0], ["Частично", 1], ["Нет", 2])),
  q(14, "profit", "Бывают ли месяцы с хорошей выручкой, но без прибыли?", scored(["Да", 2], ["Иногда", 1], ["Нет", 0], ["Не знаю", 2])),
  q(15, "profit", "Учитываются ли в прибыли зарплата, налоги, аренда, кредиты, амортизация и управленческие расходы?", scored(["Да", 0], ["Частично", 1], ["Нет", 2], ["Не знаю", 2])),
  q(16, "profit", "Можете ли быстро ответить, можно ли вывести дивиденды?", scored(["Да", 0], ["Примерно", 1], ["Нет", 2])),

  multi(17, "reports", "Какие отчеты сейчас есть?", ["ДДС", "ОПиУ", "Управленческий баланс", "Платежный календарь", "План-факт", "Дашборд", "Только бухгалтерские отчеты", "Ничего"]),
  q(18, "reports", "Как часто собственник смотрит финансовые отчеты?", scored(["Еженедельно", 0], ["Ежемесячно", 0], ["Редко", 1], ["Только когда проблема", 2])),
  q(19, "reports", "Отчеты помогают принимать решения?", scored(["Да", 0], ["Частично", 1], ["Нет", 2])),
  multi(20, "reports", "Какие боли сейчас актуальны?", [
    "Непонятно, куда уходят деньги",
    "Налоги становятся неожиданностью",
    "Бухгалтерия дает данные поздно",
    "Деньги компаний перемешиваются",
    "Есть займы и авансы",
    "Нет финансовой дисциплины",
  ]),

  q(21, "readiness", "Готовы ли передавать данные по банку, кассе, договорам и задолженности?", scored(["Да", 0], ["Частично", 1], ["Нет", 2])),
  q(22, "readiness", "Есть ли сотрудник, который может давать первичные данные?", scored(["Да", 0], ["Нужно назначить", 1], ["Нет", 2])),
  q(23, "readiness", "Готовы ли смотреть отчеты регулярно?", scored(["Да, еженедельно", 0], ["Да, ежемесячно", 0], ["Пока не знаю", 1], ["Нет", 2])),
  q(24, "readiness", "Когда нужно начать?", scored(["Срочно", 2], ["В течение месяца", 1], ["Позже", 0], ["Пока изучаю", 0])),
  q(25, "readiness", "Какой формат ближе?", ["Разовая диагностика", "Запуск управленческого учета", "Финдиректор на аутсорсе", "Пока нужен расчет"]),
  q(26, "readiness", "Куда удобнее отправить результат?", ["Telegram", "Почта", "Скопировать текст", "Печать в PDF"]),
];

const state = {
  answers: {},
  currentIndex: 0,
};

const nodes = {
  stageList: document.querySelector("#stage-list"),
  progressLabel: document.querySelector("#progress-label"),
  progressFill: document.querySelector("#progress-fill"),
  panel: document.querySelector("#question-panel"),
  prev: document.querySelector("#prev-button"),
  next: document.querySelector("#next-button"),
  restart: document.querySelector("#restart-button"),
  offerTitle: document.querySelector("#offer-title"),
  offerSummary: document.querySelector("#offer-summary"),
  metrics: document.querySelector("#metrics-grid"),
  experts: document.querySelector("#expert-grid"),
  proposalText: document.querySelector("#proposal-text"),
  copy: document.querySelector("#copy-button"),
  print: document.querySelector("#print-button"),
  telegram: document.querySelector("#telegram-link"),
  mail: document.querySelector("#mail-link"),
  status: document.querySelector("#status-line"),
};

renderStages();
renderQuestion();
renderResult();

nodes.prev.addEventListener("click", () => {
  state.currentIndex = Math.max(0, state.currentIndex - 1);
  renderQuestion();
});

nodes.next.addEventListener("click", () => {
  if (state.currentIndex < questions.length - 1) {
    state.currentIndex += 1;
    renderQuestion();
  } else {
    renderResult();
    document.querySelector("#proposal").scrollIntoView({ behavior: "smooth", block: "start" });
  }
});

nodes.restart.addEventListener("click", () => {
  state.answers = {};
  state.currentIndex = 0;
  renderQuestion();
  renderResult();
  setStatus("");
});

nodes.copy.addEventListener("click", copyProposal);
nodes.print.addEventListener("click", () => window.print());

function q(number, stage, title, options) {
  return {
    number,
    stage,
    title,
    type: "single",
    options: options.map((option) => (typeof option === "string" ? { label: option } : option)),
  };
}

function multi(number, stage, title, options) {
  return {
    number,
    stage,
    title,
    type: "multi",
    options: options.map((label) => ({ label })),
  };
}

function scored(...items) {
  return items.map(([label, score]) => ({ label, score }));
}

function renderStages() {
  nodes.stageList.innerHTML = stages
    .map((stage, index) => {
      const total = questions.filter((item) => item.stage === stage.id).length;
      return `
        <button class="stage-button" type="button" data-stage="${stage.id}">
          <span>${index + 1}</span>
          <strong>${stage.title}</strong>
          <small>${total}</small>
        </button>
      `;
    })
    .join("");

  nodes.stageList.querySelectorAll("button").forEach((button) => {
    button.addEventListener("click", () => {
      const target = questions.findIndex((item) => item.stage === button.dataset.stage);
      if (target >= 0) {
        state.currentIndex = target;
        renderQuestion();
      }
    });
  });
}

function renderQuestion() {
  const question = questions[state.currentIndex];
  const stage = stages.find((item) => item.id === question.stage);
  const selected = state.answers[question.number];

  nodes.panel.innerHTML = `
    <div class="question-meta">
      <span class="pill">Вопрос ${question.number} из ${questions.length}</span>
      <span class="pill">${stage.title}</span>
      <span class="pill">${question.type === "multi" ? "можно несколько" : "один ответ"}</span>
    </div>
    <h3>${question.title}</h3>
    <div class="option-grid">
      ${question.options.map((option) => optionButton(question, option, selected)).join("")}
    </div>
  `;

  nodes.panel.querySelectorAll("[data-value]").forEach((button) => {
    button.addEventListener("click", () => {
      applyAnswer(question, button.dataset.value);
      renderQuestion();
      renderResult();
    });
  });

  updateNavigation();
  updateProgress();
}

function optionButton(question, option, selected) {
  const active = question.type === "multi"
    ? Array.isArray(selected) && selected.includes(option.label)
    : selected === option.label;
  const hint = typeof option.score === "number" ? scoreHint(option.score) : "";
  return `
    <button class="option ${active ? "is-selected" : ""}" type="button" data-value="${option.label}">
      <strong>${option.label}</strong>
      ${hint ? `<small>${hint}</small>` : ""}
    </button>
  `;
}

function applyAnswer(question, value) {
  if (question.type !== "multi") {
    state.answers[question.number] = value;
    return;
  }

  const current = Array.isArray(state.answers[question.number]) ? [...state.answers[question.number]] : [];
  const exists = current.includes(value);
  let next = exists ? current.filter((item) => item !== value) : [...current, value];

  if (question.number === 17 && value === "Ничего" && !exists) next = ["Ничего"];
  if (question.number === 17 && value !== "Ничего") next = next.filter((item) => item !== "Ничего");

  state.answers[question.number] = next;
}

function updateNavigation() {
  const question = questions[state.currentIndex];
  nodes.prev.disabled = state.currentIndex === 0;
  nodes.next.textContent = state.currentIndex === questions.length - 1 ? "Сформировать КП" : "Далее";

  nodes.stageList.querySelectorAll("button").forEach((button) => {
    button.classList.toggle("is-active", button.dataset.stage === question.stage);
  });
}

function updateProgress() {
  const answered = questions.filter((question) => {
    const value = state.answers[question.number];
    return Array.isArray(value) ? value.length > 0 : Boolean(value);
  }).length;
  const percent = Math.round((answered / questions.length) * 100);
  nodes.progressLabel.textContent = `${answered} из ${questions.length}`;
  nodes.progressFill.style.width = `${percent}%`;
}

function renderResult() {
  const result = buildResult();
  nodes.offerTitle.textContent = result.offerTitle;
  nodes.offerSummary.textContent = result.summary;
  nodes.metrics.innerHTML = result.metrics.map(metricCard).join("");
  nodes.experts.innerHTML = result.experts.map(expertCard).join("");
  nodes.proposalText.textContent = result.proposalText;

  const encodedText = encodeURIComponent(result.proposalText);
  nodes.telegram.href = `https://t.me/share/url?url=&text=${encodedText}`;
  nodes.mail.href = `mailto:?subject=${encodeURIComponent("Результат финансовой диагностики МБП")}&body=${encodedText}`;
}

function metricCard(metric) {
  return `
    <div class="metric">
      <span>${metric.label}</span>
      <strong>${metric.value}</strong>
    </div>
  `;
}

function expertCard(expert) {
  return `
    <article class="expert-card">
      <div>
        <span>${expert.score} / 10</span>
        <strong>${expert.title}</strong>
      </div>
      <p>${expert.text}</p>
    </article>
  `;
}

function buildResult() {
  const score = calculateRiskScore();
  const level = riskLevel(score);
  const revenue = revenueMap[state.answers[2]] || 0;
  const lossRate = lossRateByScore(score);
  const loss = revenue * lossRate;
  const format = serviceFormat(score);
  const recommendations = buildRecommendations();
  const experts = buildExperts(score);
  const formula = revenue
    ? `${formatMoney(revenue)} x ${Math.round(lossRate * 100)}% = ${formatMoney(loss)}`
    : "выручка не указана, расчет потерь невозможен";

  const offerTitle = `${level.title}: ${format}`;
  const summary = level.text;
  const metrics = [
    { label: "Баллы риска", value: `${score} из ${maxRiskScore}` },
    { label: "Ориентир потерь", value: revenue ? formatMoney(loss) : "данных нет" },
    { label: "Формула", value: formula },
    { label: "Старт", value: state.answers[24] || "данных нет" },
  ];

  return {
    offerTitle,
    summary,
    metrics,
    experts,
    proposalText: buildProposalText({ score, level, revenue, loss, lossRate, formula, format, recommendations, experts }),
  };
}

function calculateRiskScore() {
  let score = 0;

  questions.forEach((question) => {
    const value = state.answers[question.number];
    if (!value || (Array.isArray(value) && value.length === 0)) return;

    if (question.number === 17) {
      score += reportsScore(value);
      return;
    }

    if (question.number === 20) {
      score += Math.min(8, value.length * 2);
      return;
    }

    const option = question.options.find((item) => item.label === value);
    if (option && typeof option.score === "number") score += option.score;
  });

  return score;
}

function reportsScore(value) {
  const selected = Array.isArray(value) ? value : [];
  if (selected.includes("Ничего")) return 6;
  if (selected.includes("Только бухгалтерские отчеты")) return 4;
  if (selected.length >= 5) return 0;
  if (selected.length >= 3) return 1;
  if (selected.length >= 1) return 2;
  return 0;
}

function riskLevel(score) {
  if (score <= 10) {
    return {
      title: "Низкий риск",
      text: "Учет частично выстроен. Нужна проверка качества отчетов и управленческих регламентов.",
    };
  }
  if (score <= 22) {
    return {
      title: "Средний риск",
      text: "Есть системные пробелы. В первую очередь нужны ДДС, платежный календарь и регулярный контроль обязательств.",
    };
  }
  if (score <= 34) {
    return {
      title: "Высокий риск",
      text: "Финансовые решения принимаются с задержкой или неполной картиной. Нужен запуск управленческого учета.",
    };
  }
  return {
    title: "Критический риск",
    text: "Финансы управляются хаотично. Требуется восстановление картины, регламенты и регулярная работа финдиректора.",
  };
}

function lossRateByScore(score) {
  if (score <= 10) return 0.01;
  if (score <= 22) return 0.03;
  if (score <= 34) return 0.05;
  return 0.08;
}

function serviceFormat(score) {
  const chosen = state.answers[25];
  if (chosen && chosen !== "Пока нужен расчет") return chosen;
  if (score <= 10) return "Разовая диагностика";
  if (score <= 28) return "Запуск управленческого учета";
  return "Финдиректор на аутсорсе";
}

function buildRecommendations() {
  const result = [];
  const reports = Array.isArray(state.answers[17]) ? state.answers[17] : [];
  const pains = Array.isArray(state.answers[20]) ? state.answers[20] : [];

  if (hasRisk([7, 8, 9, 10, 11]) || pains.includes("Нет финансовой дисциплины")) {
    result.push("Платежный календарь на 4-8 недель и регламент согласования оплат.");
  }
  if (!reports.includes("ДДС") || pains.includes("Непонятно, куда уходят деньги")) {
    result.push("ДДС по статьям: поступления, оплаты, налоги, кредиты, вывод денег.");
  }
  if (hasRisk([12, 13, 14, 15, 16])) {
    result.push("Управленческий ОПиУ: выручка, расходы, прибыль, рентабельность.");
  }
  if (state.answers[3] === "3 и более" || state.answers[4] === "Более 3" || pains.includes("Деньги компаний перемешиваются")) {
    result.push("Раздельный учет по юрлицам, направлениям, проектам или объектам.");
  }
  if (!reports.includes("Управленческий баланс") || pains.includes("Есть займы и авансы")) {
    result.push("Управленческий баланс: активы, обязательства, капитал, займы, авансы.");
  }
  if (pains.includes("Налоги становятся неожиданностью")) {
    result.push("Налоговый календарь и предварительное согласование сумм к оплате.");
  }
  if (hasRisk([18, 19]) || pains.includes("Бухгалтерия дает данные поздно")) {
    result.push("Финансовый цикл: неделя, месяц, квартал и дашборд для собственника.");
  }

  return result.length ? result : ["Проверка действующих отчетов и точности управленческих данных."];
}

function hasRisk(numbers) {
  return numbers.some((number) => {
    const question = questions.find((item) => item.number === number);
    const value = state.answers[number];
    if (!question || !value) return false;
    const option = question.options.find((item) => item.label === value);
    return option && typeof option.score === "number" && option.score > 0;
  });
}

function buildExperts(score) {
  const pains = Array.isArray(state.answers[20]) ? state.answers[20] : [];
  const reports = Array.isArray(state.answers[17]) ? state.answers[17] : [];

  return [
    {
      title: "Финансовый директор",
      score: expertScore([7, 8, 9, 12, 16], score),
      text: state.answers[16] === "Нет"
        ? "Собственнику сложно принимать решения о дивидендах, инвестициях и обязательствах."
        : "Ключевая задача - закрепить регулярный финансовый контур.",
    },
    {
      title: "Методолог учета",
      score: reports.includes("ДДС") && reports.includes("ОПиУ") ? 3 : 8,
      text: "Нужна связка ДДС, ОПиУ, баланса, план-факта и единых правил сбора данных.",
    },
    {
      title: "Налоговый эксперт",
      score: pains.includes("Налоги становятся неожиданностью") ? 9 : 4,
      text: pains.includes("Налоги становятся неожиданностью")
        ? "Налоговые платежи нужно включить в платежный календарь заранее."
        : "Налоговый календарь стоит держать как часть регулярного финансового цикла.",
    },
    {
      title: "Риск-аналитик",
      score: expertScore([8, 9, 10, 11], score),
      text: "Главный риск - кассовые разрывы, задолженность и отсутствие графика обязательств.",
    },
    {
      title: "B2B-коммерсант",
      score: state.answers[24] === "Срочно" ? 9 : state.answers[24] === "В течение месяца" ? 7 : 5,
      text: "КП лучше строить вокруг ближайшего результата: контроль денег, прибыль и спокойный календарь оплат.",
    },
  ];
}

function expertScore(numbers, totalScore) {
  const local = numbers.reduce((sum, number) => {
    const question = questions.find((item) => item.number === number);
    const value = state.answers[number];
    const option = question && question.options.find((item) => item.label === value);
    return sum + (option && typeof option.score === "number" ? option.score : 0);
  }, 0);
  return Math.max(1, Math.min(10, Math.round(local * 1.7 + totalScore / 12)));
}

function buildProposalText(data) {
  const a = state.answers;
  const recommendations = data.recommendations.map((item, index) => `${index + 1}. ${item}`).join("\n");
  const experts = data.experts.map((item) => `${item.title}: ${item.score}/10 - ${item.text}`).join("\n");
  const revenueText = data.revenue ? formatMoney(data.revenue) : "данных нет";
  const lossText = data.revenue ? formatMoney(data.loss) : "данных нет";

  return [
    "Предварительное коммерческое предложение",
    "",
    `Бизнес: ${a[1] || "данных нет"}`,
    `Выручка в месяц: ${revenueText}`,
    `Главный приоритет: ${a[6] || "данных нет"}`,
    `Срок старта: ${a[24] || "данных нет"}`,
    "",
    `Диагноз: ${data.level.title}`,
    `Баллы риска: ${data.score} из ${maxRiskScore}`,
    `Ориентир потерь: ${lossText}`,
    `Формула: ${data.formula}`,
    "",
    `Рекомендуемый формат: ${data.format}`,
    "",
    "Что предложить:",
    recommendations,
    "",
    "Консилиум экспертов:",
    experts,
    "",
    "План первых 30 дней:",
    "1. Собрать банк, кассу, договоры, дебиторскую и кредиторскую задолженность.",
    "2. Настроить платежный календарь и ДДС.",
    "3. Собрать управленческий ОПиУ и проверить прибыль.",
    "4. Сформировать дашборд собственника и регулярный финансовый цикл.",
  ].join("\n");
}

function scoreHint(score) {
  if (score === 0) return "риск не добавляется";
  if (score === 1) return "умеренный риск";
  return "высокий риск";
}

function formatMoney(value) {
  return new Intl.NumberFormat("ru-RU", {
    style: "currency",
    currency: "RUB",
    maximumFractionDigits: 0,
  }).format(value);
}

async function copyProposal() {
  const text = nodes.proposalText.textContent;

  try {
    await navigator.clipboard.writeText(text);
    setStatus("Результат скопирован.");
  } catch (error) {
    const textarea = document.createElement("textarea");
    textarea.value = text;
    textarea.setAttribute("readonly", "");
    textarea.style.position = "fixed";
    textarea.style.left = "-999px";
    document.body.appendChild(textarea);
    textarea.select();
    document.execCommand("copy");
    textarea.remove();
    setStatus("Результат скопирован.");
  }
}

function setStatus(text) {
  nodes.status.textContent = text;
}
