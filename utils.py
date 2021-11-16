#!/usr/bin/env python
# -*- coding: utf-8 -*-
###################################################################
# Author: Wenfeng Zhang
# Email : zwf.vfx@Foxmail.com
###################################################################


def name_format(filename):
    """
    一个标准化的文件名方法，会分出文件名、序列化符号、文件格式名字和绝对名字，这个可以很好的来比较两个复杂文件名是否是同一个文件
    最后返回的一个namedtuple， 里面有 name， pattern， ext， absname， pattern_num方法
    之所以有name还要增加一个absname，是因为name返回一个序列化符号之前的名字，而这个名字可能是后面带‘.’号，这是为了严谨的比较
    例如 D:/a/b.%04d.exr和D:/a/b%04d.exr 并不是同一个文件序列，只是返回绝对的名字可能误以为是同一个序列。
    还有一种情况是D:/a/b.%04d.exr和D:/a/b.%03d.exr，虽然得到的name和ext都一样，但是序列帧位数pattern_num却不一样，也不是一个序列，这都需要精确的比较
    而纯文件名用absname，是去掉最后的‘.’号的，方便使用。
    :param filename: 文件名字，可以是完整路径，也可以只是文件名字 D:/a/b.%04d.exr 或者 b.%04d.exr
    :return: namedtuple， 里面有 name， pattern， ext， absname， pattern_num方法方法
    """
    import re
    import os
    from collections import namedtuple
    basename = os.path.basename(filename)
    num = len(basename.split('.'))
    if num == 1:
        return False
    bgeo_sc = '.bgeo.sc'
    pattern_regex = re.compile(r'(%\d*d|#+|<UDIM>|%\(UDIM\)d|\$F\d*|\d+)$', re.IGNORECASE)
    nameformat = namedtuple('nameformat', ['name', 'pattern', 'ext', 'absname', 'pattern_num'])
    ext = os.path.splitext(basename)[-1][1:].lower()
    if basename.endswith(bgeo_sc):
        basename = basename.rsplit('.', 1)[0]
        bgeo_format = name_format(basename)
        return bgeo_format._replace(ext='bgeo.sc')
    if ext in ['mp4', 'mov', 'avi']:
        name = os.path.splitext(basename)[0]
        pattern = ''
    elif num > 2:
        stem = os.path.splitext(basename)[0]
        pattern_name = '.'.join(basename.split('.')[1:-1])
        pattern_digit = '.'.join(basename.split('.')[-2:-1])
        if pattern_digit.isdigit():
            name = '.'.join(basename.split('.')[:-2])+'.'
            pattern = pattern_digit
        elif pattern_regex.findall(pattern_name):
            pattern = pattern_regex.findall(pattern_name)[0]
            name = stem.rsplit(pattern, 1)[0]
        else:
            name = stem
            pattern = ''
    else:
        stem = os.path.splitext(basename)[0]
        version_regex = re.compile(r'v\d+$', re.IGNORECASE)
        if stem.isdigit() or version_regex.findall(stem):
            name = stem
            pattern = ''
        elif pattern_regex.findall(stem):
            pattern = pattern_regex.findall(stem)[0]
            name = stem.rsplit(pattern, 1)[0]
        else:
            name = stem
            pattern = ''
    pattern_num = ''
    if pattern:
        p_regex = re.compile(r'\$F(\d*)|%(\d*)d', re.IGNORECASE)
        if pattern in ['<udim>', '<UDIM>', '%(udim)d', '%(UDIM)d']:
            pattern_num = 4
        elif pattern[0] == '#' or pattern.isdigit():
            pattern_num = len(pattern)
        elif p_regex.search(pattern):
            pattern_num = p_regex.search(pattern).group(1) or p_regex.search(pattern).group(2)
            pattern_num = int(pattern_num) if pattern_num else ''
    absname = name.rstrip('.')
    return nameformat(name, pattern, ext, absname, pattern_num)


def find_folder_name(path):
    """
    检测已存在的文件夹，如果已存在，则返回一个新名字，末尾自带(x)排序,例如D:/a/b, D:/a/b(1), D:/a/b(2)
    :param path:
    :return: 文件夹名字
    """
    import re
    import os
    directory, basename = os.path.dirname(path), os.path.basename(path)
    while os.path.isdir(path):
        pattern = r'\((\d+)\)'
        if re.search(pattern, basename) is None:
            basename = basename + '(1)'
        else:
            current_number = int(re.findall(pattern, basename)[-1])
            new_number = current_number + 1
            basename = basename.replace('({})'.format(current_number), '({})'.format(new_number))
        path = os.path.join(directory, basename)
    return path


