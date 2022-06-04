#!/usr/bin/env python
#-*- coding:utf-8 -*-
"""
Track定义
Author: cdhigh <https://github.com/cdhigh>
"""

from .sprint_element import *

#里面的长度单位都是mm
class SprintTrack(SprintElement):
    def __init__(self, layerIdx: int=1, width: float=0):
        super().__init__(layerIdx)
        self.width = width
        self.points = [] #元素为(x,y)元祖
        self.clearance = None
        self.cutout = None
        self.soldermask = None
        self.flatstart = None
        self.flatend = None
    
    def isValid(self):
        return (len(self.points) >= 2)

    def updateSelfBbox(self):
        self.xMin = self.yMin = 100000.0
        self.xMax = self.yMax = -100000.0
        for (x, y) in self.points:
            self.updateBbox(x, y)

    #增加一个点
    def addPoint(self, x: float, y: float):
        self.points.append((x, y))

    def __str__(self):
        if (not self.isValid()):
            return ''

        outStr = ['TRACK,LAYER={},WIDTH={:0.0f}'.format(self.layerIdx, self.width * 10000)]
        if self.clearance:
            outStr.append('CLEAR={:0.0f}'.format(self.clearance * 10000))
        if self.cutout is not None:
            outStr.append('CUTOUT={}'.format(self.booleanStr(self.cutout)))
        if self.soldermask is not None:
            outStr.append('SOLDERMASK={}'.format(self.booleanStr(self.soldermask)))
        if self.flatstart is not None:
            outStr.append('FLATSTART={}'.format(self.booleanStr(self.flatstart)))
        if self.flatend is not None:
            outStr.append('FLATEND={}'.format(self.booleanStr(self.flatend)))
        
        #点列表
        for idx, (x, y) in enumerate(self.points):
            outStr.append('P{}={:0.0f}/{:0.0f}'.format(idx, x * 10000, y * 10000))

        return ','.join(outStr) + ';'

    #重载等号运算符，判断两个Track是否相等
    def __eq__(self, other):
        if not isinstance(other, SprintTrack):
            return False

        if ((self.layerIdx != other.layerIdx) or (self.width != other.width) or (self.points != other.points)):
            return False
            
        return True

    #复制一个自身，并且将坐标相对某个新原点进行移动，
    #ox/oy: 新的原点坐标
    def cloneToNewOrigin(self, ox: float, oy: float):
        ins = SprintTrack(self.layerIdx, self.width)
        ins.points = [(round(pt[0] - ox, 2), round(pt[1] - oy, 2)) for pt in self.points]
        ins.clearance = self.clearance
        ins.cutout = self.cutout
        ins.soldermask = self.soldermask
        ins.flatstart = self.flatstart
        ins.flatend = self.flatend
        ins.updateSelfBbox()
        return ins
    
    #移动自身的位置
    def moveByOffset(self, offsetX: float, offsetY: float):
        for idx in range(len(self.points)):
            self.points[idx] = (round(self.points[idx][0] - offsetX, 2), round(self.points[idx][1] - offsetY, 2))
        self.updateSelfBbox()
