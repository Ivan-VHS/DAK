export const SUPPORTED_LOCALES = ["ru", "uk", "en"];
export const LOCALE_STORAGE_KEY = "duckos.mora.locale.v1";

const translations = {
  "Рабочий стол": ["Рабочий стіл", "Desktop"],
  "Система": ["Система", "System"],
  "Приложения": ["Застосунки", "Applications"],
  "ВАШЕ ПРОСТРАНСТВО": ["ВАШ ПРОСТІР", "YOUR SPACE"],
  "Спокойный вечер начинается с порядка.": ["Спокійний вечір починається з порядку.", "A calm evening starts with a little order."],
  "Состояние системы": ["Стан системи", "System status"],
  "Открыть параметры системы": ["Відкрити параметри системи", "Open system settings"],
  "Открыть Duck Files": ["Відкрити Duck Files", "Open Duck Files"],
  "Файлы": ["Файли", "Files"],
  "Терминал": ["Термінал", "Terminal"],
  "Настройки": ["Налаштування", "Settings"],
  "Быстрые настройки": ["Швидкі налаштування", "Quick settings"],
  "Уведомления": ["Сповіщення", "Notifications"],
  "Рабочие пространства": ["Робочі простори", "Workspaces"],
  "Файлы и папки": ["Файли й папки", "Files and folders"],
  "Поиск файлов и папок": ["Пошук файлів і папок", "Search files and folders"],
  "Новая папка": ["Нова папка", "New folder"],
  "Загрузить": ["Завантажити", "Upload"],
  "Назад": ["Назад", "Back"],
  "Вперёд": ["Вперед", "Forward"],
  "Вверх": ["Вгору", "Up"],
  "Папка": ["Тека", "Folder"],
  "Имя": ["Назва", "Name"],
  "Дата": ["Дата", "Date"],
  "Размер": ["Розмір", "Size"],
  "Тип": ["Тип", "Type"],
  "Список": ["Список", "List"],
  "Сетка": ["Сітка", "Grid"],
  "Открыть": ["Відкрити", "Open"],
  "Переименовать": ["Перейменувати", "Rename"],
  "Удалить": ["Видалити", "Delete"],
  "Скачать": ["Завантажити", "Download"],
  "Предпросмотр": ["Попередній перегляд", "Preview"],
  "Содержимое": ["Вміст", "Contents"],
  "Этот файл пуст.": ["Цей файл порожній.", "This file is empty."],
  "Виртуальное пространство Duck Files хранится в профиле браузера. Оно не является доступом к диску или настоящей файловой системе DuckOS.": [
    "Віртуальний простір Duck Files зберігається у профілі браузера. Це не доступ до диска чи справжньої файлової системи DuckOS.",
    "Duck Files is stored in this browser profile. It is not access to a host drive or the native DuckOS filesystem."
  ],
  "Загрузите файл, чтобы добавить его в локальное пространство.": [
    "Завантажте файл, щоб додати його до локального простору.",
    "Upload a file to add it to this local workspace."
  ],
  "Команда не найдена. Введите help.": ["Команду не знайдено. Введіть help.", "Command not found. Type help."],
  "Язык интерфейса": ["Мова інтерфейсу", "Interface language"],
  "Русский": ["Російська", "Russian"],
  "Українська": ["Українська", "Ukrainian"],
  "English": ["Англійська", "English"],
  "Движение интерфейса": ["Рух інтерфейсу", "Interface motion"],
  "Уменьшить анимацию": ["Зменшити анімацію", "Reduce motion"],
  "Акцент": ["Акцент", "Accent"],
  "Жёлтый Duck": ["Жовтий Duck", "Duck yellow"],
  "Тёмный графит": ["Темний графіт", "Dark graphite"],
  "Только локальные настройки оболочки. Системные службы и оборудование браузеру не управляются.": [
    "Лише локальні налаштування оболонки. Браузер не керує системними службами й обладнанням.",
    "Shell-only settings. Browser code does not control native services or hardware."
  ],
  "Только интерфейсный индикатор": ["Лише індикатор інтерфейсу", "Interface indicator only"],
  "Состояние": ["Стан", "Status"],
  "Подключено": ["Підключено", "Connected"],
  "Отключено": ["Відключено", "Disconnected"],
  "Очистить": ["Очистити", "Clear"],
  "Отметить прочитанным": ["Позначити прочитаним", "Mark as read"],
  "Симуляция, не телеметрия ядра": ["Симуляція, не телеметрія ядра", "Simulation, not kernel telemetry"],
  "Загрузка CPU": ["Завантаження CPU", "CPU load"],
  "Память": ["Пам’ять", "Memory"],
  "Диск": ["Диск", "Disk"],
  "Демо": ["Демо", "Demo"],
  "Закрыть": ["Закрити", "Close"],
  "Свернуть": ["Згорнути", "Minimize"],
  "Развернуть": ["Розгорнути", "Maximize"],
  "Восстановить": ["Відновити", "Restore"],
  "Сохранить": ["Зберегти", "Save"],
  "Отмена": ["Скасувати", "Cancel"],
  "Не удалось сохранить настройки в профиле браузера.": ["Не вдалося зберегти налаштування у профілі браузера.", "Could not save settings in this browser profile."],
  "Папка не найдена.": ["Теку не знайдено.", "Folder not found."],
  "Нет элементов в этой папке.": ["У цій теці немає елементів.", "This folder is empty."],
  "Выберите файл для просмотра.": ["Виберіть файл для перегляду.", "Select a file to preview."],
  "Локальная оболочка DuckOS": ["Локальна оболонка DuckOS", "DuckOS local shell"],
  "Доступ к настоящему терминалу не подключён. Команды выполняются только в виртуальном пространстве Mora.": [
    "Доступ до справжнього термінала не підключено. Команди виконуються лише у віртуальному просторі Mora.",
    "A native terminal is not connected. Commands run only inside Mora's virtual workspace."
  ],
  "Помощь": ["Довідка", "Help"],
  "Команда": ["Команда", "Command"],
  "Папка создана.": ["Теку створено.", "Folder created."],
  "Файл добавлен в виртуальное пространство.": ["Файл додано до віртуального простору.", "File added to the virtual workspace."],
  "Изменения сохранены локально.": ["Зміни збережено локально.", "Changes saved locally."],
  "Сначала откройте Duck Files.": ["Спочатку відкрийте Duck Files.", "Open Duck Files first."]
};


