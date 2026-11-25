#include <QApplication>
#include <QButtonGroup>
#include <QCloseEvent>
#include <QColor>
#include <QComboBox>
#include <QDateTime>
#include <QDir>
#include <QFile>
#include <QFileDialog>
#include <QFileInfo>
#include <QKeySequence>
#include <QLocale>
#include <QGridLayout>
#include <QHash>
#include <QJsonArray>
#include <QJsonDocument>
#include <QJsonObject>
#include <QLabel>
#include <QLineEdit>
#include <QMainWindow>
#include <QPlainTextEdit>
#include <QPointer>
#include <QPushButton>
#include <QShortcut>
#include <QScreen>
#include <QScrollArea>
#include <QSettings>
#include <QStackedWidget>
#include <QSizePolicy>
#include <QTimer>
#include <QTreeWidget>
#include <QTreeWidgetItem>
#include <QVector>
#include <QVBoxLayout>
#include <QPainter>
#include <QPainterPath>
#include <QPaintEvent>
#include <QResizeEvent>
#include <QStatusBar>
#include <QStyle>
#include <QTextBrowser>
#include <QWidget>

#include <algorithm>
#include <cmath>

#ifndef DUCKOS_MORA_CATALOG_PATH
#define DUCKOS_MORA_CATALOG_PATH "mora/apps.json"
#endif
#ifndef DUCKOS_MORA_THEME_PATH
#define DUCKOS_MORA_THEME_PATH "mora/theme.json"
#endif

