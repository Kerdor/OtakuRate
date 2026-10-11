const CRITERIA = {
  anime: [
    ["Сюжет", "Логика событий, конфликты и связность истории."],
    ["Персонажи", "Характеры, мотивация и отношения."],
    ["Эмоции", "Насколько сильно произведение вызывает чувства."],
    ["Интерес", "Насколько хотелось продолжать просмотр."],
    ["Атмосфера", "Настроение и ощущение от происходящего."],
    ["Мир", "Устройство и убедительность мира."],
    ["Развитие", "Изменения героев и развитие истории."],
    ["Визуал", "Анимация, композиция и визуальный стиль."],
    ["Звук", "Музыка, озвучка и звуковое оформление."],
    ["Послевкусие", "Насколько произведение запомнилось после просмотра."]
  ],
  manga: [
    ["Сюжет", "Логика событий, конфликты и связность истории."],
    ["Персонажи", "Характеры, мотивация и отношения."],
    ["Эмоции", "Насколько сильно произведение вызывает чувства."],
    ["Интерес", "Насколько хотелось читать дальше."],
    ["Атмосфера", "Настроение и ощущение от происходящего."],
    ["Мир", "Устройство и убедительность мира."],
    ["Развитие", "Изменения героев и развитие истории."],
    ["Рисовка", "Стиль, выразительность и качество рисунка."],
    ["Подача страниц", "Панели, композиция и читаемость."],
    ["Послевкусие", "Насколько произведение запомнилось после чтения."]
  ]
};

const byId = (id) => document.getElementById(id);
let currentTitle = null;
let currentValues = {};

function storageKey(title) {
  return "rating:shikimori:" + title.mediaType + ":" + title.externalId;
}

function calculateOverall() {
  const values = Object.values(currentValues);
  if (!values.length) return "0,0";
  return (values.reduce((sum, value) => sum + Number(value), 0) / values.length).toFixed(1).replace(".", ",");
}

function renderCriteria(criteria) {
  const container = byId("criteria");
  container.replaceChildren();

  criteria.forEach(([name, help], index) => {
    const key = String(index);
    if (currentValues[key] === undefined) currentValues[key] = 0;

    const row = document.createElement("div");
    row.className = "criterion";

    const head = document.createElement("div");
    head.className = "criterion-head";

    const label = document.createElement("label");
    label.htmlFor = "score-" + key;
    label.textContent = name;

    const output = document.createElement("output");
    output.htmlFor = "score-" + key;
    output.textContent = currentValues[key];

    const slider = document.createElement("input");
    slider.type = "range";
    slider.min = "0";
    slider.max = "10";
    slider.step = "1";
    slider.id = "score-" + key;
    slider.value = currentValues[key];
    slider.setAttribute("aria-label", name + ", оценка от 0 до 10");
    slider.addEventListener("input", () => {
      currentValues[key] = Number(slider.value);
      output.textContent = slider.value;
      byId("overall").textContent = calculateOverall();
    });

    const helpText = document.createElement("p");
    helpText.className = "criterion-help";
    helpText.textContent = help;

    head.append(label, output);
    row.append(head, helpText, slider);
    container.append(row);
  });
  byId("overall").textContent = calculateOverall();
}

async function init() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab?.id || !tab.url) {
    byId("notOnTitle").classList.remove("hidden");
    return;
  }

  let tabUrl;
  try {
    tabUrl = new URL(tab.url);
  } catch {
    byId("notOnTitle").classList.remove("hidden");
    return;
  }

  if (!["shikimori.one", "www.shikimori.one", "shikimori.me", "www.shikimori.me", "shikimori.org", "www.shikimori.org", "shikimori.io", "www.shikimori.io"].includes(tabUrl.hostname)) {
    byId("notOnTitle").classList.remove("hidden");
    return;
  }

  // Request fresh data from the active page instead of relying only on stale storage.
  let currentShikimoriTitle = null;
  try {
    const response = await chrome.tabs.sendMessage(tab.id, { type: "OTAKURATE_GET_TITLE" });
    currentShikimoriTitle = response?.title || null;
  } catch {
    // The content script may not have run on a tab that was already open when the extension was installed.
  }

  if (!currentShikimoriTitle) {
    const stored = await chrome.storage.local.get("currentShikimoriTitle");
    const candidate = stored.currentShikimoriTitle;
    if (candidate?.url) {
      try {
        const candidateUrl = new URL(candidate.url);
        if (candidateUrl.origin === tabUrl.origin && candidateUrl.pathname === tabUrl.pathname) {
          currentShikimoriTitle = candidate;
        }
      } catch {
        // Ignore malformed stale storage.
      }
    }
  }

  if (!currentShikimoriTitle) {
    byId("notOnTitle").classList.remove("hidden");
    return;
  }

  currentTitle = currentShikimoriTitle;
  byId("ratingView").classList.remove("hidden");
  byId("title").textContent = currentTitle.title;
  byId("mediaType").textContent = currentTitle.mediaType === "anime" ? "Аниме" : "Манга / манхва";
  const countLabel = currentTitle.mediaType === "anime" ? "серий" : "глав";
  byId("details").textContent = [
    currentTitle.year,
    currentTitle.totalCount ? currentTitle.totalCount + " " + countLabel : null
  ].filter(Boolean).join(" · ") || "Дополнительные данные не найдены";
  byId("sourceLink").href = currentTitle.url;

  if (currentTitle.image) {
    byId("cover").src = currentTitle.image;
    byId("cover").classList.remove("hidden");
    byId("cover").addEventListener("error", () => byId("cover").classList.add("hidden"), { once: true });
  }

  const key = storageKey(currentTitle);
  const stored = await chrome.storage.local.get(key);
  const rating = stored[key];
  currentValues = rating?.values || {};
  byId("review").value = rating?.review || "";

  renderCriteria(CRITERIA[currentTitle.mediaType === "anime" ? "anime" : "manga"]);

  byId("save").addEventListener("click", async () => {
    await chrome.storage.local.set({
      [key]: {
        title: currentTitle,
        values: currentValues,
        review: byId("review").value.trim(),
        updatedAt: new Date().toISOString()
      }
    });
    byId("status").textContent = "Оценка сохранена на этом устройстве.";
  });
}

byId("openOptions").addEventListener("click", () => chrome.runtime.openOptionsPage());
init().catch(() => {
  byId("notOnTitle").classList.remove("hidden");
});
