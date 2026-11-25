#include <QAbstractItemView>
#include "native_apps.hpp"

#include <QCheckBox>
#include <QComboBox>
#include <QCryptographicHash>
#include <QDateTime>
#include <QDialog>
#include <QDialogButtonBox>
#include <QDir>
#include <QDoubleSpinBox>
#include <QFile>
#include <QFileDialog>
#include <QFileInfo>
#include <QFileSystemModel>
#include <QFormLayout>
#include <QLabel>
#include <QListWidget>
#include <QLineEdit>
#include <QHBoxLayout>
#include <QJsonArray>
#include <QJsonDocument>
#include <QJsonParseError>
#include <QSaveFile>
#include <QRegularExpression>
#include <QMessageBox>
#include <QPlainTextEdit>
#include <QPushButton>
#include <QSettings>
#include <QStandardPaths>
#include <QSysInfo>
#include <QTimer>
#include <QTreeView>
#include <QVBoxLayout>

namespace {
QString appDataDirectory()
{
    const QString path = QStandardPaths::writableLocation(QStandardPaths::AppDataLocation);
    QDir().mkpath(path);
    return path;
}

QDialog *makeDialog(const QString &title, QWidget *parent)
{
    auto *dialog = new QDialog(parent);
    dialog->setAttribute(Qt::WA_DeleteOnClose);
    dialog->setWindowTitle(title);
    dialog->resize(680, 460);
    return dialog;
}
}

void NativeApps::open(const QString &action, const QString &appId, const QString &appName, QWidget *parent)
{
    if (action == QStringLiteral("system-overview") || action == QStringLiteral("security-status")
        || action == QStringLiteral("release-status") || action == QStringLiteral("performance-status")
        || action == QStringLiteral("app-catalog")) {
        showSystemOverview(parent);
    } else if (action == QStringLiteral("settings")) {
        showSettings(parent);
    } else if (action == QStringLiteral("file-manager")) {
        showFileManager(parent);
    } else if (action == QStringLiteral("executable-inspector")) {
        showExecutableInspector(parent);
    } else if (action == QStringLiteral("archive-inspector")) {
        showFileInspector(parent, false);
    } else if (action == QStringLiteral("file-verifier")) {
        showFileInspector(parent, true);
    } else if (action == QStringLiteral("notes")) {
        showNotes(appId, appName, parent);
    } else if (action == QStringLiteral("local-collection")) {
        showLocalCollection(appId, appName, parent);
    } else if (action == QStringLiteral("calculator")) {
        showCalculator(parent);
    } else if (action == QStringLiteral("clock")) {
        auto *dialog = makeDialog(QStringLiteral("DuckOS Clock"), parent);
        auto *layout = new QVBoxLayout(dialog);
        auto *time = new QLabel(dialog);
        time->setAlignment(Qt::AlignCenter);
        time->setStyleSheet(QStringLiteral("font-size:42px;font-weight:700;color:#ffd400;"));
        layout->addWidget(time);
        auto *timer = new QTimer(dialog);
        QObject::connect(timer, &QTimer::timeout, dialog, [time] {
            time->setText(QDateTime::currentDateTime().toString(QStringLiteral("HH:mm:ss\ndd MMMM yyyy")));
        });
        timer->start(1000);
        time->setText(QDateTime::currentDateTime().toString(QStringLiteral("HH:mm:ss\ndd MMMM yyyy")));
        dialog->show();
    } else if (action == QStringLiteral("rhythm-profile")) {
        showRhythmProfile(parent);
    } else {
        QMessageBox::information(parent, appName,
            QStringLiteral("%1 is present in the historical application catalogue, but its native application service has not been ported yet.\n\nThe native shell does not open a browser or pretend a prototype is a finished application.").arg(appName));
    }
}


