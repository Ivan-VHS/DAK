#pragma once

#include "application_catalog.hpp"
#include "application_launcher.hpp"

#include <QMainWindow>
#include <QProcess>

class QComboBox;
class QGridLayout;
class QLabel;
class QLineEdit;
class QWidget;

class DesktopWindow final : public QMainWindow {
    Q_OBJECT
public:
    explicit DesktopWindow(ApplicationCatalog catalog, QWidget *parent = nullptr);

private:
    void buildUi();
    void rebuildGrid();
    void openApplication(const QString &id);
    void launchProcess(const ApplicationInfo &application);
    void showProcessOutput(const ApplicationInfo &application, QProcess *process);
    void showApplicationInfo(const ApplicationInfo &application);
    QString statusText(const ApplicationInfo &application) const;

    ApplicationCatalog catalog_;
    ApplicationLauncher launcher_;
    QLineEdit *search_ = nullptr;
    QComboBox *category_ = nullptr;
    QGridLayout *grid_ = nullptr;
    QWidget *gridHost_ = nullptr;
    QLabel *clock_ = nullptr;
    QLabel *status_ = nullptr;
};
