# -*- coding: utf-8 -*-
__author__ = 'Wenfeng Zhang'

import time
try:
    from PySide2.QtCore import *
    from PySide2.QtGui import *
    from PySide2.QtWidgets import *
except:
    from PySide.QtCore import *
    from PySide.QtGui import *
    from PySide.QtWebKit import *


class ProgressTask(QDialog):
    def __init__(self, win_title='Copy files', parent=None):
        super(ProgressTask, self).__init__(parent)
        self.resize(750, 120)
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.setWindowTitle(win_title)
        self.initUI()
        self.show()
        self.cancel = False

    def initUI(self):
        self.label = QLabel('Copy all files')
        self.label.setFont(QFont("", 11, QFont.Bold))
        self.label.setStyleSheet('Color: DarkGray')
        self.label.setWordWrap(True)

        self.label_child = QLabel('Child Copy')
        self.label_child.setFont(QFont("", 11, QFont.Bold))
        self.label_child.setStyleSheet('Color: DarkGray')
        self.label_child.setWordWrap(True)

        self.pb = QProgressBar()
        self.pb.setRange(0, 100)
        self.pb.setValue(0)
        self.pb.setAlignment(Qt.AlignHCenter)

        self.pb_child = QProgressBar()
        self.pb_child.setRange(0, 100)
        self.pb_child.setValue(0)
        self.pb_child.setAlignment(Qt.AlignHCenter)
        self.pb_child.setStyleSheet('''
                                QProgressBar::chunk {
                                    width: 2px; 
                                    margin: 0.5px;
                                    background-color: green;
                                }
                                ''')

        self.cancel_btn = QPushButton('Cancel')

        view_Layout = QVBoxLayout()
        view_Layout.addWidget(self.label)
        view_Layout.addWidget(self.pb)
        view_Layout.addWidget(self.label_child)
        view_Layout.addWidget(self.pb_child)
        view_Layout.addWidget(self.cancel_btn, alignment=Qt.AlignRight)
        self.setLayout(view_Layout)

        self.cancel_btn.clicked.connect(lambda: self.canceled())

    def setParentProgress(self, value):
        self.pb.setValue(value)
        QApplication.processEvents()
        if value == 100:
            time.sleep(1)
            self.close()

    def setChildProgress(self, value):
        self.pb_child.setValue(value)
        QApplication.processEvents()

    def setParentMessage(self, text):
        self.label.setText(text)

    def setChildMessage(self, text):
        self.label_child.setText(text)

    def canceled(self):
        QApplication.processEvents()
        self.close()
        self.cancel = True

    def wasCanceled(self):
        QApplication.processEvents()
        return self.cancel

    def set_pb_child_visible(self, flag):
        self.label_child.setVisible(flag)
        self.pb_child.setVisible(flag)


if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    p = ProgressTask()
    p.set_pb_child_visible(False)
    num = 10
    for i in range(num):
        i += 1
        p.setParentMessage(str(i))
        # time.sleep(0.1)
        num_child = 10
        for x in range(num_child):
            x += 1
            p.setChildMessage(str(x))
            time.sleep(0.1)
            p.setChildProgress(float(x)/num_child*100)
        p.setParentProgress(float(i)/num*100)
    sys.exit(app.exec_())