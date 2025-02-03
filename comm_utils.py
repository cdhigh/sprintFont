#!/usr/bin/env python
#-*- coding:utf-8 -*-
"""
公共工具
Author: cdhigh <https://github.com/cdhigh>
"""
import math
from vector2d import Vector2d

#字符串转整数，出错则返回defaultValue
def str_to_int(txt: str, defaultValue: int=0):
    try:
        return int(str(txt).strip())
    except:
        return defaultValue

#字符串转浮点数，出错则返回defaultValue
def str_to_float(txt: str, defaultValue: float=0.0):
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

#线段和X轴夹角，返回单位为角度
def angleWithXAxis(pt1: tuple, pt2: tuple):
    x1, y1 = pt1
    x2, y2 = pt2
    return math.degrees(math.atan2(y2 - y1, x2 - x1))

#计算一条线段上离起点pt1一定距离d的点坐标
def pointInLineWithDistance(pt1: tuple, pt2: tuple, d: float):
    startPt = Vector2d(pt1[0], pt1[1])
    endPt = Vector2d(pt2[0], pt2[1])
    newVect = endPt - startPt
    length = newVect.Mod()
    if length == 0:
        return round(pt1[0], 4), round(pt1[1], 4)  # 避免除零错误，返回起点

    t = d / length
    ret = startPt + newVect.Scalar(t)
    return round(ret.x, 4), round(ret.y, 4)

#获取两根直线的交点
#https://blog.csdn.net/yangtrees/article/details/7965983
#pt1-pt2和pt3-pt4为两个直线上任意两点
def getCrossPoint(pt1: tuple, pt2: tuple, pt3: tuple, pt4: tuple):
    x1, y1 = pt1
    x2, y2 = pt2
    x3, y3 = pt3
    x4, y4 = pt4
    
    k1 = ((y2 - y1) / (x2 - x1)) if (x2 != x1) else None #斜率None表示垂直线
    b1 = y1 - x1 * k1 if (x2 != x1) else 0
    k2 = ((y4 - y3) / (x4 - x3)) if (x4 != x3) else None
    b2 = y3 - x3 * k2 if (x4 != x3) else 0

    #如果两根直线的斜率相等，说明没有交点
    if (k1 == k2):
        return None

    if (k1 is None):
        x = x1
        y = k2 * x + b2  #如果k1为垂直线
    elif (k2 == None):
        x = x3
        y = (k1 * x + b1)
    else:
        x = (b2 - b1) / (k1 - k2)
        y = (k1 * x + b1)

    return (round(x, 4), round(y, 4))

#判断三个点的一个序列是顺时针还是逆时针
#https://blog.csdn.net/Jamence/article/details/77608659
#返回：0-顺时针，1-逆时针，其他值-共线
def isPointListClockwise(pt1: tuple, pt2: tuple, pt3: tuple):
    x1, y1 = pt1
    x2, y2 = pt2
    x3, y3 = pt3
    ans = (x2 - x1) * (y3 - y1) - (y2 - y1) * (x3 - x1) #表示向量AB与AC的叉积的结果 
    if (ans > 0):
        return 1 #逆时针
    elif (ans < 0):
        return 0 #顺时针
    else:
        return 2 #共线

#圆上三点求圆心和半径
def calCenterByThreePoints(pt1: tuple, pt2: tuple, pt3: tuple):
    x1, y1 = pt1
    x2, y2 = pt2
    x3, y3 = pt3
    a = 2 * (x2 - x1)
    b = 2 * (y2 - y1)
    c = x2 * x2 + y2 * y2 - x1 * x1 - y1 * y1
    d = 2 * (x3 - x2)
    e = 2 * (y3 - y2)
    f = x3 * x3 + y3 * y3 - x2 * x2 - y2 * y2
    x = (b * f - e * c) / (b * d - e * a)
    y = (d * c - a * f) / (b * d - e * a)
    return (round(x, 4), round(y, 4))

#已知两点和半径，求圆心  [已废弃，使用svgArcToCenterParam()代替]
#x1/y1: 起点坐标
#x2/y2: 终点坐标
#radius: 半径
#bigArc: 1-大圆弧, 0-小圆弧
#dirCC: 方向，1-顺时针，0-逆时针
#返回：(cx, cy)
def calCenterByPointsAndRadius(x1: float, y1: float, x2: float, y2: float, radius: float, bigArc: bool, dirCC: bool):
    lineLen = math.dist((x1, y1), (x2, y2))
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


