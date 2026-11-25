#pragma once

#include "application_catalog.hpp"

#include <QObject>
#include <QProcess>

class ApplicationLauncher final : public QObject {
    Q_OBJECT
public:
    explicit ApplicationLauncher(QString rootPath, QObject *parent = nullptr);
    QProcess *start(const ApplicationInfo &application, QString *error);
    QString resolveTarget(const ApplicationInfo &application, QString *error) const;
private:
    QString rootPath_;
};
