(() => {
  const shell = document.getElementById('shell');
  const appDialog = document.getElementById('appDialog');
  const commandDialog = document.getElementById('commandDialog');
  const toast = document.getElementById('toast');
  const commandInput = document.getElementById('commandInput');
  const commandResults = document.getElementById('commandResults');
  let toastTimer;

  const appDetails = {
    'Обзор': 'Сводка рабочего пространства DuckOS.',
    'Файлы': 'Локальные пространства, документы и недавние файлы.',
    'Приложения': 'Каталог приложений федерации Ivan-VHS.',
    'Система': 'Системные метрики, диагностика и пользовательские инструменты DuckOS.',
    'Настройки': 'Внешний вид, доступность и поведение оболочки.',
    'Pytyliki': 'Процессорная рабочая станция: CPU, память и ограниченные измерения.',
    'Reaper': 'Язык программирования, reference runtime и локальная Studio.',
    'OPlague': 'Read-only инвентаризация устройств и проверка метаданных драйверов.',
    'VentuSample': 'Генерация сэмплов и офлайн-обработка аудио.',
    'Cockos': 'Системный граф аудио: обнаружение портов PipeWire и безопасное соединение потоков.',
    'Kavun': 'Планировщик тайловых, сеточных и плавающих геометрий окон.',
    'Ka-bon': 'Контекстные сочетания клавиш и маршрутизация разрешённых действий.',
    'Gloverty': 'Семантические палитры и аудит контрастности интерфейса.',
    'Po': 'Поиск зарегистрированных системных команд без выполнения произвольной shell-строки.',
    'Illidia': 'Контрольные точки настроек и рабочего пространства с проверкой целостности.',
    'Unify': 'Профили, общая конфигурация и событийная шина пользовательских служб.',
    'Профиль': 'Локальная учётная запись и настройки пользовательской сессии.',
    'Проект DuckOS': 'Архитектура и пользовательская оболочка DuckOS.'
  };

  const coreServiceApps = new Set(['Cockos', 'Kavun', 'Ka-bon', 'Gloverty', 'Po', 'Illidia', 'Unify']);

  function showToast(message) {
    toast.textContent = message;
    toast.classList.add('visible');
    window.clearTimeout(toastTimer);
    toastTimer = window.setTimeout(() => toast.classList.remove('visible'), 2600);
  }

  function openApp(name, description) {
    if (name === 'Обзор') {
      showToast('Вы уже на главном экране DuckOS.');
      return;
    }

    const details = description || appDetails[name] || 'Локальное приложение DuckOS.';
    document.getElementById('dialogTitle').textContent = name;
    document.getElementById('dialogSubtitle').textContent = coreServiceApps.has(name)
      ? 'DuckOS Core Services · пользовательский прототип'
      : 'Приложение DuckOS';
    document.getElementById('dialogHeading').textContent = name;
    document.getElementById('dialogDescription').textContent = details;
    if (typeof appDialog.showModal === 'function' && !appDialog.open) appDialog.showModal();

    document.querySelectorAll('.nav-item').forEach((item) => {
      item.classList.toggle('active', item.dataset.app === name);
    });
    document.querySelectorAll('.dock-app').forEach((item) => {
      item.classList.toggle('selected', item.dataset.app === name);
    });
  }

  function openSearch() {
    if (typeof commandDialog.showModal === 'function' && !commandDialog.open) {
      commandDialog.showModal();
      commandInput.value = '';
      filterCommands('');
      window.setTimeout(() => commandInput.focus(), 40);
    }
  }

  function filterCommands(query) {
    const term = query.trim().toLocaleLowerCase();
    commandResults.querySelectorAll('button').forEach((button) => {
      const haystack = (button.dataset.app || '') + ' ' +
        (button.dataset.description || '') + ' ' + button.textContent;
      button.hidden = !haystack.toLocaleLowerCase().includes(term);
    });
  }

  document.addEventListener('click', (event) => {
    const appButton = event.target.closest('[data-app]');
    if (!appButton || appButton.closest('#commandResults')) return;
    event.preventDefault();
    openApp(appButton.dataset.app, appButton.dataset.description);
    if (commandDialog.open) commandDialog.close();
  });

  document.getElementById('searchTrigger').addEventListener('click', openSearch);
  document.getElementById('dockSearch').addEventListener('click', openSearch);
  commandInput.addEventListener('input', () => filterCommands(commandInput.value));

  commandResults.addEventListener('click', (event) => {
    const button = event.target.closest('button[data-app]');
    if (!button) return;
    openApp(button.dataset.app, button.dataset.description);
    if (commandDialog.open) commandDialog.close();
  });

  document.addEventListener('keydown', (event) => {
    if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'k') {
      event.preventDefault();
      openSearch();
    }
  });

  function setTheme(theme) {
    shell.dataset.theme = theme;
    const darkEnabled = theme === 'dark';
    document.querySelectorAll('[data-toggle="dark"]').forEach((button) => {
      button.classList.toggle('selected', darkEnabled);
      button.setAttribute('aria-pressed', String(darkEnabled));
      const note = button.querySelector('small');
      if (note) note.textContent = darkEnabled ? 'Midnight blue' : 'Светлая тема';
    });
  }

  document.getElementById('themeToggle').addEventListener('click', () => {
    setTheme(shell.dataset.theme === 'dark' ? 'light' : 'dark');
    showToast(shell.dataset.theme === 'dark' ? 'Тёмная тема включена.' : 'Светлая тема включена.');
  });

  document.querySelectorAll('[data-toggle]').forEach((button) => {
    button.addEventListener('click', () => {
      const setting = button.dataset.toggle;
      const enabled = button.getAttribute('aria-pressed') !== 'true';

      if (setting === 'dark') {
        setTheme(enabled ? 'dark' : 'light');
      } else if (setting === 'motion') {
        shell.dataset.reducedMotion = String(enabled);
        button.classList.toggle('selected', enabled);
        button.setAttribute('aria-pressed', String(enabled));
        showToast(enabled ? 'Уменьшение анимации включено.' : 'Обычная анимация включена.');
      } else {
        button.classList.toggle('selected', enabled);
        button.setAttribute('aria-pressed', String(enabled));
        const note = button.querySelector('small');
        if (note) {
          const label = setting === 'wifi' ? 'Wi-Fi' : 'Bluetooth';
          note.textContent = enabled ? 'Включён' : 'Выключен';
          showToast(label + ': ' + (enabled ? 'включён' : 'выключен') + ' в демонстрации.');
        }
      }
    });
  });

  document.getElementById('brightness').addEventListener('input', (event) => {
    document.getElementById('brightnessValue').textContent = event.target.value + '%';
  });

  document.getElementById('dialogClose').addEventListener('click', () => appDialog.close());
  document.getElementById('dialogOk').addEventListener('click', () => appDialog.close());
  appDialog.addEventListener('click', (event) => {
    if (event.target === appDialog) appDialog.close();
  });

  document.getElementById('notificationsTrigger').addEventListener('click', () => {
    const panel = document.getElementById('notificationsPanel');
    panel.scrollIntoView({ behavior: shell.dataset.reducedMotion === 'true' ? 'auto' : 'smooth', block: 'center' });
    panel.classList.add('notification-focus');
    window.setTimeout(() => panel.classList.remove('notification-focus'), 850);
  });

  document.getElementById('clearNotifications').addEventListener('click', () => {
    const list = document.querySelector('.notification-list');
    list.innerHTML = '<div class="empty-notices"><span>✓</span><strong>Всё просмотрено</strong><small>Новых уведомлений нет</small></div>';
    showToast('Уведомления очищены в этой сессии.');
  });

  function updateClock() {
    const now = new Date();
    document.getElementById('clock').textContent = new Intl.DateTimeFormat('ru-RU', {
      hour: '2-digit',
      minute: '2-digit'
    }).format(now);
  }

  updateClock();
  window.setInterval(updateClock, 15000);
  filterCommands('');
})();