namespace {

QColor kPage("#080808");
QColor kSurface("#151515");
QColor kRaised("#242424");
QColor kText("#FFFFFF");
QColor kSecondary("#E5E5E5");
QColor kMuted("#A6A6A6");
QColor kBrand("#FFD400");
QColor kBrandHover("#FFE45C");
QColor kBorder("#3A3A3A");
QColor kSelection("#3A3100");

void loadThemeTokens()
{
    QFile file(QString::fromUtf8(DUCKOS_MORA_THEME_PATH));
    if (!file.open(QIODevice::ReadOnly)) return;

    QJsonParseError error{};
    const QJsonDocument document = QJsonDocument::fromJson(file.readAll(), &error);
    if (error.error != QJsonParseError::NoError || !document.isObject()) return;

    const QJsonObject palette = document.object()
        .value("palettes").toObject().value("duck").toObject();

    auto readColor = [&palette](const char* key, QColor& target) {
        const QColor candidate(palette.value(QLatin1String(key)).toString());
        if (candidate.isValid()) target = candidate;
    };
    readColor("page", kPage);
    readColor("surface", kSurface);
    readColor("elevated", kRaised);
    readColor("text", kText);
    readColor("secondary", kSecondary);
    readColor("muted", kMuted);
    readColor("brand", kBrand);
    readColor("brandHover", kBrandHover);
    readColor("border", kBorder);
    readColor("selection", kSelection);
}

QString applyThemeTokens(QString style)
{
    const QList<QPair<QString, QString>> replacements{
        {"#080808", "@@MORA_PAGE@@"},
        {"#151515", "@@MORA_SURFACE@@"},
        {"#242424", "@@MORA_RAISED@@"},
        {"#FFFFFF", "@@MORA_TEXT@@"},
        {"#E5E5E5", "@@MORA_SECONDARY@@"},
        {"#A6A6A6", "@@MORA_MUTED@@"},
        {"#FFD400", "@@MORA_BRAND@@"},
        {"#FFE45C", "@@MORA_BRAND_HOVER@@"},
        {"#3A3A3A", "@@MORA_BORDER@@"},
        {"#3A3100", "@@MORA_SELECTION@@"}
    };
    for (const auto& replacement : replacements) {
        style.replace(replacement.first, replacement.second);
    }
    style.replace("@@MORA_PAGE@@", kPage.name(QColor::HexRgb));
    style.replace("@@MORA_SURFACE@@", kSurface.name(QColor::HexRgb));
    style.replace("@@MORA_RAISED@@", kRaised.name(QColor::HexRgb));
    style.replace("@@MORA_TEXT@@", kText.name(QColor::HexRgb));
    style.replace("@@MORA_SECONDARY@@", kSecondary.name(QColor::HexRgb));
    style.replace("@@MORA_MUTED@@", kMuted.name(QColor::HexRgb));
    style.replace("@@MORA_BRAND@@", kBrand.name(QColor::HexRgb));
    style.replace("@@MORA_BRAND_HOVER@@", kBrandHover.name(QColor::HexRgb));
    style.replace("@@MORA_BORDER@@", kBorder.name(QColor::HexRgb));
    style.replace("@@MORA_SELECTION@@", kSelection.name(QColor::HexRgb));
    return style;
}

struct AppInfo {
    QString id;
    QString name;
    QString category;
    QString maturity;
};

QString categoryName(const QString& category)
{
    static const QHash<QString, QString> names{
        {"audio", "Аудио"},
        {"photos", "Изображения"},
        {"finance", "Финансы"},
        {"automation", "Автоматизация"},
        {"compass", "Компас"},
        {"games", "Игры"},
        {"devices", "Устройства"},
        {"system", "Система"},
        {"productivity", "Работа"},
        {"files", "Файлы"},
        {"multimedia", "Медиа"},
        {"privacy", "Приватность"},
        {"journal", "Дневник"},
        {"notes", "Заметки"},
        {"knowledge", "Знания"},
        {"navigation", "Навигация"},
        {"gaming", "Игры"},
        {"compatibility", "Совместимость"},
        {"creative", "Творчество"},
        {"security", "Безопасность"},
        {"recovery", "Восстановление"},
        {"workspace", "Рабочее место"},
        {"provenance", "Достоверность"},
        {"application_catalogue", "Каталог"},
        {"ecosystem", "Инструменты"}
    };
    return names.value(category, category.isEmpty() ? "Приложение" : category);
}

QString categoryGlyph(const QString& category)
{
    if (category == "files") return "▱";
    if (category == "notes" || category == "knowledge") return "▤";
    if (category == "audio") return "∿";
    if (category == "games" || category == "gaming") return "⌘";
    if (category == "devices") return "⌁";
    if (category == "system" || category == "security") return "✳";
    if (category == "finance") return "₴";
    if (category == "automation") return "ϟ";
    if (category == "photos" || category == "multimedia") return "◒";
    if (category == "creative") return "◇";
    return "◈";
}

QString maturityText(const QString& maturity)
{
    if (maturity.isEmpty() || maturity == "implemented_local_catalog") {
        return "Карточка каталога";
    }
    if (maturity.contains("partial")) return "Частичная интеграция";
    if (maturity.contains("planned")) return "В плане";
    if (maturity.contains("specified")) return "Спецификация";
    return "Локальная панель";
}

QLabel* label(const QString& text, const QString& role = "body")
{
    auto* result = new QLabel(text);
    result->setProperty("role", role);
    result->setWordWrap(true);
    return result;
}

QFrame* panel()
{
    auto* frame = new QFrame;
    frame->setObjectName("panel");
    return frame;
}

QPushButton* actionButton(const QString& text, const QString& objectName = {})
{
    auto* button = new QPushButton(text);
    button->setCursor(Qt::PointingHandCursor);
    button->setMinimumHeight(42);
    if (!objectName.isEmpty()) button->setObjectName(objectName);
    return button;
}

class Backdrop final : public QWidget {
public:
    explicit Backdrop(QWidget* parent = nullptr) : QWidget(parent)
    {
        setAttribute(Qt::WA_StyledBackground, false);
    }

protected:
    void paintEvent(QPaintEvent*) override
    {
        QPainter painter(this);
        painter.setRenderHint(QPainter::Antialiasing, true);
        painter.fillRect(rect(), kPage);

        QRadialGradient glow(QPointF(width() * 0.51, height() * 0.38),
                             std::max(width(), height()) * 0.78);
        glow.setColorAt(0.0, QColor("#242018"));
        glow.setColorAt(0.46, QColor("#11100E"));
        glow.setColorAt(1.0, kPage);
        painter.fillRect(rect(), glow);

        const int foldCount = 15;
        for (int i = 0; i < foldCount; ++i) {
            const qreal x = (static_cast<qreal>(i) / (foldCount - 1)) * width();
            QPainterPath path;
            path.moveTo(x, 0);
            path.cubicTo(x - width() * 0.025, height() * 0.29,
                         x + width() * 0.035, height() * 0.63,
                         x + width() * 0.008, height());
            QPen pen(QColor(255, 255, 255, i % 3 == 0 ? 15 : 7));
            pen.setWidthF(i % 3 == 0 ? 1.3 : 0.8);
            painter.setPen(pen);
            painter.drawPath(path);
        }
        QLinearGradient lower(0, height() * 0.72, 0, height());
        lower.setColorAt(0.0, QColor(0, 0, 0, 0));
        lower.setColorAt(1.0, QColor(0, 0, 0, 105));
        painter.fillRect(rect(), lower);
    }
};

class WaveformView final : public QWidget {
public:
    explicit WaveformView(QWidget* parent = nullptr) : QWidget(parent)
    {
        setMinimumHeight(112);
        setSizePolicy(QSizePolicy::Expanding, QSizePolicy::Fixed);
    }

protected:
    void paintEvent(QPaintEvent*) override
    {
        QPainter painter(this);
        painter.setRenderHint(QPainter::Antialiasing, true);
        painter.fillRect(rect(), QColor("#101010"));
        painter.setPen(QPen(QColor("#303030"), 1));
        for (int i = 1; i < 4; ++i) {
            const int y = height() * i / 4;
            painter.drawLine(0, y, width(), y);
        }
        const qreal mid = height() / 2.0;
        QPainterPath waveform;
        for (int x = 0; x < width(); ++x) {
            const qreal phase = static_cast<qreal>(x) / std::max(1, width());
            const qreal envelope = 0.18 + 0.72 * std::abs(std::sin(phase * 3.141592653589793));
            const qreal sample = std::sin(phase * 77.0) * 0.62
                               + std::sin(phase * 181.0) * 0.24
                               + std::sin(phase * 331.0) * 0.14;
            const qreal y = mid - sample * envelope * height() * 0.39;
            if (x == 0) waveform.moveTo(x, y);
            else waveform.lineTo(x, y);
        }
        painter.setPen(QPen(kBrand, 1.35));
        painter.drawPath(waveform);
        painter.setPen(QPen(QColor(255, 212, 0, 55), 5));
        painter.drawLine(width() * 0.42, 8, width() * 0.42, height() - 8);
    }
};

class AppWindow final : public QMainWindow {
public:
    explicit AppWindow(const AppInfo& app, QWidget* owner = nullptr)
        : QMainWindow(owner), app_(app)
    {
        setWindowFlag(Qt::Window, true);
        setAttribute(Qt::WA_DeleteOnClose, true);
        setProperty("moraAppId", app_.id);
        setWindowTitle(app_.name + " — Mora");
        setMinimumSize(480, 340);
        resize(720, 470);
        setStyleSheet(applyThemeTokens(QString::fromUtf8(R"(
            QMainWindow { background: #080808; color: #FFFFFF; }
            QWidget { color: #FFFFFF; font-family: "Segoe UI"; font-size: 10pt; }
            QFrame#panel { background: #151515; border: 1px solid #3A3A3A; border-radius: 16px; }
            QLabel[role="muted"] { color: #A6A6A6; }
            QLabel[role="eyebrow"] { color: #FFD400; font-size: 8pt; font-weight: 700; letter-spacing: 1px; }
            QPushButton { color: #FFFFFF; background: #242424; border: 1px solid #3A3A3A; border-radius: 10px; padding: 9px 14px; }
            QPushButton:hover { border-color: #FFD400; background: #2B281A; }
            QPlainTextEdit, QTreeWidget { background: #101010; color: #FFFFFF; border: 1px solid #3A3A3A; border-radius: 10px; padding: 8px; selection-background-color: #3A3100; }
            QHeaderView::section { background: #242424; color: #FFD400; border: 0; padding: 7px; }
        )")));
        buildContent();
    }

private:
    AppInfo app_;

    void buildContent()
    {
        auto* root = new QWidget;
        auto* layout = new QVBoxLayout(root);
        layout->setContentsMargins(22, 20, 22, 18);
        layout->setSpacing(14);

        layout->addWidget(label(categoryName(app_.category).toUpper(), "eyebrow"));
        auto* heading = label(app_.name, "heading");
        QFont headingFont = heading->font();
        headingFont.setPointSize(22);
        headingFont.setWeight(QFont::DemiBold);
        heading->setFont(headingFont);
        layout->addWidget(heading);
        layout->addWidget(label(maturityText(app_.maturity), "muted"));

        if (app_.id == "poi") {
            buildNotes(layout);
        } else if (app_.id == "abriganza") {
            buildFiles(layout);
        } else if (app_.id == "ventusample-workbench" || app_.id == "ventusample") {
            buildAudio(layout);
        } else {
            buildCataloguePanel(layout);
        }

        setCentralWidget(root);
    }

    void buildNotes(QVBoxLayout* layout)
    {
        auto* editor = new QPlainTextEdit;
        editor->setObjectName("poi-note-editor");
        editor->setPlaceholderText("Запишите мысль, идею или короткую заметку…");
        QSettings settings("DuckOS", "Mora");
        editor->setPlainText(settings.value("notes/poi").toString());
        layout->addWidget(editor, 1);

        auto* footer = new QHBoxLayout;
        auto* state = label("Хранится локально в настройках Mora", "muted");
        auto* save = actionButton("Сохранить заметку");
        footer->addWidget(state, 1);
        footer->addWidget(save);
        layout->addLayout(footer);

        auto* timer = new QTimer(editor);
        timer->setSingleShot(true);
        QObject::connect(editor, &QPlainTextEdit::textChanged, editor, [timer, state]() {
            state->setText("Есть несохранённые изменения");
            timer->start(450);
        });
        QObject::connect(timer, &QTimer::timeout, editor, [editor, state]() {
            QSettings local("DuckOS", "Mora");
            local.setValue("notes/poi", editor->toPlainText());
            local.sync();
            state->setText("Сохранено локально");
        });
        QObject::connect(save, &QPushButton::clicked, editor, [timer, editor, state]() {
            timer->stop();
            QSettings local("DuckOS", "Mora");
            local.setValue("notes/poi", editor->toPlainText());
            local.sync();
            state->setText("Сохранено локально");
        });
    }

    void buildFiles(QVBoxLayout* layout)
    {
        auto* description = label(
            "Выберите папку, чтобы просмотреть имена и метаданные файлов. "
            "Mora не открывает и не запускает выбранные элементы.", "muted");
        layout->addWidget(description);

        auto* tree = new QTreeWidget;
        tree->setObjectName("abriganza-file-list");
        tree->setColumnCount(4);
        tree->setHeaderLabels({"Имя", "Тип", "Размер", "Изменено"});
        tree->setRootIsDecorated(false);
        tree->setAlternatingRowColors(false);
        layout->addWidget(tree, 1);

        auto* footer = new QHBoxLayout;
        auto* pathLabel = label("Папка не выбрана", "muted");
        pathLabel->setTextInteractionFlags(Qt::TextSelectableByMouse);
        auto* choose = actionButton("Выбрать папку");
        footer->addWidget(pathLabel, 1);
        footer->addWidget(choose);
        layout->addLayout(footer);

        QObject::connect(choose, &QPushButton::clicked, this, [this, tree, pathLabel]() {
            const QString path = QFileDialog::getExistingDirectory(
                this, "Выберите папку для просмотра", QDir::homePath());
            if (path.isEmpty()) return;

            QDir directory(path);
            const QFileInfoList entries = directory.entryInfoList(
                QDir::Files | QDir::Readable | QDir::NoDotAndDotDot,
                QDir::Name | QDir::IgnoreCase);
            tree->clear();
            int shown = 0;
            for (const QFileInfo& info : entries) {
                if (shown++ >= 100) break;
                auto* item = new QTreeWidgetItem(tree);
                item->setText(0, info.fileName());
                item->setText(1, info.suffix().isEmpty() ? "Файл" : info.suffix().toUpper());
                item->setText(2, info.isFile() ? QString::number(info.size() / 1024.0, 'f', 1) + " КБ" : "—");
                item->setText(3, info.lastModified().toString("dd.MM.yyyy HH:mm"));
            }
            pathLabel->setText(path);
            if (entries.isEmpty()) pathLabel->setText(path + " · пусто");
        });
    }

    void buildAudio(QVBoxLayout* layout)
    {
        layout->addWidget(label("Soft arrival · пример рабочей сессии", "body"));
        auto* waveform = new WaveformView;
        auto* waveformPanel = panel();
        auto* panelLayout = new QVBoxLayout(waveformPanel);
        panelLayout->setContentsMargins(12, 12, 12, 12);
        panelLayout->addWidget(waveform);
        layout->addWidget(waveformPanel);

        layout->addWidget(label(
            "Визуализация демонстрационная. Аудиодвижок, устройства и "
            "воспроизведение в этой сборке не подключены.", "muted"));

        auto* controls = new QHBoxLayout;
        controls->addWidget(label("48 kHz · локальная сессия", "muted"), 1);
        auto* unavailable = actionButton("Аудиодвижок не подключён");
        unavailable->setEnabled(false);
        controls->addWidget(unavailable);
        layout->addLayout(controls);
        layout->addStretch(1);
    }

    void buildCataloguePanel(QVBoxLayout* layout)
    {
        auto* info = panel();
        auto* infoLayout = new QVBoxLayout(info);
        infoLayout->setContentsMargins(18, 16, 18, 16);
        infoLayout->setSpacing(8);
        infoLayout->addWidget(label("Нативное окно Mora", "eyebrow"));
        infoLayout->addWidget(label(
            "Это отдельное окно приложения хостовой ОС. Оно не встроено "
            "в HTML, WebView или браузерный контейнер."));
        infoLayout->addWidget(label(
            "Специализированный исполняемый модуль этой карточки пока не подключён. "
            "Окно не запускает команды из каталога и не запрашивает привилегии.",
            "muted"));
        layout->addWidget(info);
        layout->addStretch(1);
    }
};

class MoraWindow final : public QMainWindow {
public:
    explicit MoraWindow(QWidget* parent = nullptr)
        : QMainWindow(parent)
    {
        setWindowTitle("Mora — DuckOS");
        setMinimumSize(1120, 720);
        resize(1440, 900);
        loadCatalogue();
        buildInterface();

        QSettings settings("DuckOS", "Mora");
        const QByteArray geometry = settings.value("shell/geometry").toByteArray();
        if (!geometry.isEmpty()) restoreGeometry(geometry);

        auto* clock = new QTimer(this);
        QObject::connect(clock, &QTimer::timeout, this, [this]() { updateClock(); });
        clock->start(30'000);
        updateClock();
    }

    ~MoraWindow() override
    {
        QSettings settings("DuckOS", "Mora");
        settings.setValue("shell/geometry", saveGeometry());
        settings.sync();
    }

    bool runSelfTest(QString* failure)
    {
        auto fail = [failure](const QString& reason) {
            if (failure) *failure = reason;
            return false;
        };
        if (!pageStack_ || !homePage_ || !appsPage_ || !workspacePage_) {
            return fail("A required desktop page was not created.");
        }
        auto* appsButton = findChild<QPushButton*>("nav-apps");
        if (!appsButton) return fail("The native app navigation control is missing.");
        appsButton->click();
        if (pageStack_->currentWidget() != appsPage_) {
            return fail("The Applications navigation action did not change pages.");
        }
        openDesignWorkspace();
        QApplication::processEvents();
        int nativeWindows = 0;
        for (QWidget* widget : QApplication::topLevelWidgets()) {
            if (widget->property("moraAppId").isValid()) ++nativeWindows;
        }
        if (nativeWindows < 3) {
            return fail("The three-window workspace did not create three native top-level windows.");
        }
        for (QWidget* widget : QApplication::topLevelWidgets()) {
            if (widget->property("moraAppId").isValid()) widget->close();
        }
        return true;
    }

    void openDesignWorkspace()
    {
        openAppWindow("abriganza");
        openAppWindow("poi");
        openAppWindow("ventusample-workbench");
        showPage(2);
    }

private:
    QVector<AppInfo> apps_;
    QHash<QString, QPointer<AppWindow>> windows_;
    QStackedWidget* pageStack_ = nullptr;
    QWidget* homePage_ = nullptr;
    QWidget* appsPage_ = nullptr;
    QWidget* workspacePage_ = nullptr;
    QLineEdit* globalSearch_ = nullptr;
    QLineEdit* appsSearch_ = nullptr;
    QComboBox* categoryFilter_ = nullptr;
    QGridLayout* appGrid_ = nullptr;
    QLabel* dateLabel_ = nullptr;
    QLabel* timeLabel_ = nullptr;
    QButtonGroup* navigationGroup_ = nullptr;

    void loadCatalogue()
    {
        QFile file(QString::fromUtf8(DUCKOS_MORA_CATALOG_PATH));
        if (!file.open(QIODevice::ReadOnly)) return;
        QJsonParseError error{};
        const QJsonDocument document = QJsonDocument::fromJson(file.readAll(), &error);
        if (error.error != QJsonParseError::NoError || !document.isObject()) return;

        const QJsonObject root = document.object();
        const QJsonArray builtIns = root.value("built_in_apps").toArray();
        for (const QJsonValue& value : builtIns) {
            if (!value.isObject()) continue;
            const QJsonObject object = value.toObject();
            AppInfo app{
                object.value("id").toString(),
                object.value("name").toString(),
                object.value("category").toString(),
                object.value("maturity").toString()
            };
            if (!app.id.isEmpty() && !app.name.isEmpty()) apps_.push_back(app);
        }

        const QJsonArray workbenches = root.value("ecosystem_workbenches").toArray();
        for (const QJsonValue& value : workbenches) {
            if (!value.isObject()) continue;
            const QJsonObject object = value.toObject();
            AppInfo app{
                object.value("id").toString(),
                object.value("name").toString(),
                "ecosystem",
                "partial_native_workbench"
            };
            const bool exists = std::any_of(apps_.cbegin(), apps_.cend(),
                [&app](const AppInfo& current) { return current.id == app.id; });
            if (!exists && !app.id.isEmpty() && !app.name.isEmpty()) apps_.push_back(app);
        }
    }

    void buildInterface()
    {
        setStyleSheet(applyThemeTokens(QString::fromUtf8(R"(
            QWidget { color: #FFFFFF; font-family: "Segoe UI"; font-size: 10pt; }
            QLabel[role="muted"] { color: #A6A6A6; }
            QLabel[role="eyebrow"] { color: #FFD400; font-size: 8pt; font-weight: 700; letter-spacing: 1px; }
            QLabel[role="title"] { color: #FFFFFF; font-size: 25pt; font-weight: 650; }
            QLabel[role="subtitle"] { color: #E5E5E5; }
            QFrame#panel { background: rgba(21,21,21,238); border: 1px solid #3A3A3A; border-radius: 16px; }
            QFrame#softPanel { background: rgba(36,36,36,218); border: 1px solid #3A3A3A; border-radius: 14px; }
            QPushButton { color: #FFFFFF; background: #151515; border: 1px solid #3A3A3A; border-radius: 10px; padding: 9px 12px; text-align: left; }
            QPushButton:hover { border-color: #FFD400; background: #222016; }
            QPushButton:checked { color: #080808; background: #FFD400; border-color: #FFD400; }
            QPushButton:disabled { color: #777777; background: #171717; border-color: #303030; }
            QPushButton#appTile { background: rgba(21,21,21,235); border-radius: 14px; min-height: 78px; }
            QPushButton#appTile:hover { background: #242118; border-color: #FFD400; }
            QLineEdit, QComboBox { color: #FFFFFF; background: #151515; border: 1px solid #3A3A3A; border-radius: 10px; padding: 9px 12px; min-height: 24px; }
            QLineEdit:focus, QComboBox:focus { border: 2px solid #FFE45C; }
            QScrollArea { border: 0; background: transparent; }
        )")));

        auto* background = new Backdrop;
        auto* outer = new QVBoxLayout(background);
        outer->setContentsMargins(0, 0, 0, 0);
        outer->setSpacing(0);
        outer->addWidget(buildTopBar());

        auto* body = new QWidget;
        auto* bodyLayout = new QHBoxLayout(body);
        bodyLayout->setContentsMargins(12, 12, 12, 10);
        bodyLayout->setSpacing(12);
        bodyLayout->addWidget(buildNavigationRail());

        pageStack_ = new QStackedWidget;
        pageStack_->setObjectName("mora-page-stack");
        homePage_ = buildHomePage();
        appsPage_ = buildAppsPage();
        workspacePage_ = buildWorkspacePage();
        pageStack_->addWidget(homePage_);
        pageStack_->addWidget(appsPage_);
        pageStack_->addWidget(workspacePage_);
        bodyLayout->addWidget(pageStack_, 1);
        outer->addWidget(body, 1);
        outer->addWidget(buildDock());
        setCentralWidget(background);

        auto* searchShortcut = new QShortcut(QKeySequence("Ctrl+K"), this);
        QObject::connect(searchShortcut, &QShortcut::activated, this, [this]() {
            showPage(1);
            if (appsSearch_) appsSearch_->setFocus();
        });
        auto* homeShortcut = new QShortcut(QKeySequence("Ctrl+1"), this);
        QObject::connect(homeShortcut, &QShortcut::activated, this, [this]() { showPage(0); });
        auto* appsShortcut = new QShortcut(QKeySequence("Ctrl+2"), this);
        QObject::connect(appsShortcut, &QShortcut::activated, this, [this]() { showPage(1); });
        auto* workspaceShortcut = new QShortcut(QKeySequence("Ctrl+3"), this);
        QObject::connect(workspaceShortcut, &QShortcut::activated, this, [this]() { showPage(2); });
    }

    QWidget* buildTopBar()
    {
        auto* bar = new QWidget;
        bar->setFixedHeight(52);
        auto* layout = new QHBoxLayout(bar);
        layout->setContentsMargins(22, 4, 22, 4);
        layout->setSpacing(16);

        auto* brand = label("mora", "eyebrow");
        QFont brandFont = brand->font();
        brandFont.setPointSize(15);
        brandFont.setWeight(QFont::Bold);
        brand->setFont(brandFont);
        layout->addWidget(brand);
        layout->addWidget(label("Рабочее пространство", "muted"));
        layout->addStretch(1);
        layout->addWidget(label("DuckOS", "muted"));

        globalSearch_ = new QLineEdit;
        globalSearch_->setObjectName("global-search");
        globalSearch_->setPlaceholderText("Найти в Mora   Ctrl+K");
        globalSearch_->setMaximumWidth(270);
        globalSearch_->setClearButtonEnabled(true);
        layout->addWidget(globalSearch_);

        dateLabel_ = label({}, "muted");
        timeLabel_ = label({}, "body");
        layout->addWidget(dateLabel_);
        layout->addWidget(timeLabel_);
        QObject::connect(globalSearch_, &QLineEdit::returnPressed, this, [this]() {
            showPage(1);
            if (appsSearch_) appsSearch_->setText(globalSearch_->text());
        });
        return bar;
    }

    QWidget* buildNavigationRail()
    {
        auto* rail = new QWidget;
        rail->setFixedWidth(64);
        auto* layout = new QVBoxLayout(rail);
        layout->setContentsMargins(0, 4, 0, 4);
        layout->setSpacing(9);

        navigationGroup_ = new QButtonGroup(this);
        navigationGroup_->setExclusive(true);

        const QList<QPair<QString, QString>> items{
            {"⌂", "Домой"}, {"▦", "Приложения"}, {"▱", "Рабочее пространство"}
        };
        const QStringList ids{"nav-home", "nav-apps", "nav-workspace"};
        for (int i = 0; i < items.size(); ++i) {
            auto* button = new QPushButton(items[i].first);
            button->setObjectName(ids[i]);
            button->setAccessibleName(items[i].second);
            button->setToolTip(items[i].second);
            button->setCheckable(true);
            button->setFixedSize(48, 48);
            QFont iconFont = button->font();
            iconFont.setPointSize(17);
            button->setFont(iconFont);
            navigationGroup_->addButton(button, i);
            layout->addWidget(button);
            QObject::connect(button, &QPushButton::clicked, this, [this, i]() { showPage(i); });
            if (i == 0) button->setChecked(true);
        }
        layout->addStretch(1);

        auto* settings = new QPushButton("⚙");
        settings->setAccessibleName("Настройки Mora");
        settings->setToolTip("Настройки Mora");
        settings->setFixedSize(48, 48);
        layout->addWidget(settings);
        QObject::connect(settings, &QPushButton::clicked, this, [this]() { openAppWindow("workspace"); });

        auto* power = new QPushButton("⏻");
        power->setAccessibleName("Закрыть Mora");
        power->setToolTip("Закрыть Mora");
        power->setFixedSize(48, 48);
        layout->addWidget(power);
        QObject::connect(power, &QPushButton::clicked, this, &QWidget::close);
        return rail;
    }

    QWidget* buildDock()
    {
        auto* wrap = new QWidget;
        auto* layout = new QHBoxLayout(wrap);
        layout->setContentsMargins(0, 4, 0, 12);
        layout->addStretch(1);
        auto* dock = new QFrame;
        dock->setObjectName("softPanel");
        auto* dockLayout = new QHBoxLayout(dock);
        dockLayout->setContentsMargins(12, 7, 12, 7);
        dockLayout->setSpacing(8);

        const QList<QPair<QString, QString>> items{
            {"▱", "abriganza"}, {"▤", "poi"}, {"∿", "ventusample-workbench"},
            {"R", "reaper-workbench"}, {"✳", "security"}, {"⌁", "unify"}
        };
        for (const auto& item : items) {
            auto* button = new QPushButton(item.first);
            button->setFixedSize(42, 40);
            button->setToolTip(item.second);
            QFont font = button->font();
            font.setPointSize(15);
            button->setFont(font);
            dockLayout->addWidget(button);
            QObject::connect(button, &QPushButton::clicked, this,
                [this, id = item.second]() { openAppWindow(id); });
        }
        layout->addWidget(dock);
        layout->addStretch(1);
        return wrap;
    }

    QWidget* buildHomePage()
    {
        auto* page = new QWidget;
        auto* root = new QHBoxLayout(page);
        root->setContentsMargins(18, 12, 18, 14);
        root->setSpacing(16);

        auto* mainColumn = new QVBoxLayout;
        mainColumn->setSpacing(14);
        mainColumn->addWidget(label("ВАШЕ ПРОСТРАНСТВО", "eyebrow"));
        mainColumn->addWidget(label("Добро пожаловать.", "title"));
        mainColumn->addWidget(label("Всё нужное под рукой. Окна — ваши, рабочее пространство — единое.", "subtitle"));

        auto* pinnedHeading = new QHBoxLayout;
        pinnedHeading->addWidget(label("Закреплено"));
        pinnedHeading->addStretch(1);
        auto* allApps = actionButton("Все приложения  →");
        allApps->setObjectName("open-all-apps");
        pinnedHeading->addWidget(allApps);
        mainColumn->addLayout(pinnedHeading);
        QObject::connect(allApps, &QPushButton::clicked, this, [this]() { showPage(1); });

        auto* pinned = new QGridLayout;
        pinned->setSpacing(10);
        const QList<QPair<QString, QString>> pinnedApps{
            {"abriganza", "Файлы и архивы"},
            {"poi", "Быстрые заметки"},
            {"reaper-workbench", "Язык и toolchain"},
            {"ventusample-workbench", "Аудио и DSP"}
        };
        for (int i = 0; i < pinnedApps.size(); ++i) {
            const AppInfo info = findApp(pinnedApps[i].first);
            auto* tile = makeAppTile(info, pinnedApps[i].second);
            pinned->addWidget(tile, i / 2, i % 2);
        }
        mainColumn->addLayout(pinned);

        auto* recent = panel();
        auto* recentLayout = new QVBoxLayout(recent);
        recentLayout->setContentsMargins(16, 14, 16, 14);
        auto* recentHeader = new QHBoxLayout;
        recentHeader->addWidget(label("Недавняя работа"));
        recentHeader->addStretch(1);
        recentHeader->addWidget(label("Локально", "muted"));
        recentLayout->addLayout(recentHeader);
        recentLayout->addWidget(label(
            "Здесь появятся документы и проекты, которые вы откроете в нативных приложениях Mora.",
            "muted"));
        recentLayout->addStretch(1);
        mainColumn->addWidget(recent, 1);
        root->addLayout(mainColumn, 3);

        auto* side = new QVBoxLayout;
        side->setSpacing(12);
        auto* session = panel();
        auto* sessionLayout = new QVBoxLayout(session);
        sessionLayout->setContentsMargins(16, 14, 16, 16);
        sessionLayout->addWidget(label("СЕССИЯ", "eyebrow"));
        sessionLayout->addWidget(label("Нативная Mora", "heading"));
        sessionLayout->addWidget(label("Работает как отдельное приложение хостовой ОС.", "muted"));
        sessionLayout->addWidget(label("Окна ОС", "muted"));
        sessionLayout->addWidget(label("Включены", "body"));
        sessionLayout->addWidget(label("Службы ядра DuckOS", "muted"));
        sessionLayout->addWidget(label("Пока не подключены", "body"));
        side->addWidget(session);

        auto* quick = panel();
        auto* quickLayout = new QVBoxLayout(quick);
        quickLayout->setContentsMargins(16, 14, 16, 16);
        quickLayout->addWidget(label("БЫСТРЫЕ ДЕЙСТВИЯ", "eyebrow"));
        auto* openWorkspace = actionButton("Открыть три окна");
        openWorkspace->setObjectName("open-design-workspace");
        quickLayout->addWidget(openWorkspace);
        auto* browseApps = actionButton("Каталог приложений");
        browseApps->setObjectName("open-app-catalog");
        quickLayout->addWidget(browseApps);
        QObject::connect(openWorkspace, &QPushButton::clicked, this, [this]() { openDesignWorkspace(); });
        QObject::connect(browseApps, &QPushButton::clicked, this, [this]() { showPage(1); });
        side->addWidget(quick);
        side->addStretch(1);
        root->addLayout(side, 1);
        return page;
    }

    QWidget* buildAppsPage()
    {
        auto* page = new QWidget;
        auto* layout = new QVBoxLayout(page);
        layout->setContentsMargins(18, 12, 18, 14);
        layout->setSpacing(12);

        layout->addWidget(label("MORA COMMONS", "eyebrow"));
        layout->addWidget(label("Приложения", "title"));
        layout->addWidget(label("Знакомые инструменты. Одно пространство. Отдельные нативные окна.", "subtitle"));

        auto* filters = new QHBoxLayout;
        appsSearch_ = new QLineEdit;
        appsSearch_->setObjectName("apps-search");
        appsSearch_->setPlaceholderText("Поиск по названию или задаче");
        appsSearch_->setClearButtonEnabled(true);
        filters->addWidget(appsSearch_, 2);
        categoryFilter_ = new QComboBox;
        categoryFilter_->addItem("Все приложения", "all");
        categoryFilter_->addItem("Творчество", "creative");
        categoryFilter_->addItem("Работа", "work");
        categoryFilter_->addItem("Система", "system");
        filters->addWidget(categoryFilter_, 1);
        layout->addLayout(filters);

        auto* scroll = new QScrollArea;
        scroll->setWidgetResizable(true);
        auto* gridHost = new QWidget;
        appGrid_ = new QGridLayout(gridHost);
        appGrid_->setContentsMargins(0, 4, 6, 4);
        appGrid_->setHorizontalSpacing(10);
        appGrid_->setVerticalSpacing(10);
        scroll->setWidget(gridHost);
        layout->addWidget(scroll, 1);

        QObject::connect(appsSearch_, &QLineEdit::textChanged, this, [this]() { rebuildAppsGrid(); });
        QObject::connect(categoryFilter_, &QComboBox::currentIndexChanged, this, [this]() { rebuildAppsGrid(); });
        rebuildAppsGrid();
        return page;
    }

    QWidget* buildWorkspacePage()
    {
        auto* page = new QWidget;
        auto* layout = new QVBoxLayout(page);
        layout->setContentsMargins(18, 12, 18, 14);
        layout->setSpacing(14);
        layout->addWidget(label("РЕЖИМ РАБОЧЕГО СТОЛА", "eyebrow"));
        layout->addWidget(label("Три окна. Один поток.", "title"));
        layout->addWidget(label("Приложения открываются в самостоятельных окнах, которыми управляет оконная система хоста.", "subtitle"));

        auto* openSet = actionButton("Открыть рабочий набор");
        openSet->setObjectName("open-design-workspace");
        openSet->setMinimumHeight(48);
        layout->addWidget(openSet, 0, Qt::AlignLeft);
        QObject::connect(openSet, &QPushButton::clicked, this, [this]() { openDesignWorkspace(); });

        auto* cards = new QGridLayout;
        cards->setSpacing(12);
        const QList<QPair<QString, QString>> entries{
            {"abriganza", "Файлы и архивы"},
            {"poi", "Заметки и идеи"},
            {"ventusample-workbench", "Аудио и DSP"}
        };
        for (int i = 0; i < entries.size(); ++i) {
            const AppInfo info = findApp(entries[i].first);
            auto* tile = makeAppTile(info, entries[i].second);
            cards->addWidget(tile, 0, i);
        }
        layout->addLayout(cards);
        layout->addWidget(label(
            "Окна не являются HTML-элементами внутри рабочего стола: каждое окно создаётся как отдельный top-level QWidget с системной рамкой, фокусом и перемещением средствами оконной системы хоста.",
            "muted"));
        layout->addStretch(1);
        return page;
    }

    QPushButton* makeAppTile(const AppInfo& app, const QString& subtitle)
    {
        auto* tile = new QPushButton;
        tile->setObjectName("appTile");
        tile->setMinimumHeight(86);
        tile->setCursor(Qt::PointingHandCursor);
        auto* row = new QHBoxLayout(tile);
        row->setContentsMargins(14, 10, 14, 10);
        row->setSpacing(12);
        auto* glyph = label(categoryGlyph(app.category), "eyebrow");
        QFont glyphFont = glyph->font();
        glyphFont.setPointSize(22);
        glyph->setFont(glyphFont);
        glyph->setAlignment(Qt::AlignCenter);
        glyph->setFixedWidth(38);
        row->addWidget(glyph);

        auto* textColumn = new QVBoxLayout;
        textColumn->setSpacing(4);
        auto* name = label(app.name);
        QFont nameFont = name->font();
        nameFont.setWeight(QFont::DemiBold);
        name->setFont(nameFont);
        textColumn->addWidget(name);
        textColumn->addWidget(label(subtitle.isEmpty() ? categoryName(app.category) : subtitle, "muted"));
        row->addLayout(textColumn, 1);
        row->addWidget(label("↗", "muted"));
        QObject::connect(tile, &QPushButton::clicked, this, [this, id = app.id]() { openAppWindow(id); });
        return tile;
    }

    AppInfo findApp(const QString& id) const
    {
        const auto it = std::find_if(apps_.cbegin(), apps_.cend(),
            [&id](const AppInfo& app) { return app.id == id; });
        if (it != apps_.cend()) return *it;
        if (id == "ventusample-workbench") return {id, "VentuSample", "audio", "partial"};
        if (id == "reaper-workbench") return {id, "Reaper", "ecosystem", "partial"};
        if (id == "abriganza") return {id, "Abriganza", "files", "partial"};
        if (id == "poi") return {id, "Poi", "notes", "partial"};
        return {id, id, "system", "planned"};
    }

    void rebuildAppsGrid()
    {
        if (!appGrid_) return;
        while (QLayoutItem* item = appGrid_->takeAt(0)) {
            if (item->widget()) item->widget()->deleteLater();
            delete item;
        }

        const QString query = appsSearch_ ? appsSearch_->text().trimmed().toCaseFolded() : QString{};
        const QString category = categoryFilter_ ? categoryFilter_->currentData().toString() : "all";
        int position = 0;
        for (const AppInfo& app : apps_) {
            if (!query.isEmpty()
                && !app.name.toCaseFolded().contains(query)
                && !categoryName(app.category).toCaseFolded().contains(query)) {
                continue;
            }
            if (category == "creative" && app.category != "creative"
                && app.category != "audio" && app.category != "photos") continue;
            if (category == "work" && app.category != "productivity"
                && app.category != "files" && app.category != "notes"
                && app.category != "knowledge" && app.category != "ecosystem") continue;
            if (category == "system" && app.category != "system"
                && app.category != "security" && app.category != "recovery"
                && app.category != "workspace") continue;

            auto* tile = makeAppTile(app, categoryName(app.category) + " · " + maturityText(app.maturity));
            appGrid_->addWidget(tile, position / 3, position % 3);
            ++position;
        }
        if (position == 0) {
            auto* empty = label("Ничего не найдено. Измените запрос или категорию.", "muted");
            appGrid_->addWidget(empty, 0, 0, 1, 3);
        }
        appGrid_->setRowStretch((position + 2) / 3, 1);
    }

    void openAppWindow(const QString& id)
    {
        const AppInfo app = findApp(id);
        if (windows_.contains(id) && !windows_.value(id).isNull()) {
            windows_.value(id)->showNormal();
            windows_.value(id)->raise();
            windows_.value(id)->activateWindow();
            return;
        }

        auto* window = new AppWindow(app, this);
        windows_.insert(id, window);
        // QPointer tracks window lifetime without a callback into MoraWindow during base-class teardown.

        const QRect available = QApplication::primaryScreen()
            ? QApplication::primaryScreen()->availableGeometry() : QRect(0, 0, 1440, 900);
        const int offset = (windows_.size() - 1) * 34;
        window->move(available.x() + 90 + offset, available.y() + 70 + offset);
        window->show();
        window->raise();
        window->activateWindow();
    }

    void showPage(int index)
    {
        if (!pageStack_ || index < 0 || index >= pageStack_->count()) return;
        pageStack_->setCurrentIndex(index);
        if (navigationGroup_) {
            if (auto* button = navigationGroup_->button(index)) button->setChecked(true);
        }
    }

    void updateClock()
    {
        const QDateTime now = QDateTime::currentDateTime();
        if (dateLabel_) dateLabel_->setText(QLocale::system().toString(now.date(), QLocale::ShortFormat));
        if (timeLabel_) timeLabel_->setText(now.toString("HH:mm"));
    }
};

} // namespace

int main(int argc, char* argv[])
{
    QApplication application(argc, argv);
    loadThemeTokens();
    QApplication::setApplicationName("Mora");
    QApplication::setOrganizationName("DuckOS");

    const bool selfTest = application.arguments().contains("--self-test");
    MoraWindow window;
    if (selfTest) {
        QString failure;
        if (!window.runSelfTest(&failure)) {
            qCritical("Mora native smoke test failed: %s", qPrintable(failure));
            return 1;
        }
        qInfo("Mora native smoke test passed.");
        return 0;
    }

    window.show();
    return application.exec();
}
