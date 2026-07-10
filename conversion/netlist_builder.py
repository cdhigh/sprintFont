#!/usr/bin/env python3
# -*- coding:utf-8 -*-
"""根据铜箔连通性自动生成Sprint-Layout的网表
Author: cdhigh <https://github.com/cdhigh>
"""
import math
from utils.comm_utils import pointToLineDistance
from sprint_struct.sprint_track import SprintTrack
from sprint_struct.sprint_pad import SprintPad
from sprint_struct.sprint_polygon import SprintPolygon
from sprint_struct.sprint_element import LAYER_C1, LAYER_C2, LAYER_I1, LAYER_I2

# 并查集类，用于管理和合并具有连通性的元素集合
class UnionFind:
    def __init__(self):
        self.parent = {}
        
    # 查找元素所属的集合根节点，并进行路径压缩优化
    def find(self, i):
        if i not in self.parent:
            self.parent[i] = i
        elif self.parent[i] != i:
            self.parent[i] = self.find(self.parent[i])
        return self.parent[i]
        
    # 合并两个元素所在的集合
    def union(self, i, j):
        root_i = self.find(i)
        root_j = self.find(j)
        if root_i != root_j:
            self.parent[root_i] = root_j

# 判断三个点构成的方向（逆时针或顺时针），用于辅助线段相交检测
def ccw(A, B, C):
    return (C[1]-A[1]) * (B[0]-A[0]) > (B[1]-A[1]) * (C[0]-A[0])

# 判断两条线段是否相交（包含端点触碰或完全交叉）
def segments_intersect(p1, p2, p3, p4):
    if ccw(p1, p3, p4) != ccw(p2, p3, p4) and ccw(p1, p2, p3) != ccw(p1, p2, p4):
        return True
    
    # 检查端点是否在另一条线段上
    for p, seg in [(p1, (p3,p4)), (p2, (p3,p4)), (p3, (p1,p2)), (p4, (p1,p2))]:
        dist, proj = pointToLineDistance(p[0], p[1], seg[0][0], seg[0][1], seg[1][0], seg[1][1])
        if dist < 0.001:
            min_x, max_x = min(seg[0][0], seg[1][0]), max(seg[0][0], seg[1][0])
            min_y, max_y = min(seg[0][1], seg[1][1]), max(seg[0][1], seg[1][1])
            if min_x - 0.001 <= proj[0] <= max_x + 0.001 and min_y - 0.001 <= proj[1] <= max_y + 0.001:
                return True
    return False

# 判断一个焊盘是否为圆形或近似圆形（八边形也按圆处理）
def is_pad_circular(pad):
    if pad.padType == 'PAD':
        return pad.form in (1, 2) # Round, Octagon (treat as round)
    return False

# 计算矩形类焊盘在任意旋转角度下的四个物理顶点坐标
# inflate参数可用于外扩边界（如增加容差或线宽的一半）
def get_pad_corners(pad, inflate=0.0):
    cx, cy = pad.pos
    w = pad.sizeX
    h = pad.sizeY
    
    if pad.padType == 'PAD':
        w = h = max(pad.sizeX, pad.sizeY)
        if pad.form in (4, 5, 6): # _H
            w *= 2
        elif pad.form in (7, 8, 9): # _V
            h *= 2
            
    w += inflate * 2
    h += inflate * 2
    
    corners = [
        (-w/2, -h/2),
        (w/2, -h/2),
        (w/2, h/2),
        (-w/2, h/2)
    ]
    
    rad = math.radians(pad.rotation) if getattr(pad, 'rotation', 0) else 0
    cos_a = math.cos(rad)
    sin_a = math.sin(rad)
    
    rotated_corners = []
    for x, y in corners:
        rx = x * cos_a - y * sin_a
        ry = x * sin_a + y * cos_a
        rotated_corners.append((cx + rx, cy + ry))
        
    return rotated_corners

# 使用光线投射法 (Ray Casting) 判断一个点是否在多边形内部
def point_in_polygon(pt, poly):
    x, y = pt
    inside = False
    j = len(poly) - 1
    for i in range(len(poly)):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi) + xi):
            inside = not inside
        j = i
    return inside

# 判断两个多边形是否相交（边缘相交或相互包含）
def polygons_intersect(poly1, poly2):
    for i in range(len(poly1)):
        p1 = poly1[i]
        p2 = poly1[(i+1)%len(poly1)]
        for j in range(len(poly2)):
            p3 = poly2[j]
            p4 = poly2[(j+1)%len(poly2)]
            if segments_intersect(p1, p2, p3, p4):
                return True
    if point_in_polygon(poly1[0], poly2): return True
    if point_in_polygon(poly2[0], poly1): return True
    return False

