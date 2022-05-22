#!/usr/bin/env python
#-*- coding:utf-8 -*-
"""
Sprint-Layout v6 2022版的插件
将SVG转换为Sprint-Layout的多边形填充
Author: cdhigh <https://github.com/cdhigh>
"""
import os, sys
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.svgLib.path import SVGPath
from fontTools.misc import bezierTools
from sprint_struct.font_to_polygon import mergePolygons, SMOOTH_MAP
from sprint_struct.sprint_textio import *
from comm_utils import *

#SVG转换为spring-layout的多边形
#svgFile: svg文件
#layerIdx: 电路板图层索引，从1开始
#height: 绘制高度，单位为毫米
#smooth: 曲线平滑系数，参见 SMOOTH_MAP
#usePolygon: 绘制模式，0-使用线条，1-使用多边形
#返回SprintTextIO实例
#字体坐标原点在屏幕左下角，但Sprint-Layout坐标原点在左上角，所以字形需要垂直翻转
def svgToPolygon(svgFile: str, layerIdx: int=2, height: float=10, smooth: int=2, usePolygon: bool=True):
    try:
        svg = SVGPath(svgFile)
        pen = SVGPathPen(None)
        svg.draw(pen)
    except:
        return None

    svgCmds = pen._commands  #提取绘制语句
    xMin, yMin, xMax, yMax = getSvgBoundingBox(svgCmds)
    svgWidth = xMax - xMin
    svgHeight = yMax - yMin
    lineWidth = 0 #0.01 if (height <= 2.0) else 0.1

    #计算缩放后的宽度
    width = (svgWidth * height) / svgHeight
    
    #如果是下方板层，则进行水平翻转
    if (layerIdx in (LAYER_C2, LAYER_S2)):
        scaleX = lambda x: -((x * width) / svgWidth)
    else:
        scaleX = lambda x: ((x * width) / svgWidth)

    scaleY = lambda y: ((y * height) / svgHeight)

    drawElements = []
    currElem = SprintPolygon(layerIdx) if usePolygon else SprintTrack(layerIdx, lineWidth)
    prevX = prevY = 0 #笔的前一个位置
    currX = currY = 0 #笔的当前位置
    ctrlX1 = ctrlY1 = ctrlX2 = ctrlY2 = 0 #控制点坐标
    #开始解析和转换命令，并且转换为多个多边形
    for cmd in svgCmds:
        code = cmd[0] #第一个字符是指令
        vert = cmd[1:].split(' ') #其余字符是坐标点，以空格分隔
        # M = 路径起始 - 参数 - 起始点坐标 (x y)
        if code == 'M':
            if currElem.isValid():
                drawElements.append(currElem)
            currElem = SprintPolygon(layerIdx) if usePolygon else SprintTrack(layerIdx, lineWidth)
            currX = scaleX(str_to_float(vert[0]))  #保存笔的起始位置
            currY = scaleY(str_to_float(vert[1]))
            currElem.addPoint(currX, currY)
            prevX = currX #保存笔的当前位置(由于是起笔，所以当前位置就是起始位置)
            prevY = currY
        # Q = 绘制二次贝塞尔曲线 - 参数 - 曲线控制点和终点坐标(x1 y1 x y)+
        elif code == 'Q':
            ctrlX1 = scaleX(str_to_float(vert[0]))
            ctrlY1 = scaleY(str_to_float(vert[1]))
            currX = scaleX(str_to_float(vert[2]))
            currY = scaleY(str_to_float(vert[3]))
            pt1 = (prevX, prevY)
            pt2 = (ctrlX1, ctrlY1)
            pt3 = (currX, currY)
            
            #每个线段分成若干份
            for i in SMOOTH_MAP.get(smooth, [0.5,]):
                newX, newY = bezierTools.quadraticPointAtT(pt1, pt2, pt3, i)
                currElem.addPoint(newX, newY)

            #最后一段
            currElem.addPoint(currX, currY)
            prevX = currX
            prevY = currY
        # C = 绘制三次贝塞尔曲线 - 参数 - 曲线控制点1，控制点2和终点坐标(x1 y1 x2 y2 x y)+
        elif code == 'C':
            ctrlX1 = scaleX(str_to_float(vert[0]))
            ctrlY1 = scaleY(str_to_float(vert[1]))
            ctrlX2 = scaleX(str_to_float(vert[2]))
            ctrlY2 = scaleY(str_to_float(vert[3]))
            currX = scaleX(str_to_float(vert[4]))
            currY = scaleY(str_to_float(vert[5]))
            pt1 = (prevX, prevY)
            pt2 = (ctrlX1, ctrlY1)
            pt3 = (ctrlX2, ctrlY2)
            pt4 = (currX, currY)
            #每个线段分成若干份
            for i in SMOOTH_MAP.get(smooth, [0.5,]):
                newX, newY = bezierTools.cubicPointAtT(pt1, pt2, pt3, pt4, i)
                currElem.addPoint(newX, newY)
            currElem.addPoint(currX, currY)
            prevX = currX
            prevY = currY
        # L = 绘制直线 - 参数 - 直线终点(x, y)+
        elif code == 'L':
            prevX = scaleX(str_to_float(vert[0]))
            prevY = scaleY(str_to_float(vert[1]))
            currElem.addPoint(prevX, prevY)
        # V = 绘制垂直线 - 参数 - 直线y坐标 (y)+
        elif code == 'V':
            #由于是垂直线，x坐标不变，提取y坐标
            prevY = scaleY(str_to_float(vert[0]))
            currElem.addPoint(prevX, prevY)
        # H = 绘制水平线 - 参数 - 直线x坐标 (x)+
        elif code == 'H':
            #由于是水平线，y坐标不变，提取x坐标
            prevX = scaleX(str_to_float(vert[0]))
            currElem.addPoint(prevX, prevY)
        # Z = 路径结束，无参数
        elif code == 'Z':
            if currElem.isValid():
                drawElements.append(currElem)
            currElem = SprintPolygon(layerIdx) if usePolygon else SprintTrack(layerIdx, lineWidth)
        #有一些语句指令为空，为绘制直线
        else:
            prevX = scaleX(str_to_float(vert[0]))
            prevY = scaleY(str_to_float(vert[1]))
            currElem.addPoint(prevX, prevY)

    #分析里面的多边形，看是否有相互包含关系，如果有相互包含关系，则将相互包含的多边形合并
    if usePolygon:
        mergePolygons(drawElements)

    textIo = SprintTextIO()
    textIo.addAll(drawElements)
    return textIo

