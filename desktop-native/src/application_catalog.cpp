#include "application_catalog.hpp"

#include <QDir>
#include <QFile>
#include <QFileInfo>
#include <QJsonArray>
#include <QJsonDocument>
#include <QJsonParseError>
#include <QMap>
#include <QSet>
#include <QStandardPaths>

namespace {
bool readObject(const QString &path, QJsonObject *object, QString *error)
{
    QFile file(path);
    if (!file.open(QIODevice::ReadOnly)) {
        if (error) *error = QStringLiteral("Cannot open %1: %2").arg(path, file.errorString());
        return false;
    }
    QJsonParseError parseError;
    const QJsonDocument document = QJsonDocument::fromJson(file.readAll(), &parseError);
    if (parseError.error != QJsonParseError::NoError || !document.isObject()) {
        if (error) *error = QStringLiteral("Invalid JSON in %1: %2").arg(path, parseError.errorString());
        return false;
    }
    *object = document.object();
    return true;
}

bool isInsideRoot(const QString &root, const QString &candidate)
{
    const QString canonicalRoot = QFileInfo(root).canonicalFilePath();
    const QString canonicalCandidate = QFileInfo(candidate).canonicalFilePath();
    if (canonicalRoot.isEmpty() || canonicalCandidate.isEmpty()) return false;
    const QString relative = QDir::fromNativeSeparators(
        QDir::cleanPath(QDir(canonicalRoot).relativeFilePath(canonicalCandidate)));
    return relative == QStringLiteral(".")
        || (relative != QStringLiteral("..")
            && !relative.startsWith(QStringLiteral("../"))
            && !QDir::isAbsolutePath(relative));
}

QString nativeActionFor(const QString &id)
{
    static const QMap<QString, QString> actions{
        {QStringLiteral("sestem"), QStringLiteral("system-overview")},
        {QStringLiteral("kavun"), QStringLiteral("local-collection")},
        {QStringLiteral("kabon"), QStringLiteral("local-collection")},
        {QStringLiteral("gloverty"), QStringLiteral("local-collection")},
        {QStringLiteral("illidia"), QStringLiteral("local-collection")},
        {QStringLiteral("unify"), QStringLiteral("local-collection")},
        {QStringLiteral("orriganize"), QStringLiteral("local-collection")},
        {QStringLiteral("olaab"), QStringLiteral("local-collection")},
        {QStringLiteral("seu-beu"), QStringLiteral("local-collection")},
        {QStringLiteral("red-sparrow"), QStringLiteral("local-collection")},
        {QStringLiteral("exedotexe"), QStringLiteral("executable-inspector")},
        {QStringLiteral("runtime"), QStringLiteral("executable-inspector")},
        {QStringLiteral("love-il"), QStringLiteral("local-collection")},
        {QStringLiteral("poi"), QStringLiteral("local-collection")},
        {QStringLiteral("poi-2"), QStringLiteral("local-collection")},
        {QStringLiteral("po-2"), QStringLiteral("local-collection")},
        {QStringLiteral("gamecharager"), QStringLiteral("local-collection")},
        {QStringLiteral("workspace"), QStringLiteral("system-overview")},
        {QStringLiteral("setupup"), QStringLiteral("settings")},
        {QStringLiteral("desktop"), QStringLiteral("file-manager")},
        {QStringLiteral("abriganza"), QStringLiteral("archive-inspector")},
        {QStringLiteral("provenance"), QStringLiteral("file-verifier")},
        {QStringLiteral("concrete-thump"), QStringLiteral("rhythm-profile")},
        {QStringLiteral("mora-commons"), QStringLiteral("app-catalog")},
        {QStringLiteral("security"), QStringLiteral("security-status")},
        {QStringLiteral("updates"), QStringLiteral("release-status")},
        {QStringLiteral("mora-boost"), QStringLiteral("performance-status")},
        {QStringLiteral("files"), QStringLiteral("file-manager")},
        {QStringLiteral("notes"), QStringLiteral("notes")},
        {QStringLiteral("calculator"), QStringLiteral("calculator")},
        {QStringLiteral("clock"), QStringLiteral("clock")}
    };
    return actions.value(id);
}

QString categoryFor(const QString &domain)
{
    if (domain.contains(QStringLiteral("audio")) || domain.contains(QStringLiteral("media"))) return QStringLiteral("Multimedia");
    if (domain.contains(QStringLiteral("game"))) return QStringLiteral("Games");
    if (domain.contains(QStringLiteral("system")) || domain.contains(QStringLiteral("setup"))) return QStringLiteral("System");
    if (domain.contains(QStringLiteral("archive")) || domain.contains(QStringLiteral("executable"))) return QStringLiteral("Tools");
    if (domain.contains(QStringLiteral("project")) || domain.contains(QStringLiteral("task")) || domain.contains(QStringLiteral("journal"))) return QStringLiteral("Productivity");
    return QStringLiteral("Applications");
}

QStringList stringArray(const QJsonValue &value)
{
    QStringList result;
    if (!value.isArray()) return result;
    for (const QJsonValue &entry : value.toArray()) if (entry.isString()) result.push_back(entry.toString());
    return result;
}

QString platformKey()
{
#ifdef Q_OS_WIN
    return QStringLiteral("windows");
#elif defined(Q_OS_MACOS)
    return QStringLiteral("macos");
#else
    return QStringLiteral("unix");
#endif
}
}