# 判断焊盘与线段是否相交，支持考虑线宽和容差
def pad_segment_intersect(pad, p1, p2, track_width, tol=0.01):
    if is_pad_circular(pad):
        pad_r = max(pad.sizeX, pad.sizeY) / 2.0
        dist, proj = pointToLineDistance(pad.pos[0], pad.pos[1], p1[0], p1[1], p2[0], p2[1])
        if dist <= pad_r + (track_width / 2.0) + tol:
            min_x, max_x = min(p1[0], p2[0]), max(p1[0], p2[0])
            min_y, max_y = min(p1[1], p2[1]), max(p1[1], p2[1])
            if min_x - tol <= proj[0] <= max_x + tol and min_y - tol <= proj[1] <= max_y + tol:
                return True
        if math.dist(pad.pos, p1) <= pad_r + tol or math.dist(pad.pos, p2) <= pad_r + tol:
            return True
        return False
    else:
        poly = get_pad_corners(pad, inflate=(track_width/2.0 + tol))
        if point_in_polygon(p1, poly) or point_in_polygon(p2, poly):
            return True
        for i in range(len(poly)):
            e1 = poly[i]
            e2 = poly[(i+1)%len(poly)]
            if segments_intersect(p1, p2, e1, e2):
                return True
        return False

# 判断两条导线（折线段）是否相交，先利用Bounding Box做快速过滤
def track_track_intersect(t1, t2, tol=0.01):
    if (t1.xMax + tol < t2.xMin or t1.xMin > t2.xMax + tol or
        t1.yMax + tol < t2.yMin or t1.yMin > t2.yMax + tol):
        return False
        
    for i in range(len(t1.points)-1):
        p1, p2 = t1.points[i], t1.points[i+1]
        for j in range(len(t2.points)-1):
            p3, p4 = t2.points[j], t2.points[j+1]
            if segments_intersect(p1, p2, p3, p4):
                return True
            # 端点距离检查
            if math.dist(p1, p3) < tol or math.dist(p1, p4) < tol or \
               math.dist(p2, p3) < tol or math.dist(p2, p4) < tol:
                return True
    return False

# 判断多边形铺铜区域与线段是否相交
def zone_segment_intersect(zone, p1, p2, track_width, tol=0.01):
    if zone.encircle(p1[0], p1[1]) or zone.encircle(p2[0], p2[1]):
        return True
    for i in range(len(zone.points)):
        p3 = zone.points[i]
        p4 = zone.points[(i+1)%len(zone.points)]
        if segments_intersect(p1, p2, p3, p4):
            return True
    return False

# 判断两个焊盘是否相交，自动区分圆-圆、圆-矩形、矩形-矩形的碰撞情况
def pad_pad_intersect(pad1, pad2, tol=0.01):
    c1 = is_pad_circular(pad1)
    c2 = is_pad_circular(pad2)
    
    if c1 and c2:
        dist = math.dist(pad1.pos, pad2.pos)
        r1 = max(pad1.sizeX, pad1.sizeY) / 2.0
        r2 = max(pad2.sizeX, pad2.sizeY) / 2.0
        return dist <= (r1 + r2 + tol)
    
    elif c1 and not c2:
        r1 = max(pad1.sizeX, pad1.sizeY) / 2.0
        poly = get_pad_corners(pad2, inflate=(r1 + tol))
        return point_in_polygon(pad1.pos, poly)
        
    elif not c1 and c2:
        r2 = max(pad2.sizeX, pad2.sizeY) / 2.0
        poly = get_pad_corners(pad1, inflate=(r2 + tol))
        return point_in_polygon(pad2.pos, poly)
        
    else:
        poly1 = get_pad_corners(pad1, inflate=tol/2.0)
        poly2 = get_pad_corners(pad2, inflate=tol/2.0)
        return polygons_intersect(poly1, poly2)

# 判断焊盘与多边形铺铜区域是否相交
def pad_zone_intersect(pad, zone, tol=0.01):
    if is_pad_circular(pad):
        if zone.encircle(pad.pos[0], pad.pos[1]):
            return True
        pad_r = max(pad.sizeX, pad.sizeY) / 2.0
        for i in range(len(zone.points)):
            p1 = zone.points[i]
            p2 = zone.points[(i+1)%len(zone.points)]
            dist, proj = pointToLineDistance(pad.pos[0], pad.pos[1], p1[0], p1[1], p2[0], p2[1])
            if dist <= pad_r + tol:
                min_x, max_x = min(p1[0], p2[0]), max(p1[0], p2[0])
                min_y, max_y = min(p1[1], p2[1]), max(p1[1], p2[1])
                if min_x - tol <= proj[0] <= max_x + tol and min_y - tol <= proj[1] <= max_y + tol:
                    return True
        return False
    else:
        poly = get_pad_corners(pad, inflate=tol)
        return polygons_intersect(poly, zone.points)

