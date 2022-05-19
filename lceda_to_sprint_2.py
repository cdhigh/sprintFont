#!/usr/bin/env python
#-*- coding:utf-8 -*-
"""
将力创的封装库转换为Sprint-Layout的Text-IO格式
"""
import os, sys, tempfile, json
from fontTools.misc import bezierTools
from sprint_struct.sprint_textio import *
from sprint_struct.font_to_polygon import str_to_int, str_to_float
#sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'mylib'))
#TEST_FILE = os.path.join(os.path.dirname(__file__), 'ttt.kicad_mod')
from easyeda2kicad.easyeda.easyeda_api import easyeda_api
from easyeda2kicad.easyeda.easyeda_importer import easyeda_footprint_importer
from easyeda2kicad.kicad.export_kicad_footprint import exporter_footprint_kicad, compute_arc, rotate

#力创板层和Sprint-Layout板层的对应关系
lcLayerMap = {
    1:  LAYER_C1,
    2:  LAYER_C2,
    3:  LAYER_S1,
    4:  LAYER_S2,
    5:  LAYER_S1, #F.Paste
    6:  LAYER_S2, #B.Paste
    7:  LAYER_S1, #F.Mask
    8:  LAYER_S2, #B.Mask
    10: LAYER_U,  #Edge.Cuts
    11: LAYER_U,  #Edge.Cuts
    12: LAYER_U,  #Cmts.User
    13: LAYER_U,  #F.Fab
    14: LAYER_U,  #B.Fab
    15: LAYER_U,  #Dwgs.User
    21: LAYER_I1,
    22: LAYER_I2,
    101: LAYER_U,  #F.Fab
}

#力创焊盘形状和Sprint-Layout的对应关系
lcPadShapeMap = {
    'ELLIPSE': PAD_FORM_ROUND,
    'RECT': PAD_FORM_SQUARE,
    'OVAL': PAD_FORM_ROUND,
    'POLYGON': PAD_FORM_OCTAGON,
}

#判断是否是力创EDA的组件ID，为字母C+4个数字
def isLcedaComponent(txt: str):
    if ((len(txt) < 5) or (not txt.startswith(('C', 'c')))):
        return False

    for ch in txt[1:]:
        if not ch.isdigit():
            return False

    return True

def convert_to_mm(dim: float):
    return round(float(dim) * 10 * 0.0254, 2)