void NativeApps::showLocalCollection(const QString &appId, const QString &title, QWidget *parent)
{
    static const QRegularExpression safeId(QStringLiteral("^[a-z0-9-]{1,64}$"));
    if (!safeId.match(appId).hasMatch()) {
        QMessageBox::warning(parent, QStringLiteral("DuckOS"), QStringLiteral("Invalid local application identifier."));
        return;
    }

    auto *dialog = makeDialog(title, parent);
    auto *layout = new QVBoxLayout(dialog);
    auto *list = new QListWidget(dialog);
    list->setSelectionMode(QAbstractItemView::SingleSelection);

    const QString fileName = QDir(appDataDirectory()).filePath(appId + QStringLiteral(".json"));
    QFile input(fileName);
    if (input.open(QIODevice::ReadOnly)) {
        if (input.size() > 1024 * 1024) {
            QMessageBox::warning(dialog, QStringLiteral("DuckOS"), QStringLiteral("Local collection is larger than the 1 MiB safety limit."));
        } else {
            QJsonParseError parseError;
            const QJsonDocument document = QJsonDocument::fromJson(input.readAll(), &parseError);
            if (parseError.error == QJsonParseError::NoError && document.isArray()) {
                const QJsonArray entries = document.array();
                const qsizetype count = qMin<qsizetype>(entries.size(), 500);
                for (qsizetype index = 0; index < count; ++index) {
                    const QJsonValue entry = entries.at(index);
                    if (entry.isString() && entry.toString().size() <= 2000)
                        list->addItem(entry.toString());
                }
            } else {
                QMessageBox::warning(dialog, QStringLiteral("DuckOS"), QStringLiteral("Local data is invalid JSON and was not loaded."));
            }
        }
    }

    auto *editor = new QLineEdit(dialog);
    editor->setMaxLength(2000);
    editor->setPlaceholderText(QStringLiteral("Новая запись…"));
    auto *add = new QPushButton(QStringLiteral("Добавить"), dialog);
    auto *remove = new QPushButton(QStringLiteral("Удалить выбранное"), dialog);
    auto *save = new QPushButton(QStringLiteral("Сохранить"), dialog);

    const auto persist = [list, fileName, dialog] {
        if (list->count() > 500) {
            QMessageBox::warning(dialog, QStringLiteral("DuckOS"), QStringLiteral("Collection is limited to 500 entries."));
            return;
        }
        QJsonArray entries;
        for (int index = 0; index < list->count(); ++index)
            entries.append(list->item(index)->text());
        QSaveFile output(fileName);
        if (!output.open(QIODevice::WriteOnly)) {
            QMessageBox::warning(dialog, QStringLiteral("DuckOS"), output.errorString());
            return;
        }
        const QByteArray payload = QJsonDocument(entries).toJson(QJsonDocument::Compact);
        if (output.write(payload) != payload.size() || !output.commit()) {
            QMessageBox::warning(dialog, QStringLiteral("DuckOS"), output.errorString());
            return;
        }
        QMessageBox::information(dialog, QStringLiteral("DuckOS"), QStringLiteral("Сохранено локально."));
    };

    const auto addEntry = [editor, list, dialog] {
        const QString value = editor->text().trimmed();
        if (value.isEmpty()) return;
        if (list->count() >= 500) {
            QMessageBox::warning(dialog, QStringLiteral("DuckOS"), QStringLiteral("Collection is limited to 500 entries."));
            return;
        }
        list->addItem(value);
        editor->clear();
        list->setCurrentRow(list->count() - 1);
    };

    QObject::connect(add, &QPushButton::clicked, dialog, addEntry);
    QObject::connect(editor, &QLineEdit::returnPressed, dialog, addEntry);
    QObject::connect(remove, &QPushButton::clicked, dialog, [list] {
        delete list->takeItem(list->currentRow());
    });
    QObject::connect(save, &QPushButton::clicked, dialog, persist);

    auto *row = new QHBoxLayout;
    row->addWidget(editor, 1);
    row->addWidget(add);
    layout->addWidget(list, 1);
    layout->addLayout(row);
    layout->addWidget(remove);
    layout->addWidget(save);
    dialog->show();
}

void NativeApps::showNotes(const QString &appId, const QString &title, QWidget *parent)
{
    auto *dialog = makeDialog(title, parent);
    auto *layout = new QVBoxLayout(dialog);
    auto *editor = new QPlainTextEdit(dialog);
    editor->setPlaceholderText(QStringLiteral("Записи хранятся локально в профиле пользователя."));
    const QString fileName = QDir(appDataDirectory()).filePath(appId + QStringLiteral(".txt"));
    QFile file(fileName);
    if (file.open(QIODevice::ReadOnly | QIODevice::Text)) editor->setPlainText(QString::fromUtf8(file.readAll()));
    layout->addWidget(editor);

    auto *buttons = new QDialogButtonBox(QDialogButtonBox::Save | QDialogButtonBox::Close, dialog);
    QObject::connect(buttons, &QDialogButtonBox::rejected, dialog, &QDialog::reject);
    QObject::connect(buttons, &QDialogButtonBox::accepted, dialog, [editor, fileName, dialog] {
        QFile output(fileName);
        if (!output.open(QIODevice::WriteOnly | QIODevice::Text | QIODevice::Truncate)) {
            QMessageBox::warning(dialog, QStringLiteral("DuckOS"), output.errorString());
            return;
        }
        output.write(editor->toPlainText().toUtf8());
        QMessageBox::information(dialog, QStringLiteral("DuckOS"), QStringLiteral("Сохранено локально."));
    });
    layout->addWidget(buttons);
    dialog->show();
}

