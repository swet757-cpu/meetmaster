const sections = [
  { id: "profile", title: "Бизнес", range: [1, 6] },
  { id: "cash", title: "Деньги", range: [7, 12] },
  { id: "profit", title: "Прибыль", range: [13, 18] },
  { id: "reports", title: "Отчеты", range: [19, 26] },
  { id: "pains", title: "Проблемы", range: [27, 38] },
  { id: "decisions", title: "Решения", range: [39, 44] },
  { id: "readiness", title: "Готовность", range: [45, 50] },
];

const questions = [
  q(1, "profile", "Какая сфера бизнеса?", ["Производство", "Строительство", "Услуги", "Торговля", "Другое"]),
  q(2, "profile", "Сколько лет работает бизнес?", ["До 1 года", "1-3 года", "3-5 лет", "Более 5 лет"]),
  q(3, "profile", "Сколько юридических лиц или ИП используется в бизнесе?", ["1", "2", "3 и более"]),
  q(4, "profile", "Сколько направлений деятельности есть внутри бизнеса?", ["1", "2-3", "Более 3"]),
  q(5, "profile", "Есть ли наемные сотрудники?", ["Нет", "До 10", "10-50", "Более 50"]),
  q(6, "profile", "Примерная выручка в месяц", ["До 1 млн", "1-5 млн", "5-15 млн", "Более 15 млн"]),

  q(7, "cash", "Понимаете ли вы, сколько денег будет на расчетном счете через 7-14 дней?", scored(["Да", 0], ["Примерно", 1], ["Нет", 2])),
  q(8, "cash", "Бывают ли ситуации, когда деньги должны быть, но их не хватает?", scored(["Часто", 2], ["Иногда", 1], ["Редко", 1], ["Никогда", 0])),
  q(9, "cash", "Есть ли платежный календарь?", scored(["Да, ведется регулярно", 0], ["Есть, но неактуальный", 1], ["Нет", 2])),
  q(10, "cash", "Кто контролирует обязательные платежи: налоги, зарплату, аренду, кредиты?", scored(["Собственник", 1], ["Бухгалтер", 1], ["Финансист", 0], ["Никто системно", 2])),
  q(11, "cash", "Есть ли список будущих платежей по договорам?", scored(["Да", 0], ["Частично", 1], ["Нет", 2])),
  q(12, "cash", "Бывают ли просрочки поставщикам, сотрудникам, налоговой или банкам?", scored(["Да", 2], ["Иногда", 1], ["Нет", 0])),

  q(13, "profit", "Понимаете ли вы, сколько бизнес реально зарабатывает в месяц?", scored(["Да", 0], ["Примерно", 1], ["Нет", 2])),
  q(14, "profit", "Отличаете ли вы выручку, прибыль и остаток денег на счете?", scored(["Да", 0], ["Частично", 1], ["Нет", 2])),
  q(15, "profit", "Считаете ли вы прибыль по направлениям, проектам или объектам?", scored(["Да", 0], ["Частично", 1], ["Нет", 2])),
  q(16, "profit", "Знаете ли вы, какие клиенты, проекты или направления самые прибыльные?", scored(["Да", 0], ["Примерно", 1], ["Нет", 2])),
  q(17, "profit", "Бывают ли месяцы с хорошей выручкой, но без прибыли?", scored(["Да", 2], ["Иногда", 1], ["Нет", 0], ["Не знаю", 2])),
  q(18, "profit", "Учитываются ли в прибыли зарплата, налоги, аренда, кредиты, амортизация, управленческие расходы?", scored(["Да", 0], ["Частично", 1], ["Нет", 2], ["Не знаю", 2])),

  {
    number: 19,
    section: "reports",
    title: "Какие отчеты вы сейчас получаете?",
    type: "multi",
    options: [
      { label: "ДДС" },
      { label: "ОПиУ" },
      { label: "Платежный календарь" },
      { label: "Баланс" },
      { label: "План-факт анализ" },
      { label: "Финансовый дашборд" },
      { label: "Только бухгалтерские отчеты" },
      { label: "Ничего" },
    ],
    score(value) {
      const selected = Array.isArray(value) ? value : [];
      if (selected.includes("Ничего")) return 2;
      if (selected.includes("Только бухгалтерские отчеты")) return 1;
      return selected.length >= 3 ? 0 : 1;
    },
  },
  q(20, "reports", "Как часто вы смотрите финансовые отчеты?", scored(["Еженедельно", 0], ["Ежемесячно", 0], ["Редко", 1], ["Только когда проблема", 2])),
  q(21, "reports", "Отчеты помогают принимать решения?", scored(["Да", 0], ["Частично", 1], ["Нет", 2])),
  q(22, "reports", "Есть ли отчет ДДС - движение денег по статьям?", scored(["Да", 0], ["Частично", 1], ["Нет", 2])),
  q(23, "reports", "Есть ли ОПиУ - доходы, расходы, прибыль?", scored(["Да", 0], ["Частично", 1], ["Нет", 2])),
  q(24, "reports", "Есть ли управленческий баланс - активы, обязательства, капитал?", scored(["Да", 0], ["Частично", 1], ["Нет", 2])),
  q(25, "reports", "Есть ли план-факт анализ?", scored(["Да", 0], ["Частично", 1], ["Нет", 2])),
  q(26, "reports", "Есть ли финансовый дашборд для собственника?", scored(["Да", 0], ["Частично", 1], ["Нет", 2])),

  pain(27, "Непонятно, куда уходят деньги"),
  pain(28, "Есть кассовые разрывы"),
  pain(29, "Налоги становятся неожиданностью"),
  pain(30, "Собственник сам постоянно контролирует платежи"),
  pain(31, "Бухгалтерия дает данные поздно или непонятно"),
  pain(32, "Нет понимания реальной прибыли"),
  pain(33, "Сложно принимать решение: нанимать людей, покупать технику, брать кредит"),
  pain(34, "Несколько компаний, деньги перемешиваются"),
  pain(35, "Есть займы между компаниями или собственником"),
  pain(36, "Есть дебиторская задолженность, но непонятно, когда придут деньги"),
  pain(37, "Есть кредиторская задолженность, но нет общего графика оплат"),
  pain(38, "Нет регулярной финансовой дисциплины"),

  q(39, "decisions", "На основании чего вы принимаете финансовые решения?", scored(["По отчетам", 0], ["По остатку денег", 1], ["По ощущениям", 2], ["По совету бухгалтера", 1])),
  q(40, "decisions", "Можете ли вы быстро ответить: можно ли вывести дивиденды?", scored(["Да", 0], ["Примерно", 1], ["Нет", 2])),
  q(41, "decisions", "Можете ли вы быстро ответить: сколько бизнес заработал за прошлый месяц?", scored(["Да", 0], ["Примерно", 1], ["Нет", 2])),
  q(42, "decisions", "Можете ли вы быстро ответить: сколько денег понадобится в ближайшие 2 недели?", scored(["Да", 0], ["Примерно", 1], ["Нет", 2])),
  q(43, "decisions", "Можете ли вы быстро ответить: какие расходы можно сократить?", scored(["Да", 0], ["Примерно", 1], ["Нет", 2])),
  q(44, "decisions", "Есть ли у вас финансовые показатели, по которым вы оцениваете бизнес?", scored(["Да", 0], ["Частично", 1], ["Нет", 2])),

  q(45, "readiness", "Готовы ли вы передавать данные по банку, кассе, договорам и задолженности?", ["Да", "Частично", "Нет"]),
  q(46, "readiness", "Есть ли ответственный сотрудник, который может давать первичные данные?", ["Да", "Нет", "Нужно назначить"]),
  q(47, "readiness", "Готовы ли вы смотреть отчеты регулярно: раз в неделю или раз в месяц?", ["Да", "Нет", "Пока не знаю"]),
  multi(48, "readiness", "Что для вас важнее всего сейчас?", ["Контроль денег", "Прибыль", "Налоги", "Долги", "Рост бизнеса", "Порядок в учете"]),
  multi(49, "readiness", "Какой результат вы хотите получить от управленческого учета?", ["Видеть деньги", "Понимать прибыль", "Убрать хаос", "Контролировать платежи", "Принимать решения"]),
  q(50, "readiness", "Когда нужно начать?", ["Срочно", "В течение месяца", "Позже", "Пока изучаю"]),
];

