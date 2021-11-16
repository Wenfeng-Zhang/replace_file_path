#!/usr/bin/env python
# -*- encoding: utf-8 -*-

__author__ = 'Wenfeng Zhang'

import re
import os
import sys
from utils import name_format
from utils import recursive_file
from utils import get_pattern_sequence
from FolderWidget import FolderWidget
from dayu_path import DayuPath as DiskPath
from ProgressBar import ProgressTask

try:
    from PySide2.QtCore import *
    from PySide2.QtGui import *
    from PySide2.QtWidgets import *
except:
    from PySide.QtCore import *
    from PySide.QtGui import *
    from PySide.QtWebKit import *

# 这些是nuke里会用到导入素材的节点类型列表
NUKE_FILE_NODE = ['OCIOCDLTransform', 'ReadGeo2', 'ParticleCache', 'Read', 'DeepRead', 'ReadGeo', 'Precomp',
                  'LiveGroup', 'AudioRead', 'Light2', 'OCIOFileTransform', 'Axis2', 'LiveInput', 'Camera2',
                  'ScannedGrain', 'Vectorfield']
Maya_FILE_NODE = []
dcc_name = os.path.basename(sys.executable).lower()


def hou_file_parm_dict(nonExist=True):
    """
    得到houdini工程内使用的素材资产路径和使用者parm的字典，例如：
    {'d:/a/b/c.$F4.exr': [<hou.Parm basecolor_texture in /mat/principledshader1>]，
     'd:/a/b/d.$F4.exr': [parm对象1， parm对象2]，
    }
    :param nonExist: 是否只收集不存在路径的对应字典，大部分时候是只对不存在的错误路径做查找替换，所以默认是True。
    :return: 路径和parm对象列表的对应字典
    """
    import hou
    file_parm_dict = {}
    root_node = hou.node('/')
    file_rex = re.compile("^([a-zA-Z]):/")
    for parm in root_node.allParms():
        parm_temp_late = parm.parmTemplate()
        if parm_temp_late.type().name() != 'String':
            continue
        if parm_temp_late.stringType().name() == 'FileReference':
            old_filename = parm.rawValue().replace('\\', '/')
            if not old_filename:
                continue
            win32_flag = file_rex.search(old_filename)
            if win32_flag:
                if nonExist:
                    if not get_pattern_sequence(old_filename, flag=True):
                        parm_list = file_parm_dict.setdefault(old_filename, [])
                        parm_list.append(parm)
                else:
                    parm_list = file_parm_dict.setdefault(old_filename, [])
                    parm_list.append(parm)
                parm.lock(False)
    return file_parm_dict


def nuke_file_parm_dict(nonExist=True):
    """
    得到nuke工程内使用的素材路径和使用者knob的字典，例如：
    {'d:/a/b/c.%04d.exr': [<File_Knob object at 0x000001F52AF5EA38>]，
     'd:/a/b/d.%04d.exr': [knob对象1， knob对象2]，
    }
    :param nonExist: 是否只收集不存在路径的对应字典，大部分时候是只对不存在的错误路径做查找替换，所以默认是True。
    :return: 路径和knob对象列表的对应字典
    """
    import nuke
    file_parm_dict = {}
    nodes = nuke.allNodes(recurseGroups=True)
    # 只查找报错不存在的路径
    if nonExist:
        nuke_file_node = [node for node in nodes if node.error() and node.Class() in NUKE_FILE_NODE]
    else:
        nuke_file_node = [node for node in nodes if node.Class() in NUKE_FILE_NODE]
    for node in nuke_file_node:
        if node.Class() == 'ScannedGrain':
            knob = node.knob('fullGrain')
            filename = os.path.dirname(knob.evaluate()) + '/' + os.path.basename(knob.value())
            knob_list = file_parm_dict.setdefault(filename, [])
            knob_list.append(knob)
        elif node.Class() == 'Vectorfield':
            knob = node.knob('vfield_file')
            filename = os.path.dirname(knob.evaluate()) + '/' + os.path.basename(knob.value())
            knob_list = file_parm_dict.setdefault(filename, [])
            knob_list.append(knob)
        else:
            knob = node.knob('file')
            filename = nuke.filename(node)
            if filename:
                knob_list = file_parm_dict.setdefault(filename, [])
                knob_list.append(knob)
    return file_parm_dict


