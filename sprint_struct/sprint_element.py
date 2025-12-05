#!/usr/bin/env python
#-*- coding:utf-8 -*-
"""
Sprint-Layout的绘图元素共同基类
Author: cdhigh <https://github.com/cdhigh>
"""

#Sprint-Layout的各板层索引定义
LAYER_C1 = 1
LAYER_S1 = 2
LAYER_C2 = 3
LAYER_S2 = 4
LAYER_I1 = 5
LAYER_I2 = 6
LAYER_U  = 7

#对应索引的板层名字，主要用于Kicad/DSN导出
sprintLayerMap = {
    LAYER_C1: 'F.Cu',
    LAYER_S1: 'F.SilkS',
    LAYER_C2: 'B.Cu',
    LAYER_S2: 'B.SilkS',
    LAYER_I1: 'In1.Cu',
    LAYER_I2: 'In2.Cu',
    LAYER_U: 'Edge.Cuts',
}

#DSN/SES里面的板层对应到Sprint-Layout的板层索引
sprintLayerMapSes = {
    'F.Cu': LAYER_C1,
    'F.SilkS': LAYER_S1,
    'B.Cu': LAYER_C2,
    'B.SilkS': LAYER_S2,
    'In1.Cu': LAYER_I1,
    'In2.Cu': LAYER_I2,
    'Edge.Cuts': LAYER_U,
}

class SprintElement:
    def __init__(self, layerIdx: int=1):
        self.layerIdx = layerIdx
        self.xMin = self.yMin = 100000.0
        self.xMax = self.yMax = -100000.0
        self.name = ''
    
    #子类实现是否有效的函数
    def isValid(self):
        return False

    #适用于一些外部直接设置内部变量的绘图元素比如PAD等
    #在添加进绘图元素列表前被调用，更新自己内部的外框
    def updateSelfBbox(self):
        return

    #更新元件的外框 boundingbox
    def updateBboxX(self, x: float):
        if x < self.xMin:
            self.xMin = x
        if x > self.xMax:
            self.xMax = x
    
    def updateBboxY(self, y: float):
        if y < self.yMin:
            self.yMin = y
        if y > self.yMax:
            self.yMax = y
    
    def updateBbox(self, x: float, y: float):
        self.updateBboxX(x)
        self.updateBboxY(y)
    
    #返回true/false字符串
    @classmethod
    def booleanStr(cls, value):
        return 'true' if value else 'false'

    #去除名字中的非法字符
    @classmethod
    def justifiedText(cls, txt):
        return str(txt).replace(';', '_').replace(',', '_').replace('|', '_') if txt else ''

    #毫米浮点数转换为0.1微米整数
    @classmethod
    def mm2um01(cls, value):
        return int(value * 10000)

    #重载等号运算符，判断两个是否相等，子类需要重新实现
    def __eq__(self, other):
        return False
        
            