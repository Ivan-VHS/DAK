(() => {
  "use strict";
  const $ = (selector, root = document) => root.querySelector(selector);
  const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];
  const records = [
    ["cockos","Cockos","∿","audio"],["kavun","Kavun","◒","creative"],["kabon","Ka-bon","₴","tools"],["gloverty","Gloverty","ϟ","tools"],
    ["po","Po","⌖","tools"],["illidia","Illidia","⌘","creative"],["unify","Unify","∞","system"],["sestem","Sestem","♟","system"],
    ["setupup","SetupUP","✳","system"],["orriganize","ORGze","▦","tools"],["abriganza","Abriganza","▤","tools"],["olaab","Olaab","◉","creative"],
    ["concrete-thump","Concrete Thump","◌","creative"],["seu-beu","Seu-Beu","◇","system"],["love-il","Love-IL","♡","creative"],["poi","Poi","✎","tools"],
    ["poi-2","Poi-2","⌑","tools"],["po-2","Po-2","⌖","tools"],["gamecharager","GameCharager","⌘","creative"],["exedotexe","EXEdotEXE","EX","system"],
    ["red-sparrow","Red Sparrow / 赤雀","雀","creative"],["mora-ai","Mora AI","✦","system"],["security","Sentinel","⬡","system"],["updates","Restore","↻","system"],
    ["runtime","Bridge","⇄","system"],["workspace","Control","⚙","system"],["provenance","Proof","✓","system"],["mora-boost","Mora Boost","↗","creative"],
    ["desktop","Duck Desktop","D","system"],["mora-commons","Mora Commons","▦","tools"],
    ["reaper","Reaper","R","ecosystem"],["pytyliki","Pytyliki","P","ecosystem"],["oplague","OPlague","O","ecosystem"],["ventusample","VentuSample","V","ecosystem"]
  ].map(([id,name,icon,category]) => ({id,name,icon,category}));
  const byId = new Map(records.map(app => [app.id, app]));
  const featured = ["cockos","kavun","kabon","gloverty","po","illidia","unify","orriganize"];
  const overlayIds = ["launcherPanel","quickPanel","notificationPanel","searchPanel"];
  const escapeHTML = value => String(value).replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
  const glyph = app => '<span class="app-glyph">' + escapeHTML(app.icon) + '</span>';
  let activeCategory = "all";
  let toastTimer = 0;
  let dragState = null;

  function toast(message) {
    const node = $("#toast");
    node.textContent = message;
    node.classList.add("show");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => node.classList.remove("show"), 2200);
  }

  function renderHome() {
    $("#featuredApps").innerHTML = featured.map(id => {
      const app = byId.get(id);
      return '<button class="app-card" data-app="' + id + '">' + glyph(app) +
        '<span class="app-card-copy"><strong>' + escapeHTML(app.name) +
        '</strong><small>' + escapeHTML(app.category.toUpperCase()) +
        '</small></span><span class="app-card-arrow">↗</span></button>';
    }).join("");
    $("#dockApps").innerHTML = ["cockos","poi","abriganza","reaper"].map(id => {
      const app = byId.get(id);
      return '<button data-app="' + id + '" title="' + escapeHTML(app.name) +
        '" aria-label="Открыть ' + escapeHTML(app.name) + '">' + glyph(app) + '</button>';
    }).join("");
  }

  function renderLauncher() {
    const query = $("#launcherSearch").value.trim().toLocaleLowerCase();
    const visible = records.filter(app =>
      (activeCategory === "all" || app.category === activeCategory) &&
      (!query || app.name.toLocaleLowerCase().includes(query))
    );
    $("#launcherGrid").innerHTML = visible.length
      ? visible.map(app => '<button class="launcher-app" data-app="' + app.id + '">' +
        glyph(app) + '<span>' + escapeHTML(app.name) + '</span></button>').join("")
      : '<div class="search-hint">Ничего не найдено</div>';
  }

  function closePanels() {
    overlayIds.forEach(id => {
      $("#" + id).classList.remove("open");
      $("#" + id).setAttribute("aria-hidden", "true");
    });
    $("#overlayBackdrop").classList.remove("visible");
  }

  function openPanel(id) {
    closePanels();
    const panel = $("#" + id);
    panel.classList.add("open");
    panel.setAttribute("aria-hidden", "false");
    $("#overlayBackdrop").classList.add("visible");
  }

  function openLauncher() {
    activeCategory = "all";
    $$("#launcherTabs button").forEach(button => button.classList.toggle("selected", button.dataset.category === "all"));
    $("#launcherSearch").value = "";
    renderLauncher();
    openPanel("launcherPanel");
    requestAnimationFrame(() => $("#launcherSearch").focus());
  }

  function searchGlobal() {
    $("#globalSearch").value = "";
    renderSearch("");
    openPanel("searchPanel");
    requestAnimationFrame(() => $("#globalSearch").focus());
  }

  function renderSearch(query) {
    const normalized = query.trim().toLocaleLowerCase();
    const matches = records.filter(app => app.name.toLocaleLowerCase().includes(normalized)).slice(0,8);
    $("#searchResults").innerHTML = matches.length
      ? matches.map(app => '<button class="search-result" data-app="' + app.id + '">' +
        glyph(app) + '<span><strong>' + escapeHTML(app.name) + '</strong><small>' +
        escapeHTML(app.category) + '</small></span></button>').join("")
      : '<div class="search-hint">Нет совпадений в локальном каталоге</div>';
  }

  function appBody(app) {
    if (app.id === "poi") {
      let note = "";
      try { note = localStorage.getItem("duckos.demo.poi") || ""; } catch {}
      return '<div class="window-hero"><div><h3>Личные заметки.</h3><p>Локальная рабочая область Poi. Черновик хранится в браузере этого устройства.</p></div><div class="window-hero-mark">✎</div></div>' +
        '<div class="window-section-title">ЧЕРНОВИК</div><textarea class="notes-area" id="noteText" placeholder="Запишите мысль…">' +
        escapeHTML(note) + '</textarea><div class="notes-toolbar"><span id="noteState">Локальный черновик</span><button class="note-save" id="saveNote">Сохранить локально</button></div>';
    }
    if (app.id === "abriganza") {
      return '<div class="window-hero"><div><h3>Файлы под контролем.</h3><p>Выберите файл вручную, чтобы показать его имя и размер. Никакого чтения каталога без разрешения.</p></div><div class="window-hero-mark">▤</div></div>' +
        '<button class="window-button" id="pickFile">Выбрать файл</button><input id="fileInput" type="file" hidden><p class="demo-note" id="fileMeta">Демо не извлекает архивы и не запускает исполняемые файлы.</p>';
    }
    const descriptions = {
      reaper: "Typed IR, Span, DABI64 и инструментальная цепочка языка Reaper.",
      pytyliki: "C11 core, CPU inspection и диагностический workbench.",
      oplague: "Read-only evidence, инвентаризация устройств и данные о драйверах.",
      ventusample: "Offline audio / DSP и библиотека звуковых модулей."
    };
    const isEcosystem = app.category === "ecosystem";
    return '<div class="window-hero"><div><h3>' + escapeHTML(app.name) + '.</h3><p>' +
      (descriptions[app.id] || "Рабочая область приложения " + app.name + " в локальной оболочке Mora. Это интерактивная демонстрационная поверхность.") +
      '</p></div><div class="window-hero-mark">' + escapeHTML(app.icon) + '</div></div>' +
      '<div class="window-section-title">СВЕДЕНИЯ О ПРИЛОЖЕНИИ</div><div class="window-info-grid">' +
      '<div class="window-info"><small>ПРИЛОЖЕНИЕ</small><strong>' + escapeHTML(app.name) + '</strong><p>Mora · ' + escapeHTML(app.category) + '</p></div>' +
      '<div class="window-info"><small>ТИП ИНТЕГРАЦИИ</small><strong>' + (isEcosystem ? "User-space workbench" : "HTML preview") + '</strong><p>Отдельный проект, не часть ядра ОС.</p></div>' +
      '<div class="window-info"><small>ИСТОЧНИК ДАННЫХ</small><strong>Локальная демонстрация</strong><p>Пример интерфейса без подключения к системным службам.</p></div>' +
      '<div class="window-info"><small>ИСПОЛНЕНИЕ</small><strong>Не запускается</strong><p>Не создаёт процессы, не устанавливает драйверы и не получает привилегии.</p></div></div>' +
      '<div class="window-callout">' + (isEcosystem
        ? "Workbenches остаются четырьмя самостоятельными user-space проектами с отдельными исходниками и лицензиями. Это окно показывает интеграцию интерфейса, а не выполнение их бинарных файлов."
        : "Это демонстрационная HTML-поверхность. Она не подключена к kernel compositor, системному IPC или реальному оборудованию.") + '</div>';
  }

  function openApp(id) {
    const app = byId.get(id);
    if (!app) return;
    closePanels();
    $("#windowTitle").textContent = app.name;
    $("#windowSubtitle").textContent = app.category.toUpperCase() + " · MORA WORKSPACE";
    $("#windowIcon").textContent = app.icon;
    $("#windowContent").innerHTML = appBody(app);
    $("#windowStatusText").textContent = app.category === "ecosystem" ? "USER-SPACE / NO EXECUTION" : "DEMO / LOCAL ONLY";
    const win = $("#appWindow");
    win.classList.remove("maximized");
    win.style.cssText = "";
    win.classList.add("open");
    win.setAttribute("aria-hidden","false");
  }

  function minimizeWindow() {
    const win = $("#appWindow");
    if (!win.classList.contains("open")) return;
    win.classList.remove("open");
    win.setAttribute("aria-hidden","true");
    toast("Окно свёрнуто — откройте приложение из панели или меню");
  }

  function closeWindow() {
    $("#appWindow").classList.remove("open","maximized");
    $("#appWindow").setAttribute("aria-hidden","true");
    $("#appWindow").style.cssText = "";
  }

  function updateClock() {
    const now = new Date();
    $("#topTime").textContent = new Intl.DateTimeFormat("uk-UA",{hour:"2-digit",minute:"2-digit"}).format(now);
    $("#topDate").textContent = new Intl.DateTimeFormat("ru-RU",{day:"2-digit",month:"2-digit",year:"numeric"}).format(now);
    const dateLine = new Intl.DateTimeFormat("ru-RU",{weekday:"long",day:"numeric",month:"long",year:"numeric"}).format(now);
    $("[data-i18n='today']").textContent = dateLine.toLocaleUpperCase("ru-RU");
  }

  renderHome();
  renderLauncher();
  updateClock();
  setInterval(updateClock,15000);

  document.addEventListener("click", event => {
    const appButton = event.target.closest("[data-app]");
    if (appButton) { openApp(appButton.dataset.app); return; }
    const viewButton = event.target.closest("[data-view]");
    if (viewButton) {
      if (viewButton.dataset.view === "apps") openLauncher();
      else { closePanels(); closeWindow(); $$(".nav-item").forEach(node => node.classList.toggle("active", node === viewButton)); }
      return;
    }
    const closer = event.target.closest("[data-close]");
    if (closer) { closePanels(); return; }
  });

  $("#brandButton").addEventListener("click",openLauncher);
  $("#dockLauncher").addEventListener("click",openLauncher);
  $("#openApps").addEventListener("click",openLauncher);
  $("#pinAdd").addEventListener("click",openLauncher);
  $("#searchTop").addEventListener("click",searchGlobal);
  $("#searchField").addEventListener("click",searchGlobal);
  $("#systemTray").addEventListener("click",() => openPanel("quickPanel"));
  $("#notifyTop").addEventListener("click",() => openPanel("notificationPanel"));
  $("#dockFiles").addEventListener("click",() => openApp("abriganza"));
  $("#dockSettings").addEventListener("click",() => openApp("workspace"));
  $("#ecosystemMore").addEventListener("click",() => openApp("mora-commons"));
  $("#focusMode").addEventListener("click",event => { event.currentTarget.classList.toggle("active"); toast("Режим фокуса переключён в preview"); });
  $("#windowClose").addEventListener("click",closeWindow);
  $("#windowMin").addEventListener("click",minimizeWindow);
  $("#windowMax").addEventListener("click",() => $("#appWindow").classList.toggle("maximized"));
  $("#overlayBackdrop").addEventListener("click",closePanels);
  $("#launcherSearch").addEventListener("input",renderLauncher);
  $("#launcherTabs").addEventListener("click",event => {
    const tab = event.target.closest("[data-category]");
    if (!tab) return;
    activeCategory = tab.dataset.category;
    $$("#launcherTabs button").forEach(button => button.classList.toggle("selected",button === tab));
    renderLauncher();
  });
  $("#globalSearch").addEventListener("input",event => renderSearch(event.target.value));
  $("#quickSettingsLink")?.addEventListener("click",() => openApp("workspace"));
  $("#brightnessRange").addEventListener("input",event => {
    $("#brightnessValue").textContent = event.target.value + "%";
    document.documentElement.style.setProperty("--demo-brightness",event.target.value / 100);
  });
  $$(".quick-tile").forEach(tile => tile.addEventListener("click",() => {
    tile.classList.toggle("selected");
    const state = tile.querySelector("small");
    if (state) state.textContent = tile.classList.contains("selected") ? "Активно в preview" : "Выключено в preview";
  }));
  $$(".workspace-dot").forEach(dot => dot.addEventListener("click",() => {
    $$(".workspace-dot").forEach(item => item.classList.toggle("active",item === dot));
    $("#workspaceLabel").textContent = "РАБОЧЕЕ ПРОСТРАНСТВО 0" + dot.dataset.workspace;
    toast("Открыто демонстрационное пространство " + dot.dataset.workspace);
  }));
  $("#demoNotification").addEventListener("click",() => {
    $(".notification-empty").innerHTML = '<span class="notification-bell">✓</span><strong>Пример уведомления</strong><p>Рабочее пространство Mora готово к демонстрации. Никакие системные службы не запускались.</p>';
  });
  $("#windowContent").addEventListener("click",event => {
    if (event.target.id === "saveNote") {
      try {
        localStorage.setItem("duckos.demo.poi",$("#noteText").value);
        $("#noteState").textContent = "Сохранено локально";
        toast("Черновик Poi сохранён в браузере");
      } catch { toast("Локальное хранилище недоступно"); }
    }
    if (event.target.id === "pickFile") $("#fileInput").click();
  });
  $("#windowContent").addEventListener("change",event => {
    if (event.target.id !== "fileInput") return;
    const file = event.target.files?.[0];
    $("#fileMeta").textContent = file ? file.name + " · " + file.size.toLocaleString("ru-RU") + " bytes" : "Файл не выбран";
  });
  $("#windowDrag").addEventListener("pointerdown",event => {
    if (event.target.closest(".window-controls") || $("#appWindow").classList.contains("maximized")) return;
    const rect = $("#appWindow").getBoundingClientRect();
    dragState = {x:event.clientX,y:event.clientY,left:rect.left,top:rect.top};
    event.currentTarget.setPointerCapture(event.pointerId);
  });
  $("#windowDrag").addEventListener("pointermove",event => {
    if (!dragState) return;
    const win = $("#appWindow");
    win.style.left = Math.max(8,Math.min(innerWidth - win.offsetWidth - 8,dragState.left + event.clientX - dragState.x)) + "px";
    win.style.top = Math.max(66,Math.min(innerHeight - 100,dragState.top + event.clientY - dragState.y)) + "px";
    win.style.transform = "none";
  });
  ["pointerup","pointercancel"].forEach(type => $("#windowDrag").addEventListener(type,() => { dragState = null; }));
  document.addEventListener("keydown",event => {
    if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k") { event.preventDefault(); searchGlobal(); }
    if (event.key === "Escape") { closePanels(); closeWindow(); }
    if (event.altKey && event.code === "Space") { event.preventDefault(); openLauncher(); }
  });
})();