def get_path_all_file(path, exts):
    """
    从给与的path路径里，循环查找列出指定的类型的文件，并组合成一个属性字典，并将这些字典放在一个列表里。例如：
    [{'ext': '.exr', 'filename': 'd:/a/b/c.%04d.exr', 'pattern': '%04d', 'pattern_num': 4, 'frames': [1001,1002,1003],},
     {'ext': '.jpg', 'filename': 'd:/a/b/c.%03d.jpg', 'pattern': '%03d', 'pattern_num': 3, 'frames': [1,2,3,4,5],}
    ]
    :param path: 要查找的路径
    :param exts: 指定类型列表
    :return: 返回一个列表，内部是路径属性字典
    """
    def function_filter(filename):
        return next((ext_ for ext_ in exts if filename.lower().endswith(ext_)), False)

    basename_file_value_dict = {}
    file_list = DiskPath(path).scan(recursive=True, function_filter=function_filter)
    for file_name in file_list:
        nf = name_format(file_name)
        name, pattern, ext, pattern_num = nf.name, nf.pattern, nf.ext, nf.pattern_num
        file_value_dict = {
            'ext': ext,
            'filename': file_name,
            'pattern': pattern,
            'pattern_num': pattern_num,
            'frames': file_name.frames,
        }
        file_value_dict_list = basename_file_value_dict.setdefault(name, [])
        file_value_dict_list.append(file_value_dict)
    return basename_file_value_dict


def get_new_file_knob_dict(path, dcc_file_knob_dict):
    """
    根据查找的路径和DCC软件工程内使用的素材路径和使用者parm（knob）的字典，生成从path里查找到的新路径和parm（knob）的字典。例如：
    原始dcc_file_knob_dict：
    {'d:/a/b/c.%04d.exr': [<File_Knob object at 0x000001F52AF5EA38>]，
     'd:/a/b/d.%04d.exr': [knob对象1， knob对象2]，
    }
    得到新的dcc_file_knob_dict：
    {'d:/NEW/c.%04d.exr': [<File_Knob object at 0x000001F52AF5EA38>]，
     'd:/NEW/d.%04d.exr': [knob对象1， knob对象2]，
    }
    :param path: 要查找的路径
    :param dcc_file_knob_dict: houdini或nuke工程内使用的素材路径和使用者parm（knob）的字典
    :return: 新路径和parm（knob）的字典，以及没有从path匹配到新路径的按钮字典
    """
    exts = set([os.path.splitext(file_)[-1] for file_ in dcc_file_knob_dict.keys()])
    all_file_dict = get_path_all_file(path, exts)
    new_file_knob_dict = {}
    # 这个复制出来的字典是为了得到没有找到新路径的parm和knob，利用字典的del，删除已经找到的，最后就剩下没有找到的键值对。
    copy_file_knob_dict = dcc_file_knob_dict.copy()

    for filename, knobs in dcc_file_knob_dict.items():
        old_filename = filename
        if path.replace('\\', '/').lower() in old_filename.replace('\\', '/').lower():
            del copy_file_knob_dict[filename]
            continue
        nf = name_format(old_filename)
        name, pattern, ext, pattern_num = nf.name, nf.pattern, nf.ext, nf.pattern_num
        attr_dict_list = all_file_dict.get(name)
        old_filename = DiskPath(old_filename)
        if not attr_dict_list:
            continue
        if len(attr_dict_list) == 1:
            attr_dict = attr_dict_list[0]
            check_filename = DiskPath(attr_dict.get('filename'))
            if old_filename.name.lower() == check_filename.name.lower():
                new_file_knob_dict.setdefault(check_filename.parent.child(old_filename.name).__str__(), knobs)
                del copy_file_knob_dict[filename]
            elif ext == attr_dict.get('ext'):
                if not pattern:
                    continue
                if pattern.isdigit() and int(pattern) in attr_dict.get('frames'):
                    new_file_knob_dict.setdefault(check_filename.parent.child(old_filename.name).__str__(), knobs)
                    del copy_file_knob_dict[filename]
                elif pattern_num == attr_dict.get('pattern_num'):
                    new_file_knob_dict.setdefault(check_filename.parent.child(old_filename.name).__str__(), knobs)
                    del copy_file_knob_dict[filename]
                elif pattern in ['%d', '$F']:
                    if attr_dict.get('pattern_num'):
                        new_file_knob_dict.setdefault(check_filename.parent.child(old_filename.name).__str__(), knobs)
                        del copy_file_knob_dict[filename]
        else:
            check_filenames = []
            for attr_dict in attr_dict_list:
                check_filename = DiskPath(attr_dict.get('filename'))
                if old_filename.name.lower() == check_filename.name.lower():
                    check_filenames.append(check_filename)
                elif ext == attr_dict.get('ext'):
                    if not pattern:
                        continue
                    if pattern.isdigit() and int(pattern) in attr_dict.get('frames'):
                        check_filenames.append(check_filename)
                    elif pattern_num == attr_dict.get('pattern_num'):
                        check_filenames.append(check_filename)
                    elif pattern in ['%d', '$F']:
                        if attr_dict.get('pattern_num'):
                            check_filenames.append(check_filename)
            if check_filenames:
                filterfile_name = recursive_file(old_filename.__str__().lower(), check_filenames)
                if not filterfile_name:
                    check_filename = DiskPath(check_filenames[0])
                else:
                    check_filename = DiskPath(filterfile_name)
                new_file_knob_dict.setdefault(check_filename.parent.child(old_filename.name).__str__(), knobs)
                del copy_file_knob_dict[filename]
    return new_file_knob_dict, copy_file_knob_dict


