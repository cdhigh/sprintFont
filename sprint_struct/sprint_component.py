#!/usr/bin/env python
#-*- coding:utf-8 -*-
"""
Track定义
Author: cdhigh <https://github.com/cdhigh>
"""

#Sprint-Layout的元件共同基类
class SprintComponent:
    def __init__(self, layerIdx: int=1):
        self.layerIdx = layerIdx
        self.xMin = self.yMin = 10000 * 10000
        self.xMax = self.yMax = -10000 * 10000
    
    #更新元件的外框
    def updateLimitX(self, x: float):
        if x < self.xMin:
            self.xMin = x
        if x > self.xMax:
            self.xMax = x
    
    def updateLimitY(self, y: float):
        if y < self.yMin:
            self.yMin = y
        if y > self.yMax:
            self.yMax = y
    
    def updateLimit(self, x: float, y: float):
        self.updateLimitX(x)
        self.updateLimitY(y)
    
    
    