Object.assign(translations, {
  "Mora — DuckOS": ["Mora — DuckOS", "Mora — DuckOS"],
  "ПОНЕДЕЛЬНИК · РАБОЧЕЕ ПРОСТРАНСТВО": ["ПОНЕДІЛОК · РОБОЧИЙ ПРОСТІР", "MONDAY · WORKSPACE"],
  "Пространства": ["Простори", "Spaces"],
  "+ Новая папка": ["+ Нова тека", "+ New folder"],
  "Новый файл": ["Новий файл", "New file"],
  "Сортировка": ["Сортування", "Sort by"],
  "Показать список": ["Показати список", "Show list"],
  "Показать сетку": ["Показати сітку", "Show grid"],
  "Ничего не найдено.": ["Нічого не знайдено.", "No matches found."],
  "Папка содержит ": ["Тека містить ", "Folder contains "],
  "Папка · ": ["Тека · ", "Folder · "],
  "Файл добавлен в виртуальное пространство.": ["Файл додано до віртуального простору.", "File added to the virtual workspace."],
  "Готово · локальное виртуальное пространство": ["Готово · локальний віртуальний простір", "Ready · local virtual workspace"],
  "Локальное виртуальное пространство": ["Локальний віртуальний простір", "Local virtual workspace"],
  "Текстовые файлы ограничены 2 MiB.": ["Текстові файли обмежені 2 MiB.", "Text files are limited to 2 MiB."],
  "Загрузить файл": ["Завантажити файл", "Upload file"],
  "Имя новой папки": ["Назва нової теки", "New folder name"],
  "Новое имя": ["Нова назва", "New name"],
  "Удалить «": ["Видалити «", "Delete “"],
  "» из виртуального пространства?": ["» із віртуального простору?", "” from the virtual workspace?"],
  "Удалено из локального пространства.": ["Видалено з локального простору.", "Removed from the local workspace."],
  "Выбран файл: ": ["Вибрано файл: ", "Selected file: "],
  "Файл не найден.": ["Файл не знайдено.", "File not found."],
  "Файл не выбран.": ["Файл не вибрано.", "No file selected."],
  "Выберите файл для просмотра.": ["Виберіть файл для перегляду.", "Select a file to preview."],
  "Папка создана.": ["Теку створено.", "Folder created."],
  "Команда не найдена. Введите help.": ["Команду не знайдено. Введіть help.", "Command not found. Type help."],
  "Ошибка": ["Помилка", "Error"],
  "Включено": ["Увімкнено", "On"],
  "Выключено": ["Вимкнено", "Off"],
  "Открыть папку": ["Відкрити теку", "Open folder"],
  "Только для чтения": ["Лише для читання", "Read-only"],
  "Локальный индикатор": ["Локальний індикатор", "Local indicator"],
  "Mora запущена": ["Mora запущена", "Mora is ready"],
  "Рабочая оболочка готова. Файловые и системные действия ограничены браузерным профилем.": [
    "Робоча оболонка готова. Файлові й системні дії обмежені профілем браузера.",
    "The shell is ready. File and system actions are limited to the browser profile."
  ],
  "Sentinel активен": ["Sentinel активний", "Sentinel is active"],
  "Профиль разрешений действует как настройка интерфейса и не заменяет нативный брокер доступа.": [
    "Профіль дозволів є налаштуванням інтерфейсу й не замінює нативний брокер доступу.",
    "The permission profile is a UI preference and does not replace a native capability broker."
  ],
  "Новых уведомлений нет.": ["Нових сповіщень немає.", "No notifications."],
  "Прочитать всё": ["Прочитати все", "Mark all read"],
  "Очистить": ["Очистити", "Clear"],
  "Новое": ["Нове", "New"],
  "Прочитано": ["Прочитано", "Read"],
  "Режим фокуса оболочки обновлён.": ["Режим фокусування оболонки оновлено.", "Shell focus mode updated."],
  "Изменён локальный индикатор ": ["Змінено локальний індикатор ", "Local indicator changed: "],
  ". Нативное устройство не переключалось.": [". Нативний пристрій не перемикався.", ". No native device was toggled."],
  "Язык интерфейса изменён.": ["Мову інтерфейсу змінено.", "Interface language changed."],
  "Не удалось сохранить состояние настройки.": ["Не вдалося зберегти стан налаштування.", "Could not save the setup state."],
  "Настройка Mora завершена и сохранена в профиле браузера.": ["Налаштування Mora завершено й збережено у профілі браузера.", "Mora setup is complete and saved in this browser profile."],
  "Первичная настройка Mora завершена": ["Початкове налаштування Mora завершено", "Mora setup completed"],
  "Сохранено локально": ["Збережено локально", "Saved locally"],
  "Команды выполняются только внутри виртуального пространства Mora.": [
    "Команди виконуються лише у віртуальному просторі Mora.",
    "Commands run only inside Mora's virtual workspace."
  ],
  "Доступ к настоящему терминалу не подключён.": [
    "Доступ до справжнього термінала не підключено.",
    "A native terminal is not connected."
  ],
  "Команды доступны только для виртуального пространства.": [
    "Команди доступні лише для віртуального простору.",
    "Commands are limited to the virtual workspace."
  ],
  "Симуляция, не телеметрия ядра": ["Симуляція, не телеметрія ядра", "Simulation, not kernel telemetry"],
  "Открыть Duck Files": ["Відкрити Duck Files", "Open Duck Files"],
  "Быстрые настройки": ["Швидкі налаштування", "Quick settings"],
  "Уведомления": ["Сповіщення", "Notifications"],
  "Файлы": ["Файли", "Files"],
  "Терминал": ["Термінал", "Terminal"],
  "Настройки": ["Налаштування", "Settings"],
  "Завершить настройку": ["Завершити налаштування", "Finish setup"],
  "Профиль ресурсов": ["Профіль ресурсів", "Resource profile"],
  "Рабочая среда Mora": ["Робоче середовище Mora", "Mora workspace"],
  "Профиль оболочки": ["Профіль оболонки", "Shell profile"],
  "Единая палитра DuckOS": ["Єдина палітра DuckOS", "Single DuckOS palette"],
  "Темп": ["Темп", "Tempo"],
  "Сохранить профиль": ["Зберегти профіль", "Save profile"],
  "Прочитать всё": ["Прочитати все", "Mark all read"],
  "Проверка списка": ["Перевірка списку", "Review checklist"],
  "Запись остановлена": ["Запис зупинено", "Recording stopped"],
  "Проверка ещё не запускалась.": ["Перевірку ще не запускали.", "Review has not started."],
  "Настройка ещё не завершена.": ["Налаштування ще не завершено.", "Setup is not complete."]
});

