#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# Sprint-Layout PCB 导出为 AutoCAD DXF 格式
# 生成标准 ASCII DXF (AutoCAD 2000 / AC1015) 文件
# 可直接导入 AutoCAD, SolidWorks, FreeCAD, Fusion 360, LibreCAD 等 CAD 软件
#Author: cdhigh <https://github.com/cdhigh>

import math
from sprint_struct.sprint_element import *
from sprint_struct.sprint_pad import *
from sprint_struct.sprint_track import SprintTrack
from sprint_struct.sprint_circle import SprintCircle
from sprint_struct.sprint_polygon import SprintPolygon
from sprint_struct.sprint_text import SprintText

#保留4位小数，返回干净的数字表示
def r4(value):
    try:
        val = round(float(value), 4)
        return int(val) if val.is_integer() else val
    except:
        return 0

#保留1位小数
def r1(value):
    try:
        val = round(float(value), 1)
        return int(val) if val.is_integer() else val
    except:
        return 0

#Sprint角度(顺时针为正)转DXF角度(逆时针为正)
def sprintAngleToDxf(angle):
    if not angle:
        return 0
    return r4((360 - angle) % 360)

class DXFGenerator:
    #textIo: SprintTextIO对象
    #layers: 要导出的板层，None或0为所有板层，也可为单个层索引或列表
    #strokeWidth: 默认线宽(mm)
    #mirrorY: 是否镜像Y轴(默认True：Sprint屏幕坐标Y向下，DXF标准笛卡尔坐标Y向上，需镜像以保持正向)
    def __init__(self, textIo, layers=None, strokeWidth=0.1, mirrorY=True):
        self.textIo = textIo
        if not layers or layers < 0:
            self.layers = list(range(1, 8))
        elif isinstance(layers, (list, tuple)):
            self.layers = list(layers)
        else:
            self.layers = [layers]

        self.strokeWidth = strokeWidth or 0.1
        self.mirrorY = mirrorY
        self._handleId = 1

        #计算Y轴翻转参考原点（优先使用PCB实际板高，若无则使用元素最大Y）
        if self.textIo.pcbHeight and self.textIo.pcbHeight > 0:
            self.originY = self.textIo.pcbHeight
        elif self.textIo.yMax != float('-inf'):
            self.originY = self.textIo.yMax
        else:
            self.originY = 0

        #板层名称映射
        self.layerNameMap = {
            LAYER_C1: 'C1',
            LAYER_S1: 'S1',
            LAYER_C2: 'C2',
            LAYER_S2: 'S2',
            LAYER_I1: 'I1',
            LAYER_I2: 'I2',
            LAYER_U:  'U',
        }

        #AutoCAD 颜色索引 (ACI)
        self.layerColorMap = {
            'C1': 1,     # 红色 (前铜)
            'S1': 7,     # 白色 (前丝印)
            'C2': 5,     # 蓝色 (后铜)
            'S2': 2,     # 黄色 (后丝印)
            'I1': 4,     # 青色 (内铜1)
            'I2': 6,     # 洋红 (内铜2)
            'U':  3,     # 绿色 (板框)
            'DRILL': 7,  # 白色 (钻孔)
        }

        #实体收集容器：键为图层名，值为实体DXF字符串列表
        self.entities = []
        self.hasDrillLayer = False

        #边界范围
        self.minX = float('inf')
        self.minY = float('inf')
        self.maxX = float('-inf')
        self.maxY = float('-inf')

    #生成下一个唯一句柄(十六进制字符串)
    def nextHandle(self):
        handle = f"{self._handleId:X}"
        self._handleId += 1
        return handle

    #获取板层名称
    def getLayerName(self, layerIdx):
        return self.layerNameMap.get(layerIdx, f'LAYER_{layerIdx}')

    #坐标转换
    def _transform(self, x, y):
        tx = r4(x)
        ty = r4(self.originY - y if self.mirrorY else y)
        return tx, ty

    #更新边界框
    def _updateBounds(self, x, y):
        self.minX = min(self.minX, x)
        self.minY = min(self.minY, y)
        self.maxX = max(self.maxX, x)
        self.maxY = max(self.maxY, y)

    #导出到DXF主接口，成功返回空字符串，失败返回错误说明
    def generate(self, outputFile):
        try:
            #添加焊盘
            for pad in self.textIo.getPads(layerIdx=self.layers):
                self.addPad(pad)

            #添加导线
            for track in self.textIo.getTracks(self.layers):
                self.addTrack(track)

            #添加圆形与圆弧
            for circle in self.textIo.getCircles(self.layers):
                self.addCircle(circle)

            #添加多边形覆铜
            for zone in self.textIo.getPolygons(self.layers):
                self.addPolygon(zone)

            #添加文本
            for text in self.textIo.getTexts(self.layers):
                self.addText(text)

            #若选择导出板框层(U)但U层没有任何图元，且有PCB板尺寸，则自动生成板框矩形
            if (LAYER_U in self.layers) and (not self.textIo.getAllElementsInLayer(LAYER_U)):
                if self.textIo.pcbWidth and self.textIo.pcbHeight:
                    self.addBoardOutline(self.textIo.pcbWidth, self.textIo.pcbHeight)

            return self.save(outputFile)
        except Exception as e:
            return str(e)

    #添加板框矩形
    def addBoardOutline(self, width, height):
        p0 = self._transform(0, 0)
        p1 = self._transform(width, 0)
        p2 = self._transform(width, height)
        p3 = self._transform(0, height)
        for p in (p0, p1, p2, p3):
            self._updateBounds(p[0], p[1])
        pts = [p0, p1, p2, p3]
        self.addLwpolyline('U', pts, closed=True, width=self.strokeWidth)

    #添加焊盘
    def addPad(self, pad):
        cx, cy = self._transform(*pad.pos)
        size = r4(pad.size)
        radius = r4(size / 2)
        drill = pad.drill
        layerName = self.getLayerName(pad.layerIdx)
        rotDxf = sprintAngleToDxf(pad.rotation)

        targetLayers = [layerName]
        #通孔焊盘若同时导出了正面与背面铜层，两面均添加铜皮
        if (pad.padType == 'PAD' or pad.via):
            if (LAYER_C1 in self.layers) and (LAYER_C2 in self.layers) and (layerName == 'C1'):
                targetLayers.append('C2')

        #钻孔
        if drill > 0:
            self.hasDrillLayer = True
            rDrill = r4(drill / 2)
            self.addCircleEntity('DRILL', cx, cy, rDrill)
            self._updateBounds(cx - rDrill, cy - rDrill)
            self._updateBounds(cx + rDrill, cy + rDrill)

        #不同焊盘形状绘制
        for lyr in targetLayers:
            if pad.padType == 'SMDPAD':
                w, h = r4(pad.sizeX), r4(pad.sizeY)
                self.addRotatedRect(lyr, cx, cy, w, h, rotDxf)
            elif pad.form == PAD_FORM_OCTAGON:
                self.addOctagon(lyr, cx, cy, radius, rotDxf)
            elif pad.form == PAD_FORM_SQUARE:
                self.addRotatedRect(lyr, cx, cy, size, size, rotDxf)
            elif pad.form == PAD_FORM_RECT_H:
                self.addRotatedRect(lyr, cx, cy, size * 2, size, rotDxf)
            elif pad.form == PAD_FORM_RECT_V:
                self.addRotatedRect(lyr, cx, cy, size, size * 2, rotDxf)
            elif pad.form == PAD_FORM_RECT_ROUND_H:
                self.addObroundH(lyr, cx, cy, radius, rotDxf)
            elif pad.form == PAD_FORM_RECT_ROUND_V:
                self.addObroundV(lyr, cx, cy, radius, rotDxf)
            elif pad.form == PAD_FORM_RECT_OCTAGON_H:
                self.addChamferedRect(lyr, cx, cy, size * 2, size, rotDxf)
            elif pad.form == PAD_FORM_RECT_OCTAGON_V:
                self.addChamferedRect(lyr, cx, cy, size, size * 2, rotDxf)
            else:
                #圆形焊盘
                self.addCircleEntity(lyr, cx, cy, radius)
                self._updateBounds(cx - radius, cy - radius)
                self._updateBounds(cx + radius, cy + radius)

    #添加带旋转角度的矩形闭合折线
    def addRotatedRect(self, layer, cx, cy, w, h, rotDeg):
        hw, hh = w / 2, h / 2
        pts = [(-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh)]
        ptsRotated = [self._rotatePoint(px, py, rotDeg, cx, cy) for (px, py) in pts]
        for p in ptsRotated:
            self._updateBounds(p[0], p[1])
        self.addLwpolyline(layer, ptsRotated, closed=True)

    #添加八角形焊盘
    def addOctagon(self, layer, cx, cy, radius, rotDeg):
        rOuter = radius / math.cos(math.pi / 8)
        pts = []
        for i in range(8):
            angle = math.radians(22.5 + 45 * i)
            px = rOuter * math.cos(angle)
            py = rOuter * math.sin(angle)
            pts.append(self._rotatePoint(px, py, rotDeg, cx, cy))
        for p in pts:
            self._updateBounds(p[0], p[1])
        self.addLwpolyline(layer, pts, closed=True)

    #添加水平圆角矩形(跑道型)焊盘
    #两端为半圆弧，利用LWPOLYLINE凸度(bulge=1.0表示180度逆时针圆弧)
    def addObroundH(self, layer, cx, cy, radius, rotDeg):
        p0 = (-radius, radius)
        p1 = (radius, radius)
        p2 = (radius, -radius)
        p3 = (-radius, -radius)
        rp0 = self._rotatePoint(p0[0], p0[1], rotDeg, cx, cy)
        rp1 = self._rotatePoint(p1[0], p1[1], rotDeg, cx, cy)
        rp2 = self._rotatePoint(p2[0], p2[1], rotDeg, cx, cy)
        rp3 = self._rotatePoint(p3[0], p3[1], rotDeg, cx, cy)
        for p in (rp0, rp1, rp2, rp3):
            self._updateBounds(p[0], p[1])
        #点序 rp1 -> rp0 -> rp3 -> rp2:
        #从 rp1 沿直线到 rp0 (bulge=0)
        #从 rp0 沿半圆到 rp3 (逆时针半圆 bulge=1.0)
        #从 rp3 沿直线到 rp2 (bulge=0)
        #从 rp2 沿半圆到 rp1 (逆时针半圆 bulge=1.0)
        verticesWithBulge = [
            (rp1[0], rp1[1], 0.0),
            (rp0[0], rp0[1], 1.0),
            (rp3[0], rp3[1], 0.0),
            (rp2[0], rp2[1], 1.0),
        ]
        self.addLwpolylineWithBulge(layer, verticesWithBulge, closed=True)

    #添加垂直圆角矩形(跑道型)焊盘
    def addObroundV(self, layer, cx, cy, radius, rotDeg):
        p0 = (radius, -radius)
        p1 = (radius, radius)
        p2 = (-radius, radius)
        p3 = (-radius, -radius)
        rp0 = self._rotatePoint(p0[0], p0[1], rotDeg, cx, cy)
        rp1 = self._rotatePoint(p1[0], p1[1], rotDeg, cx, cy)
        rp2 = self._rotatePoint(p2[0], p2[1], rotDeg, cx, cy)
        rp3 = self._rotatePoint(p3[0], p3[1], rotDeg, cx, cy)
        for p in (rp0, rp1, rp2, rp3):
            self._updateBounds(p[0], p[1])
        #点序 rp0 -> rp1 -> rp2 -> rp3:
        #从 rp0 沿直线到 rp1 (bulge=0)
        #从 rp1 沿半圆到 rp2 (逆时针半圆 bulge=1.0)
        #从 rp2 沿直线到 rp3 (bulge=0)
        #从 rp3 沿半圆到 rp0 (逆时针半圆 bulge=1.0)
        verticesWithBulge = [
            (rp0[0], rp0[1], 0.0),
            (rp1[0], rp1[1], 1.0),
            (rp2[0], rp2[1], 0.0),
            (rp3[0], rp3[1], 1.0),
        ]
        self.addLwpolylineWithBulge(layer, verticesWithBulge, closed=True)

    #添加倒角矩形焊盘
    def addChamferedRect(self, layer, cx, cy, w, h, rotDeg):
        hw, hh = w / 2, h / 2
        c = min(hw, hh) * 0.4142
        pts = [
            (hw - c, hh),
            (-hw + c, hh),
            (-hw, hh - c),
            (-hw, -hh + c),
            (-hw + c, -hh),
            (hw - c, -hh),
            (hw, -hh + c),
            (hw, hh - c),
        ]
        ptsRotated = [self._rotatePoint(px, py, rotDeg, cx, cy) for (px, py) in pts]
        for p in ptsRotated:
            self._updateBounds(p[0], p[1])
        self.addLwpolyline(layer, ptsRotated, closed=True)

    #二维点旋转并平移
    def _rotatePoint(self, x, y, angleDeg, cx=0, cy=0):
        if not angleDeg:
            return r4(cx + x), r4(cy + y)
        rad = math.radians(angleDeg)
        cosA = math.cos(rad)
        sinA = math.sin(rad)
        rx = x * cosA - y * sinA
        ry = x * sinA + y * cosA
        return r4(cx + rx), r4(cy + ry)

    #添加导线
    def addTrack(self, track):
        if len(track.points) < 2:
            return
        layerName = self.getLayerName(track.layerIdx)
        points = [self._transform(p[0], p[1]) for p in track.points]
        for p in points:
            self._updateBounds(p[0], p[1])
        trackWidth = r4(track.width)
        self.addLwpolyline(layerName, points, closed=False, width=trackWidth)

    #添加圆或圆弧
    def addCircle(self, circle):
        cx, cy = self._transform(circle.center[0], circle.center[1])
        radius = r4(circle.radius)
        layerName = self.getLayerName(circle.layerIdx)

        self._updateBounds(cx - radius, cy - radius)
        self._updateBounds(cx + radius, cy + radius)

        if circle.start == circle.stop:
            #完整圆
            self.addCircleEntity(layerName, cx, cy, radius)
            #若是开孔，钻孔层也添加
            if circle.cutout:
                self.hasDrillLayer = True
                self.addCircleEntity('DRILL', cx, cy, radius)
        else:
            #圆弧
            startAng = r1(circle.start)
            stopAng = r1(circle.stop)
            if self.mirrorY:
                startAng, stopAng = (360 - stopAng) % 360, (360 - startAng) % 360
            self.addArcEntity(layerName, cx, cy, radius, startAng, stopAng)

    #添加多边形
    def addPolygon(self, zone):
        if len(zone.points) < 3:
            return
        layerName = self.getLayerName(zone.layerIdx)
        points = [self._transform(p[0], p[1]) for p in zone.points]
        cleanPoints = self._cleanPolygon(points)
        if len(cleanPoints) < 3:
            return
        for p in cleanPoints:
            self._updateBounds(p[0], p[1])
        self.addLwpolyline(layerName, cleanPoints, closed=True, width=r4(zone.width))

    #添加文本
    def addText(self, text):
        if not text.text or not text.isValid() or not getattr(text, 'visible', True):
            return
        cx, cy = self._transform(text.pos[0], text.pos[1])
        layerName = self.getLayerName(text.layerIdx)
        height = r4(text.height)
        rotDxf = sprintAngleToDxf(text.rotation)

        self._updateBounds(cx, cy)
        mirrorH = bool(getattr(text, 'mirrorH', False))
        self.addTextEntity(layerName, cx, cy, height, text.text, rotDxf, mirrorH=mirrorH)

    #多边形点集清洗
    def _cleanPolygon(self, points):
        if not points:
            return []
        epsilon = 0.0001
        merged = [points[0]]
        for p in points[1:]:
            if (p[0] - merged[-1][0]) ** 2 + (p[1] - merged[-1][1]) ** 2 > epsilon:
                merged.append(p)
        if len(merged) > 1 and ((merged[0][0] - merged[-1][0]) ** 2 + (merged[0][1] - merged[-1][1]) ** 2 <= epsilon):
            merged.pop()
        return merged if len(merged) >= 3 else []

    #输出 LWPOLYLINE 实体
    def addLwpolyline(self, layer, points, closed=False, width=0):
        handle = self.nextHandle()
        flag = 1 if closed else 0
        lines = [
            '0', 'LWPOLYLINE',
            '5', handle,
            '8', layer,
            '100', 'AcDbEntity',
            '100', 'AcDbPolyline',
            '90', str(len(points)),
            '70', str(flag),
        ]
        if width > 0:
            lines.extend(['43', str(width)])
        for p in points:
            lines.extend(['10', str(p[0]), '20', str(p[1])])
        self.entities.append('\n'.join(lines))

    #输出带 Bulge 凸度的 LWPOLYLINE 实体
    def addLwpolylineWithBulge(self, layer, verticesWithBulge, closed=True, width=0):
        handle = self.nextHandle()
        flag = 1 if closed else 0
        lines = [
            '0', 'LWPOLYLINE',
            '5', handle,
            '8', layer,
            '100', 'AcDbEntity',
            '100', 'AcDbPolyline',
            '90', str(len(verticesWithBulge)),
            '70', str(flag),
        ]
        if width > 0:
            lines.extend(['43', str(width)])
        for v in verticesWithBulge:
            lines.extend(['10', str(v[0]), '20', str(v[1])])
            if len(v) >= 3 and v[2] != 0.0:
                lines.extend(['42', str(r4(v[2]))])
        self.entities.append('\n'.join(lines))

    #输出 CIRCLE 实体
    def addCircleEntity(self, layer, cx, cy, radius):
        handle = self.nextHandle()
        lines = [
            '0', 'CIRCLE',
            '5', handle,
            '8', layer,
            '100', 'AcDbEntity',
            '100', 'AcDbCircle',
            '10', str(cx),
            '20', str(cy),
            '30', '0.0',
            '40', str(radius),
        ]
        self.entities.append('\n'.join(lines))

    #输出 ARC 实体
    def addArcEntity(self, layer, cx, cy, radius, startAngle, stopAngle):
        handle = self.nextHandle()
        lines = [
            '0', 'ARC',
            '5', handle,
            '8', layer,
            '100', 'AcDbEntity',
            '100', 'AcDbCircle',
            '10', str(cx),
            '20', str(cy),
            '30', '0.0',
            '40', str(radius),
            '100', 'AcDbArc',
            '50', str(startAngle),
            '51', str(stopAngle),
        ]
        self.entities.append('\n'.join(lines))

    #输出 TEXT 实体
    def addTextEntity(self, layer, cx, cy, height, textStr, rotation=0, mirrorH=False):
        handle = self.nextHandle()
        cleanStr = textStr.replace('\r', '').replace('\n', ' ')
        lines = [
            '0', 'TEXT',
            '5', handle,
            '8', layer,
            '100', 'AcDbEntity',
            '100', 'AcDbText',
            '10', str(cx),
            '20', str(cy),
            '30', '0.0',
            '40', str(height),
            '1', cleanStr,
            '100', 'AcDbText',
        ]
        if rotation:
            lines.extend(['50', str(rotation)])
        if mirrorH:
            lines.extend(['71', '2'])
        self.entities.append('\n'.join(lines))

    #保存为标准 DXF 文件
    def save(self, filename):
        minX = self.minX if self.minX != float('inf') else 0.0
        minY = self.minY if self.minY != float('inf') else 0.0
        maxX = self.maxX if self.maxX != float('-inf') else 100.0
        maxY = self.maxY if self.maxY != float('-inf') else 100.0

        #需要包含的图层名列表
        activeLayerNames = [self.getLayerName(lyr) for lyr in self.layers]
        if self.hasDrillLayer and ('DRILL' not in activeLayerNames):
            activeLayerNames.append('DRILL')

        lines = []

        #HEADER 段
        lines.extend([
            '0', 'SECTION',
            '2', 'HEADER',
            '9', '$ACADVER',
            '1', 'AC1015',
            '9', '$HANDSEED',
            '5', f"{self._handleId + 100:X}",
            '9', '$MEASUREMENT',
            '70', '1',          # 公制单位
            '9', '$INSUNITS',
            '70', '4',          # 毫米(mm)
            '9', '$EXTMIN',
            '10', str(minX),
            '20', str(minY),
            '30', '0.0',
            '9', '$EXTMAX',
            '10', str(maxX),
            '20', str(maxY),
            '30', '0.0',
            '0', 'ENDSEC',
        ])

        #TABLES 段
        lines.extend([
            '0', 'SECTION',
            '2', 'TABLES',
            #线型表
            '0', 'TABLE',
            '2', 'LTYPE',
            '5', self.nextHandle(),
            '100', 'AcDbSymbolTable',
            '70', '1',
            '0', 'LTYPE',
            '5', self.nextHandle(),
            '100', 'AcDbSymbolTableRecord',
            '100', 'AcDbLinetypeTableRecord',
            '2', 'CONTINUOUS',
            '70', '0',
            '3', 'Solid line',
            '72', '65',
            '73', '0',
            '40', '0.0',
            '0', 'ENDTAB',
            #图层表
            '0', 'TABLE',
            '2', 'LAYER',
            '5', self.nextHandle(),
            '100', 'AcDbSymbolTable',
            '70', str(len(activeLayerNames)),
        ])

        for lyrName in activeLayerNames:
            color = self.layerColorMap.get(lyrName, 7)
            lines.extend([
                '0', 'LAYER',
                '5', self.nextHandle(),
                '100', 'AcDbSymbolTableRecord',
                '100', 'AcDbLayerTableRecord',
                '2', lyrName,
                '70', '0',
                '62', str(color),
                '6', 'CONTINUOUS',
            ])

        lines.extend([
            '0', 'ENDTAB',
            '0', 'ENDSEC',
        ])

        #BLOCKS 段
        lines.extend([
            '0', 'SECTION',
            '2', 'BLOCKS',
            '0', 'ENDSEC',
        ])

        #ENTITIES 段
        lines.extend([
            '0', 'SECTION',
            '2', 'ENTITIES',
        ])

        for ent in self.entities:
            lines.append(ent)

        lines.extend([
            '0', 'ENDSEC',
            '0', 'EOF',
        ])

        content = '\n'.join(lines) + '\n'
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)

        return ''