const answers = {};
let currentIndex = 0;

const panel = document.querySelector("#question-panel");
const sectionNav = document.querySelector("#section-nav");
const progressFill = document.querySelector("#progress-fill");
const progressLabel = document.querySelector("#progress-label");
const liveRisk = document.querySelector("#live-risk");
const riskFill = document.querySelector("#risk-fill");
const resultContent = document.querySelector("#result-content");
const prevButton = document.querySelector("#prev-button");
const nextButton = document.querySelector("#next-button");
const resultButton = document.querySelector("#result-button");
const restartButton = document.querySelector("#restart-button");

renderSectionNav();
renderQuestion();
renderResult();

prevButton.addEventListener("click", () => {
  currentIndex = Math.max(0, currentIndex - 1);
  renderQuestion();
});

nextButton.addEventListener("click", () => {
  if (currentIndex < questions.length - 1) {
    currentIndex += 1;
    renderQuestion();
  } else {
    renderResult();
  }
});

resultButton.addEventListener("click", () => {
  renderResult();
});

restartButton.addEventListener("click", () => {
  Object.keys(answers).forEach((key) => delete answers[key]);
  currentIndex = 0;
  renderQuestion();
  renderResult();
});

function q(number, section, title, options) {
  return {
    number,
    section,
    title,
    type: "single",
    options: options.map((option) => (typeof option === "string" ? { label: option } : option)),
  };
}

