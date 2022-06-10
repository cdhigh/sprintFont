#!/usr/bin/env python
#-*- coding:utf-8 -*-
"""
公共工具
Author: cdhigh <https://github.com/cdhigh>
"""
import math

#字符串转整数，出错则返回defaultValue
def str_to_int(txt: str, defaultValue: int=0):
    try:
        return int(str(txt).strip())
    except:
        return defaultValue

#字符串转浮点数，出错则返回defaultValue
def str_to_float(txt: str, defaultValue: int=0.0):
    try:
        return float(str(txt).strip())
    except:
        return defaultValue

#判断一个字符串是否是十六进制字符串
def isHexString(txt: str):
    txt = txt.lower()
    for ch in txt:
        if ((not ('0' <= ch <= '9')) and (not ('a' <= ch <= 'f'))):
            return False
    return True

#弧度转角度
def radiansToDegrees(ra):
    return ra / math.pi * 180

#角度转弧度
def degreesToRadians(angle):
    return math.pi / 180 * angle

#计算二维空间两点之间的距离
def euclideanDistance(x1: float, y1: float, x2: float, y2: float):
    return math.sqrt(((x1 - x2) * (x1 - x2)) + ((y1 - y2) * (y1 - y2)))

#已知两点和半径，求圆心  [已废弃，使用svgArcToCenterParam()代替]
#x1/y1: 起点坐标
#x2/y2: 终点坐标
#radius: 半径
#bigArc: 1-大圆弧, 0-小圆弧
#dirCC: 方向，1-顺时针，0-逆时针
#返回：(cx, cy)
def calCenterByPointsAndRadius(x1: float, y1: float, x2: float, y2: float, radius: float, bigArc: bool, dirCC: bool):
    lineLen = euclideanDistance(x1, y1, x2, y2)
    x3 = (x1 + x2) / 2
    y3 = (y1 + y2) / 2

    xTmp = math.sqrt(radius * radius - (lineLen / 2) * (lineLen / 2)) * (y1 - y2) / lineLen
    yTmp = math.sqrt(radius * radius - (lineLen / 2) * (lineLen / 2)) * (x2 - x1) / lineLen

    #分别为两个圆心
    cx1 = round(x3 + xTmp, 4)
    cy1 = round(y3 + yTmp, 4)
    cx2 = round(x3 - xTmp, 4)
    cy2 = round(y3 - yTmp, 4)

    angleLine = round(math.acos((x2 - x1) / lineLen) * 180 / math.pi)
    if (y2 < y1):
        angleLine = -angleLine

    if (((angleLine > 0) and (angleLine < 180)) or (angleLine == 180)):
        if (dirCC): #顺时针圆
            return (cx1, cy1) if (bigArc) else (cx2, cy2)
        else: #逆时针圆
            return (cx2, cy2) if (bigArc) else (cx1, cy1)
    else:
        if (dirCC): #顺时针圆
            return (cx2, cy2) if (bigArc) else (cx1, cy1)
        else:
            return (cx1, cy1) if (bigArc) else (cx2, cy2)


#通过SVG语法的圆弧参数计算圆心/开始角度/结束角度
#https://blog.csdn.net/cuixiping/article/details/7958298
#输入：svg : [A | a] (rx ry x-axis-rotation large-arc-flag sweep-flag x y)+
# x1 y1 rx ry φ fA fS x2 y2
# sample :  svgArcToCenterParam(200, 200, 50, 50, 0, 1, 1, 300, 200)
def svgArcToCenterParam(x1, y1, rx, ry, phi, fA, fS, x2, y2):
    pix2 = math.pi * 2

    if (rx < 0):
        rx = -rx
    if (ry < 0):
        ry = -ry
    
    if ((rx == 0.0) or (ry == 0.0)): #非法参数
        raise Exception('rx and ry can not be 0')

    s_phi = math.sin(phi)
    c_phi = math.cos(phi)
    hd_x = (x1 - x2) / 2.0 #half diff of x
    hd_y = (y1 - y2) / 2.0 #half diff of y
    hs_x = (x1 + x2) / 2.0 #half sum of x
    hs_y = (y1 + y2) / 2.0 #half sum of y

    #F6.5.1
    x1_ = c_phi * hd_x + s_phi * hd_y
    y1_ = c_phi * hd_y - s_phi * hd_x

    #F.6.6 Correction of out-of-range radii
    #  Step 3: Ensure radii are large enough
    _lambda = (x1_ * x1_) / (rx * rx) + (y1_ * y1_) / (ry * ry)
    if (_lambda > 1):
        rx = rx * math.sqrt(_lambda)
        ry = ry * math.sqrt(_lambda)

    rxry = rx * ry
    rxy1_ = rx * y1_
    ryx1_ = ry * x1_
    sum_of_sq = rxy1_ * rxy1_ + ryx1_ * ryx1_  #sum of square
    if (sum_of_sq == 0):
        raise Exception('start point can not be same as end point')
    
    coe = math.sqrt(abs((rxry * rxry - sum_of_sq) / sum_of_sq))
    if (fA == fS):
        coe = -coe

    #F6.5.2
    cx_ = coe * rxy1_ / ry
    cy_ = -coe * ryx1_ / rx

    #F6.5.3
    cx = c_phi * cx_ - s_phi * cy_ + hs_x
    cy = s_phi * cx_ + c_phi * cy_ + hs_y

    xcr1 = (x1_ - cx_) / rx
    xcr2 = (x1_ + cx_) / rx
    ycr1 = (y1_ - cy_) / ry
    ycr2 = (y1_ + cy_) / ry

    #F6.5.5
    startAngle = radian(1.0, 0.0, xcr1, ycr1)

    #F6.5.6
    deltaAngle = radian(xcr1, ycr1, -xcr2, -ycr2)
    while (deltaAngle > pix2):
        deltaAngle -= pix2

    while (deltaAngle < 0.0):
        deltaAngle += pix2

    if not fS:
        deltaAngle -= pix2

    endAngle = startAngle + deltaAngle
    while (endAngle > pix2):
        endAngle -= pix2

    while (endAngle < 0.0):
        endAngle += pix2

    #角度转换为度数
    startAngle = round(math.degrees(startAngle), 1)
    deltaAngle = round(math.degrees(deltaAngle), 1)
    endAngle = round(math.degrees(endAngle), 1)

    #因为SVG的Y轴向下是增加的，而Sprint-Layout的Y轴向下是减小的，将角度沿X轴反转
    if startAngle < 0:
        startAngle = -startAngle
    else:
        startAngle = 360 - startAngle

    if endAngle < 0:
        endAngle = -endAngle
    else:
        endAngle = 360 - endAngle

    if fS: #Sprint-Layout逆时针计算角度
        startAngle, endAngle = endAngle, startAngle

    if fA: #大圆弧标识
        startAngle, endAngle = max(startAngle, endAngle), min(startAngle, endAngle)
        if startAngle > (endAngle + 180):
            startAngle, endAngle = endAngle, startAngle
        
    ret = {'cx': cx, 'cy': cy, 'startAngle': startAngle,
        'deltaAngle': deltaAngle, 'endAngle': endAngle,
        'clockwise': True if fS else False}
    return ret