#获取SVG绘图指令列表中的坐标最大最小值，返回(xMin, yMin, xMax, yMax)
def getSvgBoundingBox(svgCmds: list):
    xMin = yMin = 9999999999
    xMax = yMax = -9999999999
    def update_bbox(x, y):
        nonlocal xMin, xMax, yMin, yMax
        x = str_to_float(x)
        y = str_to_float(y)
        if x < xMin:
            xMin = x
        if x > xMax:
            xMax = x
        if y < yMin:
            yMin = y
        if y > yMax:
            yMax = y
    def update_bbox_x(x):
        nonlocal xMin, xMax, yMin, yMax
        x = str_to_float(x)
        if x < xMin:
            xMin = x
        if x > xMax:
            xMax = x
    def update_bbox_y(y):
        nonlocal xMin, xMax, yMin, yMax
        y = str_to_float(y)
        if y < yMin:
            yMin = y
        if y > yMax:
            yMax = y

    for cmd in svgCmds:
        code = cmd[0] #第一个字符是指令
        vert = cmd[1:].split(' ') #其余字符是坐标点，以空格分隔
        # M = 路径起始 - 参数 - 起始点坐标 (x y)
        if code == 'M':
            update_bbox(vert[0], vert[1])
        # Q = 绘制二次贝塞尔曲线 - 参数 - 曲线控制点和终点坐标(x1 y1 x y)+
        elif code == 'Q':
            update_bbox(vert[0], vert[1])
            update_bbox(vert[2], vert[3])
        # C = 绘制三次贝塞尔曲线 - 参数 - 曲线控制点1，控制点2和终点坐标(x1 y1 x2 y2 x y)+
        elif code == 'C':
            update_bbox(vert[0], vert[1])
            update_bbox(vert[2], vert[3])
            update_bbox(vert[4], vert[5])
        # L = 绘制直线 - 参数 - 直线终点(x, y)+
        elif code == 'L':
            update_bbox(vert[0], vert[1])
        # V = 绘制垂直线 - 参数 - 直线y坐标 (y)+
        elif code == 'V':
            #由于是垂直线，x坐标不变，提取y坐标
            update_bbox_y(vert[0])
        # H = 绘制水平线 - 参数 - 直线x坐标 (x)+
        elif code == 'H':
            #由于是水平线，y坐标不变，提取x坐标
            update_bbox_x(vert[0])
        # Z = 路径结束，无参数
        elif code == 'Z':
            pass
        #有一些语句指令为空，为绘制直线
        else:
            update_bbox(vert[0], vert[1])
    
    return (xMin, yMin, xMax, yMax)