bool ApplicationCatalog::load(const QString &rootPath, ApplicationCatalog *catalog, QString *error)
{
    if (!catalog) {
        if (error) *error = QStringLiteral("Catalog output pointer is null.");
        return false;
    }
    const QFileInfo rootInfo(rootPath);
    if (!rootInfo.exists() || !rootInfo.isDir()) {
        if (error) *error = QStringLiteral("DuckOS root directory does not exist: %1").arg(rootPath);
        return false;
    }

    ApplicationCatalog loaded;
    loaded.rootPath_ = rootInfo.canonicalFilePath();
    QJsonObject mora, preinstalled, workbenches, launchers;
    if (!readObject(QDir(loaded.rootPath_).filePath(QStringLiteral("mora/apps.json")), &mora, error)
        || !readObject(QDir(loaded.rootPath_).filePath(QStringLiteral("catalogs/preinstalled-applications.v1.json")), &preinstalled, error)
        || !readObject(QDir(loaded.rootPath_).filePath(QStringLiteral("federation/mora-workbenches.v1.json")), &workbenches, error)
        || !readObject(QDir(loaded.rootPath_).filePath(QStringLiteral("catalogs/native-launchers.v1.json")), &launchers, error)) {
        return false;
    }
    if (!loaded.addBuiltIns(mora, preinstalled, error) || !loaded.addWorkbenches(workbenches, launchers, error)) return false;
    *catalog = std::move(loaded);
    return true;
}