void NativeApps::showSettings(QWidget *parent)
{
    QSettings settings(QStringLiteral("Ivan-VHS"), QStringLiteral("DuckOS Native Desktop"));
    auto *dialog = makeDialog(QStringLiteral("SetupUP · Native settings"), parent);
    auto *layout = new QVBoxLayout(dialog);
    auto *form = new QFormLayout;
    auto *accent = new QComboBox(dialog);
    accent->addItem(QStringLiteral("Imperial Gold"), QStringLiteral("#ffd400"));
    accent->addItem(QStringLiteral("Soft Gold"), QStringLiteral("#e7bd26"));
    accent->addItem(QStringLiteral("White"), QStringLiteral("#f3f3f3"));
    const int current = accent->findData(settings.value(QStringLiteral("appearance/accent"), QStringLiteral("#ffd400")));
    accent->setCurrentIndex(qMax(0, current));
    auto *reducedMotion = new QCheckBox(QStringLiteral("Уменьшить анимацию"), dialog);
    reducedMotion->setChecked(settings.value(QStringLiteral("appearance/reduced-motion"), false).toBool());
    form->addRow(QStringLiteral("Акцент оболочки"), accent);
    form->addRow(QStringLiteral("Доступность"), reducedMotion);
    layout->addLayout(form);
    auto *buttons = new QDialogButtonBox(QDialogButtonBox::Save | QDialogButtonBox::Close, dialog);
    QObject::connect(buttons, &QDialogButtonBox::rejected, dialog, &QDialog::reject);
    QObject::connect(buttons, &QDialogButtonBox::accepted, dialog, [accent, reducedMotion, dialog] {
        QSettings output(QStringLiteral("Ivan-VHS"), QStringLiteral("DuckOS Native Desktop"));
        output.setValue(QStringLiteral("appearance/accent"), accent->currentData().toString());
        output.setValue(QStringLiteral("appearance/reduced-motion"), reducedMotion->isChecked());
        QMessageBox::information(dialog, QStringLiteral("SetupUP"), QStringLiteral("Настройки сохранены в профиле этого пользователя. Перезапусти оболочку, чтобы обновить акцент."));
    });
    layout->addWidget(buttons);
    dialog->show();
}

void NativeApps::showFileManager(QWidget *parent)
{
    auto *dialog = makeDialog(QStringLiteral("DuckOS Files"), parent);
    auto *layout = new QVBoxLayout(dialog);
    auto *model = new QFileSystemModel(dialog);
    model->setRootPath(QDir::homePath());
    auto *tree = new QTreeView(dialog);
    tree->setModel(model);
    tree->setRootIndex(model->index(QDir::homePath()));
    tree->setColumnWidth(0, 360);
    layout->addWidget(tree);
    dialog->show();
}


