#ifndef WINDOW_H
#define WINDOW_H

#include <QWidget>
#include <QtWidgets>

class Window : public QWidget
{
    Q_OBJECT

public:
    Window(QWidget *parent = nullptr);
    void viewImage(QString fn);
    void loadFolder(int id);
    ~Window();

private:
    QHBoxLayout * mainlayout;
    QLabel* views[2];
    QListWidget* listWidget;
    QDir dirs[2];
    QPushButton*buttons [2];
    QButtonGroup* buttonGroup;
};
#endif // WINDOW_H