function multi(number, section, title, options) {
  return {
    number,
    section,
    title,
    type: "multi",
    options: options.map((option) => ({ label: option })),
  };
}

function scored(...items) {
  return items.map(([label, score]) => ({ label, score }));
}

function pain(number, title) {
  return q(number, "pains", title, scored(["Да", 2], ["Нет", 0]));
}

function renderSectionNav() {
  sectionNav.innerHTML = sections
    .map((section, index) => {
      const total = questions.filter((item) => item.section === section.id).length;
      return `
        <button class="section-button" type="button" data-section="${section.id}">
          <span>${index + 1}</span>
          <span>${section.title}</span>
          <small>${total}</small>
        </button>
      `;
    })
    .join("");

  sectionNav.querySelectorAll("button").forEach((button) => {
    button.addEventListener("click", () => {
      const target = questions.findIndex((item) => item.section === button.dataset.section);
      if (target >= 0) {
        currentIndex = target;
        renderQuestion();
      }
    });
  });
}

function renderQuestion() {
  const question = questions[currentIndex];
  const section = sections.find((item) => item.id === question.section);
  const selected = answers[question.number];
  const scoredLabel = question.type === "multi"
    ? "можно выбрать несколько"
    : isScored(question)
      ? "влияет на риск"
      : "профиль";

  panel.innerHTML = `
    <div class="question-meta">
      <span class="pill">Вопрос ${question.number} из ${questions.length}</span>
      <span class="pill">${section.title}</span>
      <span class="pill">${scoredLabel}</span>
    </div>
    <h3 class="question-title">${question.title}</h3>
    ${renderOptions(question, selected)}
  `;

  panel.querySelectorAll("[data-value]").forEach((button) => {
    button.addEventListener("click", () => handleAnswer(question, button.dataset.value));
  });

  updateNavigation();
  updateProgress();
}

