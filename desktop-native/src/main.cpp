#include "application_catalog.hpp"
#include "desktop_window.hpp"

#include <QApplication>
#include <QCommandLineParser>
#include <QDir>
#include <QFileInfo>
#include <QMessageBox>
#include <QTimer>
#include <QTextStream>

#ifndef DUCKOS_SOURCE_ROOT
#define DUCKOS_SOURCE_ROOT "."
#endif

namespace {
QString discoverRoot(const QString &executablePath)
{
    const QString envRoot = qEnvironmentVariable("DUCKOS_ROOT");
    if (!envRoot.isEmpty() && QFileInfo(QDir(envRoot).filePath(QStringLiteral("mora/apps.json"))).isFile())
        return QFileInfo(envRoot).canonicalFilePath();

    QDir candidate = QFileInfo(executablePath).absoluteDir();
    for (int depth = 0; depth < 7; ++depth) {
        if (QFileInfo(candidate.filePath(QStringLiteral("mora/apps.json"))).isFile()
            && QFileInfo(candidate.filePath(QStringLiteral("catalogs/native-launchers.v1.json"))).isFile())
            return candidate.canonicalPath();
        if (!candidate.cdUp()) break;
    }
    const QString sourceRoot = QString::fromUtf8(DUCKOS_SOURCE_ROOT);
    if (QFileInfo(QDir(sourceRoot).filePath(QStringLiteral("mora/apps.json"))).isFile())
        return QFileInfo(sourceRoot).canonicalFilePath();
    return {};
}
}

int main(int argc, char *argv[])
{
    QApplication app(argc, argv);
    QApplication::setOrganizationName(QStringLiteral("Ivan-VHS"));
    QApplication::setApplicationName(QStringLiteral("DuckOS Native Desktop"));
    QApplication::setApplicationDisplayName(QStringLiteral("DuckOS · Native Desktop"));

    QCommandLineParser parser;
    parser.setApplicationDescription(QStringLiteral("Native Qt desktop shell for DuckOS. It does not embed a browser or WebView."));
    parser.addHelpOption();
    parser.addVersionOption();
    QCommandLineOption rootOption({QStringLiteral("r"), QStringLiteral("root")},
        QStringLiteral("DuckOS package root containing mora/, catalogs/ and federation/."), QStringLiteral("path"));
    QCommandLineOption validateOption(QStringLiteral("validate-catalog"), QStringLiteral("Load and validate the native app catalog, then exit."));
    QCommandLineOption smokeOption(QStringLiteral("smoke-test"), QStringLiteral("Create the native shell offscreen and exit."));
    QCommandLineOption fullscreenOption(QStringLiteral("fullscreen"), QStringLiteral("Open the desktop full-screen."));
    parser.addOption(rootOption);
    parser.addOption(validateOption);
    parser.addOption(smokeOption);
    parser.addOption(fullscreenOption);
    parser.process(app);

    const QString root = parser.isSet(rootOption)
        ? QFileInfo(parser.value(rootOption)).canonicalFilePath()
        : discoverRoot(QCoreApplication::applicationFilePath());
    if (root.isEmpty()) {
        QMessageBox::critical(nullptr, QStringLiteral("DuckOS"),
            QStringLiteral("Не найден каталог DuckOS. Укажи --root PATH или установи приложение рядом с пакетом DuckOS."));
        return 2;
    }

    ApplicationCatalog catalog;
    QString error;
    if (!ApplicationCatalog::load(root, &catalog, &error)) {
        QMessageBox::critical(nullptr, QStringLiteral("DuckOS · Catalog error"), error);
        return 2;
    }
    if (parser.isSet(validateOption)) {
        QTextStream output(stdout);
        output << QStringLiteral("DuckOS native catalog: %1 apps, %2 built-in modules, %3 external launchers.")
            .arg(catalog.applications().size()).arg(catalog.nativeCount()).arg(catalog.launchableCount()) << Qt::endl;
        return 0;
    }

    DesktopWindow window(std::move(catalog));
    window.showMaximized();
    if (parser.isSet(fullscreenOption)) window.showFullScreen();
    if (parser.isSet(smokeOption)) QTimer::singleShot(250, &app, &QApplication::quit);
    return app.exec();
}