export function detectLocale(savedLocale, browserLanguage = globalThis.navigator?.language ?? "ru") {
  if (SUPPORTED_LOCALES.includes(savedLocale)) return savedLocale;
  const language = String(browserLanguage).toLowerCase();
  if (language.startsWith("uk")) return "uk";
  if (language.startsWith("en")) return "en";
  return "ru";
}

export function translateText(value, locale = "ru") {
  const text = String(value ?? "");
  if (!SUPPORTED_LOCALES.includes(locale)) return text;
  const index = locale === "uk" ? 0 : locale === "en" ? 1 : -1;
  for (const [original, variants] of Object.entries(translations)) {
    if (text === original || text === variants[0] || text === variants[1]) {
      return index < 0 ? original : (variants[index] ?? original);
    }
  }
  return text;
}

export function applyTranslations(root, locale = "ru") {
  if (!root || !SUPPORTED_LOCALES.includes(locale)) return;
  const doc = root.nodeType === 9 ? root : root.ownerDocument;
  const view = doc?.defaultView;
  const nodeFilter = view?.NodeFilter;
  if (nodeFilter) {
    const walker = doc.createTreeWalker(root, nodeFilter.SHOW_TEXT, {
      acceptNode(node) {
        const parent = node.parentElement;
        if (!parent || parent.closest("script,style,textarea,code,pre,[data-user-content]")) {
          return nodeFilter.FILTER_REJECT;
        }
        return nodeFilter.FILTER_ACCEPT;
      }
    });
    let node;
    while ((node = walker.nextNode())) {
      const raw = node.nodeValue ?? "";
      const trimmed = raw.trim();
      if (!trimmed) continue;
      const next = translateText(trimmed, locale);
      if (next !== trimmed) node.nodeValue = raw.replace(trimmed, next);
    }
  }

  if (root.querySelectorAll) {
    root.querySelectorAll("[aria-label],[placeholder],[title]").forEach((element) => {
      for (const attribute of ["aria-label", "placeholder", "title"]) {
        if (!element.hasAttribute(attribute)) continue;
        const value = element.getAttribute(attribute);
        const next = translateText(value, locale);
        if (next !== value) element.setAttribute(attribute, next);
      }
    });
  }

  if (doc?.documentElement) doc.documentElement.lang = locale;
  if (doc) doc.title = translateText("Mora — DuckOS", locale);
}
