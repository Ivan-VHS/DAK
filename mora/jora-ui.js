import { JORA_PARAMETER_REGISTRY, buildJoraPackage } from "./jora-core.js";

export function joraPanelMarkup() {
  return [
    '<p class="window-kicker">JORA · APP SYNTHESIS STUDIO</p>',
    '<h2 class="window-heading">Соберите приложение из формулы</h2>',
    '<p class="jora-intro">Комбинируйте возможности, получите имя, интеграционный граф и Reaper-first план. Проект создаётся локально; панель не устанавливает и не запускает программы.</p>',
    '<form class="jora-form" data-jora-form>',
    '<label for="jora-formula">Формула приложения</label>',
    '<textarea id="jora-formula" data-jora-formula rows="3" maxlength="2048">текстовый редактор + аудиоредактор + переводчик</textarea>',
    '<div class="jora-presets">',
    '<button type="button" data-jora-preset="текстовый редактор + аудиоредактор + переводчик">Текст + звук + перевод</button>',
    '<button type="button" data-jora-preset="заметки + доска задач + календарь">Рабочее пространство</button>',
    '<button type="button" data-jora-preset="текстовый редактор + субтитры + переводчик">Локализация видео</button>',
    '</div><div class="jora-form-actions"><button class="action-button" type="submit">Синтезировать проект</button><button class="subtle-button" type="button" data-jora-save disabled>Сохранить формулу</button></div></form>',
    '<div class="jora-status" data-jora-status role="status" aria-live="polite">Реестр содержит ',
    String(JORA_PARAMETER_REGISTRY.length),
    ' базовых возможностей.</div>',
    '<div class="jora-saved-row"><label for="jora-drafts">Мои формулы</label><select id="jora-drafts" data-jora-drafts><option value="">Нет сохранённых формул</option></select></div>',
    '<section class="jora-results" data-jora-results hidden>',
    '<div class="jora-product-heading"><div><span class="eyebrow">НОВОЕ ПРИЛОЖЕНИЕ</span><h3 data-jora-name></h3></div><span class="jora-state">SOURCE DRAFT</span></div>',
    '<p class="jora-tagline" data-jora-tagline></p>',
    '<div class="jora-block"><span class="eyebrow">КАНОНИЧЕСКАЯ ФОРМУЛА</span><p data-jora-canonical></p></div>',
    '<div class="jora-two-columns"><div class="jora-block"><span class="eyebrow">ЯЗЫКОВОЙ СТЕК</span><ul data-jora-languages></ul></div><div class="jora-block"><span class="eyebrow">ИНТЕГРАЦИОННЫЙ ГРАФ</span><p data-jora-graph-summary></p><pre data-jora-graph></pre></div></div>',
    '<div class="jora-block"><span class="eyebrow">ДЕМО-НАПОЛНЕНИЕ</span><p data-jora-content></p></div>',
    '<div class="jora-block"><span class="eyebrow">REAPER · SOURCE PREVIEW</span><pre data-jora-source></pre></div>',
    '<div class="jora-export-actions"><button class="action-button" type="button" data-jora-export="manifest">Скачать манифест</button><button class="subtle-button" type="button" data-jora-export="reaper">Скачать .rpr</button></div>',
    '<p class="jora-footnote">Полный ZIP с SHA-256 создаётся командой duckos jora create. Reaper static-check выполняется при валидации. Установка и исполнение не выполняются.</p></section>'
  ].join("");
}

function downloadFile(filename, content, mimeType) {
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.hidden = true;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  window.setTimeout(() => URL.revokeObjectURL(url), 1000);
}

