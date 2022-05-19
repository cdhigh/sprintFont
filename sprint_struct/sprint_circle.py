#!/usr/bin/env python
#-*- coding:utf-8 -*-
"""
圆形定义
Author: cdhigh <https://github.com/cdhigh>
"""
import math
from .sprint_component import SprintComponent
from comm_utils import euclideanDistance

#里面的长度单位都是0.1微米
class SprintCircle(SprintComponent):
    def __init__(self, layerIdx: int=1):
        super().__init__(layerIdx)
        self.center = (0, 0)
        self.width = 0
        self.radius = 0
        self.clearance = None
        self.cutout = None
        self.soldermask = None
        self.start = None  #起始角度，0为3点钟方向，逆时针计算，角度*1000
        self.stop = None   #结束角度，0为3点钟方向，逆时针计算，角度*1000
        self.fill = None
    
    def updateCircleLimit(self):
        self.updateLimit(self.center[0] - self.radius, self.center[1] + self.radius)
        self.updateLimit(self.center[0] + self.radius, self.center[1] - self.radius)
        
    #Kicad没有直接指定半径，而是指定处于圆弧上的一个点来定义半径
    #注意调用此函数前请先保证设置了圆心坐标
    def setRadiusByArcPoint(self, x: float, y: float):
        self.radius = euclideanDistance(self.center[0], self.center[1], x, y)
        self.updateCircleLimit()

    #通过圆心，起点，和角度来设定一段圆弧
    #这个是Kicad的规则，圆弧角度为从起点开始顺时针旋转为正，而Sprint-Layout逆时针旋转为正
    #如果是绝对角度，都是3点钟方向为0度
    def setArcByCenterStartAngle(self, cX: float, cY: float, sX: float, sY: float, angle: float):
        self.center = (cX, cY)
        self.radius = euclideanDistance(cX, cY, sX, sY)
        start = math.degrees(math.atan2(cY - sY, sX - cX)) * 1000 #弧度转角度，角度单位为0.001度
        stop = start - angle #逆时针计数
        self.start = min(start, stop)
        self.stop = max(start, stop)
        self.updateCircleLimit()

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