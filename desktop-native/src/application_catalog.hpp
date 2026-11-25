#pragma once

#include <QJsonObject>
#include <QString>
#include <QStringList>
#include <QVector>

struct ApplicationInfo {
    QString id;
    QString name;
    QString category;
    QString description;
    QString state;
    QString nativeAction;
    QString launchKind;
    QString target;
    QString workingDirectory;
    QStringList arguments;
    QStringList pythonArguments;
    bool launchable = false;
};

class ApplicationCatalog final {
public:
    static bool load(const QString &rootPath, ApplicationCatalog *catalog, QString *error);
    const QVector<ApplicationInfo> &applications() const noexcept;
    QString rootPath() const;
    const ApplicationInfo *find(const QString &id) const noexcept;
    int launchableCount() const noexcept;
    int nativeCount() const noexcept;

private:
    QString rootPath_;
    QVector<ApplicationInfo> applications_;
    bool addBuiltIns(const QJsonObject &mora, const QJsonObject &preinstalled, QString *error);
    bool addWorkbenches(const QJsonObject &workbenches, const QJsonObject &launchers, QString *error);
};
