#!/usr/bin/env python
# -*- coding:utf-8 -*-

import os
import hashlib


def get_all_file(path):
    all_file = []
    for root, dirs, files in os.walk(path):
        for file in files:
            all_file.append(os.path.join(root, file))
    return all_file


def get_file_md5(file_path):
    with open(file_path, 'rb') as fp:
        data = fp.read()
        file_md5 = hashlib.md5(data).hexdigest()
        return file_md5


def get_file_size(file_path):
    file_size = os.path.getsize(file_path)
    return file_size


def get_file_create_time(file_path):
    file_ctime = os.path.getctime(file_path)
    return file_ctime


def get_file_modify_time(file_path):
    file_mtime = os.path.getmtime(file_path)
    return file_mtime


def get_file_access_time(file_path):
    file_atime = os.path.getatime(file_path)
    return file_atime


def get_file_info(file_path):
    file_info = {}
    file_info['file_path'] = file_path
    file_info['file_md5'] = get_file_md5(file_path)
    file_info['file_size'] = get_file_size(file_path)
    file_info['file_ctime'] = get_file_create_time(file_path)
    file_info['file_mtime'] = get_file_modify_time(file_path)
    file_info['file_atime'] = get_file_access_time(file_path)
    return file_info


def get_all_file_info(path):
    all_file_info = []
    all_file = get_all_file(path)
    for file in all_file:
        file_info = get_file_info(file)
        all_file_info.append(file_info)
    return all_file_info


def deduplication_by_md5(path):
    all_file_info = get_all_file_info(path)
    md5_list = []
    dupication_list = []
    for file_info in all_file_info:
        if file_info['file_md5'] not in md5_list:
            md5_list.append(file_info['file_md5'])
        else:
            dupication_list.append(file_info['file_path'])
            os.remove(file_info['file_path'])


# deduplication_by_md5("text")


def deduplication_by_size(path):
    all_file_info = get_all_file_info(path)
    size_list = []
    for file_info in all_file_info:
        if file_info['file_size'] not in size_list:
            size_list.append(file_info['file_size'])
        else:
            os.remove(file_info['file_path'])


def deduplication_by_ctime(path):
    all_file_info = get_all_file_info(path)
    ctime_list = []
    for file_info in all_file_info:
        if file_info['file_ctime'] not in ctime_list:
            ctime_list.append(file_info['file_ctime'])
        else:
            os.remove(file_info['file_path'])


def deduplication_by_mtime(path):
    all_file_info = get_all_file_info(path)
    mtime_list = []
    for file_info in all_file_info:
        if file_info['file_mtime'] not in mtime_list:
            mtime_list.append(file_info['file_mtime'])
        else:
            os.remove(file_info['file_path'])


def deduplication_by_atime(path):
    all_file_info = get_all_file_info(path)
    atime_list = []
    for file_info in all_file_info:
        if file_info['file_atime'] not in atime_list:
            atime_list.append(file_info['file_atime'])
        else:
            os.remove(file_info['file_path'])


def deduplication_by_md5_size(path):
    all_file_info = get_all_file_info(path)
    md5_size_list = []
    for file_info in all_file_info:
        md5_size = file_info['file_md5'] + str(file_info['file_size'])
        if md5_size not in md5_size_list:
            md5_size_list.append(md5_size)
        else:
            os.remove(file_info['file_path'])
