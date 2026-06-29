const sections = [
  { id: "profile", title: "Бизнес", range: [1, 6] },
  { id: "cash", title: "Деньги", range: [7, 13] },
  { id: "profit", title: "Прибыль", range: [14, 17] },
  { id: "reports", title: "Отчетность", range: [18, 20] },
];

const questions = [
  q(1, "profile", "Какая сфера бизнеса?", ["Производство", "Строительство", "Услуги", "Торговля", "Другое"]),
  q(2, "profile", "Сколько лет работает бизнес?", ["До 1 года", "1-3 года", "3-5 лет", "Более 5 лет"]),
  q(3, "profile", "Сколько юридических лиц или ИП используется в бизнесе?", ["1", "2", "3 и более"]),
  q(4, "profile", "Сколько направлений деятельности есть внутри бизнеса?", ["1", "2-3", "Более 3"]),
  q(5, "profile", "Есть ли наемные сотрудники?", ["Нет", "До 10", "10-50", "Более 50"]),
  q(6, "profile", "Примерная выручка в месяц", ["До 1 млн", "1-5 млн", "5-15 млн", "Более 15 млн"]),

  q(7, "cash", "Непонятно, куда уходят деньги: понимаете ли вы, сколько денег будет на расчетном счете через 7-14 дней?", scored(["Да, понимаю точно", 0], ["Примерно", 1], ["Нет", 2])),
  q(8, "cash", "Есть кассовые разрывы: бывают ли ситуации, когда деньги должны быть, но их не хватает?", scored(["Нет", 0], ["Иногда", 1], ["Часто", 2])),
  q(9, "cash", "Собственник сам постоянно контролирует платежи?", scored(["Нет, есть ответственный", 0], ["Частично", 1], ["Да", 2])),
  q(10, "cash", "Кто контролирует обязательные платежи: налоги, зарплату, аренду, кредиты?", scored(["Финансист или регламент", 0], ["Бухгалтер", 1], ["Собственник", 1], ["Никто системно", 2])),
  q(11, "cash", "Есть ли список будущих платежей по договорам?", scored(["Да", 0], ["Частично", 1], ["Нет", 2])),
  q(12, "cash", "Бухгалтерия дает данные поздно или непонятно?", scored(["Нет", 0], ["Иногда", 1], ["Да", 2])),
  q(13, "cash", "Есть регулярная финансовая дисциплина: контролируются займы, дебиторская и кредиторская задолженность?", scored(["Да", 0], ["Частично", 1], ["Нет", 2])),

  q(14, "profit", "Нет понимания реальной прибыли: понимаете ли вы, сколько бизнес реально зарабатывает в месяц?", scored(["Да", 0], ["Примерно", 1], ["Нет", 2])),
  {
    number: 15,
    section: "profit",
    title: "Считаете ли вы прибыль по направлениям, проектам или объектам?",
    type: "single",
    options: scored(["Да", 0], ["Частично", 1], ["Нет", 2]),
    score(value) {
      if (answers[4] === "1") return 0;
      return scoreByOption(this, value);
    },
  },
  q(16, "profit", "Налоги становятся неожиданностью: учитываются ли в прибыли зарплата, налоги, аренда, кредиты и управленческие расходы?", scored(["Да", 0], ["Частично", 1], ["Нет", 2], ["Не знаю", 2])),
  q(17, "profit", "Сложно принимать решение: нанимать людей, покупать технику, брать кредит?", scored(["Нет", 0], ["Иногда", 1], ["Да", 2])),

  q(18, "reports", "Знаете ли вы об отчетах: платежный календарь, ДДС, ОПиУ, управленческий баланс?", scored(["Да", 0], ["Частично", 1], ["Нет", 2])),
  multi(19, "reports", "Что для вас важнее всего сейчас?", ["Контроль денег", "Прибыль", "Долги", "Рост бизнеса", "Порядок в учете"]),
  multi(20, "reports", "Какой результат вы хотите получить от управленческого учета?", ["Видеть деньги", "Понимать прибыль", "Убрать хаос", "Контролировать платежи", "Принимать решения"]),
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
  const conditionalNote = question.number === 15 && answers[4] === "1"
    ? "<p class=\"note\">В анкете вар2 этот вопрос не влияет на баллы, если в бизнесе одно направление.</p>"
    : "";

  panel.innerHTML = `
    <div class="question-meta">
      <span class="pill">Вопрос ${question.number} из ${questions.length}</span>
      <span class="pill">${section.title}</span>
      <span class="pill">${scoredLabel}</span>
    </div>
    <h3 class="question-title">${question.title}</h3>
    ${conditionalNote}
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
          const note = typeof option.score === "number" ? scoreHint(question, option.score) : "";
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
    answers[question.number] = exists ? current.filter((item) => item !== value) : [...current, value];
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
  const maxScore = calculateMaxScore();
  const level = getRiskLevel(score, maxScore);
  const percent = maxScore ? Math.min(100, Math.round((score / maxScore) * 100)) : 0;
  const recommendations = buildRecommendations();
  const scoredQuestions = questions.filter((item) => isScored(item) && maxQuestionScore(item) > 0);
  const answeredScored = scoredQuestions.filter((item) => answers[item.number]).length;

  liveRisk.textContent = `${score} баллов`;
  riskFill.style.width = `${percent}%`;
  riskFill.style.background = level.color;

  resultContent.innerHTML = `
    <div class="result-box">
      <p class="eyebrow">Итог диагностики вар2</p>
      <h3>${level.title}</h3>
      <p>${level.text}</p>
      <div class="metric"><span>Баллы риска</span><strong>${score} из ${maxScore}</strong></div>
      <div class="metric"><span>Оценено вопросов</span><strong>${answeredScored} из ${scoredQuestions.length}</strong></div>
      <div class="metric"><span>Приоритет</span><strong>${formatValue(answers[19])}</strong></div>
    </div>
    <div class="result-box">
      <p class="eyebrow">Что предложить</p>
      <ul class="recommendations">
        ${recommendations.map((item) => `<li>${item}</li>`).join("")}
      </ul>
    </div>
    <div class="result-box">
      <p class="eyebrow">Следующий шаг</p>
      <p class="note">${buildNextStep(score, maxScore)}</p>
    </div>
  `;
}

function calculateScore() {
  return questions.reduce((sum, question) => {
    if (!isScored(question)) return sum;
    const value = answers[question.number];
    if (!value || (Array.isArray(value) && value.length === 0)) return sum;
    if (typeof question.score === "function") return sum + question.score(value);
    return sum + scoreByOption(question, value);
  }, 0);
}

function calculateMaxScore() {
  return questions.reduce((sum, question) => sum + maxQuestionScore(question), 0);
}

function maxQuestionScore(question) {
  if (!isScored(question)) return 0;
  if (question.number === 15 && answers[4] === "1") return 0;
  return Math.max(...question.options.map((option) => option.score || 0));
}

function scoreByOption(question, value) {
  const option = question.options.find((item) => item.label === value);
  return option && typeof option.score === "number" ? option.score : 0;
}

function isScored(question) {
  return question.number >= 7 && question.number <= 18;
}

function getRiskLevel(score, maxScore) {
  const percent = maxScore ? score / maxScore : 0;
  if (percent <= 0.25) {
    return {
      title: "Учет частично выстроен",
      text: "Финансовая картина уже частично понятна. Нужна проверка качества отчетов и точности данных.",
      color: "#0f766e",
    };
  }
  if (percent <= 0.5) {
    return {
      title: "Есть системные пробелы",
      text: "Нужны ДДС, платежный календарь и регулярный контроль обязательств.",
      color: "#b45309",
    };
  }
  if (percent <= 0.75) {
    return {
      title: "Высокий риск кассовых разрывов",
      text: "Нужен полноценный управленческий учет и регулярный финансовый цикл.",
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

  if (hasRisk([7, 8, 9, 10, 11])) {
    result.push("Платежный календарь и регламент контроля обязательных платежей.");
  }
  if (hasRisk([7, 8])) {
    result.push("Отчет ДДС по статьям: поступления, оплаты, налоги, кредиты, вывод денег.");
  }
  if (hasRisk([14, 16])) {
    result.push("Управленческий ОПиУ: выручка, расходы, прибыль и рентабельность.");
  }
  if (hasRisk([15]) || answers[4] === "2-3" || answers[4] === "Более 3") {
    result.push("ОПиУ по направлениям, проектам или объектам.");
  }
  if (hasRisk([13])) {
    result.push("Управленческий баланс: активы, обязательства, капитал, займы и задолженность.");
  }
  if (hasRisk([16])) {
    result.push("Налоговый календарь и предварительное согласование сумм к оплате.");
  }
  if (hasRisk([12, 18])) {
    result.push("Финансовый цикл: неделя, месяц, квартал, регулярные отчеты для собственника.");
  }
  if (hasRisk([17])) {
    result.push("План-факт анализ и набор финансовых показателей для управленческих решений.");
  }

  return result.length ? result : ["Проверка действующих отчетов и точности управленческих данных."];
}

function hasRisk(numbers) {
  return numbers.some((number) => {
    const question = questions.find((item) => item.number === number);
    const value = answers[number];
    if (!question || !value) return false;
    if (typeof question.score === "function") return question.score(value) > 0;
    return scoreByOption(question, value) > 0;
  });
}

function buildNextStep(score, maxScore) {
  const priority = formatValue(answers[19]) || "определить главный приоритет";
  const result = formatValue(answers[20]) || "зафиксировать ожидаемый результат";
  const percent = maxScore ? score / maxScore : 0;

  if (percent <= 0.25) {
    return `Провести аудит текущих отчетов и сверить методику ДДС, ОПиУ и баланса. Приоритет: ${priority}. Результат: ${result}.`;
  }
  if (percent <= 0.5) {
    return `Начать с платежного календаря и ДДС, затем добавить ОПиУ и регулярный финансовый цикл. Приоритет: ${priority}. Результат: ${result}.`;
  }
  if (percent <= 0.75) {
    return `Собрать данные по банку, кассе, договорам, дебиторской и кредиторской задолженности, затем внедрить полный пакет отчетов. Приоритет: ${priority}. Результат: ${result}.`;
  }
  return `Сначала восстановить финансовую картину и задолженность, затем запустить платежный календарь, ДДС, ОПиУ, баланс и регламент контроля. Приоритет: ${priority}. Результат: ${result}.`;
}

function formatValue(value) {
  if (Array.isArray(value)) return value.length ? value.join(", ") : "данных нет";
  return value || "данных нет";
}

function scoreHint(question, score) {
  if (question.number === 15 && answers[4] === "1") return "не влияет на баллы";
  if (score === 0) return "риск не добавляется";
  if (score === 1) return "умеренный риск";
  return "высокий риск";
}
