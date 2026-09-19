#!/usr/bin/env python3
# -*- coding:utf-8 -*-
"""PCB设计规则检查(DRC)：间距/线宽/孤立焊盘
供MCP的checkDrc工具使用，纯几何检查，无第三方依赖：
1. 间距违规：同层不同网络的铜元素边缘间距小于规则值(pad-pad/pad-track/track-track/zone组合)
   网络划分复用NetlistBuilder的物理接触连通性——同一网络的有意连接(接触/搭接)不算违规
2. 线宽违规：导线宽度小于规则最小线宽
3. 孤立焊盘：所在网络只有它自己(未与任何元素相连)，布线时待连接
注意：与NetlistBuilder一致，覆铜按实心多边形处理(忽略hatch)、圆忽略(不导电)、
cutout禁止区不参与。元素量大时为O(n²)检查，超大板会慢。
Author: cdhigh <https://github.com/cdhigh>
"""
import math
from utils.comm_utils import pointToLineDistance
from sprint_struct.sprint_track import SprintTrack
from sprint_struct.sprint_pad import SprintPad
from sprint_struct.sprint_polygon import SprintPolygon
from sprint_struct.sprint_element import LAYER_C1, LAYER_C2, LAYER_I1, LAYER_I2
from conversion.netlist_builder import (NetlistBuilder, segments_intersect,
    point_in_polygon, get_pad_corners, is_pad_circular)

MAX_DRC_VIOLATIONS = 200 #返回给LLM的违规条数上限，防止撑爆上下文

#点到线段的最近距离，返回(距离, 输入点, 线段上最近点)
#pointToLineDistance已内置端点钳位(t限制在[0,1])，即线段距离
def pointSegmentDistance(px, py, x1, y1, x2, y2):
    dist, proj = pointToLineDistance(px, py, x1, y1, x2, y2)
    return dist, (px, py), (proj[0], proj[1])