class ReplaceList(QDialog):
    """
    最后替换完成要列出来新的路径和按钮对照表GUI
    """
    def __init__(self, parent=None):
        super(ReplaceList, self).__init__(parent)
        self.resize(1080, 600)
        self.setWindowTitle('Replace List')

        formLayout = QFormLayout()
        formLayout.setLabelAlignment(Qt.AlignRight)
        formLayout.addRow(QLabel(u'<font color=green>绿色表示已经替换完成的新素材或资产路径'),)
        formLayout.addRow(QLabel(u'<font color=yellow>黄色表示原始的路径是存在的，但是新文件夹里没有发现同名文件，所以没有替换'), )
        formLayout.addRow(QLabel(u'<font color=red>红色表示原始路径和新文件夹里都不存在这个素材或资产'),)

        self.tree = QTreeWidget(self)
        self.tree.setSortingEnabled(True)
        # 设置列数
        self.tree.setColumnCount(1)
        # 设置头的标题
        self.tree.setHeaderLabels(['File Name'])
        # 设置控件大小随着内容长短自动变化
        head = self.tree.header()
        # 设置自适应的模式为QHeaderView.ResizeToContents，意思是自动填充为最大，不可更改
        # 只有pyside2或者PyQt5有
        head.setSectionResizeMode(QHeaderView.ResizeToContents)
        # 下面这句话是标题栏宽度自适应以后最后一项的长度一定要弹到最大
        head.setStretchLastSection(True)
        # 设置渐变色
        self.tree.setAlternatingRowColors(True)

        self.tree.itemDoubleClicked.connect(self.selecte_node)

        mainLayout = QVBoxLayout(self)
        mainLayout.addLayout(formLayout)
        mainLayout.addWidget(self.tree)
        self.setLayout(mainLayout)

    def clear_all_widget(self):
        """
        清除所有镜头列表
        :return:
        """
        self.tree.clear()

    def addItem(self, texture_dict):
        self.clear_all_widget()
        if not texture_dict:
            return
        node_name = ''
        if dcc_name.startswith('houdini'):
            node_name = 'path'
        elif dcc_name.startswith('nuke'):
            node_name = 'name'

        for file_name, value_dict in texture_dict.items():
            root = QTreeWidgetItem(self.tree)
            color = value_dict.get('color')
            root.setText(0, file_name)
            root.setForeground(0, color)
            for knob in value_dict.get('knobs'):
                knob_root = QTreeWidgetItem(root)
                knob_root.setText(0, getattr(knob.node(), node_name)())
            self.tree.addTopLevelItem(root)

    def selecte_node(self, qmodelindex):
        """
        在houdini里双击GUI上节点路径或者nuke里双击GUI上节点名，会展示这个节点工具栏
        :param qmodelindex:
        :return:
        """
        node = qmodelindex.text(0)
        if dcc_name.startswith('houdini'):
            import hou
            if node[0] != '/':
                return
            node = hou.node(node)
            node.setSelected(True)
        elif dcc_name.startswith('nuke'):
            import nuke
            import nukescripts
            node = nuke.toNode(node)
            nukescripts.clear_selection_recursive()
            node.showControlPanel(True)


