#!/usr/bin/env python
#-*- coding:utf-8 -*-
"""
泪滴焊盘算法相关，主要代码来自 <https://github.com/NilujePerchut/kicad_scripts>
外部接口：
createTeardrops() - 创建泪滴焊盘多边形列表
getTeardrops() - 获取可能的泪滴焊盘多边形列表
Author: cdhigh <https://github.com/cdhigh>
"""
import math
from .sprint_textio import *

#将向量变成标准单位
def tdNormalizeVector(pt):
    norm = math.sqrt(pt[0] * pt[0] + pt[1] * pt[1]) #点到原点的距离
    return [t / norm for t in pt]

#计算贝塞尔曲线上的若干点
def tdBezier(p1: tuple, p2: tuple, p3: tuple, p4: tuple, n: int=10):
    if (n == 0):
        return []

    pts = []
    for i in range(int(n) + 1):
        t = i / float(n)
        a = (1.0 - t) ** 3
        b = 3.0 * t * (1.0 - t) ** 2
        c = 3.0 * t ** 2 * (1.0 - t)
        d = t ** 3

        x = round(a * p1[0] + b * p2[0] + c * p3[0] + d * p4[0], 3)
        y = round(a * p1[1] + b * p2[1] + c * p3[1] + d * p4[1], 3)
        pts.append((x, y))
    return pts


#计算泪滴焊盘曲线上的点列表
#vPercent: 泪滴焊盘高度占焊盘直径的百分比，默认为70
#width: 走线宽度
#vecT: 走线的方向向量 (x, y)
#pad: 焊盘实例
def tdComputeCurved(vPercent: float, width: float, vecT: tuple, pad: SprintPad, pts: list, segs: int):
    """Compute the curves part points"""
    # A and B are points on the track
    # C and E are points on the via
    # D is midpoint behind the via centre
    ptA, ptB, ptC, ptD, ptE = pts
    padSize = pad.size if (pad.padType == 'PAD') else min(pad.sizeX, pad.sizeY)
    radius = padSize / 2
    if ((radius == 0.0) or (padSize == 0.0)):
        return pts

    minVpercent = width / padSize
    weaken = (vPercent / 100.0 - minVpercent) / (1 - minVpercent) / radius

    biasBC = 0.5 * math.dist(ptB, ptC)
    biasAE = 0.5 * math.dist(ptE, ptA)

    vecC = (ptC[0] - pad.pos[0], ptC[1] - pad.pos[1])
    tangentC = (ptC[0] - vecC[1] * biasBC * weaken, ptC[1] + vecC[0] * biasBC * weaken)
    vecE = (ptE[0] - pad.pos[0], ptE[1] - pad.pos[1])
    tangentE = (ptE[0] + vecE[1] * biasAE * weaken, ptE[1] - vecE[0] * biasAE * weaken)

    tangentB = (ptB[0] - vecT[0] * biasBC, ptB[1] - vecT[1] * biasBC)
    tangentA = (ptA[0] - vecT[0] * biasAE, ptA[1] - vecT[1] * biasAE)

    curve1 = tdBezier(ptB, tangentB, tangentC, ptC, n=segs)
    curve2 = tdBezier(ptE, tangentE, tangentA, ptA, n=segs)

    return curve1 + [ptD,] + curve2 if (curve1 and curve2) else pts

