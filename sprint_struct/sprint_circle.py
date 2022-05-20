#!/usr/bin/env python
#-*- coding:utf-8 -*-
"""
圆形定义
Author: cdhigh <https://github.com/cdhigh>
"""
import math
from .sprint_component import SprintComponent
from comm_utils import euclideanDistance, calCenterByPointsAndRadius, radiansToDegrees

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
        start = round(math.degrees(math.atan2(cY - sY, sX - cX))) * 1000 #弧度转角度，角度单位为0.001度
        stop = start - angle #逆时针计数
        self.start = min(start, stop)
        self.stop = max(start, stop)
        self.updateCircleLimit()

    #通过起点/终点/半径设置圆心坐标
    #x1/y1: 起点
    #x2/y2: 终点
    #radius: 半径
    #bigArc: 是否为大圆弧还是小圆弧
    #dirCC: 方向，1-顺时针，0-逆时针
    def setByStartEndRadius(self, x1: float, y1: float, x2: float, y2: float, radius: float, bigArc: bool, dirCC: bool):
        #先判断弦长度是否小于直径
        arcLineLen = euclideanDistance(x1, y1, x2, y2)
        if ((arcLineLen == 0) or (arcLineLen > (radius * 2))):
            return

        self.radius = radius

        #计算圆心
        cx, cy = calCenterByPointsAndRadius(x1, y1, x2, y2, radius, bigArc, dirCC)
        self.center = (cx, cy)
        #print(round(x1), round(y1), round(cx), round(cy), round(x2), round(y2))
        #print(x1 - cx, y1 - cy)

        #计算角度，力创顺时针为正，Sprint-Layout逆时针为正
        angle = round(math.degrees(math.asin((arcLineLen / 2) / radius))) * 2 #起点终点对应圆心的夹角
        startAngle = round(math.degrees(math.atan2(y1 - cy, x1 - cx)))
        if startAngle <= 90:
            if angle < 180:
                endAngle = startAngle + angle
            else:
                endAngle = startAngle + (360 - angle)

        #if bigArc: #如果是大圆弧，则
        self.start = round(math.degrees(math.atan2(y1 - cy, x1 - cx)))
        if dirCC: #顺时针
            self.stop = self.start - angle
        else:
            self.stop = self.start + angle

        #if self.start < 0:
        #    self.start = 360 - self.start
        #if self.stop < 0:
        #    self.stop = 360 - self.stop

        #print(self.start, self.stop, angle)

        self.start *= 1000
        self.stop *= 1000
        self.updateCircleLimit()

    def __str__(self):
        if self.radius <= 0:
            return ''

        outStr = ['CIRCLE,LAYER={},CENTER={:0.0f}/{:0.0f},WIDTH={:0.0f},RADIUS={:0.0f}'.format(
            self.layerIdx, self.center[0], self.center[1], self.width, self.radius)]
        if self.clearance:
            outStr.append('CLEAR={:0.0f}'.format(self.clearance))
        if self.cutout is not None:
            outStr.append('CUTOUT={}'.format('true' if self.cutout else 'false'))
        if self.soldermask is not None:
            outStr.append('SOLDERMASK={}'.format('true' if self.soldermask else 'false'))
        if self.start is not None:
            outStr.append('START={:0.0f}'.format(self.start))
        if self.stop is not None:
            outStr.append('STOP={:0.0f}'.format(self.stop))
        if self.fill is not None:
            outStr.append('FILL={}'.format('true' if self.fill else 'false'))
        
        return ','.join(outStr) + ';'