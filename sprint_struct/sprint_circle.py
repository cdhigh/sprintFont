#!/usr/bin/env python
#-*- coding:utf-8 -*-
"""
圆形定义
Author: cdhigh <https://github.com/cdhigh>
"""
import math
from .sprint_element import *
from utils.comm_utils import svgArcToCenterParam, pointAfterRotated

#里面的长度单位都是mm
class SprintCircle(SprintElement):
    def __init__(self, layerIdx: int=1):
        super().__init__(layerIdx)
        self.center = (0, 0)
        self.width = 0
        self.radius = 0
        self.clearance = 0
        self.cutout = None  #是否为开孔区域
        self.soldermask = None
        self.start = 0  #起始角度，0为3点钟方向，逆时针计算，单位为角度
        self.stop = 0   #结束角度，0为3点钟方向，逆时针计算，单位为角度
        self.fill = None
    
    def isValid(self):
        return (self.radius > 0)

    def updateSelfBbox(self):
        self.xMin = self.yMin = float('inf')
        self.xMax = self.yMax = float('-inf')
        self.updateBbox(self.center[0], self.center[1], self.radius + self.width)
        
    #Kicad没有直接指定半径，而是指定处于圆弧上的一个点来定义半径
    #注意调用此函数前请先保证设置了圆心坐标
    def setRadiusByArcPoint(self, x: float, y: float):
        self.radius = math.dist(self.center, (x, y))
        
    #通过圆心，起点，和角度来设定一段圆弧
    #这个是Kicad的规则，圆弧角度为从起点开始顺时针旋转为正，而Sprint-Layout逆时针旋转为正
    #如果是绝对角度，都是3点钟方向为0度
    def setArcByCenterStartAngle(self, cX: float, cY: float, sX: float, sY: float, angle: float):
        self.center = (cX, cY)
        self.radius = math.dist((cX, cY), (sX, sY))
        start = round(math.degrees(math.atan2(cY - sY, sX - cX))) #弧度转角度
        stop = start - angle #逆时针计数
        self.start = min(start, stop)
        self.stop = max(start, stop)
        
    #通过起点/终点/半径设置圆心坐标，参数顺序和SVG的圆弧绘图参数一致
    #x1/y1: 起点
    #x2/y2: 终点
    #rx: x半径
    #ry: y半径
    #xAxisRotate: X轴旋转角度
    #bigArc: 是否为大圆弧还是小圆弧
    #clockwise: 方向，1-顺时针，0-逆时针
    def setByStartEndRadius(self, x1, y1, rx, ry, xAxisRotate, bigArc, clockwise, x2, y2):
        try:
            ret = svgArcToCenterParam(x1, y1, rx, ry, xAxisRotate, bigArc, clockwise, x2, y2)
        except Exception as e:
            print(str(e))
            return

        self.radius = rx
        self.center = (ret['cx'], ret['cy'])
        self.start = ret['startAngle']
        self.stop = ret['endAngle']
        if self.start == 360:
            self.start = 0
        if self.stop == 360:
            self.stop = 0
        
    def __str__(self):
        if self.radius <= 0:
            return ''

        outStr = ['CIRCLE,LAYER={},CENTER={}/{},WIDTH={},RADIUS={}'.format(self.layerIdx, 
            self.mm2um01(self.center[0]), self.mm2um01(self.center[1]), self.mm2um01(self.width), self.mm2um01(self.radius))]
        if self.clearance:
            outStr.append('CLEAR={}'.format(self.mm2um01(self.clearance)))
        if self.cutout is not None:
            outStr.append('CUTOUT={}'.format(self.booleanStr(self.cutout)))
        if self.soldermask is not None:
            outStr.append('SOLDERMASK={}'.format(self.booleanStr(self.soldermask)))
        if self.start is not None:
            outStr.append('START={:0.0f}'.format(self.start * 1000))
        if self.stop is not None:
            outStr.append('STOP={:0.0f}'.format(self.stop * 1000))
        if self.fill is not None:
            outStr.append('FILL={}'.format(self.booleanStr(self.fill)))
        if self.name:
            outStr.append('NAME=|{}|'.format(self.sanitizeText(self.name)))
        
        return ','.join(outStr) + ';'

    #重载等号运算符，判断两个是否相等
    def __eq__(self, other):
        if not isinstance(other, SprintCircle):
            return False

        if ((self.layerIdx != other.layerIdx) or (self.center != other.center) or (self.width != other.width)
            or (self.radius != other.radius) or (self.start != other.start) or (self.stop != other.stop)
            or (self.fill != other.fill)):
            return False
        else:
            return True
    
    #复制一个自身，并且将坐标相对某个新原点进行移动，
    #ox/oy: 新的原点坐标
    def cloneToNewOrigin(self, ox: float, oy: float):
        ins = SprintCircle(self.layerIdx)
        ins.center = (round(self.center[0] - ox, 4), round(self.center[1] - oy, 4))
        ins.width = self.width
        ins.radius = self.radius
        ins.clearance = self.clearance
        ins.cutout = self.cutout
        ins.soldermask = self.soldermask
        ins.start = self.start
        ins.stop = self.stop
        ins.fill = self.fill
        ins.name = self.name
        ins.updateSelfBbox()
        return ins

    #移动自身的位置
    def moveByOffset(self, offsetX: float, offsetY: float):
        self.center = (round(self.center[0] + offsetX, 4), round(self.center[1] + offsetY, 4))
        self.updateSelfBbox()

    #圆弧角度重映射：本类的start/stop是逆时针为正(0度在3点钟方向)，与焊盘/文本的顺时针为正相反，
    #所以整体旋转angle(顺时针为正)时弧角度要减去angle；水平镜像时角度关于180度翻转，垂直镜像时取反
    def remapArcAngles(self, startOffset: float, mirrorMode: int=0):
        #mirrorMode: 0=无镜像(仅旋转偏移)，1=水平镜像，2=垂直镜像
        if mirrorMode == 1:
            newStart, newStop = (180 - self.stop) % 360, (180 - self.start) % 360
        elif mirrorMode == 2:
            newStart, newStop = (-self.stop) % 360, (-self.start) % 360
        else:
            newStart, newStop = (self.start - startOffset) % 360, (self.stop - startOffset) % 360
        self.start, self.stop = newStart, newStop

    #绕指定中心旋转自身，angle为顺时针为正的度数
    #注意pointAfterRotated必须用默认的clockwise=0分支：内部坐标Y向下，该分支的旋转矩阵
    #才是屏幕视觉顺时针(与焊盘/文本ROTATION一致)，函数本身的注释按Y向上坐标书写
    def rotateBy(self, angle: float, cx: float, cy: float):
        self.center = pointAfterRotated(self.center[0], self.center[1], cx, cy, angle)
        self.remapArcAngles(angle)
        self.updateSelfBbox()

    #绕竖直线x=cx做水平镜像(左右翻转)
    def mirrorHorzBy(self, cx: float):
        self.center = (round(2 * cx - self.center[0], 4), self.center[1])
        self.remapArcAngles(0, mirrorMode=1)
        self.updateSelfBbox()

    #绕水平线y=cy做垂直镜像(上下翻转)
    def mirrorVertBy(self, cy: float):
        self.center = (self.center[0], round(2 * cy - self.center[1], 4))
        self.remapArcAngles(0, mirrorMode=2)
        self.updateSelfBbox()

    #返回一个三元组, 分别对应起点坐标,圆弧中心坐标,终点坐标
    #要求start!=stop
    def calcStartEndMidPoint(self):
        cx, cy = self.center
        sweepAngle = (self.stop - self.start) % 360
        if sweepAngle == 0 and self.start != self.stop:
            sweepAngle = 360
            
        midAngle = (self.start + (sweepAngle / 2.0)) % 360
        
        def getXy(angle):
            angleRad = math.radians(angle)
            x = cx + self.radius * math.cos(angleRad)
            y = cy - self.radius * math.sin(angleRad)
            return round(x, 2), round(y, 2)

        return  getXy(self.start), getXy(midAngle), getXy(self.stop)
