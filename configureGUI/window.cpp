#include "window.h"

Window::Window(QWidget *parent)
    : QWidget(parent)
{
    setWindowTitle(tr("Find Files"));
    resize(1080, 360);
    assetLayout = new QHBoxLayout;
    loadButtonGroup = new QButtonGroup;
    for (int i = 0; i < 4; i++)
    {
        assetLabel[i] = new QLabel(this);
        assetListWidget[i] = new QListWidget(this);
        assetVLayout[i] = new QVBoxLayout;
        loadButton[i] = new QPushButton(tr("Load"), this);
        loadButtonGroup->addButton(loadButton[i], i);
        assetVLayout[i]->addWidget(assetLabel[i]);
        assetVLayout[i]->addWidget(loadButton[i]);
        assetVLayout[i]->addWidget(assetListWidget[i]);
        assetLayout->addLayout(assetVLayout[i]);
        new QListWidgetItem(tr("test"), assetListWidget[i]);
    }

    assetLabel[0]->setText(tr("texture"));
    assetLabel[1]->setText(tr("mesh"));
    assetLabel[2]->setText(tr("env"));
    assetLabel[3]->setText(tr("conf"));

    runButton = new QPushButton(tr("run"), this);
    logView = new QTextEdit;
    QVBoxLayout *runVLayout = new QVBoxLayout;
    assetLayout->addLayout(runVLayout);

    QVBoxLayout *mainLayout = new QVBoxLayout;
    mainLayout->addLayout(assetLayout);
    mainLayout->addWidget(runButton);
    mainLayout->addWidget(logView);

    setLayout(mainLayout);
    connect(loadButtonGroup, QOverload<int>::of(&QButtonGroup::buttonClicked), this, &Window::loadAsset);
    connect(runButton, &QPushButton::clicked, this, &Window::run);
    //connect(texture, &QListWidget::currentTextChanged, texLable, &QLabel::setText);
}
void Window::run()
{
    QString program = "blender";
    QStringList arguments{"--background", "--python", "render_mesh.py", "--"};
    QString paths[4];
    for (int i = 0; i < 4; i++)
    {
        QListWidgetItem *item = assetListWidget[i]->currentItem();
        if (item == nullptr)
            return;
        paths[i] = item->text();
    }
    arguments << "--texture" << paths[0] << "--mesh" << paths[1] << "--env" << paths[2] << "--conf" << paths[3];
    logView->append(arguments.join(" "));
    QProcess *cmdProcess = new QProcess;
    QObject::connect(cmdProcess, &QProcess::readyRead, [=]() {
        QTextCodec *codec = QTextCodec::codecForName("UTF-8");
        QString dir = codec->toUnicode(cmdProcess->readAll());
        logView->append(dir);
        qDebug() << dir;
    });
    cmdProcess->start(program, arguments);
}

void Window::loadAsset(int id)
{
    QStringList directory = QFileDialog::getOpenFileNames(this, tr("Find Files"), QDir::currentPath());

    for (int i = 0; i < directory.size(); i++)
    {
        new QListWidgetItem(QDir::current().relativeFilePath(directory[i]), assetListWidget[id]);
    }
}

Window::~Window()
{
}
