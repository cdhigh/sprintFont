#!/usr/bin/env python
#-*- coding:utf-8 -*-
"""
公共工具
Author: cdhigh <https://github.com/cdhigh>
"""
import math

#字符串转整数，出错则返回defaultValue
def str_to_int(txt: str, defaultValue: int=0):
    try:
        return int(txt.strip())
    except:
        return defaultValue

#字符串转浮点数，出错则返回defaultValue
def str_to_float(txt: str, defaultValue: int=0.0):
    try:
        return float(txt.strip())
    except:
        return defaultValue

#判断一个字符串是否是十六进制字符串
def isHexString(txt: str):
    txt = txt.lower()
    for ch in txt:
        if ((not ('0' <= ch <= '9')) and (not ('a' <= ch <= 'f'))):
            return False
    return True


#计算二维空间两点之间的距离
def euclideanDistance(x1: float, y1: float, x2: float, y2: float):
    return math.sqrt(((x1 - x2) ** 2) + ((y1 - y2) ** 2))
