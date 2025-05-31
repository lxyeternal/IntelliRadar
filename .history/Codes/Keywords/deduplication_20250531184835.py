# !/usr/bin/env python
# -*-coding:utf-8 -*-

"""
# @File     : deduplication.py
# @Project  : PMonitor
# Time      : 29/1/24 4:25 pm
# version   : python 3.8
# Description：
"""


import os
import hashlib


def get_all_file(path):
    # 1. Get all files in the folder
    all_file = []
    for root, dirs, files in os.walk(path):
        for file in files:
            all_file.append(os.path.join(root, file))
    return all_file

def get_file_md5(file_path):
    # 2. Get the MD5 of the file
    with open(file_path, 'rb') as fp:
        data = fp.read()
        file_md5 = hashlib.md5(data).hexdigest()
        return file_md5

def get_file_size(file_path):
    # 3. Get the size of the file
    file_size = os.path.getsize(file_path)
    return file_size

def get_file_create_time(file_path):
    # 4. Get the creation time of the file
    file_ctime = os.path.getctime(file_path)
    return file_ctime

def get_file_modify_time(file_path):
    # 5. Get the modification time of the file
    file_mtime = os.path.getmtime(file_path)
    return file_mtime

def get_file_access_time(file_path):
    # 6. Get the access time of the file
    file_atime = os.path.getatime(file_path)
    return file_atime


def get_file_info(file_path):
    # 7. Get the basic information of the file
    file_info = {}
    file_info['file_path'] = file_path
    file_info['file_md5'] = get_file_md5(file_path)
    file_info['file_size'] = get_file_size(file_path)
    file_info['file_ctime'] = get_file_create_time(file_path)
    file_info['file_mtime'] = get_file_modify_time(file_path)
    file_info['file_atime'] = get_file_access_time(file_path)
    return file_info


def get_all_file_info(path):
    # 8. Get the basic information of all files in the folder
    all_file_info = []
    all_file = get_all_file(path)
    for file in all_file:
        file_info = get_file_info(file)
        all_file_info.append(file_info)
    return all_file_info

def deduplication_by_md5(path):
    # 9. Deduplicate files based on MD5 value
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
    # 10. Deduplicate files based on file size
    all_file_info = get_all_file_info(path)
    size_list = []
    for file_info in all_file_info:
        if file_info['file_size'] not in size_list:
            size_list.append(file_info['file_size'])
        else:
            os.remove(file_info['file_path'])

def deduplication_by_ctime(path):
    # 11. Deduplicate files based on creation time
    all_file_info = get_all_file_info(path)
    ctime_list = []
    for file_info in all_file_info:
        if file_info['file_ctime'] not in ctime_list:
            ctime_list.append(file_info['file_ctime'])
        else:
            os.remove(file_info['file_path'])

def deduplication_by_mtime(path):
    # 12. Deduplicate files based on modification time
    all_file_info = get_all_file_info(path)
    mtime_list = []
    for file_info in all_file_info:
        if file_info['file_mtime'] not in mtime_list:
            mtime_list.append(file_info['file_mtime'])
        else:
            os.remove(file_info['file_path'])

def deduplication_by_atime(path):
    # 13. Deduplicate files based on access time
    all_file_info = get_all_file_info(path)
    atime_list = []
    for file_info in all_file_info:
        if file_info['file_atime'] not in atime_list:
            atime_list.append(file_info['file_atime'])
        else:
            os.remove(file_info['file_path'])

def deduplication_by_md5_size(path):
    # 14. Deduplicate files based on MD5 value and size
    all_file_info = get_all_file_info(path)
    md5_size_list = []
    for file_info in all_file_info:
        md5_size = file_info['file_md5'] + str(file_info['file_size'])
        if md5_size not in md5_size_list:
            md5_size_list.append(md5_size)
        else:
            os.remove(file_info['file_path'])