bool ApplicationCatalog::addBuiltIns(const QJsonObject &mora, const QJsonObject &preinstalled, QString *error)
{
    const QJsonArray builtIns = mora.value(QStringLiteral("built_in_apps")).toArray();
    if (builtIns.isEmpty()) {
        if (error) *error = QStringLiteral("Mora app registry contains no built-in applications.");
        return false;
    }

    QMap<QString, QJsonObject> specs;
    for (const QJsonValue &value : preinstalled.value(QStringLiteral("applications")).toArray()) {
        const QJsonObject app = value.toObject();
        QString id = app.value(QStringLiteral("id")).toString();
        if (id == QStringLiteral("ka-bon")) id = QStringLiteral("kabon");
        if (!id.isEmpty()) specs.insert(id, app);
    }

    QSet<QString> seen;
    for (const QJsonValue &value : builtIns) {
        const QJsonObject entry = value.toObject();
        ApplicationInfo app;
        app.id = entry.value(QStringLiteral("id")).toString().trimmed();
        app.name = entry.value(QStringLiteral("name")).toString().trimmed();
        if (app.id.isEmpty() || app.name.isEmpty() || seen.contains(app.id)) continue;
        seen.insert(app.id);
        const QJsonObject spec = specs.value(app.id);
        app.category = categoryFor(spec.value(QStringLiteral("domain")).toString());
        const QJsonArray boundaries = spec.value(QStringLiteral("boundaries")).toArray();
        if (!boundaries.isEmpty()) app.description = boundaries.first().toString();
        if (app.description.isEmpty()) app.description = QStringLiteral("Historical DuckOS app identity. Native feature port is tracked separately.");
        app.nativeAction = nativeActionFor(app.id);
        app.state = app.nativeAction.isEmpty() ? QStringLiteral("not-ported") : QStringLiteral("native");
        app.launchable = !app.nativeAction.isEmpty();
        applications_.push_back(std::move(app));
    }

    const auto addUtility = [this, &seen](const QString &id, const QString &name, const QString &action, const QString &category) {
        if (seen.contains(id)) return;
        ApplicationInfo app;
        app.id = id;
        app.name = name;
        app.category = category;
        app.description = QStringLiteral("Native Qt desktop utility; no browser engine is involved.");
        app.nativeAction = action;
        app.state = QStringLiteral("native");
        app.launchable = true;
        applications_.push_back(std::move(app));
        seen.insert(id);
    };
    addUtility(QStringLiteral("files"), QStringLiteral("Files"), QStringLiteral("file-manager"), QStringLiteral("System"));
    addUtility(QStringLiteral("notes"), QStringLiteral("Notes"), QStringLiteral("notes"), QStringLiteral("Productivity"));
    addUtility(QStringLiteral("calculator"), QStringLiteral("Calculator"), QStringLiteral("calculator"), QStringLiteral("Utilities"));
    addUtility(QStringLiteral("clock"), QStringLiteral("Clock"), QStringLiteral("clock"), QStringLiteral("Utilities"));
    return true;
}

