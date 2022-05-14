#!/usr/bin/env python
#-*- coding:utf-8 -*-
"""
多边形数据结构和算法
Author: cdhigh
"""

#表示一个多边形
class Polygon:
    def __init__(self):
        self.reset()

    def reset(self):
        self._xMin = self._xMax = self._yMin = self._yMax = 0.0
        self.points = [] #元素为 (x,y)
        self._ptIdx = 0
        self._segIdx = 0

    #多边形是否合法，至少要求为三个点
    def isValid(self):
        return (len(self.points) >= 3)

    #增加一个点
    def addPoint(self, x: float, y: float):
        if x < self._xMin:
            self._xMin = x
        if x > self._xMax:
            self._xMax = x
        if y < self._yMin:
            self._yMin = y
        if y > self._yMax:
            self._yMax = y
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
    def insideMe(self, x: float, y: float):
        #先判断极限情况，如果在外包矩形外，就是在多边形外
        if ((x < self._xMin) or (x > self._xMax) or (y < self._yMin) or (y > self._yMax)):
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


    
    #将polygon合并进自己，前提是polygon在自己内部
    #算法：将polygon的第一个点反向做一个水平射线，直到和另一个多边形的某个边相交
    #然后将交点同时做为polygon的起点和终点，将polygon展开为一个“线段”
    #最好将此线段合并入另一个多边形（合并位置在交点位置）
    #因为用于字体，这里有一个假定，多边形都是凸多边形
    def mergePolygon(self, polygon):
        if (not polygon.isValid()):
            return

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

