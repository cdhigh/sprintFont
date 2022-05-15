#!/usr/bin/env python
#-*- coding:utf-8 -*-
"""
将kicad的封装库(.kicad_mod)转换为Sprint-Layout的Text-IO格式
"""
import os, sys
from sprint_struct.sprint_textio import *

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'mylib'))
TEST_FILE = os.path.join(os.path.dirname(__file__), 'ttt.kicad_mod')

from pykicad.module import *

#kicad板层和Sprint-Layout板层的对应关系
kicadLayerMap = {
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
    'oval': PAD_FORM_OCTAGON,
    'trapezoid': PAD_FORM_SQUARE,
    'roundrect': PAD_FORM_RECT_ROUND_H,
    'custom': PAD_FORM_ROUND,
}


def kicadModToTextIo(kicadFile: str):
    sprintTextIo = SprintTextIO()

    try:
        kicadMod = Module.from_file(kicadFile)
    except:
        return ''

    #线和多边形
    #因为Sprint-Layout没有Line对象，所以Kicad的Line对象转换为多边形
    for line in kicadMod.lines:
        layerIdx = kicadLayerMap.get(line.layer, LAYER_S1)
        polygon = SprintPolygon(layerIdx, line.width * 10000 if line.width else 0)
        polygon.addPoint(line.start[0] * 10000, line.start[-1] * 10000) #Sprint-Layout以0.1微米为单位
        polygon.addPoint(line.end[0] * 10000, line.end[-1] * 10000)
        sprintTextIo.addPolygon(polygon)

    #焊盘
    for kiPad in kicadMod.pads:
        layerIdx = kicadLayerMap.get(kiPad.layers[0], LAYER_C1)
        shape = kicadPadShapeMap.get(kiPad.shape, PAD_FORM_SQUARE)
        
        #thru_hole/smd/connect/np_thru_hole
        spPad = SprintPad(layerIdx=layerIdx)
        spPad.pos = (kiPad.at[0] * 10000, kiPad.at[1] * 10000)

        #spPad.padId = kiPad.name
        if (kiPad.type == 'smd'):
            spPad.padType='SMDPAD'
            spPad.sizeX = kiPad.size[0] * 10000
            spPad.sizeY = kiPad.size[1] * 10000
        else:
            spPad.padType='PAD'
            spPad.form = shape
            spPad.size = kiPad.size[0] * 10000

        if (kiPad.drill is not None):
            spPad.drill = kiPad.drill.size * 10000

        sprintTextIo.addPad(spPad)

    #文本
    for kiText in kicadMod.texts:
        layerIdx = kicadLayerMap.get(kiText.layer, LAYER_S1)
        spText = SprintText(layerIdx=layerIdx)
        spText.text = kiText.text
        spText.pos = (kiText.at[0] * 10000, kiText.at[1] * 10000)
        spText.height = kiText.size[0] * 10000
        if (kiText.bold):
            spText.thickness = 2

        sprintTextIo.addText(spText)

    #圆形
    for kiCir in kicadMod.circles:
        layerIdx = kicadLayerMap.get(kiCir.layer, LAYER_S1)
        spCir = SprintCircle(layerIdx=layerIdx)
        spCir.center = (kiCir.center[0] * 10000, kiCir.center[1] * 10000)
        spCir.width = kiCir.width * 10000
        spCir.setRadiusByArcPoint(kiCir.end[0] * 10000, kiCir.end[1] * 10000)
        sprintTextIo.addCircle(spCir)

        #print(str(kiCir))
        #print(type(kiPad.kiCir))

    return str(sprintTextIo)
        

#kicadModToTextIo(r'D:\电子类\Soft\Sprint-Layout 6.0\sprintFont\test.kicad_mod')