void NativeApps::showExecutableInspector(QWidget *parent)
{
    const QString path = QFileDialog::getOpenFileName(parent,
        QStringLiteral("Выбрать PE или ELF для безопасной инспекции"), QDir::homePath());
    if (path.isEmpty()) return;

    QFile file(path);
    if (!file.open(QIODevice::ReadOnly)) {
        QMessageBox::warning(parent, QStringLiteral("EXEdotEXE"), file.errorString());
        return;
    }
    if (file.size() < 20) {
        QMessageBox::information(parent, QStringLiteral("EXEdotEXE"), QStringLiteral("Файл слишком мал для PE/ELF заголовка."));
        return;
    }

    QByteArray header = file.read(64);
    QString format = QStringLiteral("Unknown");
    QString architecture = QStringLiteral("Unknown");
    QString bitness = QStringLiteral("Unknown");
    QString detail = QStringLiteral("No supported PE/ELF signature was found.");

    const auto byteAt = [](const QByteArray &bytes, qsizetype index) -> quint8 {
        return static_cast<quint8>(static_cast<unsigned char>(bytes.at(index)));
    };
    const auto little16 = [&byteAt](const QByteArray &bytes, qsizetype index) -> quint16 {
        return static_cast<quint16>(byteAt(bytes, index))
            | static_cast<quint16>(static_cast<quint16>(byteAt(bytes, index + 1)) << 8U);
    };

    if (header.size() >= 64 && header.startsWith("MZ")) {
        const quint32 peOffset = static_cast<quint32>(byteAt(header, 0x3c))
            | (static_cast<quint32>(byteAt(header, 0x3d)) << 8U)
            | (static_cast<quint32>(byteAt(header, 0x3e)) << 16U)
            | (static_cast<quint32>(byteAt(header, 0x3f)) << 24U);
        if (peOffset <= static_cast<quint64>(file.size()) - 6U
            && file.seek(static_cast<qint64>(peOffset))) {
            const QByteArray pe = file.read(6);
            if (pe.size() == 6 && pe.at(0) == 'P' && pe.at(1) == 'E' && pe.at(2) == 0 && pe.at(3) == 0) {
                format = QStringLiteral("PE");
                const quint16 machine = little16(pe, 4);
                switch (machine) {
                case 0x014c: architecture = QStringLiteral("x86"); bitness = QStringLiteral("32-bit"); break;
                case 0x8664: architecture = QStringLiteral("x86-64"); bitness = QStringLiteral("64-bit"); break;
                case 0xaa64: architecture = QStringLiteral("ARM64"); bitness = QStringLiteral("64-bit"); break;
                default: architecture = QStringLiteral("Unknown machine 0x%1").arg(machine, 4, 16, QLatin1Char('0')); break;
                }
                detail = QStringLiteral("PE/COFF machine header parsed. Imports, relocations, ABI and runtime support are not executed or inferred.");
            }
        }
    } else if (header.size() >= 20
        && static_cast<unsigned char>(header.at(0)) == 0x7f
        && header.mid(1, 3) == "ELF") {
        format = QStringLiteral("ELF");
        const quint8 elfClass = byteAt(header, 4);
        const quint8 data = byteAt(header, 5);
        bitness = elfClass == 1 ? QStringLiteral("32-bit") : elfClass == 2 ? QStringLiteral("64-bit") : QStringLiteral("Unknown");
        const quint16 machine = data == 1
            ? little16(header, 18)
            : data == 2
                ? static_cast<quint16>((static_cast<quint16>(byteAt(header, 18)) << 8U) | byteAt(header, 19))
                : 0;
        switch (machine) {
        case 3: architecture = QStringLiteral("x86"); break;
        case 62: architecture = QStringLiteral("x86-64"); break;
        case 40: architecture = QStringLiteral("ARM"); break;
        case 183: architecture = QStringLiteral("ARM64"); break;
        case 243: architecture = QStringLiteral("RISC-V"); break;
        default: architecture = QStringLiteral("Unknown machine %1").arg(machine); break;
        }
        detail = QStringLiteral("ELF identification and machine header parsed. No program headers are mapped and no code is executed.");
    }

    const QString message = QStringLiteral(
        "Файл: %1\\nРазмер: %2 байт\\nФормат: %3\\nРазрядность: %4\\nАрхитектура: %5\\n\\n%6\\n\\nФайл не запускался.")
        .arg(QFileInfo(path).fileName()).arg(file.size()).arg(format).arg(bitness).arg(architecture).arg(detail);
    QMessageBox::information(parent, QStringLiteral("EXEdotEXE · Read-only inspector"), message);
}

void NativeApps::showFileInspector(QWidget *parent, bool hashFile)
{
    const QString path = QFileDialog::getOpenFileName(parent,
        hashFile ? QStringLiteral("Выбрать файл для SHA-256") : QStringLiteral("Инспекция метаданных"),
        QDir::homePath());
    if (path.isEmpty()) return;
    const QFileInfo info(path);
    QString message = QStringLiteral("Файл: %1\nРазмер: %2 байт\nТип: %3\nИзменён: %4\nПуть: %5")
        .arg(info.fileName()).arg(info.size()).arg(info.suffix().isEmpty() ? QStringLiteral("unknown") : info.suffix())
        .arg(info.lastModified().toString(Qt::ISODate)).arg(info.absoluteFilePath());
    if (hashFile) {
        QFile file(path);
        if (!file.open(QIODevice::ReadOnly)) {
            QMessageBox::warning(parent, QStringLiteral("DuckOS"), file.errorString());
            return;
        }
        QCryptographicHash hash(QCryptographicHash::Sha256);
        while (!file.atEnd()) {
            const QByteArray chunk = file.read(1024 * 1024);
            if (chunk.isEmpty() && file.error() != QFileDevice::NoError) {
                QMessageBox::warning(parent, QStringLiteral("DuckOS"), file.errorString());
                return;
            }
            hash.addData(chunk);
        }
        message += QStringLiteral("\nSHA-256: %1").arg(QString::fromLatin1(hash.result().toHex()));
    }
    QMessageBox::information(parent, hashFile ? QStringLiteral("Proof · SHA-256") : QStringLiteral("Abriganza · File info"), message);
}