bool ApplicationCatalog::addWorkbenches(const QJsonObject &workbenches, const QJsonObject &launchers, QString *error)
{
    const QJsonObject policy = launchers.value(QStringLiteral("execution_policy")).toObject();
    if (policy.value(QStringLiteral("shell_interpreter")).toBool(true)
        || !policy.value(QStringLiteral("require_user_initiated_launch")).toBool(false)
        || !policy.value(QStringLiteral("fixed_manifest_arguments")).toBool(false)
        || !policy.value(QStringLiteral("executable_must_resolve_inside_package")).toBool(false)
        || !policy.value(QStringLiteral("working_directory_must_resolve_inside_package")).toBool(false)
        || policy.value(QStringLiteral("elevated_execution")).toBool(true)
        || policy.value(QStringLiteral("driver_installation")).toBool(true)) {
        if (error) *error = QStringLiteral("Native launcher policy violates the DuckOS no-shell, user-approval or package-boundary contract.");
        return false;
    }

    const QJsonArray workbenchEntries = workbenches.value(QStringLiteral("workbenches")).toArray();
    const QJsonArray launchEntries = launchers.value(QStringLiteral("applications")).toArray();
    if (workbenchEntries.isEmpty() || launchEntries.isEmpty()) {
        if (error) *error = QStringLiteral("Native workbench or launcher manifest is empty.");
        return false;
    }
    QMap<QString, QJsonObject> launchById;
    for (const QJsonValue &value : launchEntries) {
        const QJsonObject item = value.toObject();
        const QString id = item.value(QStringLiteral("id")).toString();
        if (!id.isEmpty()) launchById.insert(id, item);
    }

    for (const QJsonValue &value : workbenchEntries) {
        const QJsonObject entry = value.toObject();
        ApplicationInfo app;
        app.id = entry.value(QStringLiteral("id")).toString();
        app.name = entry.value(QStringLiteral("name")).toString();
        app.category = QStringLiteral("Developer Tools");
        app.description = entry.value(QStringLiteral("runtime_boundary")).toString();
        app.launchKind = QStringLiteral("process");

        const QJsonObject launcher = launchById.value(app.id);
        const QJsonObject platform = launcher.value(QStringLiteral("platforms")).toObject().value(platformKey()).toObject();
        const QString relativeTarget = platform.value(QStringLiteral("program")).toString();
        app.arguments = stringArray(platform.value(QStringLiteral("arguments")));
        app.pythonArguments = stringArray(platform.value(QStringLiteral("python_arguments")));
        app.workingDirectory = platform.value(QStringLiteral("working_directory")).toString();
        app.launchKind = launcher.value(QStringLiteral("kind")).toString(QStringLiteral("process"));
        app.target = relativeTarget;
        if (app.launchKind != QStringLiteral("process") && app.launchKind != QStringLiteral("python-script")) {
            if (error) *error = QStringLiteral("Unsupported native launcher kind for %1.").arg(app.id);
            return false;
        }

        if (!launcher.isEmpty() && !relativeTarget.isEmpty()) {
            const QString absoluteTarget = QDir(rootPath_).filePath(relativeTarget);
            const QFileInfo targetInfo(absoluteTarget);
            const QString workingDirectory = app.workingDirectory.isEmpty() ? rootPath_ : QDir(rootPath_).filePath(app.workingDirectory);
            const QFileInfo workingInfo(workingDirectory);
            const bool relativeSafe = !relativeTarget.startsWith(QLatin1Char('/'))
                && !relativeTarget.startsWith(QStringLiteral(".."));
            const bool targetSafe = relativeSafe && isInsideRoot(rootPath_, absoluteTarget) && targetInfo.isFile();
            const bool workingSafe = isInsideRoot(rootPath_, workingDirectory) && workingInfo.isDir();
            bool runtimeReady = true;
            if (app.launchKind == QStringLiteral("python-script")) {
#ifdef Q_OS_WIN
                runtimeReady = !QStandardPaths::findExecutable(QStringLiteral("py")).isEmpty()
                    || !QStandardPaths::findExecutable(QStringLiteral("python")).isEmpty();
#else
                runtimeReady = !QStandardPaths::findExecutable(QStringLiteral("python3")).isEmpty();
#endif
            }
            app.launchable = targetSafe && workingSafe && runtimeReady;
        }

        app.state = app.launchable ? QStringLiteral("ready") : QStringLiteral("needs-build");
        app.description += app.launchable
            ? QStringLiteral(" · Native process is present on this host.")
            : QStringLiteral(" · Build or runtime is missing on this host.");
        if (app.id.isEmpty() || app.name.isEmpty()) {
            if (error) *error = QStringLiteral("A native workbench entry is missing its id or name.");
            return false;
        }
        applications_.push_back(std::move(app));
    }
    return true;
}

const QVector<ApplicationInfo> &ApplicationCatalog::applications() const noexcept { return applications_; }
QString ApplicationCatalog::rootPath() const { return rootPath_; }
const ApplicationInfo *ApplicationCatalog::find(const QString &id) const noexcept
{
    for (const ApplicationInfo &app : applications_) if (app.id == id) return &app;
    return nullptr;
}
int ApplicationCatalog::launchableCount() const noexcept
{
    int count = 0;
    for (const ApplicationInfo &app : applications_) if (app.launchable && app.nativeAction.isEmpty()) ++count;
    return count;
}
int ApplicationCatalog::nativeCount() const noexcept
{
    int count = 0;
    for (const ApplicationInfo &app : applications_) if (!app.nativeAction.isEmpty()) ++count;
    return count;
}