function renderOptions(question, selected) {
  const values = question.options.map((option) => option.label);
  return `
    <div class="option-grid">
      ${values
        .map((value) => {
          const isSelected = question.type === "multi"
            ? Array.isArray(selected) && selected.includes(value)
            : selected === value;
          const option = question.options.find((item) => item.label === value) || {};
          const note = typeof option.score === "number" ? scoreHint(option.score) : "";
          return `
            <button class="option ${isSelected ? "is-selected" : ""}" type="button" data-value="${value}">
              <strong>${value}</strong>
              ${note ? `<small>${note}</small>` : ""}
            </button>
          `;
        })
        .join("")}
    </div>
  `;
}

function handleAnswer(question, value) {
  if (question.type === "multi") {
    const current = Array.isArray(answers[question.number]) ? [...answers[question.number]] : [];
    const exists = current.includes(value);
    let next = exists ? current.filter((item) => item !== value) : [...current, value];
    if (value === "Ничего" && !exists) next = ["Ничего"];
    if (value !== "Ничего") next = next.filter((item) => item !== "Ничего");
    answers[question.number] = next;
  } else {
    answers[question.number] = value;
  }
  renderQuestion();
  renderResult();
}

function updateNavigation() {
  prevButton.disabled = currentIndex === 0;
  nextButton.textContent = currentIndex === questions.length - 1 ? "К итогу" : "Далее";

  sectionNav.querySelectorAll("button").forEach((button) => {
    button.classList.toggle("is-active", button.dataset.section === questions[currentIndex].section);
  });
}

function updateProgress() {
  const answered = questions.filter((question) => {
    const value = answers[question.number];
    return Array.isArray(value) ? value.length > 0 : Boolean(value);
  }).length;
  const percent = Math.round((answered / questions.length) * 100);
  progressFill.style.width = `${percent}%`;
  progressLabel.textContent = `${answered} из ${questions.length}`;
}

function renderResult() {
  const score = calculateScore();
  const level = getRiskLevel(score);
  const percent = Math.min(100, Math.round((score / 76) * 100));
  const recommendations = buildRecommendations();
  const answeredScored = questions.filter((item) => isScored(item) && answers[item.number]).length;

  liveRisk.textContent = `${score} баллов`;
  riskFill.style.width = `${percent}%`;
  riskFill.style.background = level.color;

  resultContent.innerHTML = `
    <div class="result-box">
      <p class="eyebrow">Итог диагностики</p>
      <h3>${level.title}</h3>
      <p>${level.text}</p>
      <div class="metric"><span>Баллы риска</span><strong>${score}</strong></div>
      <div class="metric"><span>Оценено вопросов</span><strong>${answeredScored} из 38</strong></div>
      <div class="metric"><span>Начать</span><strong>${answers[50] || "данных нет"}</strong></div>
    </div>
    <div class="result-box">
      <p class="eyebrow">Что предложить</p>
      <ul class="recommendations">
        ${recommendations.map((item) => `<li>${item}</li>`).join("")}
      </ul>
    </div>
    <div class="result-box">
      <p class="eyebrow">Следующий шаг</p>
      <p class="note">${buildNextStep(score)}</p>
    </div>
  `;
}

function calculateScore() {
  return questions.reduce((sum, question) => {
    if (!isScored(question)) return sum;
    const value = answers[question.number];
    if (!value || (Array.isArray(value) && value.length === 0)) return sum;
    if (typeof question.score === "function") return sum + question.score(value);
    const option = question.options.find((item) => item.label === value);
    return sum + (option && typeof option.score === "number" ? option.score : 0);
  }, 0);
}

function isScored(question) {
  return question.number >= 7 && question.number <= 44;
}