def new_folder_name(path, file_list):
    """
    传入一个文件夹路径和一个文件夹列表，检测文件夹路径是否已经存在于文件夹列表中，如果已存在，则返回一个新名字，末尾自带(x)排序,
        例如D:/a/b, D:/a/b(1), D:/a/b(2)
    :param path: 文件夹名字 D:/a/b
    :param file_list: 文件夹列表 ['D:/a/b(1)', 'D:/a/b(2)']
    :return: 文件夹名字
    """
    import re
    import os
    path = os.path.normpath(path)
    directory, basename = os.path.dirname(path), os.path.basename(path)
    while path in [os.path.normpath(i) for i in file_list]:
        pattern = r'\((\d+)\)'
        if re.search(pattern, basename) is None:
            basename = basename + '(1)'
        else:
            current_number = int(re.findall(pattern, basename)[-1])
            new_number = current_number + 1
            basename = basename.replace('({})'.format(current_number), '({})'.format(new_number))
        path = os.path.join(directory, basename)
    return path.replace('\\', '/')


def is_ascii(s):
    """
    检测字符串中是否全是ascii码，如果有ascii以外的编码，则返回False
    :param s: 字符串
    :return: bool
    """
    import string
    printset = set(string.printable)
    isprintable = set(s).issubset(printset)
    return isprintable


def get_all_file(lpath, recursive=False, ext='*'):
    """
    列出所有的指定格式的文件，如果没有给格式则列出所有文件
    :param lpath: 要查找的路径
    :param recursive:是否要循环查找子文件夹，默认为不查找
    :param ext: 要筛选的文件格式,可以是单个格式字符串，也可以是格式的列表
    :return: 返回寻找到的文件列表
    """
    import os
    file_list = []

    if ext == '*':
        for dirpath, _, filenames in os.walk(lpath):
            if not recursive:
                # 如果不往子文件夹遍历就检查列出的文件路径和输入的文件路径是否相同，不同则为子文件夹，就continue
                if lpath.replace('\\', '/').lower() != dirpath.replace('\\', '/').lower():
                    continue
            for name in filenames:
                file_list.append('/'.join((dirpath, name)).replace('\\', '/'))
    else:
        exts = ext if isinstance(ext, (list, tuple)) else [ext]
        ext_list = [e.lower() if '.' in e else '.'+e.lower() for e in exts]
        for dirpath, dirnames, filenames in os.walk(lpath):
            if not recursive:
                if lpath.replace('\\', '/').lower() != dirpath.replace('\\', '/').lower():
                    continue
            for name in filenames:
                if os.path.splitext(name)[-1].lower() in ext_list:
                    file_list.append('/'.join((dirpath, name)).replace('\\', '/'))
    return file_list


def get_pattern_sequence(filename, flag=False):
    """
    得到带有pattern标记路径下所有对应的文件列表，如果没有pattern标记，会检查是不是个单文件，例如：
    filename: D:/a/b.%04d.exr  ——>  [D:/a/b.1001.exr, D:/a/b.1002.exr, D:/a/b.1003.exr, ...]
    filename: D:/a/b.exr  ——>  [D:/a/b.exr]
    :param filename: 文件完整路径
    :param flag: 只是用作判断是否存在使用，如果存在返回布尔值True，不继续迭代计算，对于序列而言可以节省很多。
    :return: 文件的列表
    """
    import os
    if os.path.exists(filename):
        if flag:
            return True
        return [filename.replace('\\', '/')]
    nameformat = name_format(filename)
    if not nameformat:
        if flag:
            return False
        return []
    ext = nameformat.ext
    name = nameformat.name.lower()
    file_list = []
    if nameformat.pattern:
        parent = os.path.dirname(filename)
        for file_ in get_all_file(lpath=parent, ext=ext):
            if not is_ascii(file_) or '.' not in file_:
                continue
            if name_format(file_).name.lower() == name:
                if flag:
                    return True
                file_list.append(file_)
        else:
            if flag:
                return False
    return file_list