#计算泪滴焊盘的多边形上的点列表
#track: 与焊盘连接的导线
#pad: 焊盘
#hpercent: 水平百分比，泪滴的水平长度占焊盘直径的百分比
#vpercent: 垂直百分比，泪滴的垂直高度占焊盘直接的百分比
#segs：曲线线段数量
#followTracks: 如果直接和焊盘相接的导线长度不够，是否继续往后找一段或几段
#noBulge: 导线延长线和焊盘中心不重合时的处理
def tdComputePoints(track, pad, hPercent, vPercent, segs, followTracks, noBulge):
    if not track.isValid() or not pad.isValid() or (track.width == 0.0):
        return []

    trackPtNum = len(track.points)
    start = track.points[0]
    end = track.points[1]
    padPosX, padPosY = pad.pos
    padSize = pad.size if (pad.padType == 'PAD') else min(pad.sizeX, pad.sizeY)
    radius = padSize / 2.0 #焊盘半径
    halfWidth = track.width / 2.0 #走线宽度的一半

    if (hPercent < 10):
        hPercent = 10
    if (vPercent > 100):
        vPercent = 100 #最大占满直径
    elif (vPercent < 10):
        vPercent = 10

    #确定开始点在焊盘直径内
    if (math.dist(start, pad.pos) > radius):
        start, end = end, start

    #找到添加泪滴的方向
    #起点和终点两个向量相减，得到一个新的向量，方向就是线段的方向
    vecT = tdNormalizeVector((end[0] - start[0], end[1] - start[1]))

    #找到走线和焊盘（假定为圆）相交的点
    backoff = newX = newY = 0
    while (backoff < radius):
        newX = start[0] + vecT[0] * backoff
        newY = start[1] + vecT[1] * backoff
        if (math.dist((newX, newY), (padPosX, padPosY)) >= radius):
            break
        backoff += 0.01 #每次步进0.01mm
    start = (newX, newY) #交点做为新的起点

    #泪滴的方向向量，为何不用上面的vecT是因为走线的起点可能不在焊盘的中心
    vec = tdNormalizeVector((start[0] - padPosX, start[1] - padPosY))

    #确定泪滴长度
    targetLength = padSize * (hPercent / 100.0)
    n = min(targetLength, math.dist(start, end)) #避免泪滴焊盘超过走线
    consumed = 0

    #如果第一段走线不够泪滴焊盘的长度，则尝试再找一段
    if followTracks:
        trIdx = 2 #开头两个点已经用了，从第三个点开始
        while ((trIdx < trackPtNum) and (n + consumed < targetLength)):
            pt = track.points[trIdx]
            trIdx += 1
            backoff = 0
            consumed += n
            n = min(targetLength - consumed, math.dist(pt, end))
            start, end = end, pt
            
        vecT = tdNormalizeVector((end[0] - start[0], end[1] - start[1]))

    #如果泪滴焊盘需要缩短，同时也缩短高度
    if (n + consumed < targetLength):
        minVpercent = 100 * float(halfWidth) / float(radius)
        vPercent = vPercent * n / targetLength + minVpercent * (1 - n / targetLength)

    #找到泪滴多边形和走线的两个交点
    pointB = (round(start[0] + vecT[0] * n + vecT[1] * halfWidth, 3), 
              round(start[1] + vecT[1] * n - vecT[0] * halfWidth, 3))
    pointA = (round(start[0] + vecT[0] * n - vecT[1] * halfWidth, 3), 
              round(start[1] + vecT[1] * n + vecT[0] * halfWidth, 3))

    #如果两个交点在焊盘内，则直接返回
    if ((math.dist(pointA, pad.pos) < radius) or (math.dist(pointB, pad.pos) < radius)):
        return []

    #焊盘和泪滴焊盘交点的角度位置
    dC = math.asin(vPercent / 100.0)
    dE = -dC

    if noBulge:
        # find (signed) angle between track and teardrop
        offAngle = math.atan2(vecT[1], vecT[0]) - math.atan2(vec[1], vec[0])
        if offAngle > 3.14159:
            offAngle -= 2 * 3.14159
        if offAngle < -3.14159:
            offAngle += 2 * 3.14159

        if offAngle + dC > 3.14159 / 2:
            dC = 3.14159 / 2 - offAngle

        if offAngle + dE < -3.14159 / 2:
            dE = -3.14159 / 2 - offAngle

    vecC = (vec[0] * math.cos(dC) + vec[1] * math.sin(dC), -vec[0] * math.sin(dC) + vec[1] * math.cos(dC))
    vecE = (vec[0] * math.cos(dE) + vec[1] * math.sin(dE), -vec[0] * math.sin(dE) + vec[1] * math.cos(dE))

    #泪滴多边形和焊盘的两个交点
    pointC = (round(padPosX + (vecC[0] * radius), 3), round(padPosY + (vecC[1] * radius), 3))
    pointE = (round(padPosX + (vecE[0] * radius), 3), round(padPosY + (vecE[1] * radius), 3))

    #最后一个点在走线方向向焊盘圆心延伸的后面
    halfRadius = 0.5 * radius
    pointD = (round(padPosX - (vec[0] * halfRadius), 3), round(padPosY - (vec[1] * halfRadius), 3))

    pts = [pointA, pointB, pointC, pointD, pointE]
    if segs > 2:
        pts = tdComputeCurved(vPercent, halfWidth, vec, pad, pts, segs)

    return pts

