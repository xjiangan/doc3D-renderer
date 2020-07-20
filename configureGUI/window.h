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

private:
    QLabel *assetLabel[4];
    QListWidget *assetListWidget[4];
    QVBoxLayout *assetVLayout[4];
    QPushButton *loadButton[4];
    QHBoxLayout *assetLayout;
    QButtonGroup *loadButtonGroup;
    QPushButton *runButton;
    QTextEdit *logView;
};
#endif // WINDOW_H
