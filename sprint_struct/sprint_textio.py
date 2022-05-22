#!/usr/bin/env python
#-*- coding:utf-8 -*-
"""
表示Sprint-Layout的TextIO对象
保存到里面的参数使用mm为单位，角度单位为度，仅仅在输出文本时再转换为0.1微米和0.001度
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
        self.name = '' #用于元件的名字，比如R1
        self.value = '' #用于元件的值，比如10k
        self.comment = '' #元件注释
        self.package = '' #封装名字
        self.elements = [] #各种绘图元素，都是SprintComponent的子类
        self.isComponent = isComponent #是否是一个元件，如果是元件的话，还要输出 ID_TEXT/VALUE_TEXT
        self.isGroup = isGroup #是否输出为一个Group
        self.xMin = self.yMin = 100000
        self.xMax = self.yMax = -100000

    def isValid(self):
        return (len(self.elements) > 0)

    #转换为字符串TextIO
    def __str__(self):
        outStr = []

        if self.isGroup:
            outStr.append('GROUP;')
        
        if self.isComponent:
            #先单独生成元件的文件头
            self.name = str(self.name).replace(';', '_').replace(',', '_').replace('|', '_')
            self.value = str(self.value).replace(';', '_').replace(',', '_').replace('|', '_')
            self.comment = str(self.comment).replace(';', '_').replace(',', '_').replace('|', '_')
            self.package = str(self.package).replace(';', '_').replace(',', '_').replace('|', '_')

            compHeadStrList = ['BEGIN_COMPONENT',]
            if self.comment:
                compHeadStrList.append('COMMENT=|{}|'.format(self.comment))
            if self.package:
                compHeadStrList.append('USE_PICKPLACE=true,PACKAGE=|{}|'.format(self.package))
            compHead = ','.join(compHeadStrList) + ';'

            outStr.append(compHead)
            #Example: ID_TEXT,LAYER=2,POS=408300/370050,HEIGHT=13000,THICKNESS=2,TEXT=|R1|;
            x = self.xMin + (self.xMax - self.xMin) / 2 - 1
            y1 = self.yMin - 1
            y2 = y1 - 1
            outStr.append('ID_TEXT,VISIBLE={},LAYER=2,POS={:0.0f}/{:0.0f},HEIGHT=13000,THICKNESS=1,TEXT=|{}|;'
                .format(('true' if self.name else 'false'), x * 10000, y2 * 10000, self.name))
            outStr.append('VALUE_TEXT,VISIBLE={},LAYER=2,POS={:0.0f}/{:0.0f},HEIGHT=13000,THICKNESS=1,TEXT=|{}|;'
                .format(('true' if self.value else 'false'), x * 10000, y1 * 10000, self.value))

        #逐个添加
        outStr.extend([str(obj) for obj in self.elements])
        
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

    #统一的添加绘图元素接口
    def add(self, elem: SprintComponent):
        if (elem and elem.isValid()):
            elem.updateSelfBbox()
            self.updateLimit(elem)
            self.elements.append(elem)

    #添加列表中所有元素
    def addAll(self, elemList: list):
        for elem in elemList:
            self.add(elem)
            