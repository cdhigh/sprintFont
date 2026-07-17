#!/usr/bin/env python3
# -*- coding:utf-8 -*-
"""Sprint-Layout的PCB导出为立创EDA标准版JSON文件格式
官方JSON格式文档:
<https://docs.easyeda.com/cn/DocumentFormat/EasyEDA-Format-Standard/>
Author: cdhigh <https://github.com/cdhigh>
"""
import datetime, uuid, json
from sprint_struct.sprint_textio import *
from .netlist_builder import NetlistBuilder

def uuid4():
    return "gge" + str(uuid.uuid4().hex[:8])

# 坐标单位换算
# Sprint-Layout 是 mm
# 立创EDA 标准版内部是 10mil (即0.254mm)为1单位
def mm2lceda(value):
    try:
        return round(float(value) / 0.254, 4)
    except:
        return 0

def r2(value):
    try:
        return round(value, 3)
    except:
        return 0

# Sprint层到立创层的映射
sprintToLcedaLayerMap = {
    LAYER_C1: '1',
    LAYER_C2: '2',
    LAYER_S1: '3',
    LAYER_S2: '4',
    LAYER_U: '10',  # 边框层
    LAYER_I1: '21',
    LAYER_I2: '22',
}

class LcedaGenerator:
    def __init__(self, textIo):
        self.textIo = textIo
        self.shapeList = []
        builder = NetlistBuilder(textIo)
        self.netlist = builder.build()

    def generate(self, outputFile):
        #try:
            self.shapeList = []
            self.writeElements()
            
            # 构造完整的 JSON 结构
            lcedaData = {
                "head": {
                    "docType": "3",  # 3是PCB文档
                    "editorVersion": "6.5.57",
                    "newgId": True,
                    "c_para": {},
                    "x": "4000",
                    "y": "3000",
                    "hasIdFlag": True,
                    "importFlag": 0,
                    "transformList": "",
                    "uuid": uuid4()
                },
                "canvas": "CA~1000~1000~#000000~yes~#FFFFFF~10~1000~1000~line~0.5~mil~1~45~visible~0.5~4000~3000~0~yes",
                "shape": self.shapeList,
                "layers": [
                    "1~TopLayer~#FF0000~true~true~true~",
                    "2~BottomLayer~#0000FF~true~false~true~",
                    "3~TopSilkLayer~#FFCC00~true~false~true~",
                    "4~BottomSilkLayer~#66CC33~true~false~true~",
                    "5~TopPasteMaskLayer~#808080~true~false~true~",
                    "6~BottomPasteMaskLayer~#800000~true~false~true~",
                    "7~TopSolderMaskLayer~#800080~true~false~true~0.3",
                    "8~BottomSolderMaskLayer~#AA00FF~true~false~true~0.3",
                    "9~Ratlines~#6464FF~false~false~true~",
                    "10~BoardOutLine~#FF00FF~true~false~true~",
                    "11~Multi-Layer~#C0C0C0~true~false~true~",
                    "12~Document~#FFFFFF~true~false~true~",
                    "13~TopAssembly~#33CC99~false~false~false~",
                    "14~BottomAssembly~#5555FF~false~false~false~",
                    "15~Mechanical~#F022F0~false~false~false~",
                    "19~3DModel~#66CCFF~false~false~false~",
                    "21~Inner1~#999966~false~false~false~~",
                    "22~Inner2~#008000~false~false~false~~",
                    "23~Inner3~#00FF00~false~false~false~~",
                    "24~Inner4~#BC8E00~false~false~false~~",
                    "25~Inner5~#70DBFA~false~false~false~~",
                    "26~Inner6~#00CC66~false~false~false~~",
                    "27~Inner7~#9966FF~false~false~false~~",
                    "28~Inner8~#800080~false~false~false~~",
                    "29~Inner9~#008080~false~false~false~~",
                    "30~Inner10~#15935F~false~false~false~~",
                    "31~Inner11~#000080~false~false~false~~",
                    "32~Inner12~#00B400~false~false~false~~",
                    "33~Inner13~#2E4756~false~false~false~~",
                    "34~Inner14~#99842F~false~false~false~~",
                    "35~Inner15~#FFFFAA~false~false~false~~",
                    "36~Inner16~#99842F~false~false~false~~",
                    "37~Inner17~#2E4756~false~false~false~~",
                    "38~Inner18~#3535FF~false~false~false~~",
                    "39~Inner19~#8000BC~false~false~false~~",
                    "40~Inner20~#43AE5F~false~false~false~~",
                    "41~Inner21~#C3ECCE~false~false~false~~",
                    "42~Inner22~#728978~false~false~false~~",
                    "43~Inner23~#39503F~false~false~false~~",
                    "44~Inner24~#0C715D~false~false~false~~",
                    "45~Inner25~#5A8A80~false~false~false~~",
                    "46~Inner26~#2B937E~false~false~false~~",
                    "47~Inner27~#23999D~false~false~false~~",
                    "48~Inner28~#45B4E3~false~false~false~~",
                    "49~Inner29~#215DA1~false~false~false~~",
                    "50~Inner30~#4564D7~false~false~false~~",
                    "51~Inner31~#6969E9~false~false~false~~",
                    "52~Inner32~#9069E9~false~false~false~~",
                    "99~ComponentShapeLayer~#00CCCC~false~false~false~0.4",
                    "100~LeadShapeLayer~#CC9999~false~false~false~",
                    "101~ComponentMarkingLayer~#66FFCC~false~false~false~",
                    "Hole~Hole~#222222~false~false~true~",
                    "DRCError~DRCError~#FAD609~false~false~true~"
                ],
                "objects": [
                    "All~true~false",
                    "Component~true~true",
                    "Prefix~true~true",
                    "Name~true~false",
                    "Track~true~true",
                    "Pad~true~true",
                    "Via~true~true",
                    "Hole~true~true",
                    "Copper_Area~true~true",
                    "Circle~true~true",
                    "Arc~true~true",
                    "Solid_Region~true~true",
                    "Text~true~true",
                    "Image~true~true",
                    "Rect~true~true",
                    "Dimension~true~true",
                    "Protractor~true~true"
                ],
                "BBox": {
                    "x": 3900,
                    "y": 2900,
                    "width": 200,
                    "height": 200
                },
                "preference": {
                    "hideFootprints": "",
                    "hideNets": ""
                },
                "DRCRULE": {
                    "Default": {
                        "trackWidth": 1,
                        "clearance": 0.6,
                        "viaHoleDiameter": 2.4,
                        "viaHoleD": 1.2
                    },
                    "isRealtime": False,
                    "isDrcOnRoutingOrPlaceVia": False,
                    "checkObjectToCopperarea": True,
                    "showDRCRangeLine": True
                },
                "netColors": {}
            }

            with open(outputFile, 'w', encoding='utf-8') as f:
                json.dump(lcedaData, f, separators=(',', ':'), indent=2)
            return ''
        #except Exception as e:
        #    return str(e)

    def writeElements(self):
        self._processGroup(self.textIo)

    def _processGroup(self, group, centroid=(0,0)):
        for elem in group.elements:
            if isinstance(elem, SprintTrack):
                self._writeTrack(elem, centroid)
            elif isinstance(elem, SprintPad):
                self._writePad(elem, centroid)
            elif isinstance(elem, SprintPolygon):
                self._writeZone(elem, centroid)
            elif isinstance(elem, SprintText):
                self._writeText(elem, centroid)
            elif isinstance(elem, SprintCircle):
                self._writeCircle(elem, centroid)
            elif isinstance(elem, SprintGroup):
                self._processGroup(elem, centroid)
            elif isinstance(elem, SprintComponent):
                self._writeComponent(elem)

    def _writeTrack(self, track, centroid=(0,0)):
        points = track.points
        if len(points) < 2:
            return
        
        layer = sprintToLcedaLayerMap.get(track.layerIdx, '1')
        width = mm2lceda(track.width)
        netNum = self.netlist['element_net_map'].get(id(track), '')
        netName = f"Net-{netNum}" if netNum else ""

        pts = []
        for p in points:
            x, y = mm2lceda(p[0] - centroid[0]), mm2lceda(p[1] - centroid[1])
            # 立创EDA画布原点通常设为 4000, 3000
            pts.extend([str(x + 4000), str(y + 3000)])
            
        pts_str = " ".join(pts)
        shape_str = f"TRACK~{width}~{layer}~{netName}~{pts_str}~{uuid4()}~0"
        self.shapeList.append(shape_str)

    def _writePad(self, pad, centroid=(0,0)):
        # PAD~shape~x~y~width~height~layerid~net~number~holeR~points~rotation~gId~holeLength~slotPointArr~plated~locked
        
        layer = sprintToLcedaLayerMap.get(pad.layerIdx, '1')
        rotation = pad.rotation
        sizeX = mm2lceda(max(pad.sizeX, 0.1))
        sizeY = mm2lceda(max(pad.sizeY, 0.1))
        x = mm2lceda(pad.pos[0] - centroid[0]) + 4000
        y = mm2lceda(pad.pos[1] - centroid[1]) + 3000
        netNum = self.netlist['element_net_map'].get(id(pad), '')
        netName = f"Net-{netNum}" if netNum else ""

        if pad.padType == 'PAD':
            if pad.via:
                layer = '11' # Multi-layer
        
        if pad.form == PAD_FORM_SQUARE:
            shape = "RECT"
        elif pad.form == PAD_FORM_RECT_H:
            shape = "RECT"
            sizeX = mm2lceda(max(pad.sizeX, 0.1) * 2)
        elif pad.form == PAD_FORM_RECT_V:
            shape = "RECT"
            sizeY = mm2lceda(max(pad.sizeY, 0.1) * 2)
        elif pad.form in (PAD_FORM_RECT_ROUND_H, PAD_FORM_RECT_OCTAGON_H):
            shape = "OVAL"
            sizeX = mm2lceda(max(pad.sizeX, 0.1) * 2)
        elif pad.form in (PAD_FORM_RECT_ROUND_V, PAD_FORM_RECT_OCTAGON_V):
            shape = "OVAL"
            sizeY = mm2lceda(max(pad.sizeY, 0.1) * 2)
        else:
            shape = "ELLIPSE"
            
        drill = mm2lceda(pad.drill)
        holeR = drill / 2.0 if drill > 0 else 0

        # 立创EDA和Sprint旋转方向相反
        rotation = (360 - rotation) % 360
        
        plated = "Y" if holeR > 0 and pad.via else "N"
        
        shape_str = f"PAD~{shape}~{r2(x)}~{r2(y)}~{sizeX}~{sizeY}~{layer}~{netName}~1~{holeR}~~{r2(rotation)}~{uuid4()}~0~~{plated}~0"
        self.shapeList.append(shape_str)

    def _writeZone(self, zone, centroid=(0,0)):
        # SOLIDREGION~layerid~net~path~type~gId~locked
        layer = sprintToLcedaLayerMap.get(zone.layerIdx, '1')
        netNum = self.netlist['element_net_map'].get(id(zone), '')
        netName = f"Net-{netNum}" if netNum else ""
        
        pts = []
        for i, p in enumerate(zone.points):
            x, y = mm2lceda(p[0] - centroid[0]) + 4000, mm2lceda(p[1] - centroid[1]) + 3000
            prefix = "M" if i == 0 else "L"
            pts.append(f"{prefix} {r2(x)} {r2(y)}")
        pts.append("Z")
        
        path_str = " ".join(pts)
        reg_type = "cutout" if zone.cutout else "solid"
        
        shape_str = f"SOLIDREGION~{layer}~{netName}~{path_str}~{reg_type}~{uuid4()}~0"
        self.shapeList.append(shape_str)

    def _writeText(self, text, centroid=(0,0), text_type='N'):
        # TEXT~type~x~y~strokeWidth~rotation~mirror~layerid~net~fontSize~text~path
        layer = sprintToLcedaLayerMap.get(text.layerIdx, '3')
        x = mm2lceda(text.pos[0] - centroid[0]) + 4000
        y = mm2lceda(text.pos[1] - centroid[1]) + 3000
        if text.thickness == 0:
            width = 0.08
        elif text.thickness == 2:
            width = 0.22
        else:
            width = 0.16
        strokeWidth = mm2lceda(width)
        rotation = (360 - text.rotation) % 360
        mirror = "1" if text.mirrorH else "0"
        fontSize = mm2lceda(text.height)
        
        # Sprint-Layout text string
        val = text.text.replace('~', '-')
        
        # path留空，立创EDA会自动生成
        shape_str = f"TEXT~{text_type}~{r2(x)}~{r2(y)}~{strokeWidth}~{r2(rotation)}~{mirror}~{layer}~~{fontSize}~{val}~"
        self.shapeList.append(shape_str)

    def _writeCircle(self, circle, centroid=(0,0)):
        # CIRCLE~cx~cy~radius~strokeWidth~layerid~gId~locked
        layer = sprintToLcedaLayerMap.get(circle.layerIdx, '1')
        x = mm2lceda(circle.center[0] - centroid[0]) + 4000
        y = mm2lceda(circle.center[1] - centroid[1]) + 3000
        r = mm2lceda(circle.radius)
        w = mm2lceda(circle.width)
        
        shape_str = f"CIRCLE~{r2(x)}~{r2(y)}~{r}~{w}~{layer}~{uuid4()}~0"
        self.shapeList.append(shape_str)

    def _writeComponent(self, comp):
        # 写入Component作为一个整体 (LIB)
        old_shape_list = self.shapeList
        self.shapeList = []
        
        # 收集组件内部的所有元素
        self._processGroup(comp)
        
        # SprintComponent的idText和valueText不在elements里，需要单独写入
        if hasattr(comp, 'idText') and comp.idText.text:
            self._writeText(comp.idText, text_type='P')
        if hasattr(comp, 'valueText') and comp.valueText.text:
            self._writeText(comp.valueText, text_type='N')
            
        sub_shapes = self.shapeList
        self.shapeList = old_shape_list
        
        if not sub_shapes:
            return
            
        # 确定组件基准点坐标
        x = mm2lceda(comp.pos[0]) + 4000
        y = mm2lceda(comp.pos[1]) + 3000
        
        package = comp.package or "PKG"
        title = comp.compName or "U?"
        
        # 构造attributes字符串
        attr_str = f"package`{package}`title`{title}`"
        
        # 组合LIB头部
        import time
        ts = int(time.time())
        lib_head = f"LIB~{r2(x)}~{r2(y)}~{attr_str}~~~{uuid4()}~1~{uuid.uuid4().hex}~{ts}~0~~yes~~{uuid.uuid4().hex}"
        
        shape_str = lib_head + "#@$" + "#@$".join(sub_shapes)
        self.shapeList.append(shape_str)
