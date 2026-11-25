#include "desktop_window.hpp"
#include "native_apps.hpp"

#include <QApplication>
#include <QComboBox>
#include <QDateTime>
#include <QDialog>
#include <QFrame>
#include <QGridLayout>
#include <QHBoxLayout>
#include <QKeySequence>
#include <QLabel>
#include <QLineEdit>
#include <QMessageBox>
#include <QPlainTextEdit>
#include <QPushButton>
#include <QScrollArea>
#include <QShortcut>
#include <QTextCursor>
#include <QTimer>
#include <QVBoxLayout>
#include <QWidget>

namespace {
QString cardStyle()
{
    return QStringLiteral(
        "QFrame#appCard { background:#111111; border:1px solid #383838; border-radius:12px; }"
        "QFrame#appCard:hover { border:1px solid #ffd400; background:#181818; }"
        "QLabel#appName { color:#f3f3f3; font-size:15px; font-weight:700; }"
        "QLabel#appState { color:#b7b7b7; font-size:11px; }"
        "QPushButton#launchButton { background:#ffd400; color:#080808; border:0; border-radius:8px; padding:8px 14px; font-weight:700; }");
}
}

DesktopWindow::DesktopWindow(ApplicationCatalog catalog, QWidget *parent)
    : QMainWindow(parent), catalog_(std::move(catalog)), launcher_(catalog_.rootPath(), this)
{
    setWindowTitle(QStringLiteral("DuckOS · Native Desktop"));
    resize(1440, 900);
    setMinimumSize(960, 640);
    setStyleSheet(QStringLiteral(
        "QMainWindow, QWidget { background:#070707; color:#f3f3f3; }"
        "QLineEdit, QComboBox, QPlainTextEdit { background:#151515; color:#f3f3f3; border:1px solid #454545; border-radius:8px; padding:8px; }"
        "QPushButton { background:#242424; color:#f3f3f3; border:1px solid #444444; border-radius:8px; padding:8px 12px; }"
        "QPushButton:hover { border-color:#ffd400; }"
        "QScrollArea { border:0; }"));
    buildUi();
}

