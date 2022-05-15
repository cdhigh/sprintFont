#!/usr/bin/env python
#-*- coding:utf-8 -*-
"""
表示Sprint-Layout的TextIO对象

Author: cdhigh <https://github.com/cdhigh>
"""

from .sprint_polygon import SprintPolygon
from .sprint_pad import *
from .sprint_text import SprintText
from .sprint_circle import SprintCircle

#Sprint-Layout的各板层索引定义
LAYER_C1 = 1
LAYER_S1 = 2
LAYER_C2 = 3
LAYER_S2 = 4
LAYER_I1 = 5
LAYER_I2 = 6
LAYER_U  = 7

class SprintTextIO:
    def __init__(self):
        self.component = {} #如果是一个元件，则此Map保存属性
        self.zones = [] #ZONE，为多边形列表
        self.tracks = []
        self.pads = []
        self.smdPads = []
        self.texts = []
        self.circles = []

    #转换为字符串TextIO
    def __str__(self):
        outStr = []

        #多边形
        currPtIndex = 0
        currScript = None
        for polygon in self.zones:
            currScript = None
            if not polygon.isValid():
                continue

            layerIdx = polygon.layerIdx
            lineWidth = polygon.lineWidth
            for (x, y) in polygon.points:
                if not currScript:
                    currScript = ['ZONE,LAYER={},WIDTH={:0.0f},P0={:0.0f}/{:0.0f}'.format(layerIdx, lineWidth, x, y)]
                    currPtIndex = 1
                else:
                    currScript.append('P{}={:0.0f}/{:0.0f}'.format(currPtIndex, x, y))
                    currPtIndex += 1
            currScript[-1] += ';'  #Sprint-Layout每行以分号结尾
            outStr.append(','.join(currScript))

        #焊盘
        for pad in self.pads:
            outStr.append(str(pad))

        #文本
        for text in self.texts:
            outStr.append(str(text))

        #圆形
        for cir in self.circles:
            outStr.append(str(cir))

        return '\n'.join(outStr)

    #添加一个多边形到zones
    def addPolygon(self, poly):
        if poly and poly.isValid():
            self.zones.append(poly)

    #添加一个多边形列表
    def addAllPolygon(self, polyList):
        for poly in polyList:
            self.addPolygon(poly)

    #添加一个焊盘 SprintPad
    def addPad(self, pad):
        self.pads.append(pad)

    #添加一个文本 SprintText
    def addText(self, text):
        self.texts.append(text)

    #添加一个圆形 SprintCircle
    def addCircle(self, cir):
        self.circles.append(cir)

