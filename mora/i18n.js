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
  "Настройка ещё не завершена.": ["Налаштування ще не завершено.", "Setup is not complete."],
  "Звук и запись": ["Звук і запис", "Audio and recording"],
  "Фотографии": ["Фотографії", "Photos"],
  "Финансы": ["Фінанси", "Finance"],
  "Сценарии": ["Сценарії", "Automations"],
  "Компас": ["Компас", "Compass"],
  "Игры": ["Ігри", "Games"],
  "Устройства": ["Пристрої", "Devices"],
  "Статус системы": ["Стан системи", "System status"],
  "Первичная настройка": ["Початкове налаштування", "First-run setup"],
  "Задачи и проекты": ["Завдання й проєкти", "Tasks and projects"],
  "Архивы и файлы": ["Архіви й файли", "Archives and files"],
  "Медиатека": ["Медіатека", "Media library"],
  "Ритм и темп": ["Ритм і темп", "Rhythm and tempo"],
  "Проверка обмена": ["Перевірка передавання", "Transfer review"],
  "Личный дневник": ["Особистий щоденник", "Personal journal"],
  "Быстрые заметки": ["Швидкі нотатки", "Quick notes"],
  "База знаний": ["База знань", "Knowledge base"],
  "Маршруты и точки": ["Маршрути й точки", "Routes and places"],
  "Игровая библиотека": ["Ігрова бібліотека", "Game library"],
  "EXE-инспектор": ["EXE-інспектор", "EXE inspector"],
  "Намерения и планы": ["Наміри й плани", "Intentions and plans"],
  "Права и доверие": ["Дозволи й довіра", "Permissions and trust"],
  "Обновления и откат": ["Оновлення й відкат", "Updates and rollback"],
  "Среда и питание": ["Середовище й живлення", "Workspace and power"],
  "Файлы и SHA-256": ["Файли й SHA-256", "Files and SHA-256"],
  "Игровая производительность": ["Ігрова продуктивність", "Gaming performance"],
  "Оптимизация рабочего пространства": ["Оптимізація робочого простору", "Workspace optimization"],
  "Единый центр приложений": ["Єдиний центр застосунків", "Unified app catalogue"],
  "Разрешено в профиле": ["Дозволено в профілі", "Allowed in profile"],
  "Запрещено": ["Заборонено", "Blocked"],
  "Точка восстановления оболочки ещё не создана.": ["Точку відновлення оболонки ще не створено.", "No shell recovery point has been created."],
  "Последняя точка оболочки:": ["Остання точка оболонки:", "Last shell recovery point:"],
  "Сохранённая точка повреждена или имеет неизвестную версию.": ["Збережена точка пошкоджена або має невідому версію.", "The saved snapshot is damaged or has an unknown version."],
  "Хранилище браузера недоступно.": ["Сховище браузера недоступне.", "Browser storage is unavailable."],
  "План не подготовлен.": ["План не підготовлено.", "No plan has been prepared."],
  "Подтверждённые локальные настройки применены.": ["Підтверджені локальні налаштування застосовано.", "Approved local settings were applied."],
  "План Mora выполнен": ["План Mora виконано", "Mora plan completed"],
  "Пока пусто. Записи сохраняются только в этом профиле Mora.": ["Поки що порожньо. Записи зберігаються лише в цьому профілі Mora.", "Nothing here yet. Entries stay in this Mora profile."],
  "Записи доступны только в текущем профиле браузера.": ["Записи доступні лише в поточному профілі браузера.", "Entries are available only in this browser profile."],
  "Состояние DuckOS": ["Стан DuckOS", "DuckOS status"],
  "Браузерная оболочка · активна": ["Браузерна оболонка · активна", "Browser shell · active"],
  "Нативный загрузочный образ ещё не готов": ["Нативний завантажувальний образ ще не готовий", "Native boot image is not ready yet"],
  "Настройте рабочее пространство": ["Налаштуйте робочий простір", "Set up your workspace"],
  "Отметьте завершение локальной настройки. Установка ОС, разметка диска и настройка загрузчика здесь не выполняются.": [
    "Позначте завершення локального налаштування. Встановлення ОС, розмітка диска й налаштування завантажувача тут не виконуються.",
    "Mark the local setup as complete. OS installation, disk partitioning and bootloader changes are not performed here."
  ],
  "Цветовая схема": ["Колірна схема", "Color scheme"],
  "Единая палитра DuckOS: чёрный, белый и жёлтый.": ["Єдина палітра DuckOS: чорний, білий і жовтий.", "DuckOS uses a single black, white and yellow palette."],
  "Завершить настройку": ["Завершити налаштування", "Finish setup"],
  "Проекты и задачи": ["Проєкти й завдання", "Projects and tasks"],
  "Собирайте рабочие пункты и идеи в локальном списке. Gloverty остаётся отдельным центром автоматизаций; системное расписание и синхронизация не подключены.": [
    "Збирайте робочі пункти й ідеї в локальному списку. Gloverty залишається окремим центром автоматизацій; системний розклад і синхронізацію не підключено.",
    "Collect work items and ideas in a local list. Gloverty remains a separate automation hub; system scheduling and sync are not connected."
  ],
  "Добавить пункт": ["Додати пункт", "Add item"],
  "Проверка архивного файла": ["Перевірка архівного файла", "Archive file inspection"],
  "Прочитать имя, формат и размер выбранного архива. Содержимое не извлекается, не изменяется и не отправляется в сеть.": [
    "Прочитати ім’я, формат і розмір вибраного архіву. Вміст не розпаковується, не змінюється й не надсилається мережею.",
    "Read the selected archive's name, format and size. Its contents are not extracted, changed or sent over the network."
  ],
  "Выбрать архив": ["Вибрати архів", "Choose archive"],
  "Архив ещё не выбран.": ["Архів ще не вибрано.", "No archive selected."],
  "Полноценный распаковщик требует отдельного безопасного системного сервиса.": ["Повноцінний розпакувальник потребує окремого безпечного системного сервісу.", "A full extractor requires a separate, secure system service."],
  "Подборки и медиатеги": ["Добірки й медіатеги", "Collections and media tags"],
  "Создавайте названия альбомов и подборок. Здесь сохраняются текстовые ссылки и метки, а не сами медиафайлы.": [
    "Створюйте назви альбомів і добірок. Тут зберігаються текстові посилання й мітки, а не самі медіафайли.",
    "Create album and collection names. This stores text links and tags, not the media files themselves."
  ],
  "Название альбома или подборки": ["Назва альбому або добірки", "Album or collection name"],
  "Новая подборка": ["Нова добірка", "New collection"],
  "Ритмический профиль": ["Ритмічний профіль", "Rhythm profile"],
  "Локальные параметры. Генерация и воспроизведение аудио не подключены.": [
    "Локальні параметри. Генерацію та відтворення аудіо не підключено.",
    "Local parameters. Audio generation and playback are not connected."
  ],
  "Проверка перед обменом": ["Перевірка перед передаванням", "Review before sharing"],
  "Ручной список для проверки получателя, состава передачи и срока хранения. Это не шифрование и не системная защита.": [
    "Ручний список для перевірки отримувача, складу передавання й строку зберігання. Це не шифрування й не системний захист.",
    "A manual checklist for the recipient, transfer contents and retention period. This is not encryption or system security."
  ],
  "Получатель и адрес передачи проверены": ["Отримувача й адресу передавання перевірено", "Recipient and destination checked"],
  "Выбраны только нужные материалы": ["Вибрано лише потрібні матеріали", "Only necessary items selected"],
  "Срок хранения и использование понятны": ["Строк зберігання й використання зрозумілі", "Retention and use are understood"],
  "Проверить список": ["Перевірити список", "Review checklist"],
  "Проверка ещё не запускалась.": ["Перевірку ще не запускали.", "Review has not started."],
  "Заметки для себя": ["Нотатки для себе", "Personal notes"],
  "Личные текстовые записи остаются в профиле браузера. Облачная синхронизация и медицинские функции не предполагаются.": [
    "Особисті текстові записи залишаються у профілі браузера. Хмарну синхронізацію й медичні функції не передбачено.",
    "Personal text notes stay in the browser profile. Cloud sync and medical features are not included."
  ],
  "Новая личная запись": ["Новий особистий запис", "New personal entry"],
  "Сохранить заметку": ["Зберегти нотатку", "Save note"],
  "Сохраняйте короткие мысли отдельно от проектных списков Orriganize.": ["Зберігайте короткі думки окремо від проєктних списків Orriganize.", "Keep quick thoughts separate from Orriganize project lists."],
  "Быстрая заметка": ["Швидка нотатка", "Quick note"],
  "Добавить заметку": ["Додати нотатку", "Add note"],
  "Карточки знаний": ["Картки знань", "Knowledge cards"],
  "Личная база коротких справок в текущем браузерном профиле; системная индексация не подключена.": [
    "Особиста база коротких довідок у поточному профілі браузера; системну індексацію не підключено.",
    "A personal collection of short reference cards in this browser profile; system indexing is not connected."
  ],
  "Новая карточка знаний": ["Нова картка знань", "New knowledge card"],
  "Добавить карточку": ["Додати картку", "Add card"],
  "Маршрут и точки": ["Маршрут і точки", "Route and places"],
  "Ручной список остановок без GPS, геолокации и навигации в реальном времени.": [
    "Ручний список зупинок без GPS, геолокації та навігації в реальному часі.",
    "A manual stop list without GPS, geolocation or live navigation."
  ],
  "Название точки или остановки": ["Назва точки або зупинки", "Place or stop name"],
  "Добавить точку": ["Додати точку", "Add place"],
  "Инспекция EXE и DLL": ["Інспекція EXE та DLL", "EXE and DLL inspection"],
  "Локальная проверка заголовка PE/ELF и контрольной суммы файла. Файл не запускается и не отправляется на сервер.": [
    "Локальна перевірка заголовка PE/ELF і контрольної суми файла. Файл не запускається й не надсилається на сервер.",
    "Local inspection of the PE/ELF header and file checksum. The file is not executed or uploaded."
  ],
  "Выбрать исполняемый файл": ["Вибрати виконуваний файл", "Choose executable"],
  "Файл ещё не выбран.": ["Файл ще не вибрано.", "No file selected."],
  "Это не антивирус, не проверка подписи издателя и не Windows runtime.": [
    "Це не антивірус, не перевірка підпису видавця й не Windows runtime.",
    "This is not antivirus, publisher-signature verification or a Windows runtime."
  ],
  "Пространство возможностей": ["Простір можливостей", "Discover capabilities"],
  "Пятнадцать направлений собраны по задачам, а не по полу. Каждый инструмент открыт каждому пользователю. Настраивайте каталог под свои интересы.": [
    "П’ятнадцять напрямів згруповано за завданнями. Кожен інструмент доступний усім користувачам. Налаштовуйте каталог під свої інтереси.",
    "Fifteen areas are grouped by task. Every tool is available to everyone. Shape the catalogue around your interests."
  ],
  "Все приложения": ["Усі застосунки", "All apps"],
  "Показано 15 приложений": ["Показано 15 застосунків", "Showing 15 apps"],
  "Каталог и избранное работают локально. Карточки описывают спецификации новых продуктов; отдельные исполняемые модули ещё не подключены.": [
    "Каталог і вибране працюють локально. Картки описують специфікації нових продуктів; окремі виконувані модулі ще не підключено.",
    "The catalogue and favourites work locally. Cards describe proposed products; separate executable modules are not connected yet."
  ],
  "Подробнее": ["Докладніше", "Details"],
  "Звук под контролем": ["Звук під контролем", "Audio controls"],
  "Системная громкость": ["Системна гучність", "System volume"],
  "Общий уровень выхода": ["Загальний рівень виходу", "Master output level"],
  "Микрофон": ["Мікрофон", "Microphone"],
  "Входной уровень": ["Рівень входу", "Input level"],
  "Запись": ["Запис", "Recording"],
  "Начать запись": ["Почати запис", "Start recording"],
  "Остановить": ["Зупинити", "Stop"],
  "Показатели демонстрационные. Управление реальными аудиоустройствами появится через системный аудиосервис DuckOS.": [
    "Показники демонстраційні. Керування реальними аудіопристроями з’явиться через системний аудіосервіс DuckOS.",
    "These values are illustrative. Real audio-device control requires the DuckOS audio service."
  ],
  "Сохранённые моменты": ["Збережені моменти", "Saved moments"],
  "Выберите плитку, чтобы отметить фотографию.": ["Виберіть плитку, щоб позначити фотографію.", "Select a tile to mark a photo."],
  "Расходы за сегодня": ["Витрати за сьогодні", "Today's expenses"],
  "Все суммы придуманы для демонстрации интерфейса. Банковские счета и платёжные сервисы не подключены.": [
    "Усі суми вигадані для демонстрації інтерфейсу. Банківські рахунки й платіжні сервіси не підключено.",
    "All amounts are illustrative. Bank accounts and payment services are not connected."
  ],
  "Сценарии дня": ["Сценарії дня", "Daily routines"],
  "Доброе утро": ["Доброго ранку", "Good morning"],
  "Рабочий режим": ["Робочий режим", "Work mode"],
  "Тихий вечер": ["Тихий вечір", "Quiet evening"],
  "Свет, погода и календарь": ["Світло, погода й календар", "Lights, weather and calendar"],
  "Фокус и уведомления": ["Фокус і сповіщення", "Focus and notifications"],
  "Приглушённый свет и звук": ["Приглушене світло й звук", "Dimmed lights and sound"],
  "Компас и направления": ["Компас і напрямки", "Compass and directions"],
  "Направления иллюстративные. Геолокация и датчики компаса не используются.": [
    "Напрямки ілюстративні. Геолокація й датчики компаса не використовуються.",
    "Directions are illustrative. Geolocation and compass sensors are not used."
  ],
  "Продолжить приключение": ["Продовжити пригоду", "Continue your adventure"],
  "Ваши устройства": ["Ваші пристрої", "Your devices"],
  "Подключённые устройства показаны условно. Сканирование оборудования не выполняется.": [
    "Підключені пристрої показані умовно. Сканування обладнання не виконується.",
    "Connected devices are illustrative. No hardware scan is performed."
  ],
  "Игровая производительность под контролем": ["Ігрова продуктивність під контролем", "Gaming performance at a glance"],
  "Сама браузерная панель не меняет настройки компьютера. Для снимка, телеметрии и игрового режима откройте нативное Windows-приложение OPlague.": [
    "Сама браузерна панель не змінює налаштування комп’ютера. Для знімка, телеметрії та ігрового режиму відкрийте нативний Windows-застосунок OPlague.",
    "The browser panel does not change PC settings. Use the native Windows OPlague app for snapshots, telemetry and gaming sessions."
  ],
  "Рабочее пространство под контролем": ["Робочий простір під контролем", "Workspace overview"],
  "Аудит файлов, пользовательской автозагрузки и процессов.": ["Аудит файлів, автозавантаження користувача й процесів.", "Audit files, user startup entries and processes."],
  "Сформулируйте задачу": ["Сформулюйте завдання", "Describe a task"],
  "Что нужно сделать?": ["Що потрібно зробити?", "What should be done?"],
  "Подготовить план": ["Підготувати план", "Prepare plan"],
  "Подтвердить план": ["Підтвердити план", "Approve plan"],
  "Отклонить": ["Відхилити", "Reject"],
  "Доступы и изоляция": ["Доступи й ізоляція", "Access and isolation"],
  "По умолчанию — запрет": ["За замовчуванням — заборонено", "Denied by default"],
  "Каждое право должно быть запрошено отдельно.": ["Кожен дозвіл потрібно запитувати окремо.", "Each capability must be requested separately."],
  "Обновления без сюрпризов": ["Оновлення без сюрпризів", "Updates without surprises"],
  "Проверить план обновления": ["Перевірити план оновлення", "Preview update plan"],
  "Проверка только сформирует локальный план. Скачивания и установки не будет.": [
    "Перевірка лише сформує локальний план. Завантаження й встановлення не відбудуться.",
    "This only creates a local plan. Nothing is downloaded or installed."
  ],
  "Совместимость Windows-приложений": ["Сумісність Windows-застосунків", "Windows app compatibility"],
  "Рабочая среда Mora": ["Робоче середовище Mora", "Mora workspace"],
  "Проверка файла": ["Перевірка файла", "File verification"],
  "Свернуть": ["Згорнути", "Minimize"],
  "Развернуть": ["Розгорнути", "Maximize"],
  "Рабочий стол": ["Робочий стіл", "Desktop"]
});