#两条线段的最近距离，返回(距离, 线段1最近点, 线段2最近点)；相交返回0
def segmentSegmentDistance(p1, p2, p3, p4):
    if segments_intersect(p1, p2, p3, p4):
        return 0.0, ((p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2), ((p3[0] + p4[0]) / 2, (p3[1] + p4[1]) / 2)
    best = None
    for pt, a, b in ((p1, p3, p4), (p2, p3, p4), (p3, p1, p2), (p4, p1, p2)):
        d, cpPt, cpSeg = pointSegmentDistance(pt[0], pt[1], a[0], a[1], b[0], b[1])
        if (best is None) or (d < best[0]):
            best = (d, cpPt, cpSeg)
    return best

#多边形的边列表
def polygonEdges(poly):
    return [(poly[i], poly[(i + 1) % len(poly)]) for i in range(len(poly))]

#点到多边形的最近距离，返回(距离, 输入点, 多边形上最近点)；点在内部返回0
def pointPolygonDistance(pt, poly):
    if point_in_polygon(pt, poly):
        return 0.0, pt, pt
    best = None
    for a, b in polygonEdges(poly):
        d, cpPt, cpSeg = pointSegmentDistance(pt[0], pt[1], a[0], a[1], b[0], b[1])
        if (best is None) or (d < best[0]):
            best = (d, cpPt, cpSeg)
    return best

#线段到多边形的最近距离，返回(距离, 线段上最近点, 多边形上最近点)；相交或端点在内部返回0
def segmentPolygonDistance(p1, p2, poly):
    if point_in_polygon(p1, poly) or point_in_polygon(p2, poly):
        mid = ((p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2)
        return 0.0, mid, mid
    best = None
    for a, b in polygonEdges(poly):
        d, cp1, cp2 = segmentSegmentDistance(p1, p2, a, b)
        if (best is None) or (d < best[0]):
            best = (d, cp1, cp2)
    return best

#多边形到多边形的最近距离，返回(距离, 最近点1, 最近点2)；相交或包含返回0
def polygonPolygonDistance(poly1, poly2):
    if point_in_polygon(poly1[0], poly2) or point_in_polygon(poly2[0], poly1):
        return 0.0, poly1[0], poly2[0]
    best = None
    for a1, b1 in polygonEdges(poly1):
        for a2, b2 in polygonEdges(poly2):
            d, cp1, cp2 = segmentSegmentDistance(a1, b1, a2, b2)
            if (best is None) or (d < best[0]):
                best = (d, cp1, cp2)
    return best

#两个元素是否在同一铜层(过孔焊盘视为C1/C2都在，与NetlistBuilder口径一致)
def onSameLayer(e1, e2):
    conductLayers = [LAYER_C1, LAYER_C2, LAYER_I1, LAYER_I2]
    layers1 = conductLayers if (isinstance(e1, SprintPad) and e1.via) else [e1.layerIdx]
    layers2 = conductLayers if (isinstance(e2, SprintPad) and e2.via) else [e2.layerIdx]
    return bool(set(layers1) & set(layers2))

#元素的类型名(与MCP getElements一致)
def elementTypeName(elem):
    if isinstance(elem, SprintTrack):
        return 'TRACK'
    if isinstance(elem, SprintPad):
        return elem.padType if elem.padType in ('PAD', 'SMDPAD') else 'PAD'
    if isinstance(elem, SprintPolygon):
        return 'ZONE'
    return 'UNKNOWN'

#把铜元素转成统一形状描述: (类别, 数据, 额外半宽)
#circle: 数据=(中心,半径)；track: 数据=折线顶点(额外半宽=线宽/2)；poly: 数据=多边形顶点
def elementShape(elem):
    if isinstance(elem, SprintTrack):
        return ('track', list(elem.points), elem.width / 2.0)
    if isinstance(elem, SprintPad):
        if is_pad_circular(elem):
            return ('circle', (elem.pos, max(elem.sizeX, elem.sizeY) / 2.0), 0.0)
        return ('poly', get_pad_corners(elem), 0.0)
    if isinstance(elem, SprintPolygon):
        return ('poly', list(elem.points), 0.0)
    return None

#圆(中心+半径)到折线的边缘间距，返回(间距, 圆上最近点, 线上最近点)
def circleTrackDistance(circleData, points, trackHalf):
    center, radius = circleData
    best = None
    for i in range(len(points) - 1):
        a, b = points[i], points[i + 1]
        d, _, cp = pointSegmentDistance(center[0], center[1], a[0], a[1], b[0], b[1])
        if (best is None) or (d < best[0]):
            best = (d, cp)
    if best is None: #单点退化
        best = (math.dist(center, points[0]), points[0])
    d, cp = best
    if d <= 1e-9:
        return 0.0, center, cp
    ux, uy = (cp[0] - center[0]) / d, (cp[1] - center[1]) / d
    pCircle = (center[0] + ux * radius, center[1] + uy * radius)
    return max(d - radius - trackHalf, 0.0), pCircle, cp

#两个铜元素形状的边缘间距(已扣除线宽/半径)，返回(间距, 最近点1, 最近点2)
def shapeDistance(shape1, shape2):
    kind1, data1, extra1 = shape1
    kind2, data2, extra2 = shape2

    if (kind1 == 'circle') and (kind2 == 'circle'):
        (c1, r1), (c2, r2) = data1, data2
        d = math.dist(c1, c2)
        if d <= 1e-9:
            return 0.0, c1, c2
        ux, uy = (c2[0] - c1[0]) / d, (c2[1] - c1[1]) / d
        return (max(d - r1 - r2, 0.0),
            (c1[0] + ux * r1, c1[1] + uy * r1), (c2[0] - ux * r2, c2[1] - uy * r2))

    if (kind1 == 'circle') and (kind2 == 'track'):
        return circleTrackDistance(data1, data2, extra2)
    if (kind1 == 'track') and (kind2 == 'circle'):
        d, p2, p1 = circleTrackDistance(data2, data1, extra1)
        return d, p1, p2

    if (kind1 == 'circle') and (kind2 == 'poly'):
        (center, radius) = data1
        d, _, cp = pointPolygonDistance(center, data2)
        if d <= 1e-9:
            return 0.0, center, cp
        ux, uy = (cp[0] - center[0]) / d, (cp[1] - center[1]) / d
        return (max(d - radius - extra2, 0.0),
            (center[0] + ux * radius, center[1] + uy * radius), cp)
    if (kind1 == 'poly') and (kind2 == 'circle'):
        d, p2, p1 = shapeDistance(shape2, shape1)
        return d, p1, p2

    if (kind1 == 'track') and (kind2 == 'track'):
        best = None
        for i in range(len(data1) - 1):
            for j in range(len(data2) - 1):
                d, p1, p2 = segmentSegmentDistance(data1[i], data1[i + 1], data2[j], data2[j + 1])
                if (best is None) or (d < best[0]):
                    best = (d, p1, p2)
        if best is None:
            return 0.0, data1[0], data2[0]
        return max(best[0] - extra1 - extra2, 0.0), best[1], best[2]

    if (kind1 == 'track') and (kind2 == 'poly'):
        best = None
        for i in range(len(data1) - 1):
            d, p1, p2 = segmentPolygonDistance(data1[i], data1[i + 1], data2)
            if (best is None) or (d < best[0]):
                best = (d, p1, p2)
        if best is None:
            return 0.0, data1[0], data2[0]
        return max(best[0] - extra1 - extra2, 0.0), best[1], best[2]
    if (kind1 == 'poly') and (kind2 == 'track'):
        d, p2, p1 = shapeDistance(shape2, shape1)
        return d, p1, p2

    #poly-poly
    d, p1, p2 = polygonPolygonDistance(data1, data2)
    return max(d - extra1 - extra2, 0.0), p1, p2

#两元素包围盒的边缘间距(bbox无效时返回0表示不跳过检查)
def bboxGap(e1, e2):
    try:
        dx = max(e2.xMin - e1.xMax, e1.xMin - e2.xMax, 0.0)
        dy = max(e2.yMin - e1.yMax, e1.yMin - e2.yMax, 0.0)
        if math.isinf(dx) or math.isinf(dy):
            return 0.0
        return math.hypot(dx, dy)
    except (TypeError, ValueError):
        return 0.0

#DRC检查器主类
class DrcChecker:
    #textIo: SprintTextIO板图; rule: PcbRule(trackWidth/clearance/smdSmdClearance单位mm)
    def __init__(self, textIo, rule):
        self.textIo = textIo
        self.rule = rule
        self.eps = 1e-6

    #执行检查
    #labelMap: 元素对象id->标签(与getNetlist一致的"a.b"格式)，由调用方传入
    #includeIsolated: 是否列出孤立焊盘
    def check(self, labelMap=None, includeIsolated=False):
        if labelMap is None:
            labelMap = {}

        #1. 网络划分(物理接触连通性，与getNetlist同一实现)
        netlist = NetlistBuilder(self.textIo).build()
        netOf = netlist.get('element_net_map', {})

        #2. 收集导电元素(与NetlistBuilder同一口径)，并确保bbox有效供快速过滤
        layers = [LAYER_C1, LAYER_C2, LAYER_I1, LAYER_I2]
        tracks = self.textIo.getTracks(layerIdx=layers)
        pads = self.textIo.getPads(layerIdx=layers)
        zones = [z for z in self.textIo.getPolygons(layerIdx=layers) if not z.cutout]
        elems = tracks + pads + zones
        for e in elems:
            e.updateSelfBbox()
        shapes = {id(e): elementShape(e) for e in elems}

        #3. 同层不同网络元素的间距检查
        violations = []
        n = len(elems)
        for i in range(n):
            e1 = elems[i]
            shape1 = shapes[id(e1)]
            for j in range(i + 1, n):
                e2 = elems[j]
                if not onSameLayer(e1, e2):
                    continue
                #同网络=有意连接，跳过间距检查；None=游离单元素(被netlist过滤，未分配网络号)，
                #两个None不是同网络，不能跳过，否则游离元素之间的清距漏检
                net1 = netOf.get(id(e1))
                net2 = netOf.get(id(e2))
                if (net1 is not None) and (net1 == net2):
                    continue
                #SMD-SMD对使用专门的间隙规则
                required = self.rule.clearance
                if (isinstance(e1, SprintPad) and (e1.padType == 'SMDPAD')
                        and isinstance(e2, SprintPad) and (e2.padType == 'SMDPAD')):
                    required = self.rule.smdSmdClearance
                #包围盒快速过滤(留足线宽余量)
                shape2 = shapes[id(e2)]
                if bboxGap(e1, e2) > required + shape1[2] + shape2[2] + 0.1:
                    continue
                gap, pt1, pt2 = shapeDistance(shape1, shape2)
                if gap < required - self.eps:
                    violations.append({
                        'type': 'clearance', 'layer': e1.layerIdx,
                        'elements': [labelMap.get(id(e1), '?'), labelMap.get(id(e2), '?')],
                        'elementTypes': [elementTypeName(e1), elementTypeName(e2)],
                        'gap': round(gap, 4), 'required': round(required, 4),
                        'pos': [round((pt1[0] + pt2[0]) / 2, 3), round((pt1[1] + pt2[1]) / 2, 3)]})

        #4. 线宽检查
        for e in tracks:
            if e.width < self.rule.trackWidth - self.eps:
                cx = sum(p[0] for p in e.points) / len(e.points)
                cy = sum(p[1] for p in e.points) / len(e.points)
                violations.append({
                    'type': 'width', 'layer': e.layerIdx,
                    'element': labelMap.get(id(e), '?'),
                    'width': round(e.width, 4), 'required': round(self.rule.trackWidth, 4),
                    'pos': [round(cx, 3), round(cy, 3)]})

        #5. 孤立焊盘(所在网络只有它自己)
        isolated = []
        if includeIsolated:
            for net in netlist.get('nets', []):
                netElems = net.get('elements', [])
                if (len(netElems) == 1) and isinstance(netElems[0], SprintPad):
                    pad = netElems[0]
                    isolated.append({
                        'element': labelMap.get(id(pad), '?'), 'layer': pad.layerIdx,
                        'pos': [round(pad.pos[0], 3), round(pad.pos[1], 3)]})

        #6. 汇总(间距近的排前面)
        violations.sort(key=lambda v: v.get('gap', 0))
        return {
            'ok': len(violations) == 0,
            'checkedElementCount': n,
            'netCount': len(netlist.get('nets', [])),
            'violationCount': len(violations),
            'violations': violations[:MAX_DRC_VIOLATIONS],
            'truncated': len(violations) > MAX_DRC_VIOLATIONS,
            'isolatedPadCount': len(isolated),
            'isolatedPads': isolated[:MAX_DRC_VIOLATIONS],
        }