#计算一个线段和X轴的角度
def lineAngleToXaxis(pt1: tuple, pt2: tuple):
    return math.degrees(math.atan2(pt2[1] - pt1[1], pt2[0] - pt1[0]))

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

    s_phi = round(math.sin(phi), 4)
    c_phi = round(math.cos(phi), 4)
    hd_x = round((x1 - x2) / 2.0, 4) #half diff of x
    hd_y = round((y1 - y2) / 2.0, 4) #half diff of y
    hs_x = round((x1 + x2) / 2.0, 4) #half sum of x
    hs_y = round((y1 + y2) / 2.0, 4) #half sum of y

    #F6.5.1
    x1_ = round(c_phi * hd_x + s_phi * hd_y, 4)
    y1_ = round(c_phi * hd_y - s_phi * hd_x, 4)

    #F.6.6 Correction of out-of-range radii
    #  Step 3: Ensure radii are large enough
    _lambda = round((x1_ * x1_) / (rx * rx) + (y1_ * y1_) / (ry * ry), 4)
    if (_lambda > 1):
        rx = round(rx * math.sqrt(_lambda), 4)
        ry = round(ry * math.sqrt(_lambda), 4)

    rxry = round(rx * ry, 4)
    rxy1_ = round(rx * y1_, 4)
    ryx1_ = round(ry * x1_, 4)
    sum_of_sq = round(rxy1_ * rxy1_ + ryx1_ * ryx1_, 4)  #sum of square
    if (sum_of_sq == 0):
        raise Exception('start point can not be same as end point')
    
    coe = round(math.sqrt(abs((rxry * rxry - sum_of_sq) / sum_of_sq)), 4)
    if (fA == fS):
        coe = -coe

    #F6.5.2
    cx_ = round(coe * rxy1_ / ry, 4)
    cy_ = round(-coe * ryx1_ / rx, 4)

    #F6.5.3
    cx = round(c_phi * cx_ - s_phi * cy_ + hs_x, 4)
    cy = round(s_phi * cx_ + c_phi * cy_ + hs_y, 4)

    xcr1 = round((x1_ - cx_) / rx, 4)
    xcr2 = round((x1_ + cx_) / rx, 4)
    ycr1 = round((y1_ - cy_) / ry, 4)
    ycr2 = round((y1_ + cy_) / ry, 4)

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
#angle: X向右为0度，逆时针为正
def pointAtCircle(cx: float, cy: float, radius: float, angle: float):
    x1 = round(cx + radius * math.cos(math.radians(-angle)), 4)
    y1 = round(cy + radius * math.sin(math.radians(-angle)), 4)
    return (x1, y1)

#判断一个点在线段的左侧还是右侧
def pointPosition(pt1: tuple, pt2: tuple, px: tuple):
    x1, y1 = pt1
    x2, y2 = pt2
    x, y = px
    crossProduct = (x2 - x1) * (y - y1) - (y2 - y1) * (x - x1)
    if crossProduct < 0:
        return "L"
    elif crossProduct > 0:
        return "R"
    else: #在线上
        return "0"

#获得圆心坐标为center 半径为r的圆cutNum等分后的圆上坐标
#center: 圆心坐标
#radius: 半径
#cutNum: 需要多少等分
#start/end: 圆弧的开始角度和结束角度，如果提供的话，Y轴正方向为0度，逆时针增加
#clockWise: 逆时针还是顺时针
#返回一个列表 [(x,y),...]
def cutCircle(center: tuple, radius: float, cutNum: int, start=0, stop=360, clockWise=True):
    cutNum = cutNum or 10
    angleStep = abs(stop - start) / cutNum
    #startAngle = min(start, stop)
    cx, cy = center
    points = []
    for idx in range(cutNum + 1):
        if clockWise:
            radians = math.radians(idx * angleStep + start)
        else:
            radians = math.radians(stop - (idx * angleStep))
        points.append((round(cx + math.sin(radians) * radius, 4), round(cy + math.cos(radians) * radius, 4)))
    
    return points

#以(cx, cy)为旋转中心点，
#已经知道旋转前点的位置(x1,y1)和旋转的角度a，求旋转后点的新位置(x2,y2)
def pointAfterRotated(x1: float, y1: float, cx: float, cy: float, angle: float, clockwise: int=0):
    angle = math.radians(angle)
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

    #保证所有点都是正数
    minValue = points[0][0]
    for x, y in points:
        if (x < minValue):
            minValue = x
        if (y < minValue):
            minValue = y

    if (minValue < 0):
        points = [(x - minValue, y - minValue) for (x, y) in points]

    area = points[0][1] * (points[-1][0] - points[1][0])
    for idx in range(pointNum):
        area += points[idx][1] * (points[idx - 1][0] - points[(idx + 1) % pointNum][0])
    return abs(area / 2.0)

#print(ComputePolygonArea([(-10, -10), (10, -10), (10, 10), (-10, 10),]))

#计算点(x, y) 到线段 (x1, y1) - (x2, y2) 的垂直距离
#返回：(距离，投影点)
def pointToLineDistance(x, y, x1, y1, x2, y2):
    dx = x2 - x1
    dy = y2 - y1
    if (-0.00001 <= dx <= 0.00001) and (-0.00001 <= dy <= 0.00001): #线段退化为一个点
        return math.dist((x, y), (x1, y1)), (x1, y1)
    
    #计算投影参数 t
    t = ((x - x1) * dx + (y - y1) * dy) / (dx ** 2 + dy ** 2)
    t = max(0, min(1, t))  #限制 t 在 [0,1] 范围内，确保投影点在线段上

    #计算投影点
    projX = round(x1 + t * dx, 4)
    projY = round(y1 + t * dy, 4)
    return math.dist((x, y), (projX, projY)), (projX, projY)

#计算与线段 AB 垂直的长度为 r 的线段的终点坐标
#返回：一个包含两个终点坐标的列表，每个坐标为 (x, y) 的元组
def perpendicularLineEndPoints(pt1: tuple, pt2: tuple, r: float):
    x1, y1 = pt1
    x2, y2 = pt2
    if x1 == x2: #垂直线
        return [(round(x2 + r, 4), y2), (round(x2 - r, 4), y2)]
    elif y1 == y2: #水平线
        return [(x2, round(y2 + r, 4)), (x2, round(y2 - r, 4))]

    k = (y2 - y1) / (x2 - x1) #斜率
    kPerp = -1 / k
    points = []
    for sign in [-1, 1]:
        x = x2 + sign * r / math.sqrt(1 + kPerp ** 2)
        y = y2 + kPerp * (x - x2)
        points.append((round(x, 4), round(y, 4)))
    return points
