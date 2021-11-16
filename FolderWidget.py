#!/usr/bin/env python
###################################################################
# Author: Wenfeng Zhang
# Email : zwf.vfx@Foxmail.com
###################################################################

try:
    from PySide2.QtCore import *
    from PySide2.QtGui import *
    from PySide2.QtWidgets import *
except:
    from PySide.QtCore import *
    from PySide.QtGui import *
    from PySide.QtWebKit import *


class BrowserButton(QToolButton):
    sig_clicked = Signal(object)
    _toolTip = 'browser'
    _toolTip_unchecked = 'tooltips_unchecked'
    _icon = 'icon-default.png'

    def __init__(self, size=24, checkable=False, user_data=None, parent=None):
        super(BrowserButton, self).__init__(parent)
        if checkable:
            self.setCheckable(checkable)
            self.toggled.connect(self.slot_check_state_changed)
            self.setChecked(True)
        self.user_data = user_data
        self.clicked.connect(self.slot_clicked)
        self.setToolTip(self._toolTip)

        folder_ico = QApplication.style().standardIcon(QStyle.SP_DialogOpenButton)
        self.setIcon(folder_ico)
        self.setFixedSize(size + 1, size + 1)
        self.setIconSize(QSize(size, size))
        self.setAutoRaise(True)

    @Slot(bool)
    def slot_check_state_changed(self, checked):
        self.setChecked(checked)
        if checked:
            self.setToolTip(self._toolTip)
        else:
            self.setToolTip(self._toolTip_unchecked)

    @Slot()
    def slot_clicked(self):
        self.sig_clicked.emit(self.user_data)


class FolderWidget(QWidget):
    sig_folder_changed = Signal(str)

    def __init__(self, title='Folder', parent=None):
        super(FolderWidget, self).__init__(parent)
        self.dialog_title = title
        self.start_path = ''

        self.line_edit = QLineEdit('')
        self.line_edit.textChanged.connect(self.sig_folder_changed)

        file_button = BrowserButton(size=18)
        file_button.clicked.connect(self.slot_open_dialog)

        main_lay = QHBoxLayout()
        main_lay.addWidget(self.line_edit)
        main_lay.addWidget(file_button)
        main_lay.setContentsMargins(0, 0, 0, 0)
        self.setLayout(main_lay)

    @Slot()
    def slot_open_dialog(self):
        r_folder = QFileDialog.getExistingDirectory(self, self.dialog_title, self.start_path)
        if r_folder:
            self.set_folder(r_folder)

    def set_dialog_title(self, title):
        self.dialog_title = title

    def set_start_path(self, path):
        self.start_path = path

    @Slot()
    def slot_clear(self):
        self.line_edit.setText('')

    def get_folder(self):
        return self.line_edit.text()

    def set_folder(self, text):
        self.set_start_path(text)
        self.line_edit.setText(text)
        self.sig_folder_changed.emit(text)