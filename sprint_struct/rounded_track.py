#!/usr/bin/env python
#-*- coding:utf-8 -*-
"""
圆弧走线算法相关
外部调用 createArcTracksInTextIo() 即可
Author: cdhigh <https://github.com/cdhigh>
"""
import math, os, sys
from utils.comm_utils import (pointInLineWithDistance, getCrossPoint, 
    isPointListClockwise, pointAtCircle, calCenterByThreePoints)
from fontTools.misc import bezierTools
from sprint_struct.sprint_textio import *

#import pysnooper

#在两个线段的交点位置创建圆弧
#textIo: SprintTextIo对象
#method: 创建圆弧方法：
#        'tangent': 离交点一段距离创建和线段相切的圆弧
#        'bizier': 贝塞尔曲线绘制
#        '3Points': 通过三点构造圆弧
#bigDistance: 离交点位置的最大距离
#smallDistance: 离交点位置的最小距离
#segNum: 平滑圆弧的线段数
#如果有走线被转换为弧形走线，则返回True
def createArcTracksInTextIo(textIo, method: str, bigDistance: float, smallDistance: float, segNum: int=10):
    hasTracksReplaced = False
    tracks = textIo.getTracks()
    pads = textIo.getPads()
    polys = textIo.getPolygons() #仅返回导电多边形

    #内嵌函数，判断一个点是否在导电区域（焊盘或多边形）内
    def isPointInsideConductiveArea(pt, layerIdx):
        for pad in pads:
            if ((pad.layerIdx == layerIdx) and pad.enclose(pt)):
                return True
        for poly in polys:
            if ((poly.layerIdx == layerIdx) and poly.encircle(pt)):
                return True
        return False

    #默认情况下线段长度小于2mm的不转换为弧形走线
    if method != 'tangent':
        bigDistance = smallDistance = 1.0

    if bigDistance < 0.1:
        bigDistance = 0.1
    if smallDistance < 0.1:
        smallDistance = 0.1
    if smallDistance > bigDistance:
        smallDistance, bigDistance = bigDistance, smallDistance

    if segNum < 2:
        segNum = 2

    for trackIdx, track in enumerate(tracks):
        oldPoints = track.points[:]
        ptNum = len(oldPoints)
        if (ptNum < 3): #必须要有至少3个点
            continue

        idx = 0

        newPoints = []
        while ((idx + 2) < ptNum):
            pt1 = oldPoints[idx]
            pt2 = oldPoints[idx + 1]
            pt3 = oldPoints[idx + 2]
            newPoints.append(pt1)

            #如果第二个线段太短，则忽略前面两个线段，并且往后取两个点
            distance23 = math.dist(pt2, pt3)
            distance12 = math.dist(pt1, pt2)
            if (distance23 <= smallDistance):
                newPoints.append(pt2)
                idx += 2
                continue
            #如果第一个线段太短，则忽略之，并且往后再取一个点
            #中间点在导电区域内也跳过一个点
            elif ((distance12 <= smallDistance) or isPointInsideConductiveArea(pt2, track.layerIdx)):
                idx += 1
                continue
            
            if (method == 'tangent'):
                distance = min(distance23, distance12)
                if (distance > bigDistance):
                    distance = bigDistance
                else:
                    distance = smallDistance
                ptList = arcByTangentLine(pt1, pt2, pt3, distance, segNum)
                #textIo.add(ptList)
                #return
            elif (method == 'bezier'):
                ptList = arcByBezier(pt1, pt2, pt3, segNum)
            else:
                ptList = arcBy3Points(pt1, pt2, pt3, segNum)

            if ptList:
                if (newPoints[-1] == ptList[0]): #去掉一个重复的点
                    newPoints.extend(ptList[1:])
                else:
                    newPoints.extend(ptList)
                oldPoints[idx + 1] = ptList[-1] #原先的中间点位置被圆弧的终点替代，将原先的点串起来

            idx += 1

        newPoints.extend(oldPoints[idx:])
        if (newPoints != oldPoints): #替换对应的Track点列表
            track.points.clear()
            track.addAllPoints(newPoints)
            track.updateSelfBbox()
            hasTracksReplaced = True

    return hasTracksReplaced

