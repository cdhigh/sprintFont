#!/usr/bin/env python3
# -*- coding:utf-8 -*-
"""Sprint-Layout的PCB导出为SVG文件
有什么用?
1. SVG是矢量图形格式,可以直接在浏览器中查看
2. 可以导入到各种设计软件中(Illustrator, Inkscape等)
3. 可以用于文档、演示等
Author: cdhigh <https://github.com/cdhigh>
"""
import math
from sprint_struct.sprint_textio import *

#保留小数位数的同时,能处理一些None或非法值之类的,比{var:.4f}健壮
def r1(value):
    try:
        return round(value, 1)
    except:
        return 0

def r4(value):
    try:
        return round(value, 4)
    except:
        return 0

class SVGGenerator:
    #textIo: SprintTextIO对象
    #layers: 要导出的板层列表, None为所有板层
    #strokeWidth: 线条宽度(用于边框等)
    #mirrorY: 是否镜像Y轴(上下颠倒)
    #layerColors: 各层颜色字典,默认为None时使用标准PCB颜色
    def __init__(self, textIo, layers=None, strokeWidth=0.1, mirrorY=False, layerColors=None):
        self.textIo = textIo
        if not layers or layers < 0:
            self.layers = list(range(1, 8))
        elif isinstance(layers, (list, tuple)):
            self.layers = layers
        else:
            self.layers = (layers,)
        self.strokeWidth = strokeWidth or 0.1
        self.mirrorY = mirrorY
        
        # 默认PCB层颜色 (Sprint-Layout板层: C1, S1, C2, S2, I1, I2, U)
        self.defaultLayerColors = {
            1: '#C87533',  # C1 前铜层 - 铜色
            2: '#333333',  # S1 前丝印层 - 深灰色 (无背景时可见)
            3: '#C87533',  # C2 后铜层 - 铜色
            4: '#333333',  # S2 后丝印层 - 深灰色 (无背景时可见)
            5: '#CD7F32',  # I1 内铜层1 - 深铜色
            6: '#CD7F32',  # I2 内铜层2 - 深铜色
            7: '#000000',  # U 外框层 - 黑色
        }
        self.layerColors = layerColors or self.defaultLayerColors
        
        # 按层分组的图形元素
        self.layerShapes = {layer: [] for layer in self.layers}
        self.drillHoles = []  # 钻孔
        
        # SVG画布边界
        self.minX = float('inf')
        self.minY = float('inf')
        self.maxX = float('-inf')
        self.maxY = float('-inf')

    #导出到SVG的主接口, 失败返回错误信息
    def generate(self, outputFile):
        for pad in self.textIo.getPads(layerIdx=self.layers):
            self.addPad(pad)
            
        for track in self.textIo.getTracks(self.layers):
            self.addTrack(track)
            
        for circle in self.textIo.getCircles(self.layers):
            self.addCircle(circle)
            
        for zone in self.textIo.getPolygons(self.layers):
            self.addPolygon(zone)

        return self.save(outputFile)

    def _transform(self, x, y):
        tx = r4(x)
        ty = r4(self.textIo.yMax - y if self.mirrorY else y)
        return tx, ty
    
    # 更新边界框 - 考虑一个矩形区域
    def _updateBounds(self, cx, cy, halfW, halfH):
        self.minX = min(self.minX, cx - halfW)
        self.minY = min(self.minY, cy - halfH)
        self.maxX = max(self.maxX, cx + halfW)
        self.maxY = max(self.maxY, cy + halfH)

    #添加焊盘
    def addPad(self, pad):
        cx, cy = self._transform(*pad.pos)
        size = r4(pad.size)
        radius = r4(size / 2)
        drill = pad.drill
        layer = pad.layerIdx
        
        # 用于更新边界的半宽和半高
        halfW, halfH = radius, radius
        
        if pad.padType == 'SMDPAD':
            w, h = r4(pad.sizeX), r4(pad.sizeY)
            halfW, halfH = w/2, h/2
            # 贴片焊盘 - 矩形
            shape = f'<rect x="{cx - w/2}" y="{cy - h/2}" width="{w}" height="{h}" stroke="none"'
            if pad.rotation:
                shape += f' transform="rotate({r1(pad.rotation)} {cx} {cy})"'
            shape += '/>'
        elif pad.form == PAD_FORM_OCTAGON:
            # 八角形焊盘
            rOuter = r4(radius / math.cos(math.pi/8))
            halfW = halfH = rOuter
            points = []
            for i in range(8):
                angle = math.radians(22.5 + 45 * i + pad.rotation)
                px = cx + rOuter * math.cos(angle)
                py = cy + rOuter * math.sin(angle)
                points.append(f"{r4(px)},{r4(py)}")
            shape = f'<polygon points="{" ".join(points)}" stroke="none"/>'
        elif pad.form == PAD_FORM_SQUARE:
            # 方形焊盘
            shape = f'<rect x="{cx - size/2}" y="{cy - size/2}" width="{size}" height="{size}" stroke="none"'
            if pad.rotation:
                shape += f' transform="rotate({r1(pad.rotation)} {cx} {cy})"'
            shape += '/>'
        elif pad.form in (PAD_FORM_RECT_ROUND_H, PAD_FORM_RECT_OCTAGON_H, PAD_FORM_RECT_H):
            # 水平矩形焊盘
            w = r4(size * 2)
            h = size
            halfW, halfH = w/2, h/2
            if pad.form == PAD_FORM_RECT_ROUND_H:
                # 圆角矩形
                shape = f'<rect x="{cx - w/2}" y="{cy - h/2}" width="{w}" height="{h}" rx="{radius}" stroke="none"'
            else:
                shape = f'<rect x="{cx - w/2}" y="{cy - h/2}" width="{w}" height="{h}" stroke="none"'
            if pad.rotation:
                shape += f' transform="rotate({r1(pad.rotation)} {cx} {cy})"'
            shape += '/>'
        elif pad.form in (PAD_FORM_RECT_ROUND_V, PAD_FORM_RECT_OCTAGON_V, PAD_FORM_RECT_V):
            # 垂直矩形焊盘
            w = size
            h = r4(size * 2)
            halfW, halfH = w/2, h/2
            if pad.form == PAD_FORM_RECT_ROUND_V:
                # 圆角矩形
                shape = f'<rect x="{cx - w/2}" y="{cy - h/2}" width="{w}" height="{h}" rx="{radius}" stroke="none"'
            else:
                shape = f'<rect x="{cx - w/2}" y="{cy - h/2}" width="{w}" height="{h}" stroke="none"'
            if pad.rotation:
                shape += f' transform="rotate({r1(pad.rotation)} {cx} {cy})"'
            shape += '/>'
        else:
            # 圆形焊盘
            shape = f'<circle cx="{cx}" cy="{cy}" r="{radius}" stroke="none"/>'

        # 更新边界框(考虑旋转的情况,使用外接矩形)
        if pad.rotation and pad.rotation != 0:
            # 旋转后使用对角线长度作为安全边界
            diagonal = math.sqrt(halfW**2 + halfH**2)
            self._updateBounds(cx, cy, diagonal, diagonal)
        else:
            self._updateBounds(cx, cy, halfW, halfH)
        
        self.layerShapes[layer].append(shape)

        # 钻孔
        if drill > 0:
            drillShape = f'<circle cx="{cx}" cy="{cy}" r="{r4(drill / 2)}" fill="white"/>'
            self.drillHoles.append(drillShape)

    #添加导线
    def addTrack(self, track):
        hWidth = r4(max(track.width / 2, 0.01))
        points = [self._transform(p[0], p[1]) for p in track.points]
        if len(points) < 2:
            return
        
        layer = track.layerIdx
        
        # 更新边界框 - 考虑线宽
        for p in points:
            self._updateBounds(p[0], p[1], track.width/2, track.width/2)
        
        # 使用path绘制带线宽的路径
        # 为每段创建一个线段
        for i in range(len(points) - 1):
            p1 = points[i]
            p2 = points[i + 1]
            # 使用line加上stroke-width
            shape = f'<line x1="{p1[0]}" y1="{p1[1]}" x2="{p2[0]}" y2="{p2[1]}" stroke-width="{track.width}" stroke-linecap="round" fill="none"/>'
            self.layerShapes[layer].append(shape)

    #添加圆或圆弧
    def addCircle(self, circle):
        cx, cy = self._transform(circle.center[0], circle.center[1])
        radius = circle.radius
        width = max(circle.width, 0.01)
        rOuter = r4(radius + width / 2)
        rInner = r4(max(radius - width / 2, 0.001))
        layer = circle.layerIdx
        
        # 更新边界框
        self._updateBounds(cx, cy, rOuter, rOuter)

        if circle.fill:  # 实心圆
            shape = f'<circle cx="{cx}" cy="{cy}" r="{rOuter}" stroke="none"/>'
        elif circle.start == circle.stop:  # 圆环
            # 使用path绘制圆环
            shape = (f'<circle cx="{cx}" cy="{cy}" r="{rOuter}" fill="none" '
                    f'stroke-width="{width}"/>')
        else:  # 圆弧
            # 绘制圆弧,使用path的arc命令
            startRad = math.radians(circle.start)
            stopRad = math.radians(circle.stop)
            
            # 外弧起点和终点
            x1Outer = cx + rOuter * math.cos(startRad)
            y1Outer = cy + rOuter * math.sin(startRad)
            x2Outer = cx + rOuter * math.cos(stopRad)
            y2Outer = cy + rOuter * math.sin(stopRad)
            
            # 内弧起点和终点
            x1Inner = cx + rInner * math.cos(stopRad)
            y1Inner = cy + rInner * math.sin(stopRad)
            x2Inner = cx + rInner * math.cos(startRad)
            y2Inner = cy + rInner * math.sin(startRad)
            
            # 判断是否大于180度
            angleDiff = circle.stop - circle.start
            if angleDiff < 0:
                angleDiff += 360
            largeArc = 1 if angleDiff > 180 else 0
            
            # 绘制圆环弧段
            shape = (f'<path d="M {r4(x1Outer)} {r4(y1Outer)} '
                    f'A {rOuter} {rOuter} 0 {largeArc} 1 {r4(x2Outer)} {r4(y2Outer)} '
                    f'L {r4(x1Inner)} {r4(y1Inner)} '
                    f'A {rInner} {rInner} 0 {largeArc} 0 {r4(x2Inner)} {r4(y2Inner)} '
                    f'Z"/>')

        self.layerShapes[layer].append(shape)

    #添加多边形
    def addPolygon(self, zone):
        points = [self._transform(p[0], p[1]) for p in zone.points]
        cleanPoints = self._cleanPolygon(points)
        if len(cleanPoints) < 3:
            return

        layer = zone.layerIdx
        
        # 更新边界框 - 找到所有点的最小/最大范围
        for p in cleanPoints:
            self._updateBounds(p[0], p[1], 0, 0)
        
        # 将点转换为SVG polygon格式
        pointsStr = " ".join([f"{r4(p[0])},{r4(p[1])}" for p in cleanPoints])
        shape = f'<polygon points="{pointsStr}" stroke="none"/>'
        
        self.layerShapes[layer].append(shape)

    #合并非常靠近的点(与OpenSCAD代码相同)
    def _cleanPolygon(self, points):
        if not points:
            return []
        
        def dist_sq(p1, p2):
            return (p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2

        epsilon = 0.001 * 0.001
        merged = [points[0]]
        for p in points[1:]:
            if dist_sq(p, merged[-1]) > epsilon:
                merged.append(p)
        if len(merged) > 1:
            if dist_sq(merged[0], merged[-1]) < epsilon:
                merged.pop()

        if len(merged) < 3:
            return []

        # 循环去噪
        changed = True
        while changed and len(merged) >= 3:
            changed = False
            n = len(merged)
            skip = [False] * n
            
            for i in range(n):
                pPrev = merged[(i - 1) % n]
                pCurr = merged[i]
                
                if dist_sq(pCurr, pPrev) < epsilon:
                    skip[i] = True
                    changed = True
                    continue

                pNext = merged[(i + 1) % n]
                if dist_sq(pPrev, pNext) < epsilon:
                    skip[i] = True
                    changed = True
            
            if changed:
                merged = [merged[i] for i in range(n) if not skip[i]]
                if len(merged) < 3:
                    break
                
        return merged

    def save(self, filename):
        try:
            # 计算画布大小并添加边距
            margin = 5
            if self.minX == float('inf'):  # 没有任何图形
                viewBoxX, viewBoxY = 0, 0
                viewBoxW, viewBoxH = 100, 100
            else:
                viewBoxX = self.minX - margin
                viewBoxY = self.minY - margin
                viewBoxW = self.maxX - self.minX + 2 * margin
                viewBoxH = self.maxY - self.minY + 2 * margin

            with open(filename, 'w', encoding='utf-8') as f:
                # SVG头部
                f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
                f.write(f'<svg xmlns="http://www.w3.org/2000/svg" ')
                f.write(f'viewBox="{r4(viewBoxX)} {r4(viewBoxY)} {r4(viewBoxW)} {r4(viewBoxH)}" ')
                f.write(f'width="{r4(viewBoxW)}mm" height="{r4(viewBoxH)}mm">\n')
                f.write('<!-- Generated by sprintFont -->\n')
                f.write(f'<!-- Stroke width: {self.strokeWidth}mm -->\n\n')
                
                # 背景(可选)
                f.write('<!-- Background -->\n')
                f.write(f'<!-- <rect x="{r4(viewBoxX)}" y="{r4(viewBoxY)}" ')
                f.write(f'width="{r4(viewBoxW)}" height="{r4(viewBoxH)}" ')
                f.write('fill="#1a472a"/> -->\n\n')  # PCB绿色背景
                
                # 按层输出图形
                for layer in self.layers:
                    if not self.layerShapes[layer]:
                        continue
                    
                    color = self.layerColors.get(layer, '#FFFFFF')
                    layerName = self._getLayerName(layer)
                    
                    f.write(f'<!-- Layer: {layerName} -->\n')
                    # 设置fill和stroke，走线和圆环需要stroke，焊盘会设置stroke="none"
                    f.write(f'<g id="layer_{layer}" fill="{color}" stroke="{color}">\n')
                    
                    for shape in self.layerShapes[layer]:
                        f.write(f'  {shape}\n')
                    
                    f.write('</g>\n\n')
                
                # 钻孔
                if self.drillHoles:
                    f.write('<!-- Drill holes -->\n')
                    f.write('<g id="drills">\n')
                    for drill in self.drillHoles:
                        f.write(f'  {drill}\n')
                    f.write('</g>\n\n')
                
                f.write('</svg>\n')
            return ""
        except Exception as e:
            return str(e)

    #Get layer name from Sprint layer index
    def _getLayerName(self, layerIdx):
        return sprintLayerMap.get(layerIdx, f"Layer {layerIdx}")
