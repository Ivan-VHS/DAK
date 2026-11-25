#include "application_launcher.hpp"

#include <QDir>
#include <QFileInfo>
#include <QStandardPaths>

namespace {
bool isInsidePackage(const QString &root, const QString &candidate)
{
    const QString canonicalRoot = QFileInfo(root).canonicalFilePath();
    const QString canonicalCandidate = QFileInfo(candidate).canonicalFilePath();
    if (canonicalRoot.isEmpty() || canonicalCandidate.isEmpty()) return false;
    const QString relative = QDir::fromNativeSeparators(
        QDir::cleanPath(QDir(canonicalRoot).relativeFilePath(canonicalCandidate)));
    return relative == QStringLiteral(".")
        || (relative != QStringLiteral("..") && !relative.startsWith(QStringLiteral("../"))
            && !QDir::isAbsolutePath(relative));
}
}

ApplicationLauncher::ApplicationLauncher(QString rootPath, QObject *parent)
    : QObject(parent), rootPath_(std::move(rootPath))
{
}

QString ApplicationLauncher::resolveTarget(const ApplicationInfo &application, QString *error) const
{
    if (!application.launchable || application.target.isEmpty()) {
        if (error) *error = QStringLiteral("%1 is not installed or is not permitted to launch.").arg(application.name);
        return {};
    }

    const QFileInfo info(QDir(rootPath_).filePath(application.target));
    const QString canonicalTarget = info.canonicalFilePath();
    if (!info.isFile() || canonicalTarget.isEmpty() || !isInsidePackage(rootPath_, canonicalTarget)) {
        if (error) *error = QStringLiteral("The configured executable is missing or resolves outside the DuckOS package.");
        return {};
    }
#ifndef Q_OS_WIN
    if (application.launchKind != QStringLiteral("python-script") && !info.isExecutable()) {
        if (error) *error = QStringLiteral("The configured file is not executable: %1").arg(application.name);
        return {};
    }
#endif
    return canonicalTarget;
}

QProcess *ApplicationLauncher::start(const ApplicationInfo &application, QString *error)
{
    const QString target = resolveTarget(application, error);
    if (target.isEmpty()) return nullptr;

    auto *process = new QProcess(this);
    QString program = target;
    QStringList arguments = application.arguments;
    if (application.launchKind == QStringLiteral("python-script")) {
#ifdef Q_OS_WIN
        program = QStandardPaths::findExecutable(QStringLiteral("py"));
        if (program.isEmpty()) program = QStandardPaths::findExecutable(QStringLiteral("python"));
        if (program.isEmpty()) {
            if (error) *error = QStringLiteral("Python 3 is required to run OPlague on this host.");
            process->deleteLater();
            return nullptr;
        }
        arguments = application.pythonArguments;
        if (QFileInfo(program).fileName().compare(QStringLiteral("py.exe"), Qt::CaseInsensitive) == 0) arguments.push_back(QStringLiteral("-3"));
#else
        program = QStandardPaths::findExecutable(QStringLiteral("python3"));
        if (program.isEmpty()) {
            if (error) *error = QStringLiteral("Python 3 is required to run OPlague on this host.");
            process->deleteLater();
            return nullptr;
        }
        arguments = application.pythonArguments;
#endif
        arguments.push_back(target);
    }

    const QString workingDirectory = application.workingDirectory.isEmpty()
        ? rootPath_
        : QDir(rootPath_).filePath(application.workingDirectory);
    const QFileInfo workingInfo(workingDirectory);
    const QString canonicalWorking = workingInfo.canonicalFilePath();
    if (!workingInfo.isDir() || canonicalWorking.isEmpty() || !isInsidePackage(rootPath_, canonicalWorking)
        || canonicalWorking == QFileInfo(rootPath_).canonicalFilePath()) {
        if (error) *error = QStringLiteral("The configured working directory is outside the DuckOS package.");
        process->deleteLater();
        return nullptr;
    }

    process->setProgram(program);
    process->setArguments(arguments);
    process->setWorkingDirectory(canonicalWorking);
    process->setProcessChannelMode(QProcess::MergedChannels);
    process->start();
    if (!process->waitForStarted(3000)) {
        if (error) *error = QStringLiteral("Could not start %1: %2").arg(application.name, process->errorString());
        process->deleteLater();
        return nullptr;
    }
    return process;
}
