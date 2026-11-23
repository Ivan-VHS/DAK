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
  "Русский": ["Українська", "Russian"],
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

export function detectLocale(savedLocale, browserLanguage = globalThis.navigator?.language ?? "ru") {
  if (SUPPORTED_LOCALES.includes(savedLocale)) return savedLocale;
  const language = String(browserLanguage).toLowerCase();
  if (language.startsWith("uk")) return "uk";
  if (language.startsWith("en")) return "en";
  return "ru";
}

export function translateText(value, locale = "ru") {
  const text = String(value ?? "");
  if (locale === "ru" || !SUPPORTED_LOCALES.includes(locale)) return text;
  const translated = translations[text];
  if (!translated) return text;
  return translated[locale === "uk" ? 0 : 1] ?? text;
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
