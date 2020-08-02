#ifndef WINDOW_H
#define WINDOW_H

#include <QWidget>
#include <QtWidgets>

class Window : public QWidget
{
    Q_OBJECT

public:
    Window(QWidget *parent = nullptr);
    ~Window();

    void loadAsset(int id);
    void run();
    void openItem(QListWidgetItem *item);
    void viewImage(QString fn);

public slots:
    void loadFolder(int id,QDir* dir=nullptr);


private:
    QLabel *assetLabel[5];
    QListWidget *assetListWidget[5];
    QVBoxLayout *assetVLayout[5];
    QPushButton *loadButton[5];
    QPushButton *folderButton[5];
    QHBoxLayout *assetLayout;
    QButtonGroup *loadButtonGroup;
    QButtonGroup *folderButtonGroup;
    QPushButton *runButton;
    QTextEdit *logView;
    QLabel* view;
};
#endif // WINDOW_H
