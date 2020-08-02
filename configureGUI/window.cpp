#include "window.h"

Window::Window(QWidget *parent)
    : QWidget(parent)
{
    setWindowTitle(tr("Find Files"));
    resize(1080, 360);
    assetLayout = new QHBoxLayout;
    loadButtonGroup = new QButtonGroup;
    folderButtonGroup=new QButtonGroup;
    QDir dirs[5];
    dirs[0]=QDir("./tex");
    dirs[1]=QDir("./obj");
    dirs[2]=QDir("./env");
    dirs[3]=QDir("./conf");
    dirs[4]=QDir("./img/1");


    for (int i = 0; i < 5; i++)
    {
        assetLabel[i] = new QLabel(this);
        assetListWidget[i] = new QListWidget(this);
        assetVLayout[i] = new QVBoxLayout;
        loadButton[i] = new QPushButton(tr("Load File"), this);
        loadButtonGroup->addButton(loadButton[i], i);
        folderButton[i]=new QPushButton(tr("Load Folder"),this);
        folderButtonGroup->addButton(folderButton[i],i);
        assetVLayout[i]->addWidget(assetLabel[i]);
        assetVLayout[i]->addWidget(loadButton[i]);
        assetVLayout[i]->addWidget(folderButton[i]);
        assetVLayout[i]->addWidget(assetListWidget[i]);
        assetLayout->addLayout(assetVLayout[i]);
        loadFolder(i,dirs+i);
    }


    assetLabel[0]->setText(tr("texture"));
    assetLabel[1]->setText(tr("mesh"));
    assetLabel[2]->setText(tr("env"));
    assetLabel[3]->setText(tr("conf"));
    assetLabel[4]->setText(tr("out"));

    runButton = new QPushButton(tr("run"), this);
    logView = new QTextEdit;
    QVBoxLayout *runVLayout = new QVBoxLayout;
    assetLayout->addLayout(runVLayout);

    QVBoxLayout *confLayout = new QVBoxLayout;
    confLayout->addLayout(assetLayout);
    confLayout->addWidget(runButton);
    confLayout->addWidget(logView);
    QHBoxLayout *mainLayout = new QHBoxLayout;
    mainLayout->addLayout(confLayout);
    view = new QLabel;
    mainLayout->addWidget(view);

    setLayout(mainLayout);
    connect(loadButtonGroup, QOverload<int>::of(&QButtonGroup::buttonClicked), this, &Window::loadAsset);
    connect(folderButtonGroup, SIGNAL(buttonClicked(int)), this, SLOT(loadFolder(int)));

    connect(runButton, &QPushButton::clicked, this, &Window::run);
    connect(assetListWidget[3], &QListWidget::itemActivated, this, &Window::openItem);
    connect(assetListWidget[4], &QListWidget::itemActivated, this, &Window::openItem);
    connect(assetListWidget[4], &QListWidget::currentTextChanged, this, &Window::viewImage);
    //connect(texture, &QListWidget::currentTextChanged, texLable, &QLabel::setText);
}
void Window::openItem(QListWidgetItem *item)
{
    QDesktopServices::openUrl(QUrl::fromLocalFile(item->text()));
}

void Window::viewImage(QString fileName){
    QImageReader reader(fileName);
    reader.setAutoTransform(true);
    const QImage newImage = reader.read();
    if (newImage.isNull()) {
        QMessageBox::information(this, QGuiApplication::applicationDisplayName(),
                                 tr("Cannot load %1: %2")
                                     .arg(QDir::toNativeSeparators(fileName), reader.errorString()));

    }
    //! [2]


    view->setPixmap(QPixmap::fromImage(newImage));




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
        QRegularExpression re("---output:(.*)---");
        QRegularExpressionMatch match=re.match(dir);
        if(match.hasMatch()){
            QListWidgetItem* item= new QListWidgetItem(QDir::current().relativeFilePath(match.captured(1)));
            assetListWidget[4]->insertItem(0,item);
            assetListWidget[4]->setCurrentItem(item);
        }
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

void Window::loadFolder(int id,QDir* dir){
    QDir directory;
    if(dir==nullptr)
        directory=QDir(QFileDialog::getExistingDirectory(this,tr("load folder"),QDir::currentPath()));
    else
        directory=*dir;
    QStringList list=directory.entryList(QDir::Files);
    for (int i = 0; i < list.size(); i++)
    {
        new QListWidgetItem(QDir::current().relativeFilePath(directory.absoluteFilePath( list[i])), assetListWidget[id]);
    }

}

Window::~Window()
{
}
