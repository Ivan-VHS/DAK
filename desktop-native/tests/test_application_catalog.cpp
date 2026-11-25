#include "application_catalog.hpp"
#include "application_launcher.hpp"

#include <QCoreApplication>
#include <QTemporaryDir>
#include <iostream>

#ifndef DUCKOS_SOURCE_ROOT
#define DUCKOS_SOURCE_ROOT "."
#endif

int main(int argc, char *argv[])
{
    QCoreApplication app(argc, argv);
    Q_UNUSED(app);

    const QString root = QString::fromUtf8(DUCKOS_SOURCE_ROOT);
    ApplicationCatalog catalog;
    QString error;
    if (!ApplicationCatalog::load(root, &catalog, &error)) {
        std::cerr << error.toStdString() << '\n';
        return 1;
    }
    if (catalog.applications().size() < 30) {
        std::cerr << "Expected the full Mora historical app registry.\n";
        return 2;
    }
    for (const QString &id : {QStringLiteral("cockos"), QStringLiteral("kabon"),
                              QStringLiteral("orriganize"), QStringLiteral("red-sparrow"),
                              QStringLiteral("mora-ai"), QStringLiteral("reaper-workbench"),
                              QStringLiteral("pytyliki-workbench"), QStringLiteral("oplague-workbench"),
                              QStringLiteral("ventusample-workbench"), QStringLiteral("files"),
                              QStringLiteral("notes"), QStringLiteral("calculator")}) {
        if (!catalog.find(id)) {
            std::cerr << "Missing app registry entry: " << id.toStdString() << '\n';
            return 3;
        }
    }
    if (catalog.nativeCount() < 30) {
        std::cerr << "Expected native built-in and local-collection apps to be registered.\n";
        return 4;
    }
    for (const QString &id : {QStringLiteral("kavun"), QStringLiteral("kabon"),
                              QStringLiteral("gloverty"), QStringLiteral("illidia"),
                              QStringLiteral("unify"), QStringLiteral("olaab"),
                              QStringLiteral("seu-beu"), QStringLiteral("love-il"),
                              QStringLiteral("poi"), QStringLiteral("poi-2"),
                              QStringLiteral("po-2"), QStringLiteral("gamecharager"),
                              QStringLiteral("red-sparrow"), QStringLiteral("exedotexe"),
                              QStringLiteral("runtime")}) {
        const ApplicationInfo *entry = catalog.find(id);
        if (!entry || !entry->launchable || entry->nativeAction != QStringLiteral("local-collection")) {
            std::cerr << "Missing native local collection port: " << id.toStdString() << '\\n';
            return 7;
        }
    }

    QTemporaryDir unsafeRoot;
    if (!unsafeRoot.isValid()) return 5;
    ApplicationInfo bad;
    bad.id = QStringLiteral("bad");
    bad.name = QStringLiteral("Bad launcher");
    bad.target = QStringLiteral("../outside");
    bad.launchable = true;
    ApplicationLauncher launcher(unsafeRoot.path());
    if (!launcher.resolveTarget(bad, &error).isEmpty()) {
        std::cerr << "Path traversal was not rejected.\n";
        return 6;
    }

    for (const QString &id : {QStringLiteral("cockos"), QStringLiteral("po"), QStringLiteral("mora-ai")}) {
        const ApplicationInfo *entry = catalog.find(id);
        if (!entry || entry->launchable || entry->state != QStringLiteral("not-ported")) {
            std::cerr << "Large legacy app must remain explicitly not ported: " << id.toStdString() << '\\n';
            return 8;
        }
    }

    std::cout << "Native app catalog passed: " << catalog.applications().size()
              << " entries, " << catalog.nativeCount() << " built-in modules, "
              << catalog.launchableCount() << " host launchers.\n";
    return 0;
}