# 网表生成器主类，负责从SprintTextIO提取图形元素并建立连通网表
class NetlistBuilder:
    def __init__(self, textIo):
        self.textIo = textIo
        self.uf = UnionFind()
        self.elements = []
        self.tol = 0.01 # 容差 0.01mm
        
    # 执行网表生成的完整流程，返回包含 networks 和 element映射 的字典
    def build(self):
        # 1. 收集所有相关的导电元素 (仅考虑铜层 C1, C2, I1, I2)
        target_layers = [LAYER_C1, LAYER_C2, LAYER_I1, LAYER_I2]
        all_pads = self.textIo.getPads(layerIdx=target_layers)
        all_tracks = self.textIo.getTracks(layerIdx=target_layers)
        all_zones = [z for z in self.textIo.getPolygons(layerIdx=target_layers) if not z.cutout]
        
        self.elements = all_pads + all_tracks + all_zones
        
        # 预先处理双面焊盘的层级属性 (对于判断是否同一层很有用)
        def on_same_layer(e1, e2):
            e1_layers = [LAYER_C1, LAYER_C2, LAYER_I1, LAYER_I2] if (isinstance(e1, SprintPad) and e1.via) else [e1.layerIdx]
            e2_layers = [LAYER_C1, LAYER_C2, LAYER_I1, LAYER_I2] if (isinstance(e2, SprintPad) and e2.via) else [e2.layerIdx]
            return bool(set(e1_layers) & set(e2_layers))
            
        # 2. 判断两两相交
        n = len(self.elements)
        for i in range(n):
            self.uf.find(id(self.elements[i])) # 初始化节点
            
        for i in range(n):
            e1 = self.elements[i]
            for j in range(i+1, n):
                e2 = self.elements[j]
                
                # 不同层且都不是过孔焊盘，不相连
                if not on_same_layer(e1, e2):
                    continue
                    
                intersect = False
                
                # e1 是 Pad
                if isinstance(e1, SprintPad):
                    if isinstance(e2, SprintPad):
                        intersect = pad_pad_intersect(e1, e2, self.tol)
                    elif isinstance(e2, SprintTrack):
                        for k in range(len(e2.points)-1):
                            if pad_segment_intersect(e1, e2.points[k], e2.points[k+1], e2.width, self.tol):
                                intersect = True
                                break
                    elif isinstance(e2, SprintPolygon):
                        intersect = pad_zone_intersect(e1, e2, self.tol)
                        
                # e1 是 Track
                elif isinstance(e1, SprintTrack):
                    if isinstance(e2, SprintPad):
                        for k in range(len(e1.points)-1):
                            if pad_segment_intersect(e2, e1.points[k], e1.points[k+1], e1.width, self.tol):
                                intersect = True
                                break
                    elif isinstance(e2, SprintTrack):
                        intersect = track_track_intersect(e1, e2, self.tol)
                    elif isinstance(e2, SprintPolygon):
                        for k in range(len(e1.points)-1):
                            if zone_segment_intersect(e2, e1.points[k], e1.points[k+1], e1.width, self.tol):
                                intersect = True
                                break
                                
                # e1 是 Zone
                elif isinstance(e1, SprintPolygon):
                    if isinstance(e2, SprintPad):
                        intersect = pad_zone_intersect(e2, e1, self.tol)
                    elif isinstance(e2, SprintTrack):
                        for k in range(len(e2.points)-1):
                            if zone_segment_intersect(e1, e2.points[k], e2.points[k+1], e2.width, self.tol):
                                intersect = True
                                break
                    elif isinstance(e2, SprintPolygon):
                        # Zone 与 Zone 相交简化处理：检查点是否在另一个Zone内
                        for p in e2.points:
                            if e1.encircle(p[0], p[1]):
                                intersect = True
                                break
                        if not intersect:
                            for p in e1.points:
                                if e2.encircle(p[0], p[1]):
                                    intersect = True
                                    break
                
                if intersect:
                    self.uf.union(id(e1), id(e2))
                    
        # 3. 提取网表
        nets = {} # root_id -> [elements]
        for e in self.elements:
            root = self.uf.find(id(e))
            if root not in nets:
                nets[root] = []
            nets[root].append(e)
            
        result = {
            'nets': [],
            'element_net_map': {}
        }
        
        net_idx = 1
        for root, elems in nets.items():
            # 过滤掉只有单个元素且不是焊盘的网络（可选，为了不生成过多无用网络）
            has_pad = any(isinstance(e, SprintPad) for e in elems)
            if len(elems) == 1 and not has_pad:
                continue
                
            net_info = {
                'number': net_idx,
                'name': f'Net-{net_idx}',
                'elements': elems
            }
            result['nets'].append(net_info)
            for e in elems:
                result['element_net_map'][id(e)] = net_idx
            net_idx += 1
            
        return result