export function initializeJoraPanel(appWindow) {
  const form = appWindow.querySelector("[data-jora-form]");
  const input = appWindow.querySelector("[data-jora-formula]");
  const status = appWindow.querySelector("[data-jora-status]");
  const results = appWindow.querySelector("[data-jora-results]");
  const saveButton = appWindow.querySelector("[data-jora-save]");
  const draftsSelect = appWindow.querySelector("[data-jora-drafts]");
  const storageKey = "mora.jora.drafts.v1";
  let current = null;

  function loadDrafts() {
    try {
      const data = JSON.parse(localStorage.getItem(storageKey) || "[]");
      return Array.isArray(data) ? data.filter((item) =>
        item && typeof item.formula === "string" && item.formula.length <= 2048
      ).slice(0, 50) : [];
    } catch {
      return [];
    }
  }

  function renderDrafts() {
    const drafts = loadDrafts();
    draftsSelect.replaceChildren();
    const empty = document.createElement("option");
    empty.value = "";
    empty.textContent = drafts.length ? "Выберите сохранённую формулу" : "Нет сохранённых формул";
    draftsSelect.appendChild(empty);
    drafts.forEach((item, index) => {
      const option = document.createElement("option");
      option.value = String(index);
      option.textContent = item.name || item.formula;
      draftsSelect.appendChild(option);
    });
  }

  function render() {
    try {
      current = buildJoraPackage(input.value);
      appWindow.querySelector("[data-jora-name]").textContent = current.displayName;
      appWindow.querySelector("[data-jora-tagline]").textContent = current.tagline;
      appWindow.querySelector("[data-jora-canonical]").textContent = current.canonicalFormula;
      appWindow.querySelector("[data-jora-graph-summary]").textContent =
        current.graph.nodes.length + " узлов · " + current.graph.edges.length + " связей · " + current.graph.topology;
      appWindow.querySelector("[data-jora-graph]").textContent = JSON.stringify({
        topology: current.graph.topology,
        componentCount: current.graph.componentCount,
        clusters: current.graph.clusters,
        growthPolicy: current.graph.growthPolicy
      }, null, 2);

      const list = appWindow.querySelector("[data-jora-languages]");
      list.replaceChildren();
      current.languages.forEach((language) => {
        const item = document.createElement("li");
        const strong = document.createElement("strong");
        strong.textContent = language.name;
        const detail = document.createElement("span");
        detail.textContent = " — " + language.reason;
        item.append(strong, detail);
        list.appendChild(item);
      });

      appWindow.querySelector("[data-jora-content]").textContent =
        current.demo.segments.length + " связанных демо-сегмента; " +
        current.demo.glossary.length + " терминов глоссария. Реальные аудиофайлы не генерируются.";
      appWindow.querySelector("[data-jora-source]").textContent = current.reaperSource;
      results.hidden = false;
      saveButton.disabled = false;
      status.textContent = "Формула распознана: " + current.components.length +
        " компонента(ов). Черновик построен; сборка и установка не запускались.";
      return true;
    } catch (error) {
      current = null;
      results.hidden = true;
      saveButton.disabled = true;
      status.textContent = error.message || "Не удалось разобрать формулу.";
      return false;
    }
  }

  form.addEventListener("submit", (event) => { event.preventDefault(); render(); });
  appWindow.querySelectorAll("[data-jora-preset]").forEach((button) => {
    button.addEventListener("click", () => { input.value = button.dataset.joraPreset; render(); });
  });

  saveButton.addEventListener("click", () => {
    if (!current) return;
    const drafts = loadDrafts();
    const record = { formula: input.value.trim(), name: current.displayName, updatedAt: new Date().toISOString() };
    const previous = drafts.findIndex((item) => item.formula === record.formula);
    if (previous >= 0) drafts.splice(previous, 1);
    drafts.unshift(record);
    try {
      localStorage.setItem(storageKey, JSON.stringify(drafts.slice(0, 50)));
      renderDrafts();
      status.textContent = "Формула сохранена локально в профиле Mora.";
    } catch {
      status.textContent = "Локальное хранилище недоступно.";
    }
  });

  draftsSelect.addEventListener("change", () => {
    if (!draftsSelect.value) return;
    const draft = loadDrafts()[Number(draftsSelect.value)];
    if (draft) { input.value = draft.formula; render(); }
  });

  appWindow.querySelectorAll("[data-jora-export]").forEach((button) => {
    button.addEventListener("click", () => {
      if (!current) return;
      if (button.dataset.joraExport === "manifest") {
        downloadFile(current.slug + ".jora.json", JSON.stringify(current.manifest, null, 2) + String.fromCharCode(10), "application/json;charset=utf-8");
      } else if (button.dataset.joraExport === "reaper") {
        downloadFile("main.rpr", current.reaperSource, "text/plain;charset=utf-8");
      }
    });
  });

  renderDrafts();
  render();
}