void DesktopWindow::buildUi()
{
    auto *root = new QWidget(this);
    auto *layout = new QVBoxLayout(root);
    layout->setContentsMargins(24, 20, 24, 18);
    layout->setSpacing(14);

    auto *top = new QHBoxLayout;
    auto *brand = new QLabel(QStringLiteral("DUCKOS  /  MORA NATIVE"), root);
    brand->setStyleSheet(QStringLiteral("font-size:17px; font-weight:800; color:#ffd400;"));
    clock_ = new QLabel(root);
    clock_->setAlignment(Qt::AlignRight | Qt::AlignVCenter);
    clock_->setStyleSheet(QStringLiteral("font-size:13px; color:#dddddd;"));
    top->addWidget(brand);
    top->addStretch();
    top->addWidget(clock_);
    layout->addLayout(top);

    auto *headline = new QLabel(QStringLiteral("Живая рабочая среда DuckOS"), root);
    headline->setStyleSheet(QStringLiteral("font-size:30px; font-weight:800; color:#f5f5f5;"));
    auto *subtitle = new QLabel(QStringLiteral("Native Qt desktop · реальные окна и процессы · без браузера, WebView и HTML-оболочки"), root);
    subtitle->setStyleSheet(QStringLiteral("color:#a1a1a1;"));
    layout->addWidget(headline);
    layout->addWidget(subtitle);

    auto *toolbar = new QHBoxLayout;
    search_ = new QLineEdit(root);
    search_->setPlaceholderText(QStringLiteral("Найти приложение…"));
    category_ = new QComboBox(root);
    category_->addItems({QStringLiteral("Все приложения"), QStringLiteral("System"), QStringLiteral("Developer Tools"),
                         QStringLiteral("Productivity"), QStringLiteral("Multimedia"), QStringLiteral("Games"),
                         QStringLiteral("Tools"), QStringLiteral("Applications"), QStringLiteral("Utilities")});
    toolbar->addWidget(search_, 1);
    toolbar->addWidget(category_);
    layout->addLayout(toolbar);

    auto *catalogHeading = new QHBoxLayout;
    auto *catalogLabel = new QLabel(QStringLiteral("ПРИЛОЖЕНИЯ"), root);
    catalogLabel->setStyleSheet(QStringLiteral("font-size:12px; font-weight:800; letter-spacing:2px; color:#ffd400;"));
    status_ = new QLabel(root);
    status_->setStyleSheet(QStringLiteral("color:#a1a1a1;"));
    catalogHeading->addWidget(catalogLabel);
    catalogHeading->addStretch();
    catalogHeading->addWidget(status_);
    layout->addLayout(catalogHeading);

    auto *scroll = new QScrollArea(root);
    scroll->setWidgetResizable(true);
    gridHost_ = new QWidget(scroll);
    grid_ = new QGridLayout(gridHost_);
    grid_->setContentsMargins(2, 2, 8, 8);
    grid_->setHorizontalSpacing(12);
    grid_->setVerticalSpacing(12);
    scroll->setWidget(gridHost_);
    layout->addWidget(scroll, 1);

    auto *dock = new QHBoxLayout;
    const auto addDockButton = [dock, root](const QString &title, const QString &id) {
        auto *button = new QPushButton(title, root);
        QObject::connect(button, &QPushButton::clicked, root, [root, id] {
            auto *window = qobject_cast<DesktopWindow *>(root->window());
            if (window) window->openApplication(id);
        });
        dock->addWidget(button);
    };
    addDockButton(QStringLiteral("Files"), QStringLiteral("files"));
    addDockButton(QStringLiteral("Notes"), QStringLiteral("notes"));
    addDockButton(QStringLiteral("Calculator"), QStringLiteral("calculator"));
    addDockButton(QStringLiteral("Settings"), QStringLiteral("setupup"));
    addDockButton(QStringLiteral("Sestem"), QStringLiteral("sestem"));
    dock->addStretch();
    layout->addLayout(dock);

    setCentralWidget(root);
    connect(search_, &QLineEdit::textChanged, this, &DesktopWindow::rebuildGrid);
    connect(category_, &QComboBox::currentTextChanged, this, &DesktopWindow::rebuildGrid);

    auto *fullscreen = new QShortcut(QKeySequence(Qt::Key_F11), this);
    connect(fullscreen, &QShortcut::activated, this, [this] {
        isFullScreen() ? showMaximized() : showFullScreen();
    });
    auto *quit = new QShortcut(QKeySequence(Qt::CTRL | Qt::Key_Q), this);
    connect(quit, &QShortcut::activated, qApp, &QApplication::quit);

    auto *timer = new QTimer(this);
    connect(timer, &QTimer::timeout, this, [this] {
        clock_->setText(QDateTime::currentDateTime().toString(QStringLiteral("ddd, dd MMM  ·  HH:mm:ss")));
    });
    timer->start(1000);
    clock_->setText(QDateTime::currentDateTime().toString(QStringLiteral("ddd, dd MMM  ·  HH:mm:ss")));
    rebuildGrid();
}

void DesktopWindow::rebuildGrid()
{
    while (QLayoutItem *item = grid_->takeAt(0)) {
        if (QWidget *widget = item->widget()) widget->deleteLater();
        delete item;
    }
    const QString query = search_->text().trimmed().toCaseFolded();
    const QString selectedCategory = category_->currentText();
    int visible = 0;
    int index = 0;
    for (const ApplicationInfo &application : catalog_.applications()) {
        if (selectedCategory != QStringLiteral("Все приложения") && application.category != selectedCategory) continue;
        if (!query.isEmpty() && !application.name.toCaseFolded().contains(query)
            && !application.id.toCaseFolded().contains(query)
            && !application.description.toCaseFolded().contains(query)) continue;

        auto *card = new QFrame(gridHost_);
        card->setObjectName(QStringLiteral("appCard"));
        card->setStyleSheet(cardStyle());
        auto *cardLayout = new QVBoxLayout(card);
        cardLayout->setContentsMargins(14, 12, 14, 12);
        auto *name = new QLabel(application.name, card);
        name->setObjectName(QStringLiteral("appName"));
        auto *state = new QLabel(statusText(application), card);
        state->setObjectName(QStringLiteral("appState"));
        state->setWordWrap(true);
        auto *description = new QLabel(application.description, card);
        description->setStyleSheet(QStringLiteral("color:#a1a1a1;"));
        description->setWordWrap(true);
        description->setMaximumHeight(42);
        auto *button = new QPushButton(application.launchable ? QStringLiteral("Открыть") : QStringLiteral("Подробнее"), card);
        button->setObjectName(QStringLiteral("launchButton"));
        cardLayout->addWidget(name);
        cardLayout->addWidget(state);
        cardLayout->addWidget(description, 1);
        cardLayout->addWidget(button);
        connect(button, &QPushButton::clicked, this, [this, id = application.id] { openApplication(id); });
        grid_->addWidget(card, index / 4, index % 4);
        ++index;
        ++visible;
    }
    status_->setText(QStringLiteral("%1 приложений · %2 нативных модулей · %3 подключаемых процессов")
        .arg(visible).arg(catalog_.nativeCount()).arg(catalog_.launchableCount()));
}

