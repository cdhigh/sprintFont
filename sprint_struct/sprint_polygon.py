#!/usr/bin/env python
#-*- coding:utf-8 -*-
"""
多边形数据结构和算法
Author: cdhigh <https://github.com/cdhigh>
"""
from .sprint_element import *

#里面的长度单位都是mm
class SprintPolygon(SprintElement):
    def __init__(self, layerIdx: int=2, width: float=0):
        super().__init__(layerIdx)
        self.reset(layerIdx, width)

    def reset(self, layerIdx: int=2, width: float=0):
        self.xMin = self.yMin = 100000.0
        self.xMax = self.yMax = -100000.0
        self.points = [] #元素为 (x,y)
        self._ptIdx = 0
        self._segIdx = 0
        self.layerIdx = layerIdx
        self.width = width if width else 0 #线宽
        self.clearance = None
        self.cutout = None  #是否为禁止布线区
        self.soldermask = None  #是否为阻焊区
        self.hatch = None  #是否为网格填充
        self.hatchAuto = None  #是否自动选择网格填充的线宽
        self.hatchWidth = None  #网格填充的自定义线宽

    #多边形是否合法，至少要求为两个点
    def isValid(self):
        return (len(self.points) >= 2)
    
    def updateSelfBbox(self):
        self.xMin = self.yMin = 100000.0
        self.xMax = self.yMax = -100000.0
        for (x, y) in self.points:
            self.updateBbox(x, y)
            
    def __str__(self):
        if (not self.isValid()):
            return ''

        outStr = ['ZONE,LAYER={},WIDTH={}'.format(self.layerIdx, self.mm2um01(self.width))]
        if self.clearance:
            outStr.append('CLEAR={}'.format(self.mm2um01(self.clearance)))
        if self.cutout is not None:
            outStr.append('CUTOUT={}'.format(self.booleanStr(self.cutout)))
        if self.soldermask is not None:
            outStr.append('SOLDERMASK={}'.format(self.booleanStr(self.soldermask)))
        if self.hatch is not None:
            outStr.append('HATCH={}'.format(self.booleanStr(self.hatch)))
        if self.hatchAuto is not None:
            outStr.append('HATCH_AUTO={}'.format(self.booleanStr(self.hatchAuto)))
        if self.hatchWidth:
            outStr.append('HATCH_WIDTH={}'.format(self.mm2um01(self.hatchWidth)))

        #点列表
        for idx, (x, y) in enumerate(self.points):
            outStr.append('P{}={}/{}'.format(idx, self.mm2um01(x), self.mm2um01(y)))

        return ','.join(outStr) + ';'

    #重载等号运算符，判断两个是否相等
    def __eq__(self, other):
        if not isinstance(other, SprintPolygon):
            return False

        if ((self.layerIdx != other.layerIdx) or (self.width != other.width) or (self.points != other.points)):
            return False
        else:
            return True

    #增加一个点
    def addPoint(self, x: float, y: float):
        self.updateBbox(x, y) #这里要先调用，因为在添加到textIo前encircle()等函数就要使用外框
        self.points.append((x, y))

    #生成器，用于迭代里面所有的线段
    def iterLineSeg(self):
        self._segIdx = 0
        while 1:
            #封闭多边形线段个数等于点数
            if ((len(self.points) <= 1) or (self._segIdx >= len(self.points))):
                return

            #最后一个线段
            if self._segIdx == len(self.points) - 1:
                ret = (self.points[-1], self.points[0])
            else:
                ret = (self.points[self._segIdx], self.points[self._segIdx + 1])
            self._segIdx += 1
            yield ret

    #判断一个点是否在此多边形内，此算法专门为字体优化，不判断很多特殊情况
    def encircle(self, x: float, y: float):
        #先判断极限情况，如果在外包矩形外，就是在多边形外
        if ((x <= self.xMin) or (x >= self.xMax) or (y <= self.yMin) or (y >= self.yMax)):
            return False

        #W. Randolph Franklin 的PNPoly算法
        inMe = 0
        for ((x1, y1), (x2, y2)) in self.iterLineSeg():
            #判断点是否在线上
            if pointInLineSeg(x, y, x1, y1, x2, y2):
                continue

            #判断水平向右的射线是否和线段相交
            if (((y1 > y) != (y2 > y)) and 
                (x < ((x2 - x1) * (y - y1) / (y2 - y1) + x1))):
                inMe ^= 0x01

        return inMe

    #移动各顶点，保证第一个点为最左边
    def ensureFirstPointLeftest(self):
        if ((not self.isValid()) or (self.points[0][0] <= self.xMin)):
            return

        idx = 0
        for idx, (x, y) in enumerate(self.points):
            if (x <= self.xMin):
                break

        #从idx开始取到末尾，然后从开始到idx
        self.points = self.points[idx:] + self.points[0:idx]
        
    #将polygon合并进自己，前提是polygon在自己内部
    #算法：将polygon的第一个点反向做一个水平射线，直到和另一个多边形的某个边相交
    #然后将交点同时做为polygon的起点和终点，将polygon展开为一个“线段”
    #最好将此线段合并入另一个多边形（合并位置在交点位置）
    #因为用于字体，这里有一个假定，多边形都是凸多边形
    def devour(self, polygon):
        if (not polygon.isValid()):
            return

        #因为要从一个点向做做水平射线，所以需要将最左边的点移到第一个点位置
        polygon.ensureFirstPointLeftest()

        x, y = polygon.points[0]
        segIdx = 0
        for ((x1, y1), (x2, y2)) in self.iterLineSeg():
            if (isRayLeftIntersect(x, y, x1, y1, x2, y2)): #有相交
                #求出交点
                xi, yi = rayIntersectPoint(x, y, x1, y1, x2, y2)
                self.points.insert(segIdx + 1, (xi, yi))
                self.points.insert(segIdx + 1, (x, y))
                self.points.insert(segIdx + 1, (xi, yi))
                self.points[segIdx + 2:segIdx + 2] = polygon.points
                break

            segIdx += 1

    #复制一个自身，并且将坐标相对某个新原点进行移动，
    #ox/oy: 新的原点坐标
    def cloneToNewOrigin(self, ox: float, oy: float):
        ins = SprintPolygon(self.layerIdx, self.width)
        ins.points = [(round(pt[0] - ox, 4), round(pt[1] - oy, 4)) for pt in self.points]
        ins._ptIdx = self._ptIdx
        ins._segIdx = self._segIdx
        ins.clearance = self.clearance
        ins.cutout = self.cutout
        ins.soldermask = self.soldermask
        ins.hatch = self.hatch
        ins.hatchAuto = self.hatchAuto
        ins.hatchWidth = self.hatchWidth
        ins.updateSelfBbox()
        return ins

    #移动自身的位置
    def moveByOffset(self, offsetX: float, offsetY: float):
        for idx in range(len(self.points)):
            self.points[idx] = (round(self.points[idx][0] - offsetX, 4), round(self.points[idx][1] - offsetY, 4))
        self.updateSelfBbox()
        

#判断一个点是否在线段上，使用向量法
def pointInLineSeg(x: float, y: float, x1: float, y1: float, x2: float, y2: float):
    s1 = x - x1
    t1 = y - y1
    s2 = x1 - x2
    t2 = y1 - y2
    return True if ((s2 != 0) and (t2 != 0) and ((s1 / s2) == (t1 / t2))) else False

#一个点向右的射线是否和线段相交
def isRayRightIntersect(x: float, y: float, x1: float, y1: float, x2: float, y2: float):
    return (((y1 > y) != (y2 > y)) and (x < ((x2 - x1) * (y - y1) / (y2 - y1) + x1)))

#一个点向左的射线是否和线段相交
def isRayLeftIntersect(x: float, y: float, x1: float, y1: float, x2: float, y2: float):
    return (((y1 > y) != (y2 > y)) and (x > ((x2 - x1) * (y - y1) / (y2 - y1) + x1)))

#一个点的射线和线段相交的交点
def rayIntersectPoint(x: float, y: float, x1: float, y1: float, x2: float, y2: float):
    return (((x2 - x1) * (y - y1) / (y2 - y1) + x1), y)