class ReassignFilePath(QDialog):
    def __init__(self, parent=None):
        super(ReassignFilePath, self).__init__(parent)
        self.resize(370, 150)
        self.setWindowTitle(u'Repath Files')
        self.init_UI()

    def init_UI(self):
        """
        界面端
        :return:
        """
        self.file_widget = FolderWidget(parent=self)
        self.relative_assignments_widget = QCheckBox(u'Only replace does not exist')
        self.relative_assignments_widget.setToolTip(u'只替换不存在的文件路径')
        self.relative_assignments_widget.setChecked(True)

        formLayout = QFormLayout()
        formLayout.setLabelAlignment(Qt.AlignRight)
        formLayout.addRow(QLabel("New Folder"), self.file_widget)
        formLayout.addRow('', self.relative_assignments_widget)

        self.export_btn = QPushButton(u'Repath')
        self.export_btn.clicked.connect(self.do_execute)
        self.cancel_btn = QPushButton(u'Cancel', clicked=self.close)

        btn_hbox = QHBoxLayout()
        btn_hbox.addStretch(2)
        btn_hbox.addWidget(self.export_btn)
        btn_hbox.addStretch(1)
        btn_hbox.addWidget(self.cancel_btn)
        btn_hbox.addStretch(2)

        view_Layout = QVBoxLayout()
        view_Layout.addStretch()
        view_Layout.addStretch(1)
        view_Layout.addLayout(formLayout)
        view_Layout.addStretch(1)
        view_Layout.addLayout(btn_hbox)
        view_Layout.addStretch()
        self.setLayout(view_Layout)

    @staticmethod
    def messageBox(strings, flag='information'):
        """
        提示栏
        :param strings: 显示信息
        :param flag: 显示的图标
        :return:
        """
        icon_dict = {
                     'information': QMessageBox.Information,
                     'critical':    QMessageBox.Critical,
                    }
        msgBox = QMessageBox()
        msgBox.setIcon(icon_dict.get(flag.lower()))
        msgBox.setText(u'{}'.format(strings))
        msgBox.setStandardButtons(QMessageBox.Ok)
        msgBox.exec_()

    def do_execute(self):
        """
        根据当前DCC软件执行替换任务
        :return:
        """
        nonExist = self.relative_assignments_widget.isChecked()
        path = self.file_widget.get_folder()
        if not path or not os.path.exists(path):
            self.messageBox(u"输入的路径不存在", 'critical')
            return False
        file_parm_dict = ''
        knob_set = 'set'
        knob_label = 'description'
        if dcc_name.startswith('houdini'):
            file_parm_dict = hou_file_parm_dict(nonExist)
        elif dcc_name.startswith('nuke'):
            file_parm_dict = nuke_file_parm_dict(nonExist)
            knob_set = 'setValue'
            knob_label = 'label'
        # elif dcc_name.startswith('maya'):
        #     file_parm_dict = {}

        flag_dict = {}

        new_file_knob_dict, no_replace_file_knob_dict = get_new_file_knob_dict(path, file_parm_dict)
        pt = ProgressTask('Copy files')
        all_filename_num = len(sum(new_file_knob_dict.values(), []))
        for num, (filename, knobs) in enumerate(new_file_knob_dict.items(), 1):
            flag_dict.setdefault(filename, {'knobs': knobs, 'color': Qt.green})
            pt.setParentMessage('filename replace "<font color=yellow>{}</font>" ({})'.format(
                os.path.basename(filename), str(num) + ' of ' + str(all_filename_num)))
            all_knob_num = len(knobs)
            knob_num = 0
            for knob in knobs:
                getattr(knob, knob_set)(filename)
                knob_num += 1
                knob_name = getattr(knob, knob_label)()
                pt.setChildMessage('Knob name  "<font color=yellow>{}</font>"  ({})'.format(
                    knob_name, str(knob_num) + ' of ' + str(all_knob_num)))
                percentage = (float(knob_num) / all_knob_num) * 100
                pt.setChildProgress(percentage)
            pt.setParentProgress((float(num) / all_filename_num) * 100)
        pt.setParentProgress(100)

        for filename, knobs in no_replace_file_knob_dict.items():
            if get_pattern_sequence(filename, True):
                flag_dict.setdefault(filename, {'knobs': knobs, 'color': Qt.yellow})
            else:
                flag_dict.setdefault(filename, {'knobs': knobs, 'color': Qt.red})

        tree_widget = ReplaceList(self)
        tree_widget.addItem(flag_dict)
        tree_widget.showNormal()


def do():
    main_window = None
    if dcc_name.startswith('houdini'):
        import hou
        main_window = hou.qt.mainWindow()
    elif dcc_name.startswith('nuke'):
        main_window = QApplication.activeWindow()
    win = ReassignFilePath(main_window)
    win.showNormal()


if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    window = ReassignFilePath()
    window.show()
    sys.exit(app.exec_())

