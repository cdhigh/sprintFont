#!/usr/bin/env python
#-*- coding:utf-8 -*-
"""
Sprint-layout v6 2022版的插件，在电路板插入其他字体（包括中文字体）的文字
将字体转换为sprint-layout的多边形填充
Author: cdhigh <https://github.com/cdhigh>
"""
import os, sys
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.misc import bezierTools
from polygon import Polygon

#sprint-layout的各板层索引定义
LAYER_C1 = 1
LAYER_S1 = 2
LAYER_C2 = 3
LAYER_S2 = 4
LAYER_I1 = 5
LAYER_I2 = 6
LAYER_U  = 7

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

SMOOTH_MAP = {
    0: [(i / 30) for i in range(1, 30)], #超精细，一个曲线分成30份
    1: [(i / 20) for i in range(1, 20)], #精细，一个曲线分成20份
    2: [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9], #正常，一个曲线分成10份
    3: [0.2, 0.4, 0.6, 0.8,], #粗糙，一个曲线分成5份
    4: [0.5,], #比较粗糙，一个曲线分成2份
}

#提取单个字体的字形，转换为spring-layout的多边形
#font: 字体对象ttfFont
#code: 字的unicode编码
#layer: 电路板图层索引，从1开始
#fontHeight: 字体高度，单位为毫米
#offsetX: X方向的偏移，单位为毫米，用于多个字形成一行
#offsetY: Y方向的偏移，单位为毫米，用于多行
#smooth: 曲线平滑系数，参见 SMOOTH_MAP
#返回{'width':, 'height':, 'polygon':}
#字体坐标原点在屏幕左下角，但sprint-layout坐标原点在左上角，所以字形需要垂直翻转
def singleWordPolygon(font, code: int, layerIdx: int=2, fontHeight: float=2.0, offsetX: float=0, 
    offsetY: float=0, smooth: int=2):
    
    #获取包含字形名称和字形对象的--字形集对象glyphSet
    glyphSet = font.getGlyphSet()
    pen = SVGPathPen(glyphSet)  #获取pen的基类

    #先通过cmap查询字形名字
    cmap = font.getBestCmap()
    codeStr = cmap.get(code)
    if not codeStr or (codeStr not in glyphSet): #再尝试使用unicode查找
        codeStr = 'uni{:04X}'.format(code)
        if codeStr not in glyphSet:
            return None

    glyph = glyphSet.get(codeStr) #提取字形对象
    if not glyph:
        return None
    
    glyph.draw(pen)  #绘制字形对象
    fontCmds = pen._commands  #提取绘制语句
    
    #从'head'表中提取所有字形的边界框，并且计算缩放系数
    xMin = font['head'].xMin
    yMin = font['head'].yMin
    xMax = font['head'].xMax
    yMax = font['head'].yMax
    width = xMax - xMin
    height = yMax - yMin
    fontHeight *= 10000  #sprint-layout以0.1微米为单位
    fontWidth = (width * fontHeight) / height
    
    #如果是下方板层，则将字形进行水平翻转
    if (layerIdx in (LAYER_C2, LAYER_S2)):
        scaleX = lambda x: -(((x * fontWidth) / width) + offsetX)
    else:
        scaleX = lambda x: (((x * fontWidth) / width) + offsetX)

    #Y轴转换数值的同时，加一个符号，表示垂直翻转
    scaleY = lambda y: -(((y * fontHeight) / height) + offsetY)

    polygons = []  #保存所有的封闭多边形
    currPolygon = Polygon()
    prevX = prevY = 0 #笔的前一个位置
    currX = currY = 0 #笔的当前位置
    ctrlX1 = ctrlY1 = ctrlX2 = ctrlY2 = 0 #控制点坐标
    #开始解析和转换命令，并且转换为多个多边形
    for cmd in fontCmds:
        code = cmd[0] #第一个字符是指令
        vert = cmd[1:].split(' ') #其余字符是坐标点，以空格分隔
        # M = 路径起始 - 参数 - 起始点坐标 (x y)
        if code == 'M':
            currX = scaleX(str_to_float(vert[0]))  #保存笔的起始位置
            currY = scaleY(str_to_float(vert[1]))
            currPolygon.addPoint(currX, currY)
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
            arcLen = bezierTools.approximateQuadraticArcLength(pt1, pt2, pt3)
            
            #每个线段分成若干份
            for i in SMOOTH_MAP.get(smooth, [0.5,]):
                newX, newY = bezierTools.quadraticPointAtT(pt1, pt2, pt3, i)
                currPolygon.addPoint(newX, newY)

            #最后一段
            currPolygon.addPoint(currX, currY)
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
                currPolygon.addPoint(newX, newY)
            currPolygon.addPoint(currX, currY)
            prevX = currX
            prevY = currY
        # L = 绘制直线 - 参数 - 直线终点(x, y)+
        elif code == 'L':
            prevX = scaleX(str_to_float(vert[0]))
            prevY = scaleY(str_to_float(vert[1]))
            currPolygon.addPoint(prevX, prevY)
        # V = 绘制垂直线 - 参数 - 直线y坐标 (y)+
        elif code == 'V':
            #由于是垂直线，x坐标不变，提取y坐标
            prevY = scaleY(str_to_float(vert[0]))
            currPolygon.addPoint(prevX, prevY)
        # H = 绘制水平线 - 参数 - 直线x坐标 (x)+
        elif code == 'H':
            #由于是水平线，y坐标不变，提取x坐标
            prevX = scaleX(str_to_float(vert[0]))
            currPolygon.addPoint(prevX, prevY)
        # Z = 路径结束，无参数
        elif code == 'Z':
            polygons.append(currPolygon)
            currPolygon = Polygon()
        #有一些语句指令为空，为绘制直线
        else:
            prevX = scaleX(str_to_float(vert[0]))
            prevY = scaleY(str_to_float(vert[1]))
            currPolygon.addPoint(prevX, prevY)

    #分析里面的多边形，看是否有相互包含关系，如果有相互包含关系，则将相互包含的多边形合并
    extensionPolygons(polygons)

    scripts = [] #保存所有生成的sprint-layout绘图指令行
    currScript = []
    currPtIndex = 0

    for polygon in polygons:
        currScript = None
        if not polygon.isValid():
            continue

        for (x, y) in polygon.points:
            if not currScript:
                currScript = ['ZONE,LAYER={},WIDTH=0,P0={:0.0f}/{:0.0f}'.format(layerIdx, x, y)]
                currPtIndex = 1
            else:
                currScript.append('P{}={:0.0f}/{:0.0f}'.format(currPtIndex, x, y))
                currPtIndex += 1
        currScript[-1] += ';'  #sprint-layout每行以分号结尾
        scripts.append(','.join(currScript))
    
    return {'width':fontWidth, 'height':fontHeight, 'polygon':'\n'.join(scripts)}

#分析里面的多边形，看是否有相互包含关系，如果有相互包含关系，则将相互包含的多边形合并
def extensionPolygons(polygons):
    copied = polygons[::]
    for poly in copied:
        if not poly.isValid():
            continue

        for poly2 in copied:
            if (poly2 is poly):
                continue
            
            #逐个点判断，只要有点在里面，就认为在里面
            for (x, y) in poly2.points:
                if not poly.insideMe(x, y):
                    continue
                
                #poly2在poly里面，所以可以将poly2合并到poly里面
                poly.mergePolygon(poly2)
                poly2.reset()
                break
    


                



