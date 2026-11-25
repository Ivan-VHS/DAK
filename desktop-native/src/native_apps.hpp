#pragma once

#include <QString>

class QWidget;

class NativeApps final {
public:
    static void open(const QString &action, const QString &appId, const QString &appName, QWidget *parent);
private:
    static void showNotes(const QString &appId, const QString &title, QWidget *parent);
    static void showLocalCollection(const QString &appId, const QString &title, QWidget *parent);
    static void showSettings(QWidget *parent);
    static void showFileManager(QWidget *parent);
    static void showFileInspector(QWidget *parent, bool hashFile);
    static void showExecutableInspector(QWidget *parent);
    static void showCalculator(QWidget *parent);
    static void showSystemOverview(QWidget *parent);
    static void showRhythmProfile(QWidget *parent);
};
