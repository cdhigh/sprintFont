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

#弧度转角度
def radiansToDegrees(ra):
    return ra / math.pi * 180

#计算二维空间两点之间的距离
def euclideanDistance(x1: float, y1: float, x2: float, y2: float):
    return math.sqrt(((x1 - x2) * (x1 - x2)) + ((y1 - y2) * (y1 - y2)))

#已知两点和半径，求圆心
#x1/y1: 起点坐标
#x2/y2: 终点坐标
#radius: 半径
#bigArc: 1-大圆弧, 0-小圆弧
#dirCC: 方向，1-顺时针，0-逆时针
#返回：(cx, cy)
def calCenterByPointsAndRadius(x1: float, y1: float, x2: float, y2: float, radius: float, bigArc: bool, dirCC: bool):
    lineLen = euclideanDistance(x1, y1, x2, y2)
    x3 = (x1 + x2) / 2
    y3 = (y1 + y2) / 2

    xTmp = math.sqrt(radius * radius - (lineLen / 2) * (lineLen / 2)) * (y1 - y2) / lineLen
    yTmp = math.sqrt(radius * radius - (lineLen / 2) * (lineLen / 2)) * (x2 - x1) / lineLen

    #分别为两个圆心
    cx1 = x3 + xTmp
    cy1 = y3 + yTmp
    cx2 = x3 - xTmp
    cy2 = y3 - yTmp

    angleLine = math.acos((x2 - x1) / lineLen) * 180 / math.pi
    if (y2 < y1):
        angleLine = -angleLine

    if (((angleLine > 0) and (angleLine < 180)) or (angleLine == 180)):
        if (dirCC): #顺时针圆
            return (cx1, cy1) if (bigArc) else (cx2, cy2)
        else: #逆时针圆
            return (cx2, cy2) if (bigArc) else (cx1, cy1)
    else:
        if (dirCC): #顺时针圆
            return (cx2, cy2) if (bigArc) else (cx1, cy1)
        else:
            return (cx1, cy1) if (bigArc) else (cx2, cy2)