def radian(ux, uy, vx, vy):
    dot = ux * vx + uy * vy
    mod = math.sqrt((ux * ux + uy * uy) * (vx * vx + vy * vy ))
    rad = math.acos(dot / mod)
    if ((ux * vy - uy * vx) < 0.0):
        rad = -rad
    
    return rad

#计算圆上点的坐标
#cx/cy: 圆心坐标
#radius: 半径
#cutNum: 需要多少等分
#angle: X向右为0度，逆时针为正
def pointAtCircle(cx: float, cy: float, radius: float, angle: float):
    x1 = round(cx + radius * math.cos(degreesToRadians(-angle)), 4)
    y1 = round(cy + radius * math.sin(degreesToRadians(-angle)), 4)
    return (x1, y1)

#获得圆心坐标为center 半径为r的圆cutNum等分后的圆上坐标
#cx/cy: 圆心坐标
#radius: 半径
#cutNum: 需要多少等分
#start/end: 圆弧的开始角度和结束角度，如果提供的话
#返回一个列表 [(x,y),...]
def cutCircle(cx: float, cy: float, radius: float, cutNum: int, start: int=None, stop: int=None):
    points = []
    if ((start is None) or (stop is None)):
        angle = 360 / cutNum
        startAngle = 0
    else:
        angle = abs(start - stop) / cutNum
        startAngle = min(start, stop)

    for idx in range(cutNum):
        radians = (math.pi / 180) * ((idx + 1) * angle + startAngle)
        points.append((round(cx + math.sin(radians) * radius, 4), round(cy + math.cos(radians) * radius, 4)))
    
    return points

#以(cx, cy)为旋转中心点，
#已经知道旋转前点的位置(x1,y1)和旋转的角度a，求旋转后点的新位置(x2,y2)
def pointAfterRotated(x1: float, y1: float, cx: float, cy: float, angle: float, clockwise: int=0):
    angle = degreesToRadians(angle)
    if clockwise: #顺时针旋转
        x2 = (x1 - cx) * math.cos(angle) + (y1 - cy) * math.sin(angle) + cx
        y2 = (y1 - cy) * math.cos(angle) - (x1 - cx) * math.sin(angle) + cy
    else:         #逆时针旋转
        x2 = (x1 - cx) * math.cos(angle) - (y1 - cy) * math.sin(angle) + cx
        y2 = (y1 - cy) * math.cos(angle) + (x1 - cx) * math.sin(angle) + cy

    return (round(x2, 4), round(y2, 4))

#print(pointAfterRotated(-5, 0, 0, 0, 180))

#计算任意多边形的面积，顶点按照顺时针或者逆时针方向排列
def ComputePolygonArea(points: list):
    pointNum = len(points)
    if pointNum < 3: #至少需要三个点
        return 0.0

    #如果最后一个点和第一个点重合，则去掉最后一个点
    if points[0] == points[-1]:
        points = points[:-1]
        pointNum -= 1
        if pointNum < 3: #至少需要三个点
            return 0.0

    s = points[0][1] * (points[-1][0] - points[1][0])
    for idx in range(pointNum):
        s += points[idx][1] * (points[idx - 1][0] - points[(idx + 1) % pointNum][0])
    return abs(s / 2.0)

