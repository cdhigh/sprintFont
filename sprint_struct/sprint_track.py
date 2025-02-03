#!/usr/bin/env python
#-*- coding:utf-8 -*-
"""
Track定义
Author: cdhigh <https://github.com/cdhigh>
"""
import math
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
    #如果y=None，则x为一个点定义(x,y)
    def addPoint(self, x: float, y: float=None):
        if (y is None):
            x, y = x
        self.points.append((x, y))

    #添加列表中所有点
    def addAllPoints(self, ptList: list):
        for pt in ptList:
            self.addPoint(pt)

    def __str__(self):
        if (not self.isValid()):
            return ''

        outStr = ['TRACK,LAYER={},WIDTH={}'.format(self.layerIdx, self.mm2um01(self.width))]
        if self.clearance:
            outStr.append('CLEAR={}'.format(self.mm2um01(self.clearance)))
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
            outStr.append('P{}={}/{}'.format(idx, self.mm2um01(x), self.mm2um01(y )))

        if self.name:
            outStr.append('NAME=|{}|'.format(self.justifiedText(self.name)))

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
        ins.points = [(round(pt[0] - ox, 4), round(pt[1] - oy, 4)) for pt in self.points]
        ins.clearance = self.clearance
        ins.cutout = self.cutout
        ins.soldermask = self.soldermask
        ins.flatstart = self.flatstart
        ins.flatend = self.flatend
        ins.name = self.name
        ins.updateSelfBbox()
        return ins
    
    #移动自身的位置
    def moveByOffset(self, offsetX: float, offsetY: float):
        for idx in range(len(self.points)):
            self.points[idx] = (round(self.points[idx][0] - offsetX, 4), round(self.points[idx][1] - offsetY, 4))
        self.updateSelfBbox()

    #计算导线的总长度
    @property
    def length(self):
        points = self.points
        return round(sum(math.dist(points[i], points[i + 1]) for i in range(len(points) - 1)), 3)

    #删除相邻的相同坐标点
    def removeDuplicatePoints(self):
        points = self.points
        if len(points) < 2:
            return
        
        ret = [points[0]]  # 先保留第一个元素
        for item in points[1:]:
            if item != ret[-1]:
                ret.append(item)
        self.points = ret
        