def recursive_file(filename, file_list, slice_=-2):
    """
    当出现不同文件重名的情况时，例如'D:/a/b/c.exr'和'D:/a/e/c.exr'都是a总文件夹下里的c.exr，但是父文件夹不一样，
    调用此函数会从父级一层一层查找相同名，直到找到位置，否则返回False
    :param filename: 给定的要替换的文件路径
    :param file_list: 列出来的重名的文件列表
    :param slice_: 要查找的文件名字序号，因为要从父级查找所以是-2开始，也就是文件所在的文件夹名字，如果有两个或两个以上都一样，就继续往上找，直至不同
    :return: 如果找到就返回文件，否则False
    """
    if filename in file_list:
        return filename
    if len(file_list) == 1:
        return file_list[0]
    file_name_list = filename.replace('\\', '/').split('/')
    if -len(file_name_list) > slice_:
        return file_list[-1]
    folder_name = file_name_list[slice_].lower()
    file_parent_name_list = [f for f in file_list if f.replace('\\', '/').split('/')[slice_].lower() == folder_name]
    if not file_parent_name_list:
        return False if slice_ == -1 else file_list[0]
    elif len(file_parent_name_list) == 1:
        return file_parent_name_list[0]
    else:
        return recursive_file(filename, file_parent_name_list, slice_-1)


def copy_progress_task(file_dict):
    """
    一个双进度条的拷贝函数，父进度条显示的是每个序列的整体进度，子进度条显示的是每个文件在其所在序列里的进度
    :param file_dict: 导入的必须是原文件序列和输出的文件夹组成字典,输出文件夹可以使个列表，也就是一套序列可以复制到多个文件夹里，类似于
                      {d:/a/b/c.%04d.exr: d:/output,
                      d:/a/b/c.%04d.exr: [d:/output, d:/output2]
                      }
    :return: 无法拷贝的路径
    """
    import os
    import subprocess
    from .ProgressBar import ProgressTask
    from collections import Iterable

    error_list = []
    pt = ProgressTask('Copy files')
    stop_flag = False
    from_file_number = len(file_dict.keys())
    for num, (from_file, output) in enumerate(file_dict.items(), 1):
        if not output:
            error_list.append(from_file)
            continue
        if stop_flag:
            break
        if os.path.exists(from_file):
            name_regexp = os.path.basename(from_file)
            all_frame_number = 1
        else:
            from_ = get_pattern_sequence(from_file)
            if not from_:
                error_list.append(from_file)
                continue
            all_frame_number = len(from_)
            nameformat = name_format(from_file)
            pattern_num = nameformat.pattern_num
            pattern = '?'*pattern_num+'.' if pattern_num else '*.'
            name_regexp = ''.join([nameformat.name, pattern, nameformat.ext])
        pt.setParentMessage('Parent Copy "<font color=yellow>{}</font>" sequence ({})'.format(
            os.path.basename(from_file), str(num)+' of '+str(from_file_number)))
        if isinstance(output, basestring):
            out_list = [output]
        elif isinstance(output, Iterable):
            out_list = output
        else:
            error_list.append(from_file)
            continue
        from_path = os.path.dirname(from_file)
        for out_path in out_list:
            if stop_flag:
                break
            if not os.path.exists(out_path):
                os.makedirs(out_path, 0o777)
            number = 0
            cmd_copy = 'robocopy "{from_path}" "{out_path}" "{name_regexp}" /NP /NDL /NJS /NJH /NS /NC'.format(
                from_path=str(from_path), out_path=str(out_path), name_regexp=str(name_regexp))
            child = subprocess.Popen(cmd_copy, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
            while child.poll() is None:
                line = child.stdout.readline().strip()
                if line:
                    number += 1
                    if is_ascii(line):
                        pt.setChildMessage('Child Copy  "<font color=yellow>{}</font>"  ({})'.format(
                            os.path.basename(line), str(number)+' of '+str(all_frame_number)))
                    percentage = (float(number)/all_frame_number)*100
                    pt.setChildProgress(percentage)
                if pt.wasCanceled():
                    child.terminate()
                    stop_flag = True
                    break
        pt.setParentProgress((float(num)/from_file_number)*100)
    pt.setParentProgress(100)
    return error_list

