#!/usr/bin/env python
#-*- coding:utf-8 -*-
"""
表示Sprint-Layout的TextIO对象
保存到里面的参数使用mm为单位，角度单位为度，仅仅在输出文本时再转换为0.1微米和0.001度
Author: cdhigh <https://github.com/cdhigh>
"""

from .sprint_element import *
from .sprint_track import SprintTrack
from .sprint_polygon import SprintPolygon
from .sprint_pad import *
from .sprint_text import SprintText
from .sprint_circle import SprintCircle
from .sprint_group import SprintGroup
from .sprint_component import SprintComponent

class SprintTextIO:
    def __init__(self):
        self.elements = [] #各种绘图元素，都是SprintElement的子类
        
    def isValid(self):
        return (len(self.elements) > 0)

    #转换为字符串TextIO
    def __str__(self):
        return '\n'.join([str(obj) for obj in self.elements])
    
    #统一的添加绘图元素接口
    def add(self, elem: SprintComponent):
        if elem:
            elem.updateSelfBbox()
            self.elements.append(elem)
            #print('add ', elem)

    #添加列表中所有元素
    def addAll(self, elemList: list):
        for elem in elemList:
            self.add(elem)
    
    #更新元件所占的外框
    def updateSelfBbox(self):
        for elem in self.elements:
            elem.updateSelfBbox()

    #获取特定板层的所有元素，返回一个列表
    def getAllElementsInLayer(self, layerIdx: int):
        elems = []
        for elem in self.elements:
            if isinstance(elem, (SprintComponent, SprintGroup)):
                elems.extend(elem.getAllElementsInLayer(layerIdx))
            elif elem.layerIdx == layerIdx:
                elems.append(elem)

        return elems

    #获取所有的下层基本绘图元素，如果碰到元件/分组则先展开，返回一个列表
    def children(self):
        elems = []
        for elem in self.elements:
            if isinstance(elem, (SprintComponent, SprintGroup)):
                elems.extend(elem.children())
            else:
                elems.append(elem)
        return elems

    #将所有焊盘分类，同样形状的存入一个列表，字典的键为焊盘形状的名字
    def categorizePads(self):
        pads = [e for e in self.children() if isinstance(e, SprintPad)]
        padDict = {}
        for pad in pads:
            name = pad.generateDsnName()
            if name in padDict:
                padDict[name].append(pad)
            else:
                padDict[name] = [pad]

        return padDict

