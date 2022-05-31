#!/usr/bin/env python
#-*- coding:utf-8 -*-
"""
将kicad的封装库(.kicad_mod)转换为Sprint-Layout的Text-IO格式
封装库格式：https://dev-docs.kicad.org/en/file-formats/sexpr-intro/index.html#_footprint
Author: cdhigh <https://github.com/cdhigh>
"""
import os, sys
from io import StringIO
from fontTools.misc import bezierTools
from sprint_struct.sprint_textio import *
from kicad_pcb.kicad_mod import KicadMod
from comm_utils import str_to_int

#sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'mylib'))
#TEST_FILE = os.path.join(os.path.dirname(__file__), 'ttt.kicad_mod')

#kicad板层和Sprint-Layout板层的对应关系
kicadLayerMap = {
    "*.Cu":    LAYER_C1,
    "F.Cu":    LAYER_C1,
    "F.SilkS": LAYER_S1,
    "B.Cu":    LAYER_C2,
    "B.SilkS": LAYER_S2,
    "F.Fab":   LAYER_U,
    "B.Fab":   LAYER_U,
    "F.CrtYd": LAYER_S1,
    "B.CrtYd": LAYER_S2,
    "F.Paste": LAYER_S1,
    "B.Paste": LAYER_S2,
    "F.Mask":  LAYER_S1,
    "B.Mask":  LAYER_S2,
    "Edge.Cuts": LAYER_U,
    "Margin":  LAYER_U,
    "In1.Cu": LAYER_I1,
    "In2.Cu": LAYER_I2,
}

#kicad焊盘形状和Sprint-Layout的对应关系
kicadPadShapeMap = {
    'circle': PAD_FORM_ROUND,
    'rect': PAD_FORM_SQUARE,
    'oval': PAD_FORM_ROUND,
    'trapezoid': PAD_FORM_SQUARE,
    'roundrect': PAD_FORM_OCTAGON,
    'custom': PAD_FORM_OCTAGON,
}


