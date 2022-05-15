#!/usr/bin/env python
#-*- coding:utf-8 -*-
"""
圆形定义
Author: cdhigh <https://github.com/cdhigh>
"""
import math

#计算二维空间两点之间的距离
def euclideanDistance(x1: float, y1: float, x2: float, y2: float):
    return math.sqrt(((x1 - x2) ** 2) + ((y1 - y2) ** 2))

#sprint的圆形类
class SprintCircle:
    def __init__(self, layerIdx: int=1):
        self.layerIdx = layerIdx
        self.center = (0, 0)
        self.width = 0
        self.radius = 0
        self.clearance = None
        self.cutout = None
        self.soldermask = None
        self.start = None
        self.stop = None
        self.fill = None

    #Kicad没有直接指定半径，而是指定处于圆弧上的一个点来定义半径
    #注意调用此函数前请先保证设置了圆心坐标
    def setRadiusByArcPoint(self, x: float, y: float):
        self.radius = euclideanDistance(self.center[0], self.center[1], x, y)
        
    def __str__(self):
        outStr = ['CIRCLE,LAYER={},CENTER={:0.0f}/{:0.0f},WIDTH={:0.0f},RADIUS={:0.0f}'.format(
            self.layerIdx, self.center[0], self.center[1], self.width, self.radius)]
        if self.clearance:
            outStr.append('CLEAR={:0.0f}'.format(self.clearance))
        if self.cutout is not None:
            outStr.append('CUTOUT={}'.format('true' if self.cutout else 'false'))
        if self.soldermask is not None:
            outStr.append('SOLDERMASK={}'.format('true' if self.soldermask else 'false'))
        if self.start is not None:
            outStr.append('START={}'.format(self.start))
        if self.stop is not None:
            outStr.append('STOP={}'.format(self.stop))
        if self.fill is not None:
            outStr.append('FILL={}'.format('true' if self.fill else 'false'))
        
        return ','.join(outStr) + ';'