#添加泪滴焊盘的入口，外部调用此函数
# usePth: 是否应用到通孔焊盘
# useSmd: 是否应用到贴片焊盘
# follow_tracks: 如果走线太短，则延长 Follow tracks if shorter than needed
#返回一个多边形列表[poly,...]
def createTeardrops(textIo, hPercent=50, vPercent=90, segs=10, usePth=True, useSmd=False, followTracks=False, noBulge=True):
    teardrops = []
    #搜集焊盘
    pads = textIo.getPads('PAD') if usePth else []
    if useSmd:
        pads.extend(textIo.getPads('SMDPAD'))
    
    #搜集走线
    tracks = textIo.getTracks()

    if not pads or not tracks:
        return []

    #搜集已有的泪滴焊盘，每个泪滴焊盘就是一个多边形
    oldTeardrops = getTeardrops(textIo, pads, tracks)
    #print('num of oldTeardrops: {}'.format(len(oldTeardrops))) #TODO
    
    for pad in pads:
        #和敷铜直接接触的焊盘/十字焊盘都不用添加泪滴焊盘
        if (pad.thermal or (pad.clearance == 0)):
            continue

        padVia = pad.via #是否是双面焊盘
        padSize = pad.size if (pad.padType == 'PAD') else min(pad.sizeX, pad.sizeY)
        enclose = pad.enclose #成员函数
        #看哪个走线和焊盘相交，一个线段的端点在焊盘内，另一个端点在焊盘外
        for track in tracks:
            #需要板层一致
            if ((not padVia) and (track.layerIdx != pad.layerIdx)):
                continue

            #如果走线宽度超过泪滴要求的高度，则跳过
            if (track.width >= (padSize * vPercent / 100)):
                continue

            points = track.points
            ptNum = len(points)
            for idx in range(ptNum - 1):
                pt1 = points[idx]
                pt2 = points[idx + 1]
                in1 = enclose(pt1)
                in2 = enclose(pt2)
                if (in1 == in2): #需要确保一个在外面，一个在里面
                    continue

                newTrack = SprintTrack(track.layerIdx, track.width)
                if in2: #确保pt1在焊盘内，然后将剩下的点依次存放
                    newTrack.addPoint(pt2)
                    newTrack.addAllPoints(points[:idx + 1][::-1])
                else:
                    newTrack.addAllPoints(points[idx:])
                    
                tPts = tdComputePoints(newTrack, pad, hPercent, vPercent, segs, followTracks, noBulge)
                if tPts: #计算出点列表后新建一个多边形保存这些点
                    tearD = SprintPolygon(track.layerIdx, width=0)
                    tearD.addAllPoints(tPts)
                    #避免重复添加，这里不能使用 not in 运算符，使用重载的 __eq__() 运算
                    allTds = oldTeardrops + teardrops
                    for poly in allTds:
                        if (poly == tearD):
                            break
                    else:
                        teardrops.append(tearD)

    return teardrops

#搜集已有的泪滴焊盘，泪滴焊盘的标准是包含焊盘中心和对应走线一个端点的一个小多边形(面积和焊盘差不多)
#返回一个列表
def getTeardrops(textIo, pads, tracks):
    teardrops = []
    polys = textIo.getPolygons() #仅返回导电多边形

    for poly in polys:
        polyLayer = poly.layerIdx
        encircle = poly.encircle
        polyArea = None
        for pad in pads:
            if ((not pad.via) and (polyLayer != pad.layerIdx)): #焊盘的板层要和多边形一致
                continue

            if (not encircle(pad.pos)): #此多边形没有包含这个焊盘，跳过
                continue

            #已经确认此多边形poly包含焊盘pad
            #还需要确认此焊盘包含某根走线的一个端点
            #padSize = pad.size
            enclose = pad.enclose
            padArea = None
            #看哪个走线和焊盘相交，一个线段的端点在焊盘内，另一个端点在焊盘外
            for track in tracks:
                if (track.layerIdx != polyLayer): #走线的板层要和多边形一致
                    continue

                points = track.points
                ptNum = len(points)
                for idx in range(ptNum - 1):
                    pt1 = points[idx]
                    pt2 = points[idx + 1]
                    #一个在外面，一个在里面
                    if (enclose(pt1) != enclose(pt2)): # and (encircle(pt1) != encircle(pt2)):
                        #判断多边形面积是否和焊盘相差不大
                        if polyArea is None:
                            #polyArea = poly.area() #发现这个面积计算有时候不准，所以使用外框的面积代替
                            polyArea = (poly.xMax - poly.xMin) * (poly.yMax - poly.yMin)
                            #print(poly.xMax, poly.xMin, poly.yMax, poly.yMin)
                        if padArea is None:
                            padArea = pad.area()
                            #print(padArea, pad.size, pad.form)
                        #print(polyArea, padArea)
                        if (padArea / 15) <= polyArea <= (padArea * 4): #确认两个面积差不多或多边形更小
                            if (poly not in teardrops):
                                teardrops.append(poly)
                            break

    return teardrops