#输入一个力创的封装ID(以C开头，后接几位数字)或本地的json文件，返回Sprint-Layout定义的Text-IO字符串
#lcIdOrFile: 力创的封装ID(以C开头，后接几位数字)或本地的json文件
#importText: 是否输出文本信息
def lcFootprintToTextIo(lcIdOrFile: str, importText: int):
    cadData = None
    try:
        if (isLcedaComponent(lcIdOrFile)):
            api = easyeda_api()
            cadData = api.get_cad_data_of_component(lcsc_id=lcIdOrFile.upper())
        else: #文件
            with open(lcIdOrFile, 'r', encoding='utf-8') as f:
                lcJsonData = json.loads(f.read())

            if isinstance(lcJsonData, dict):
                cadData = lcJsonData.get('result', '')
    except Exception as e:
        print(str(e))
        return ''

    if not cadData:
        return ''

    importer = easyeda_footprint_importer(easyeda_cp_cad_data=cadData)
    lcFp = importer.get_footprint()

    #开始生成Sprint-Layout的TextIO对象
    sprintTextIo = SprintTextIO(isGroup=True)

    #英寸转换为mm单位
    lcFp.bbox.convert_to_mm()

    for fields in (lcFp.pads, lcFp.tracks, lcFp.holes, lcFp.circles, lcFp.rectangles, lcFp.texts):
        for field in fields:
            field.convert_to_mm()

    #焊盘
    for lcPad in lcFp.pads:
        layerIdx = lcLayerMap.get(lcPad.layer_id, LAYER_U)
        #除了两个覆铜层的焊盘外，其他层的忽略（F.Paste F.Mask, B.Paste B.Mask）
        if layerIdx not in (LAYER_C1, LAYER_C2):
            continue
        
        shape = lcPadShapeMap.get(lcPad.shape, PAD_FORM_SQUARE)
        
        spPad = SprintPad(layerIdx=layerIdx)
        spPad.pos = ((lcPad.center_x - lcFp.bbox.x) * 10000, (lcPad.center_y - lcFp.bbox.y) * 10000)
        spPad.rotation = lcPad.rotation * 100 #力创的焊盘旋转角度单位为度，Sprint-Layout的角度单位为0.01度

        #spPad.padId = lcPad.name
        #thru_hole/np_thru_hole(内部不镀铜)/smd/connect(smd不镀锡)
        if (lcPad.hole_radius <= 0):
            spPad.padType='SMDPAD'
            spPad.sizeX = (max(lcPad.width, 0.01)) * 10000
            spPad.sizeY = (max(lcPad.height, 0.01)) * 10000
        else:
            spPad.padType='PAD'
            spPad.via = True #默认全部为镀铜过孔
            width, height = lcPad.width, lcPad.height
            spPad.size = min(width, height) * 10000
            if (spPad.size <= 0):
                spPad.size = max(width, height) * 10000

            #处理椭圆焊盘，确定是水平还是垂直
            if (lcPad.shape in ('ELLIPSE', 'OVAL')):
                #究竟使用圆形焊盘还是长条椭圆焊盘，取决于长轴是否大于短轴的4/3
                if ((width > height) and ((width * 2 / 3) > height)): #水平椭圆焊盘
                    spPad.form = PAD_FORM_RECT_ROUND_H
                elif ((width < height) and ((height * 2 / 3) > width)): #垂直椭圆焊盘
                    spPad.form = PAD_FORM_RECT_ROUND_V
                else: #圆形
                    spPad.form = PAD_FORM_ROUND
            elif (lcPad.shape == 'RECT'):
                if ((width > height) and ((width * 2 / 3) > height)): #水平矩形焊盘
                    spPad.form = PAD_FORM_RECT_H
                elif ((width < height) and ((height * 2 / 3) > width)): #垂直矩形焊盘
                    spPad.form = PAD_FORM_RECT_V
                else: #正方形
                    spPad.form = PAD_FORM_SQUARE
            else:
                spPad.form = shape

            spPad.drill = (lcPad.hole_radius * 2) * 10000 #转成直径
        
        sprintTextIo.addPad(spPad)

    #力创的洞转换为内外径一样的焊盘
    for lcHole in lcFp.holes:
        spPad = SprintPad(layerIdx=LAYER_C1)
        spPad.pos = ((lcPad.center_x - lcFp.bbox.x) * 10000, (lcPad.center_y - lcFp.bbox.y) * 10000)
        spPad.padType='PAD'
        spPad.form = PAD_FORM_ROUND
        spPad.size = lcHole.radius * 2 * 10000 #转成直径
        spPad.drill = spPad.size
        sprintTextIo.addPad(spPad)

    #连线
    for lcLine in lcFp.tracks:
        layerIdx = lcLayerMap.get(lcLine.layer_id, LAYER_S1)
        kiTra = SprintTrack(layerIdx, lcLine.stroke_width * 10000 if lcLine.stroke_width else 0)
        
        pts = [convert_to_mm(point) for point in lcLine.points.split(" ")]
        for i in range(0, len(pts) - 2, 2):
            kiTra.addPoint((round(pts[i] - lcFp.bbox.x, 2)) * 10000, (round(pts[i + 1] - lcFp.bbox.y, 2)) * 10000)
            kiTra.addPoint((round(pts[i + 2] - lcFp.bbox.x, 2)) * 10000, (round(pts[i + 3] - lcFp.bbox.y, 2)) * 10000)

        sprintTextIo.addTrack(kiTra)

    #圆形
    for lcCir in lcFp.circles:
        layerIdx = lcLayerMap.get(lcCir.layer_id, LAYER_S1)
        spCir = SprintCircle(layerIdx=layerIdx)
        spCir.center = ((lcCir.cx - lcFp.bbox.x) * 10000, (lcCir.cy - lcFp.bbox.y) * 10000)
        spCir.width = lcCir.stroke_width * 10000
        spCir.radius = lcCir.radius
        sprintTextIo.addCircle(spCir)
        
    #矩形，转换为四个点的多边形(填充)/四根直线（不填充）
    for lcRect in lcFp.rectangles:
        layerIdx = lcLayerMap.get(lcRect.layer_id, LAYER_S1)

        x1 = (lcRect.x - lcFp.bbox.x) * 10000
        y1 = (lcRect.y - lcFp.bbox.y) * 10000
        width = lcRect.width * 10000
        height = lcRect.height * 10000

        kiTra = SprintTrack(layerIdx, max(lcRect.stroke_width, 0.01))
        kiTra.addPoint(x1, y1)
        kiTra.addPoint(x1 + width, y1)
        kiTra.addPoint(x1 + width, y1 + height)
        kiTra.addPoint(x1, y1 + height)
        kiTra.addPoint(x1, y1)
        
        sprintTextIo.addTrack(kiTra)

    #圆弧
    for lcArc in lcFp.arcs:
        layerIdx = lcLayerMap.get(lcArc.layer_id, LAYER_S1)
        spCir = SprintCircle(layerIdx=layerIdx)
        
        #转换和计算圆弧
        arcPath = lcArc.path.replace(",", " ").replace("M ", "M").replace("A ", "A")

        startX, startY = arcPath.split("A")[0][1:].split(" ", 1)
        startX = convert_to_mm(startX) - lcFp.bbox.x
        startY = convert_to_mm(startY) - lcFp.bbox.y

        arcParameters = arcPath.split("A")[1].replace("  ", " ")
        svgRx, svgRy, xAxisRotation, largeArc, sweep, endX, endY = arcParameters.split(" ", 6)
        rx, ry = rotate(convert_to_mm(svgRx), convert_to_mm(svgRy), 0)
        endX = convert_to_mm(endX) - lcFp.bbox.x
        endY = convert_to_mm(endY) - lcFp.bbox.y
        if ry != 0:
            cx, cy, extent = compute_arc(startX, startY, rx, ry, str_to_float(xAxisRotation), largeArc=="1", sweep=="1", endX, endY)
        else:
            cx = 0.0
            cy = 0.0
            extent = 0.0

        spCir.width = max(convert_to_mm(lcArc.stroke_width), 0.01) * 10000
        spCir.setArcByCenterStartAngle(cx * 10000, cy * 10000, endX * 10000, endY * 10000, extent * 1000) #力创的圆弧角度单位为1度，Sprint-Layout的圆弧角度单位为0.001度
        
        sprintTextIo.addCircle(spCir)

    #文本
    if importText:
        for lcText in lcFp.texts:
            if (not lcText.is_displayed):
                continue

            layerIdx = lcLayerMap.get(lcText.layer_id, LAYER_S1)
            spText = SprintText(layerIdx=layerIdx)
            spText.text = lcText.text
            spText.height = max(lcText.font_size, 1) * 10000

            #尝试适当调整文本位置，Sprint-Layout都是左对齐的
            #(justify [left | right] [top | bottom] [mirror]
            offsetX = offsetY = 0
            if (lcText.rotation == 0): #中心对齐，假定Sprint-Layout的字宽是字高的三分之一
                offsetX = -(len(spText.text) * spText.height / 3)
                offsetY = spText.height / 3

            spText.pos = (((lcText.center_x - lcFp.bbox.x) * 10000 + offsetX), ((lcText.center_y - lcFp.bbox.y) * 10000 + offsetY))
            spText.rotation = (360 - lcText.rotation) if lcText.rotation else 0
            
            sprintTextIo.addText(spText)

    return str(sprintTextIo)