#通过两条相交线的切线构造圆弧
#pt1, pt2, pt3: pt1-pt2线段和pt2-pt3线段相交于pt2点
#distance: 需要的内切圆弧和线段交点到pt2的距离
#segNum: 圆弧分成多少段
#如果成功，返回圆弧上的点列表
def arcByTangentLine(pt1: tuple, pt2: tuple, pt3: tuple, distance: float, segNum: int):
    x1, y1 = pt1
    x2, y2 = pt2
    x3, y3 = pt3

    #求出圆弧和两个线段的交点
    intersectPt1 = pointInLineWithDistance(pt2, pt1, distance)
    intersectPt2 = pointInLineWithDistance(pt2, pt3, distance)

    #https://www.geek-share.com/detail/2645683357.html
    k1 = ((y2 - y1) / (x2 - x1)) if (x2 != x1) else None #线段1的斜率
    k2 = ((y3 - y2) / (x3 - x2)) if (x3 != x2) else None #线段2的斜率
    if k1 == k2: #两个线段的斜率相等则没有相切圆弧
        return None

    if k1 is None:
        vK1 = 0.0
    elif k1 == 0.0:
        vK1 = None
    else:
        vK1 = (-1 / k1) #垂线的斜率为 负倒数

    if k2 is None:
        vK2 = 0.0
    elif k2 == 0.0:
        vK2 = None
    else:
        vK2 = (-1 / k2) #垂线的斜率为 负倒数

    #线段1经过intersectPt1的垂线方程为: y - intersectPt1[1] = vK1 * (x - intersectPt1[0])
    #随便取一个x就能得到y
    if vK1 is None: #一根垂直线
        line1VertPt2 = (intersectPt1[0], round(intersectPt1[1] + 10.0, 4))
    elif vK1 == 0.0: #一根水平线
        line1VertPt2 = (round(intersectPt1[0] + 10.0, 4), intersectPt1[1])
    else:
        line1VertPt2 = (round(intersectPt1[0] + 10.0, 4), round(vK1 * 10.0 + intersectPt1[1], 4))
        
    if vK2 is None: #一根垂直线
        line2VertPt2 = (intersectPt2[0], round(intersectPt2[1] + 10.0, 4))
    elif vK2 == 0.0: #一根水平线
        line2VertPt2 = (round(intersectPt2[0] + 10.0, 4), intersectPt2[1])
    else:
        line2VertPt2 = (round(intersectPt2[0] + 10.0, 4), round(vK2 * 10.0 + intersectPt2[1], 4))

    #求两个垂线的交点，就是圆心位置
    center = getCrossPoint(intersectPt1, line1VertPt2, intersectPt2, line2VertPt2)
    if center is not None:
        radius = math.dist(center, intersectPt1)
        if (radius < 0.1) or (radius > 100.0):
            return None

        clockwise = isPointListClockwise(intersectPt1, pt2, intersectPt2)
        return pointListByStartEndRadius(intersectPt1, intersectPt2, center, radius, clockwise, segNum)
    else:
        return None

#通过起点终点和半径返回圆弧列表
def pointListByStartEndRadius(pt1, pt2, center, radius, clockwise, segNum):
    cir = SprintCircle(LAYER_C1)
    cir.setByStartEndRadius(pt1[0], pt1[1], radius, radius, 0, 0, clockwise, pt2[0], pt2[1])

    #我们输出的肯定是劣弧，不可能是优弧
    #print(cir.start, cir.stop)
    if (cir.start > cir.stop): #Sprint-Layout按逆时针旋转绘制圆弧
        angle1 = int(cir.start * 100)
        angle2 = int((cir.stop + 360) * 100)
    else:
        angle1 = int(cir.start * 100)
        angle2 = int(cir.stop * 100)

    #print(angle1, angle2)
    gap = int((angle2 - angle1) / segNum)
    ptList = [pointAtCircle(center[0], center[1], radius, angle / 100) for angle in range(angle1, angle2, gap)]

    #计算完成后看是不是需要倒序
    if (math.dist(pt1, ptList[0]) > math.dist(pt1, ptList[-1])):
        ptList = ptList[::-1]

    if (pt1 != ptList[0]):
        ptList.insert(0, pt1)
    ptList.append(pt2)
    return ptList

#通过二次贝塞尔曲线将走线转换为圆弧
#pt1, pt2, pt3: pt1-pt2线段和pt2-pt3线段相交于pt2点，pt2将做为控制点
#segNum: 圆弧分成多少段
#如果成功，返回圆弧上的点列表
def arcByBezier(pt1: tuple, pt2: tuple, pt3: tuple, segNum: int):
    x1, y1 = pt1
    x2, y2 = pt2
    x3, y3 = pt3

    ptList = []
    for i in range(0, int(100 * segNum), 100):
        ptList.append(bezierTools.quadraticPointAtT(pt1, pt2, pt3, i / (100 * segNum)))
    ptList.append(pt3) #添加最后一个点
    return ptList

#通过三点构造一个圆弧将走线转换为圆弧
#pt1, pt2, pt3: pt1-pt2线段和pt2-pt3线段相交于pt2点
#segNum: 圆弧分成多少段
#如果成功，返回圆弧上的点列表
def arcBy3Points(pt1: tuple, pt2: tuple, pt3: tuple, segNum: int):
    x1, y1 = pt1
    x2, y2 = pt2
    x3, y3 = pt3

    center = calCenterByThreePoints(pt1, pt2, pt3)
    radius = math.dist(pt1, center)
    if (radius < 0.1) or (radius > 100.0):
        return None

    clockwise = isPointListClockwise(pt1, pt2, pt3)
    return pointListByStartEndRadius(pt1, pt3, center, radius, clockwise, segNum)

if __name__ == '__main__':
    #635000/203200,P1=711200/279400,P2=593725/279400
    pt1 = (635000, 203200)
    pt2 = (711200, 279400)
    pt3 = (593725, 279400)
    print(arcByTangentLine(pt1, pt2, pt3, 5, 3))