#输入一个Kicad的封装文件(*.kicad_mod)，返回Sprint-Layout定义的Text-IO
#kicadFile: kicad_mod文件名
#importText: 是否输出文本信息
def kicadModToTextIo(kicadFile: str, importText: int):
    try:
        kicadMod = KicadMod(kicadFile)
    except:
        return None
    
    textIo = SprintTextIO()
    component = SprintComponent()

    #线
    for kiLine in kicadMod.lines:
        layerIdx = kicadLayerMap.get(kiLine['layer'], LAYER_S1)
        if (layerIdx == LAYER_U):
            continue
        kiTra = SprintTrack(layerIdx, kiLine['width'] if kiLine['width'] else 0)
        kiTra.addPoint(kiLine['start']['x'], kiLine['start']['y'])
        kiTra.addPoint(kiLine['end']['x'], kiLine['end']['y'])
        component.add(kiTra)
    
    #多边形
    for kiPoly in kicadMod.polys:
        layerIdx = kicadLayerMap.get(kiPoly['layer'], LAYER_S1)
        if (layerIdx == LAYER_U):
            continue
        polygon = SprintPolygon(layerIdx, kiPoly['width'])
        for pt in kiPoly['points']:
            polygon.addPoint(pt['x'], pt['y'])
        component.add(polygon)
    
    #矩形
    for kiRect in kicadMod.rects:
        layerIdx = kicadLayerMap.get(kiRect['layer'], LAYER_S1)
        if (layerIdx == LAYER_U):
            continue
        polygon = SprintPolygon(layerIdx, kiRect['width'])
        x1 = kiRect["start"]['x']
        y1 = kiRect["start"]['y']
        x2 = kiRect["end"]['x']
        y2 = kiRect["end"]['y']
        polygon.addPoint(x1, y1)
        polygon.addPoint(x2, y1)
        polygon.addPoint(x2, y2)
        polygon.addPoint(x1, y2)
        component.add(polygon)
    
    #焊盘
    for kiPad in kicadMod.pads:
        layers = kiPad['layers']
        if (('F.Cu' in layers) or ('*.Cu' in layers)):
            layerIdx = LAYER_C1
        elif 'B.Cu' in layers:
            layerIdx = LAYER_C2
        else:  #除了两个覆铜层的焊盘外，其他层的忽略（F.Paste F.Mask, B.Paste B.Mask）
            continue
        
        shape = kicadPadShapeMap.get(kiPad['shape'], PAD_FORM_SQUARE)
        
        spPad = SprintPad(layerIdx=layerIdx)
        spPad.pos = (kiPad['pos']['x'], kiPad['pos']['y'])

        #Kicad顺时针为正，Sprint-Layout逆时针为正
        rotation = kiPad['pos']['orientation']
        spPad.rotation = (360 - rotation) if rotation else 0
        
        #spPad.padId = kiPad.name
        #thru_hole/np_thru_hole(内部不镀铜)/smd/connect(smd不镀锡)
        if (kiPad['type'] in ('smd', 'connect')):
            spPad.padType='SMDPAD'
            spPad.sizeX = kiPad['size']['x']
            spPad.sizeY = kiPad['size']['y']
        else:
            spPad.padType='PAD'
            width, height = kiPad['size']['x'], kiPad['size']['y']
            spPad.size = min(width, height)
            if (spPad.size <= 0):
                spPad.size = max(width, height)

            #处理椭圆焊盘，确定是水平还是垂直
            if (kiPad['shape'] == 'oval'):
                #究竟使用圆形焊盘还是长条椭圆焊盘，取决于长轴是否大于短轴的4/3
                if ((width > height) and ((width * 2 / 3) > height)): #水平椭圆焊盘
                    spPad.form = PAD_FORM_RECT_ROUND_H
                elif ((width < height) and ((height * 2 / 3) > width)): #垂直椭圆焊盘
                    spPad.form = PAD_FORM_RECT_ROUND_V
                else: #圆形
                    spPad.form = PAD_FORM_ROUND
            elif (kiPad['shape'] == 'rect'):
                if ((width > height) and ((width * 2 / 3) > height)): #水平矩形焊盘
                    spPad.form = PAD_FORM_RECT_H
                elif ((width < height) and ((height * 2 / 3) > width)): #垂直矩形焊盘
                    spPad.form = PAD_FORM_RECT_V
                else: #正方形
                    spPad.form = PAD_FORM_SQUARE
            else:
                spPad.form = shape

            if (kiPad['type'] == 'thru_hole'): #thru_hole为镀铜过孔，np_thru_hole为不镀铜过孔
                spPad.via = True
        
        if kiPad['drill'] and kiPad['drill']['size']:
            spPad.drill = min(kiPad['drill']['size']['x'], kiPad['drill']['size']['y'])
        else:
            spPad.drill = 0

        #if kiPad['clearance']: #outline / convexhull
        #    spPad.clearance = kiPad['clearance']

        #if 0.0 < spPad.drill <= 0.51: #小于0.51mm的过孔默认盖绿油
        #    spPad.soldermask = False

        component.add(spPad)
    
    #文本
    if importText:
        for kiText in kicadMod.userText:
            #reference(元件编号)/value(元件名称)/user(元件数值)
            if kiText['hide'] or (not kiText['user']) or (kiText['user'] in ('REF**', '%R', 'IC**', '${REFERENCE}')):
                continue
                
            layerIdx = kicadLayerMap.get(kiText['layer'], LAYER_S1)
            spText = SprintText(layerIdx=layerIdx)
            spText.text = str(kiText['user'])
            spText.height = kiText['font']['height']

            #尝试适当调整文本位置，Sprint-Layout都是左对齐的
            #(justify [left | right] [top | bottom] [mirror]
            offsetX = offsetY = 0
            angle = str_to_int(kiText['pos']['orientation'])
            #if (angle == 0): #假定Sprint-Layout的字宽是字高的三分之一
            #    offsetX = -(len(spText.text) * spText.height / 3)
            #    offsetY = spText.height / 3

            spText.pos = ((kiText['pos']['x'] + offsetX), (kiText['pos']['y'] + offsetY))
            #Kicad逆时针旋转为正，Sprint-Layout顺时针旋转为正
            spText.rotation = (360 - angle) if angle else 0
            
            #spText.thickness = 2

            component.add(spText)
    
    #圆形
    for kiCir in kicadMod.circles:
        layerIdx = kicadLayerMap.get(kiCir['layer'], LAYER_S1)
        if (layerIdx == LAYER_U):
            continue
        spCir = SprintCircle(layerIdx=layerIdx)
        spCir.center = (kiCir['center']['x'], kiCir['center']['y'])
        spCir.width = kiCir['width']
        spCir.setRadiusByArcPoint(kiCir['end']['x'], kiCir['end']['y']) #通过end计算半径
        component.add(spCir)
    
    #弧形
    for kiArc in kicadMod.arcs:
        layerIdx = kicadLayerMap.get(kiArc['layer'], LAYER_S1)
        if (layerIdx == LAYER_U):
            continue
        spCir = SprintCircle(layerIdx=layerIdx)
        spCir.width = kiArc['width']
        if kiArc['mid']: #Kicad v6定义
            spCir.center = (kiArc["center"]['x'], kiArc["center"]['y'])
            spCir.radius = kiArc['radius']
        else:
            spCir.setArcByCenterStartAngle(kiArc['start']['x'], kiArc['start']['y'], kiArc['end']['x'], 
                kiArc['end']['y'], kiArc['angle'])
        
        component.add(spCir)

    if component.isValid():
        component.comment = '{}'.format(kicadMod.name)
        textIo.add(component)
        return textIo
    else:
        return None

    #曲线，Kicad使用三阶贝塞尔曲线，将曲线转换为Sprint-Layout的多边形
    bezierSmoothList = (0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9) #曲线分成10份
    for kiCur in kicadMod.curves:
        layerIdx = kicadLayerMap.get(kiCur.layer, LAYER_S1)
        if (layerIdx == LAYER_U):
            continue
        polygon = SprintPolygon(layerIdx, kiCur.width if kiCur.width else 0)
        start = (kiCur.start[0], kiCur.start[-1])
        ctl1 = (kiCur.bezier1[0], kiCur.bezier1[-1])
        ctl2 = (kiCur.bezier2[0], kiCur.bezier2[-1])
        end = (kiCur.end[0], kiCur.end[-1])
        midPoints = [bezierTools.cubicPointAtT(start, ctl1, ctl2, end, i) for i in bezierSmoothList]
        polygon.addPoint(start[0], start[1])
        for (x, y) in midPoints:
            polygon.addPoint(x, y)
        polygon.addPoint(end[0], end[1])
        #反方向再回去
        for (x, y) in midPoints[::-1]:
            polygon.addPoint(x, y)

        component.add(polygon)

    return textIo

