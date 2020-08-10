#include "window.h"

Window::Window(QWidget *parent)
    : QWidget(parent)
{
    setWindowTitle(tr("Compare"));
//    resize(3000,1500);
    buttonGroup=new QButtonGroup;
    mainlayout =new QHBoxLayout;
    listWidget=new QListWidget(this);
    QVBoxLayout *fileLayout=new QVBoxLayout;
//    listWidget->setSizePolicy(QSizePolicy::Maximum,QSizePolicy::Ignored);

    for(int i=0;i<2;i++){
        views[i]=new QLabel(this);
        buttons[i]=new QPushButton(QString::number(i),this);
        buttonGroup->addButton(buttons[i],i);
//        views[i]->setSizePolicy(, );
//        views[i]->setScaledContents(true);
    }
    fileLayout->addWidget(buttons[0]);
    fileLayout->addWidget(listWidget);
    fileLayout->addWidget(buttons[1]);


    mainlayout->addWidget(views[0]);
    mainlayout->addLayout(fileLayout);
    mainlayout->addWidget(views[1]);

    dirs[0]=QDir(tr("./train"));
    dirs[1]=QDir(tr("./dewarp"));


    QStringList list=dirs[0].entryList(QDir::Files);
    for (int i = 0; i < list.size(); i++)
    {
        new QListWidgetItem(list[i], listWidget);
    }
    connect(buttonGroup, QOverload<int>::of(&QButtonGroup::buttonClicked), this, &Window::loadFolder);

    connect(listWidget, &QListWidget::currentTextChanged, this, &Window::viewImage);
    setLayout(mainlayout);

}
void Window::loadFolder(int id){
    QDir directory;
    directory=dirs[id]=QDir(QFileDialog::getExistingDirectory(this,tr("load folder"),QDir::currentPath()));
    qDebug()<<dirs[id];
    if(id==0){
        listWidget->clear();
        QStringList list=directory.entryList(QDir::Files);
        for (int i = 0; i < list.size(); i++)
        {
            new QListWidgetItem(list[i], listWidget);
        }

    }

}
void Window::viewImage(QString fn){


    for(int i=0;i<2;i++){
        QString path=dirs[i].absoluteFilePath( fn);

        QImageReader reader(path);
        reader.setAutoTransform(true);
        const QImage newImage = reader.read();
        if (!newImage.isNull()) {
            QPixmap map=QPixmap::fromImage(newImage);
            map=map.scaled(2*map.size());
            views[i]->setPixmap(map);

        }



    }





}



Window::~Window()
{
}