Object.assign(translations, {
  "Открыть меню DuckOS": ["Відкрити меню DuckOS", "Open DuckOS menu"],
  "Wi-Fi · быстрые настройки": ["Wi-Fi · швидкі налаштування", "Wi-Fi · quick settings"],
  "Питание · открыть Control": ["Живлення · відкрити Control", "Power · open Control"],
  "Звук · открыть громкость": ["Звук · відкрити гучність", "Sound · open volume"],
  "Часы и дата": ["Годинник і дата", "Clock and date"],
  "Время и дата": ["Час і дата", "Time and date"],
  "Питание и Control": ["Живлення й Control", "Power and Control"],
  "Загрузка даты…": ["Завантаження дати…", "Loading date…"],
  "Найти приложение": ["Знайти застосунок", "Find an app"],
  "Локальные команды": ["Локальні команди", "Local commands"],
  "Настройки оболочки": ["Налаштування оболонки", "Shell settings"],
  "Права и доверие": ["Дозволи й довіра", "Permissions and trust"],
  "Восстановление": ["Відновлення", "Recovery"],
  "Среда Mora": ["Середовище Mora", "Mora workspace"],
  "Планы и намерения": ["Плани й наміри", "Plans and intents"],
  "Каталог приложений": ["Каталог застосунків", "App catalogue"],
  "Приложения запускаются в текущем браузерном пространстве Mora.": [
    "Застосунки запускаються в поточному браузерному просторі Mora.",
    "Apps open in the current Mora browser workspace."
  ]
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


export function formatItemCount(count, locale = "ru") {
  const value = Math.max(0, Math.trunc(Number(count) || 0));
  const tag = locale === "uk" ? "uk-UA" : locale === "en" ? "en-US" : "ru-RU";
  const category = new Intl.PluralRules(tag).select(value);
  let noun;
  if (locale === "en") noun = category === "one" ? "item" : "items";
  else if (locale === "uk") noun = category === "one" ? "елемент" : category === "few" ? "елементи" : "елементів";
  else noun = category === "one" ? "элемент" : category === "few" ? "элемента" : "элементов";
  return new Intl.NumberFormat(tag).format(value) + " " + noun;
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
    const elements = [];
    if (root.nodeType === 1 && root.matches("[aria-label],[placeholder],[title]")) elements.push(root);
    elements.push(...root.querySelectorAll("[aria-label],[placeholder],[title]"));
    elements.forEach((element) => {
      for (const attribute of ["aria-label", "placeholder", "title"]) {
        if (!element.hasAttribute(attribute)) continue;
        const value = element.getAttribute(attribute);
        const translated = translateText(value, locale);
        if (translated !== value) element.setAttribute(attribute, translated);
      }
    });
  }

  if (doc?.documentElement) doc.documentElement.lang = locale;
  if (doc) doc.title = translateText("Mora — DuckOS", locale);
}