QString DesktopWindow::statusText(const ApplicationInfo &application) const
{
    if (!application.nativeAction.isEmpty()) return QStringLiteral("NATIVE · встроенный модуль");
    if (application.launchable) return QStringLiteral("READY · подключённый процесс");
    return QStringLiteral("NOT PORTED · спецификация / прототип");
}

void DesktopWindow::openApplication(const QString &id)
{
    const ApplicationInfo *application = catalog_.find(id);
    if (!application) return;
    if (!application->nativeAction.isEmpty()) {
        NativeApps::open(application->nativeAction, application->id, application->name, this);
        return;
    }
    if (application->launchable) {
        launchProcess(*application);
        return;
    }
    showApplicationInfo(*application);
}

void DesktopWindow::launchProcess(const ApplicationInfo &application)
{
    QString error;
    QProcess *process = launcher_.start(application, &error);
    if (!process) {
        QMessageBox::warning(this, QStringLiteral("DuckOS · %1").arg(application.name), error);
        return;
    }

    bool guiProcess = application.id == QStringLiteral("ventusample-workbench")
        || application.id == QStringLiteral("oplague-workbench");
#ifdef Q_OS_WIN
    guiProcess = guiProcess || application.id == QStringLiteral("pytyliki-workbench");
#endif
    if (guiProcess) {
        status_->setText(QStringLiteral("%1 запущено как отдельное native-приложение.").arg(application.name));
        connect(process, &QProcess::finished, this, [this, name = application.name](int, QProcess::ExitStatus) {
            status_->setText(QStringLiteral("%1 закрыто.").arg(name));
        });
        connect(process, &QProcess::errorOccurred, this, [this, process, name = application.name](QProcess::ProcessError) {
            if (process->state() == QProcess::NotRunning)
                QMessageBox::warning(this, QStringLiteral("DuckOS"), QStringLiteral("%1: %2").arg(name, process->errorString()));
        });
    } else {
        showProcessOutput(application, process);
    }
}

void DesktopWindow::showProcessOutput(const ApplicationInfo &application, QProcess *process)
{
    auto *dialog = new QDialog(this);
    dialog->setAttribute(Qt::WA_DeleteOnClose);
    dialog->setWindowTitle(QStringLiteral("%1 · Native process").arg(application.name));
    dialog->resize(760, 520);
    auto *layout = new QVBoxLayout(dialog);
    auto *output = new QPlainTextEdit(dialog);
    output->setReadOnly(true);
    output->setPlaceholderText(QStringLiteral("Ожидание вывода процесса…"));
    auto *close = new QPushButton(QStringLiteral("Закрыть окно вывода"), dialog);
    layout->addWidget(output, 1);
    layout->addWidget(close);
    connect(process, &QProcess::readyReadStandardOutput, dialog, [process, output] {
        output->moveCursor(QTextCursor::End);
        output->insertPlainText(QString::fromLocal8Bit(process->readAllStandardOutput()));
    });
    connect(process, &QProcess::finished, dialog, [process, output](int code, QProcess::ExitStatus) {
        output->appendPlainText(QStringLiteral("\n[process finished: %1]").arg(code));
        process->deleteLater();
    });
    connect(close, &QPushButton::clicked, dialog, &QDialog::close);
    dialog->show();
}

void DesktopWindow::showApplicationInfo(const ApplicationInfo &application)
{
    QMessageBox::information(this, application.name,
        QStringLiteral("%1\n\nКатегория: %2\nID: %3\nСостояние: native-порт ещё не реализован.\n\nЭто историческая запись приложения. Её браузерный прототип не считается нативной программой, поэтому кнопка запуска отключена до появления настоящей реализации.")
            .arg(application.description, application.category, application.id));
}
