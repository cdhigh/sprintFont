#!/usr/bin/env python
#-*- coding:utf-8 -*-
"""
表示一个锁定的组件，锁定组件内可以包含多种绘图元素
Author: cdhigh <https://github.com/cdhigh>
"""
from .sprint_element import *

class SprintGroup(SprintElement):
    def __init__(self):
        super().__init__(self)
        self.elements = [] #各种绘图元素，都是SprintElement的子类
    
    def isValid(self):
        return (len(self.elements) > 0)

    #转换为字符串TextIO
    def __str__(self):
        if not self.isValid():
            return ''

        outStr = ['GROUP;']
        #逐个添加里面的绘图元素
        outStr.extend([str(obj) for obj in self.elements])
        outStr.append('END_GROUP;')
        
        #合并绘图元素，并去掉可能的空字符串
        return '\n'.join([s for s in outStr if s])

    #统一的添加绘图元素接口
    def add(self, elem: SprintElement):
        if elem:
            elem.updateSelfBbox()
            self.elements.append(elem)

    #添加列表中所有元素
    def addAll(self, elemList: list):
        for elem in elemList:
            self.add(elem)

    #删除某一个对象，成功返回True
    def remove(self, obj):
        from .sprint_component import SprintComponent
        for elem in self.elements:
            if elem is obj:
                self.elements.remove(obj)
                self.updateSelfBbox()
                return True

        for elem in self.elements:
            if isinstance(elem, (SprintComponent, SprintGroup)):
                if elem.remove(obj):
                    self.updateSelfBbox()
                    return True
                    
        return False

    #更新组合所占的外框
    def updateSelfBbox(self):
        self.xMin = self.yMin = float('inf')
        self.xMax = self.yMax = float('-inf')
        for elem in self.elements:
            elem.updateSelfBbox()
            self.updateBbox(elem)
            
    #根据绘图元素，更新组合自己的外框
    def updateBbox(self, elem):
        self.xMin = min(elem.xMin, self.xMin)
        self.xMax = max(elem.xMax, self.xMax)
        self.yMin = min(elem.yMin, self.yMin)
        self.yMax = max(elem.yMax, self.yMax)
        
    #获取特定板层的所有元素，返回一个列表
    def getAllElementsInLayer(self, layerIdx: int):
        return [elem for elem in self.elements if elem.layerIdx == layerIdx]
    
    #获取所有的下层绘图元素(元件当作一个绘图元素)，返回一个列表
    def children(self):
        elems = []
        for elem in self.elements:
            if isinstance(elem, SprintGroup):
                elems.extend(elem.children())
            else:
                elems.append(elem)
        return elems

    #获取所有的下层基本绘图元素(元件要展开，显示里面的基本绘图元素)，返回一个列表
    def baseDrawElements(self):
        from .sprint_component import SprintComponent
        elems = []
        for elem in self.elements:
            if isinstance(elem, (SprintComponent, SprintGroup)):
                elems.extend(elem.baseDrawElements())
            else:
                elems.append(elem)
        return elems
        
    #复制一个自身，并且将坐标相对某个新原点进行移动，
    #ox/oy: 新的原点坐标
    def cloneToNewOrigin(self, ox: float, oy: float):
        ins = SprintGroup()
        for elem in self.elements:
            if hasattr(elem, 'cloneToNewOrigin'):
                ins.elements.append(elem.cloneToNewOrigin(ox, oy))
        return ins

    #移动自身的位置
    def moveByOffset(self, offsetX: float, offsetY: float):
        for elem in self.elements:
            elem.moveByOffset(offsetX, offsetY)
        self.updateSelfBbox()