function getRiskLevel(score) {
  if (score <= 15) {
    return {
      title: "Учет частично выстроен",
      text: "Нужна проверка качества отчетов, регламентов и точности данных.",
      color: "#0f766e",
    };
  }
  if (score <= 35) {
    return {
      title: "Есть системные пробелы",
      text: "В первую очередь нужны ДДС, платежный календарь и регулярный контроль обязательств.",
      color: "#b45309",
    };
  }
  if (score <= 55) {
    return {
      title: "Высокий риск кассовых разрывов",
      text: "Нужен полноценный управленческий учет с регулярным финансовым циклом.",
      color: "#c2410c",
    };
  }
  return {
    title: "Финансы управляются хаотично",
    text: "Требуется диагностика, восстановление данных и внедрение регулярной отчетности.",
    color: "#b91c1c",
  };
}

function buildRecommendations() {
  const result = [];
  const selectedReports = Array.isArray(answers[19]) ? answers[19] : [];

  if (hasRisk([7, 8, 9, 11, 12, 28, 30, 37, 42])) {
    result.push("Платежный календарь на 4-8 недель и контроль обязательных платежей.");
  }
  if (hasRisk([22, 27]) || !selectedReports.includes("ДДС")) {
    result.push("Отчет ДДС по статьям: поступления, оплаты, налоги, кредиты, вывод денег.");
  }
  if (hasRisk([13, 14, 15, 16, 17, 18, 23, 32, 41])) {
    result.push("Управленческий ОПиУ: выручка, расходы, прибыль, рентабельность.");
  }
  if (hasRisk([3, 4, 15, 34]) || answers[3] === "3 и более" || answers[4] === "Более 3") {
    result.push("ОПиУ по направлениям, проектам, объектам или юридическим лицам.");
  }
  if (hasRisk([24, 35, 36, 37, 40])) {
    result.push("Управленческий баланс: активы, обязательства, капитал, займы и задолженность.");
  }
  if (hasRisk([25, 33, 43, 44])) {
    result.push("План-факт анализ и набор финансовых показателей для решений собственника.");
  }
  if (hasRisk([29])) {
    result.push("Налоговый календарь и предварительное согласование сумм к оплате.");
  }
  if (hasRisk([20, 21, 26, 31, 38, 39])) {
    result.push("Финансовый цикл: неделя, месяц, квартал, дашборд для собственника.");
  }

  return result.length ? result : ["Проверка действующих отчетов и точности управленческих данных."];
}

function hasRisk(numbers) {
  return numbers.some((number) => {
    const question = questions.find((item) => item.number === number);
    const value = answers[number];
    if (!question || !value) return false;
    if (typeof question.score === "function") return question.score(value) > 0;
    const option = question.options.find((item) => item.label === value);
    return option && option.score > 0;
  });
}

function buildNextStep(score) {
  const start = answers[50] || "согласовать срок старта";
  const priority = answers[48] || "определить главный приоритет";
  const result = answers[49] || "зафиксировать ожидаемый результат";

  if (score <= 15) {
    return `Провести аудит текущих отчетов, проверить методику ДДС, ОПиУ и баланса, затем настроить регулярную сверку. Приоритет: ${priority}. Результат: ${result}. Старт: ${start}.`;
  }
  if (score <= 35) {
    return `Начать с платежного календаря и ДДС, затем добавить ОПиУ и план-факт. Приоритет: ${priority}. Результат: ${result}. Старт: ${start}.`;
  }
  if (score <= 55) {
    return `Собрать данные по банку, кассе, договорам, дебиторской и кредиторской задолженности, после этого внедрить полный пакет отчетов. Приоритет: ${priority}. Результат: ${result}. Старт: ${start}.`;
  }
  return `Сначала восстановить финансовую картину и задолженность, затем запустить платежный календарь, ДДС, ОПиУ, баланс и регламент контроля. Приоритет: ${priority}. Результат: ${result}. Старт: ${start}.`;
}

function scoreHint(score) {
  if (score === 0) return "риск не добавляется";
  if (score === 1) return "умеренный риск";
  return "высокий риск";
}
