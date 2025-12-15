#!/usr/bin/env python3
# -*- coding:utf-8 -*-
"""Sprint-Layout的PCB导出为OpenSCAD文件
有什么用?
1. 使用OpenSCAD可以继续导出为STL, 就可以让3D打印机打印PCB了
2. 可以在其他3D设计软件里面根据电路板布局设计外壳/面板等
3. 可能只是好玩吧, 可以模拟"3D"可视化
Author: cdhigh <https://github.com/cdhigh>
"""
import math
from sprint_struct.sprint_textio import *

#保留小数位数的同时,能处理一些None或非法值之类的,比如{var:.4f}健壮
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

class OpenSCADGenerator:
    #textIo: SprintTextIO对象
    #layers: 要导出的板层列表, None为所有板层
    #thickness: 3D对象的默认厚度
    #mirrorY: 是否镜像Y轴(上下颠倒), 默认镜像是因为OpenSCAD的坐标系和Sprint-Layout不同
    def __init__(self, textIo, layers=None, thickness=0.2, mirrorY=True):
        self.textIo = textIo
        if not layers or layers < 0:
            self.layers = list(range(1, 8))
        elif isinstance(layers, (list, tuple)):
            self.layers = layers
        else:
            self.layers = (layers,)
        self.thickness = thickness or 0.2
        self.mirrorY = mirrorY
        self.positiveShapes = [] #包含焊盘/导线/多边形/圆等(保存2D图形)
        self.negativeShapes = [] #包含钻孔/开窗等
        self.arcRingRequired = False

    #导出到KICAD的主接口, 失败返回错误信息
    def generate(self, outputFile):
        for pad in self.textIo.getPads(layerIdx=self.layers):
            self.addPad(pad)
            
        for track in self.textIo.getTracks(self.layers):
            self.addTrack(track)
            
        for circle in self.textIo.getCircles(self.layers):
            self.addCircle(circle)
            
        for zone in self.textIo.getPolygons(self.layers):
            self.addPolygon(zone)

        #如果U层没有任何元素, 则根据PCB大小创建一个外框
        #if (not self.textIo.getAllElementsInLayer(LAYER_U) and 
        #    self.textIo.pcbWidth and self.textIo.pcbHeight):
        #    points = [(0, 0), (0, r4(self.textIo.pcbHeight)), 
        #        (r4(self.textIo.pcbWidth), r4(self.textIo.pcbHeight)), 
        #        (r4(self.textIo.pcbWidth), 0)]
        #    pointsStr = self._pointsToScadArray(points)
        #    cmd = f"offset(r=0.001) polygon(points={pointsStr});"
        #    self.positiveShapes.append(cmd)
        return self.save(outputFile)

    def _transform(self, x, y):
        return r4(x), r4(self.textIo.yMax - y if self.mirrorY else y)

    #添加焊盘
    def addPad(self, pad):
        cx, cy = self._transform(*pad.pos)
        size = r4(pad.size)
        radius = r4(size / 2)
        rOuter = r4(radius / math.cos(math.pi/8)) #外接圆半径
        drill = pad.drill

        rotCmd = f'rotate({r1(pad.rotation)}) ' if pad.rotation else ''
        
        if pad.padType == 'SMDPAD':
            w, h = r4(pad.sizeX), r4(pad.sizeY)
            shapeCmd = f"translate([{cx}, {cy}, 0]) {rotCmd}square([{w}, {h}], center=true);"
        elif pad.form == PAD_FORM_OCTAGON: #八角形焊盘的半径是内切圆, 需要转换为Openscad的外接圆
            rotCmd = f'rotate({r1(pad.rotation + 22.5)}) ' #默认就需要旋转22.5才能变成X/Y轴不是尖角
            shapeCmd = f"translate([{cx}, {cy}, 0]) {rotCmd}circle(r={rOuter}, $fn=8);"
        elif pad.form == PAD_FORM_SQUARE:
            shapeCmd = f"translate([{cx}, {cy}, 0]) {rotCmd}square([{size}, {size}], center=true);"
        elif pad.form == PAD_FORM_RECT_ROUND_H: #矩形焊盘长宽比例为2
            shapeCmd = (f"translate([{cx}, {cy}, 0]) {rotCmd}"
                f"hull() {{translate([{-radius}, 0, 0]) circle({radius}, $fn=32);translate([{radius}, 0, 0]) circle({radius}, $fn=32);}}")
        elif pad.form == PAD_FORM_RECT_OCTAGON_H:
            shapeCmd = (f"translate([{cx}, {cy}, 0]) {rotCmd}"
                f"hull() {{translate([{-radius}, 0, 0]) rotate(22.5) circle({rOuter}, $fn=8);translate([{radius}, 0, 0]) rotate(22.5) circle({rOuter}, $fn=8);}}")
        elif pad.form == PAD_FORM_RECT_H:
            w, h = r4(size * 2), size
            shapeCmd = f"translate([{cx}, {cy}, 0]) {rotCmd}square([{w}, {h}], center=true);"
        elif pad.form == PAD_FORM_RECT_ROUND_V:
            shapeCmd = (f"translate([{cx}, {cy}, 0]) {rotCmd}"
                f"hull() {{translate([0, {-radius}, 0]) circle({radius}, $fn=32);translate([0, {radius}, 0]) circle({radius}, $fn=32);}}")
        elif pad.form == PAD_FORM_RECT_OCTAGON_V:
            shapeCmd = (f"translate([{cx}, {cy}, 0]) {rotCmd}"
                f"hull() {{translate([0, {-radius}, 0]) rotate(22.5) circle({rOuter}, $fn=8);translate([0, {radius}, 0]) rotate(22.5) circle({rOuter}, $fn=8);}}")
        elif pad.form == PAD_FORM_RECT_V:
            w, h = size, r4(size * 2)
            shapeCmd = f"translate([{cx}, {cy}, 0]) {rotCmd}square([{w}, {h}], center=true);"
        else: #剩下的就是圆形
            shapeCmd = f"translate([{cx}, {cy}, 0]) circle(r={radius}, $fn=32);"

        self.positiveShapes.append(shapeCmd)

        if drill > 0: # 钻孔
            drillCmd = f"translate([{cx}, {cy}, -1]) circle(r={r4(drill / 2)}, $fn=16);"
            self.negativeShapes.append(drillCmd)

    #添加导线
    def addTrack(self, track):
        hWidth = r4(max(track.width / 2, 0.01))
        points = [self._transform(p[0], p[1]) for p in track.points]
        if len(points) < 2:
            return
        
        #要考虑线宽比较麻烦,所以不使用多边形,而是使用hull生成圆角矩形,这样可以自动处理线宽问题
        #这样就假定线头是圆的, 现在忽略线条是平的的情况
        for i in range(len(points) - 1):
            p1 = points[i]
            p2 = points[i + 1]
            
            cmd = (f"hull() {{translate([{p1[0]}, {p1[1]}, 0]) circle(r={hWidth}, $fn=16);"
                f"translate([{p2[0]}, {p2[1]}, 0]) circle(r={hWidth}, $fn=16);}}")

            self.positiveShapes.append(cmd)

    #添加圆或圆弧
    def addCircle(self, circle):
        cx, cy = self._transform(circle.center[0], circle.center[1])
        radius = circle.radius
        width = max(circle.width, 0.01)
        rOuter = r4(radius + width / 2) #外环和内环半径
        rInner = r4(max(radius - width / 2, 0.001))

        if circle.fill: #实心圆
            cmd = f"translate([{cx}, {cy}, 0]) circle(r={rOuter}, $fn=64);"
        elif circle.start == circle.stop:  #圆环
            cmd = (f"translate([{cx}, {cy}, 0]) difference() {{"
                f"circle(r={rOuter}, $fn=64);circle(r={rInner}, $fn=64);}}")
        else:
            cmd = f"arcRing({cx}, {cy}, {r4(radius)}, {r4(width)}, {r1(circle.start)}, {r1(circle.stop)});"
            self.arcRingRequired = True

        #这里不判断cutout属性,因为其他板层的cutout只是禁止铺铜,不影响外形
        #if circle.layerIdx == LAYER_U:
        #    self.negativeShapes.append(cmd)
        #else:
        self.positiveShapes.append(cmd)

    #添加多边形
    def addPolygon(self, zone):
        points = [self._transform(p[0], p[1]) for p in zone.points]
        cleanPoints = self._cleanPolygon(points)
        if len(cleanPoints) < 3:
            return

        pointsStr = self._pointsToScadArray(cleanPoints)
        
        #offset(r=0.001)用于修复多边形的可能的拓扑错误, 比如自相交/重叠边/非流形结构等
        cmd = f"offset(r=0.001) polygon(points={pointsStr});"
        
        #这里不判断cutout属性,因为其他板层的cutout只是禁止铺铜,不影响外形
        #if zone.layerIdx == LAYER_U:
        #     self.negativeShapes.append(cmd)
        #else:
        self.positiveShapes.append(cmd)

    #OpenSCAD画不完整圆环的函数
    def drawArcRing(self):
        return ("\nmodule arcRing(cx, cy, radius, width, start, stop) {\n"
                "    outer = radius + width / 2;\n"
                "    inner = max(0.001, radius - width / 2);\n"
                "    real_stop = (stop < start) ? stop + 360 : stop;\n"
                "    function arcPoints(r, a1, a2, n = 60) =\n"
                "        [ for (i = [0 : n]) let(a = a1 + (a2-a1)*i/n)\n"
                "            [ cx + r*cos(a), cy + r*sin(a) ] ];\n"
                "    polygon( concat(\n"
                "        arcPoints(outer, start, real_stop),\n"
                "        arcPoints(inner, real_stop, start)\n"
                "    ));\n"
                "}\n\n")

    #合并非常靠近的点
    def _cleanPolygon(self, points):
        if not points:
            return []
        
        #使用"距离平方"代替"距离"进行比较，避免使用 math.sqrt
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
            
            # 去尖角 (Spikes) A->B->A
            for i in range(n):
                pPrev = merged[(i - 1) % n]
                pCurr = merged[i]
                
                # 检查1: 是否因为之前的合并导致出现了新的相邻重复点
                if dist_sq(pCurr, pPrev) < epsilon:
                    skip[i] = True
                    changed = True
                    continue

                # 检查2: 尖角检测 (A -> B -> A)
                pNext = merged[(i + 1) % n]
                if dist_sq(pPrev, pNext) < epsilon:
                    skip[i] = True
                    changed = True
            
            if changed:
                merged = [merged[i] for i in range(n) if not skip[i]]
                if len(merged) < 3:
                    break
                
        return merged

    #python点列表转换为OpenSCAD的点列表字符串格式
    def _pointsToScadArray(self, points):
        return "[" + ", ".join([f"[{r4(p[0])}, {r4(p[1])}]" for p in points]) + "]"

    def save(self, filename):
        try:
            with open(filename, 'w') as f:
                f.write("// Generated by sprintFont\n\n")
                #f.write("$fa = 1;\n$fs = 0.4;\n")
                f.write(f"thickness = {self.thickness};\n")
                f.write("pcb_color = [0.2, 0.9, 0.2];\n\n")

                if self.arcRingRequired:
                    f.write(self.drawArcRing())

                f.write("//projection(cut = false) // Uncomment for SVG/PDF export\n")
                f.write("color(pcb_color)\n")
                f.write("linear_extrude(height=thickness) {\n")
                if self.negativeShapes:
                    f.write("    difference() {\n")
                    f.write("        union() {\n")
                    for shape in self.positiveShapes:
                        f.write(f"            {shape}\n")
                    f.write("        }\n")
                    #减去钻孔开窗
                    for shape in self.negativeShapes:
                        f.write(f"        {shape}\n")
                    f.write("    }\n")
                else: #没有钻孔开窗
                    f.write("    union() {\n")
                    for shape in self.positiveShapes:
                        f.write(f"        {shape}\n")
                    f.write("    }\n")
                f.write("}\n")
            return ""
        except Exception as e:
            return str(e)
