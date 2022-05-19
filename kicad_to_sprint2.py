#!/usr/bin/env python
#-*- coding:utf-8 -*-
"""
将kicad的封装库(.kicad_mod)转换为Sprint-Layout的Text-IO格式
"""
import os, sys
from io import StringIO
from fontTools.misc import bezierTools
from sprint_struct.sprint_textio import *

#sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'mylib'))
#TEST_FILE = os.path.join(os.path.dirname(__file__), 'ttt.kicad_mod')

from pykicad.module import *

#kicad板层和Sprint-Layout板层的对应关系
kicadLayerMap = {
    "*.Cu":    LAYER_C1,
    "F.Cu":    LAYER_C1,
    "F.SilkS": LAYER_S1,
    "B.Cu":    LAYER_C2,
    "B.SilkS": LAYER_S2,
    "F.Fab":   LAYER_S1,
    "B.Fab":   LAYER_S2,
    "F.CrtYd": LAYER_S1,
    "B.CrtYd": LAYER_S2,
    "F.Paste": LAYER_S1,
    "B.Paste": LAYER_S2,
    "F.Mask":  LAYER_S1,
    "B.Mask":  LAYER_S2,
    "Edge.Cuts": LAYER_U,
    "Margin":  LAYER_U,
    "In1.Cu": LAYER_I1,
    "In1.Cu": LAYER_I2,
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


#输入一个Kicad的封装文件(*.kicad_mod)，返回Sprint-Layout定义的Text-IO字符串
#kicadFile: kicad_mod文件名
#importText: 是否输出文本信息
def kicadModToTextIo(kicadFile: str, importText: int):
    sprintTextIo = SprintTextIO(isGroup=True)

    #try:
    kicadMod = Module.from_file(kicadFile)
    #except:
    #    return ''

    #线
    for kiLine in kicadMod.lines:
        layerIdx = kicadLayerMap.get(kiLine.layer, LAYER_S1)
        kiTra = SprintTrack(layerIdx, kiLine.width * 10000 if kiLine.width else 0)
        kiTra.addPoint(kiLine.start[0] * 10000, kiLine.start[-1] * 10000) #Sprint-Layout以0.1微米为单位
        kiTra.addPoint(kiLine.end[0] * 10000, kiLine.end[-1] * 10000)
        sprintTextIo.addTrack(kiTra)

    #多边形
    for kiPoly in kicadMod.polygons:
        layerIdx = kicadLayerMap.get(kiPoly.layer, LAYER_S1)
        polygon = SprintPolygon(layerIdx, kiPoly.width * 10000 if kiPoly.width else 0)
        for (x, y) in kiPoly.pts:
            polygon.addPoint(x * 10000, y * 10000) #Sprint-Layout以0.1微米为单位
        sprintTextIo.addPolygon(polygon)

    #焊盘
    for kiPad in kicadMod.pads:
        if (('F.Cu' in kiPad.layers) or ('*.Cu' in kiPad.layers)):
            layerIdx = LAYER_C1
        elif 'B.Cu' in kiPad.layers:
            layerIdx = LAYER_C2
        else:  #除了两个覆铜层的焊盘外，其他层的忽略（F.Paste F.Mask, B.Paste B.Mask）
            continue
        
        shape = kicadPadShapeMap.get(kiPad.shape, PAD_FORM_SQUARE)
        
        spPad = SprintPad(layerIdx=layerIdx)
        spPad.pos = (kiPad.at[0] * 10000, kiPad.at[1] * 10000)
        if (len(kiPad.at) > 2):
            spPad.rotation = kiPad.at[2] * 100 #Kicad的焊盘旋转角度单位为度，Sprint-Layout的角度单位为0.01度

        #spPad.padId = kiPad.name
        #thru_hole/np_thru_hole(内部不镀铜)/smd/connect(smd不镀锡)
        if (kiPad.type in ('smd', 'connect')):
            spPad.padType='SMDPAD'
            spPad.sizeX = kiPad.size[0] * 10000
            spPad.sizeY = kiPad.size[1] * 10000
        else:
            spPad.padType='PAD'
            width, height = kiPad.size[0], kiPad.size[1]
            spPad.size = min(width, height) * 10000
            if (spPad.size <= 0):
                spPad.size = max(width, height) * 10000

            #处理椭圆焊盘，确定是水平还是垂直
            if (kiPad.shape == 'oval'):
                #究竟使用圆形焊盘还是长条椭圆焊盘，取决于长轴是否大于短轴的4/3
                if ((width > height) and ((width * 2 / 3) > height)): #水平椭圆焊盘
                    spPad.form = PAD_FORM_RECT_ROUND_H
                elif ((width < height) and ((height * 2 / 3) > width)): #垂直椭圆焊盘
                    spPad.form = PAD_FORM_RECT_ROUND_V
                else: #圆形
                    spPad.form = PAD_FORM_ROUND
            elif (kiPad.shape == 'rect'):
                if ((width > height) and ((width * 2 / 3) > height)): #水平矩形焊盘
                    spPad.form = PAD_FORM_RECT_H
                elif ((width < height) and ((height * 2 / 3) > width)): #垂直矩形焊盘
                    spPad.form = PAD_FORM_RECT_V
                else: #正方形
                    spPad.form = PAD_FORM_SQUARE
            else:
                spPad.form = shape

            if (kiPad.type == 'thru_hole'): #thru_hole为镀铜过孔，np_thru_hole为不镀铜过孔
                spPad.via = True

        if (kiPad.drill is not None):
            spPad.drill = (kiPad.drill.size[0] if isinstance(kiPad.drill.size, (tuple, list)) else kiPad.drill.size) * 10000

        if (kiPad.clearance is not None):
            spPad.clearance = kiPad.clearance * 10000

        sprintTextIo.addPad(spPad)

    #文本
    if importText:
        for kiText in kicadMod.texts:
            #reference(元件编号)/value(元件名称)/user(元件数值)
            if kiText.hide or (kiText.type in ('reference', 'user') and (kiText.text in ('REF**', '%R'))):
                continue

            layerIdx = kicadLayerMap.get(kiText.layer, LAYER_S1)
            spText = SprintText(layerIdx=layerIdx)
            spText.text = kiText.text
            spText.height = kiText.size[0] * 10000

            #尝试适当调整文本位置，Sprint-Layout都是左对齐的
            #(justify [left | right] [top | bottom] [mirror]
            offsetX = offsetY = 0
            if (kiText.justify == 'mirror'):
                spText.mirrorH = True
            elif ((kiText.justify is None) and (len(kiText.at) <= 2)): #中心对齐，假定Sprint-Layout的字宽是字高的三分之一
                offsetX = -(len(spText.text) * spText.height / 3)
                offsetY = spText.height / 3

            spText.pos = ((kiText.at[0] * 10000 + offsetX), (kiText.at[1] * 10000 + offsetY))
            if (len(kiText.at) > 2):
                #Kicad的角度单位为1度，Sprint-Layout的文本角度单位为1度
                #Kicad逆时针旋转为正，Sprint-Layout顺时针旋转为正
                spText.rotation = (360 - kiText.at[2])
            
            if (kiText.bold):
                spText.thickness = 2

            sprintTextIo.addText(spText)

    #圆形
    for kiCir in kicadMod.circles:
        layerIdx = kicadLayerMap.get(kiCir.layer, LAYER_S1)
        spCir = SprintCircle(layerIdx=layerIdx)
        spCir.center = (kiCir.center[0] * 10000, kiCir.center[1] * 10000)
        spCir.width = kiCir.width * 10000
        spCir.setRadiusByArcPoint(kiCir.end[0] * 10000, kiCir.end[1] * 10000) #通过end计算半径
        sprintTextIo.addCircle(spCir)

    #弧形
    for kiArc in kicadMod.arcs:
        layerIdx = kicadLayerMap.get(kiArc.layer, LAYER_S1)
        spCir = SprintCircle(layerIdx=layerIdx)
        spCir.width = kiArc.width * 10000
        spCir.setArcByCenterStartAngle(kiArc.start[0] * 10000, kiArc.start[1] * 10000, kiArc.end[0] * 10000, 
            kiArc.end[1] * 10000, kiArc.angle * 1000) #Kicad的圆弧角度单位为1度，Sprint-Layout的圆弧角度单位为0.001度
        
        sprintTextIo.addCircle(spCir)

        #print(str(kiArc))
        #print(type(kiPad.kiArc))

    #曲线，Kicad使用三阶贝塞尔曲线，将曲线转换为Sprint-Layout的多边形
    bezierSmoothList = (0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9) #曲线分成10份
    for kiCur in kicadMod.curves:
        layerIdx = kicadLayerMap.get(kiCur.layer, LAYER_S1)
        polygon = SprintPolygon(layerIdx, kiCur.width * 10000 if kiCur.width else 0)
        start = (kiCur.start[0] * 10000, kiCur.start[-1] * 10000)
        ctl1 = (kiCur.bezier1[0] * 10000, kiCur.bezier1[-1] * 10000)
        ctl2 = (kiCur.bezier2[0] * 10000, kiCur.bezier2[-1] * 10000)
        end = (kiCur.end[0] * 10000, kiCur.end[-1] * 10000)
        midPoints = [bezierTools.cubicPointAtT(start, ctl1, ctl2, end, i) for i in bezierSmoothList]
        polygon.addPoint(start[0], start[1]) #Sprint-Layout以0.1微米为单位
        for (x, y) in midPoints:
            polygon.addPoint(x, y)
        polygon.addPoint(end[0], end[1])
        #反方向再回去
        for (x, y) in midPoints[::-1]:
            polygon.addPoint(x, y)

        sprintTextIo.addPolygon(polygon)

    return str(sprintTextIo)
        

import os
rootDir = r'C:\Program Files\KiCad\share\kicad\modules'
for root, dirs, files in os.walk(rootDir):
    for file in files:
        if file.endswith('.kicad_mod'):
            ffile = os.path.join(root, file)
            try:
                k = kicadModToTextIo(ffile, 1)
                print(file)
            except Exception as e:
                print(str(e))
                print(ffile)
                raise

#kicadModToTextIo(r'C:\Program Files\KiCad\share\kicad\modules\Battery.pretty\BatteryHolder_ComfortableElectronic_CH273-2450_1x2450.kicad_mod', 0)

