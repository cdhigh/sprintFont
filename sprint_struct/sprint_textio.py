#!/usr/bin/env python
#-*- coding:utf-8 -*-
"""
表示Sprint-Layout的TextIO对象

Author: cdhigh <https://github.com/cdhigh>
"""

from .sprint_track import SprintTrack
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
    def __init__(self, isGroup: bool=False, isComponent: bool=False):
        self.component = {} #如果是一个元件，则此Map保存其他属性
        self.name = '' #用于元件的名字，比如R1
        self.value = '' #用于元件的值，比如10k
        self.zones = [] #ZONE，为多边形列表
        self.tracks = []
        self.pads = []
        self.smdPads = []
        self.texts = []
        self.circles = []
        self.isComponent = isComponent #是否是一个元件，如果是元件的话，还要输出 ID_TEXT/VALUE_TEXT
        self.isGroup = isGroup #是否输出为一个Group
        self.xMin = self.yMin = 10000 * 10000
        self.xMax = self.yMax = -10000 * 10000

    #转换为字符串TextIO
    def __str__(self):
        outStr = []

        if self.isGroup:
            outStr.append('GROUP;')
        
        if self.isComponent:
            outStr.append('BEGIN_COMPONENT;')
            #ID_TEXT,LAYER=2,POS=408300/370050,HEIGHT=13000,THICKNESS=2,TEXT=|R1|;
            x = self.xMin + (self.xMax - self.xMin) / 2
            y1 = self.yMin - 20000
            y2 = y1 - 20000
            outStr.append('ID_TEXT,VISIBLE=false,LAYER=2,POS={:0.0f}/{:0.0f},HEIGHT=13000,THICKNESS=2,TEXT=|{}|;'
                .format(x, y2, self.name))
            outStr.append('VALUE_TEXT,VISIBLE=false,LAYER=2,POS={:0.0f}/{:0.0f},HEIGHT=13000,THICKNESS=2,TEXT=|{}|;'
                .format(x, y1, self.value))

        #逐个添加
        for objList in (self.tracks, self.pads, self.zones, self.texts, self.circles):
            outStr.extend([str(obj) for obj in objList])
        
        if self.isComponent:
            outStr.append('END_COMPONENT;')
            
        if self.isGroup:
            outStr.append('END_GROUP;')
            
        #去掉可能的空字符串
        return '\n'.join([s for s in outStr if s])
    
    #更新所有元件的外框
    def updateLimit(self, component):
        if component.xMin < self.xMin:
            self.xMin = component.xMin
        if component.xMax > self.xMax:
            self.xMax = component.xMax
        if component.yMin < self.yMin:
            self.yMin = component.yMin
        if component.yMax > self.yMax:
            self.yMax = component.yMax
    
    #添加一个连线
    def addTrack(self, track):
        self.updateLimit(track)
        self.tracks.append(track)

    #添加一个多边形
    def addPolygon(self, poly):
        if poly and poly.isValid():
            self.updateLimit(poly)
            self.zones.append(poly)

    #添加一个多边形列表
    def addAllPolygon(self, polyList):
        for poly in polyList:
            self.addPolygon(poly)

    #添加一个焊盘 SprintPad
    def addPad(self, pad):
        pad.updatePadLimit()
        self.updateLimit(pad)
        self.pads.append(pad)

    #添加一个文本 SprintText
    def addText(self, text):
        self.updateLimit(text)
        self.texts.append(text)

    #添加一个圆形 SprintCircle
    def addCircle(self, cir):
        cir.updateCircleLimit()
        self.updateLimit(cir)
        self.circles.append(cir)