void NativeApps::showCalculator(QWidget *parent)
{
    auto *dialog = makeDialog(QStringLiteral("DuckOS Calculator"), parent);
    auto *layout = new QVBoxLayout(dialog);
    auto *form = new QFormLayout;
    auto *left = new QDoubleSpinBox(dialog);
    auto *right = new QDoubleSpinBox(dialog);
    left->setRange(-1.0e12, 1.0e12);
    right->setRange(-1.0e12, 1.0e12);
    left->setDecimals(6);
    right->setDecimals(6);
    auto *operation = new QComboBox(dialog);
    operation->addItems({QStringLiteral("+"), QStringLiteral("−"), QStringLiteral("×"), QStringLiteral("÷")});
    auto *result = new QLabel(QStringLiteral("0"), dialog);
    result->setStyleSheet(QStringLiteral("font-size:26px;font-weight:700;color:#ffd400;"));
    form->addRow(QStringLiteral("Первое число"), left);
    form->addRow(QStringLiteral("Действие"), operation);
    form->addRow(QStringLiteral("Второе число"), right);
    layout->addLayout(form);
    layout->addWidget(result);
    const auto calculate = [left, right, operation, result] {
        const double a = left->value();
        const double b = right->value();
        const int op = operation->currentIndex();
        if (op == 3 && qFuzzyIsNull(b)) {
            result->setText(QStringLiteral("Деление на ноль"));
            return;
        }
        double value = 0.0;
        if (op == 0) value = a + b;
        else if (op == 1) value = a - b;
        else if (op == 2) value = a * b;
        else value = a / b;
        result->setText(QString::number(value, 'g', 12));
    };
    QObject::connect(left, &QDoubleSpinBox::valueChanged, dialog, calculate);
    QObject::connect(right, &QDoubleSpinBox::valueChanged, dialog, calculate);
    QObject::connect(operation, qOverload<int>(&QComboBox::currentIndexChanged), dialog, calculate);
    dialog->show();
}

void NativeApps::showSystemOverview(QWidget *parent)
{
    auto *dialog = makeDialog(QStringLiteral("Sestem · DuckOS status"), parent);
    auto *layout = new QVBoxLayout(dialog);
    auto *text = new QLabel(dialog);
    text->setWordWrap(true);
    text->setText(QStringLiteral(
        "<b>DuckOS Native Desktop</b><br>"
        "Mora is running as a native Qt Widgets application. No browser engine or WebView is loaded.<br><br>"
        "<b>Host:</b> %1<br><b>Architecture:</b> %2<br><b>Qt:</b> %3<br>"
        "<b>Kernel:</b> Stage 1 boot foundation; current kernel halts after the DUCKOS_BOOT_OK marker.<br>"
        "<b>Process model:</b> host QProcess launcher with explicit per-app targets; not a DuckOS kernel process manager.")
        .arg(QSysInfo::prettyProductName(), QSysInfo::currentCpuArchitecture(), QString::fromLatin1(qVersion())));
    layout->addWidget(text);
    dialog->show();
}

void NativeApps::showRhythmProfile(QWidget *parent)
{
    auto *dialog = makeDialog(QStringLiteral("Concrete Thump · Rhythm profile"), parent);
    auto *layout = new QVBoxLayout(dialog);
    auto *form = new QFormLayout;
    auto *bpm = new QDoubleSpinBox(dialog);
    bpm->setRange(40.0, 240.0);
    bpm->setValue(93.0);
    bpm->setSuffix(QStringLiteral(" BPM"));
    auto *swing = new QDoubleSpinBox(dialog);
    swing->setRange(50.0, 75.0);
    swing->setValue(58.0);
    swing->setSuffix(QStringLiteral(" %"));
    form->addRow(QStringLiteral("Темп"), bpm);
    form->addRow(QStringLiteral("Swing"), swing);
    layout->addLayout(form);
    auto *save = new QPushButton(QStringLiteral("Сохранить профиль"), dialog);
    QObject::connect(save, &QPushButton::clicked, dialog, [bpm, swing, dialog] {
        QSettings settings(QStringLiteral("Ivan-VHS"), QStringLiteral("DuckOS Native Desktop"));
        settings.setValue(QStringLiteral("rhythm/bpm"), bpm->value());
        settings.setValue(QStringLiteral("rhythm/swing"), swing->value());
        QMessageBox::information(dialog, QStringLiteral("Concrete Thump"), QStringLiteral("Профиль сохранён локально. Audio engine ещё не подключён."));
    });
    layout->addWidget(save);
    dialog->show();
}
