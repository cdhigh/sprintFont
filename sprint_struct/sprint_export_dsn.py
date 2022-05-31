#!/usr/bin/env python
#-*- coding:utf-8 -*-
"""
将Sprint-Layout的TextIO对象转换为Specctra DSN格式
Author: cdhigh <https://github.com/cdhigh>
"""
import os, sys
if 0:
    from .sprint_textio import *

#测试
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from sprint_struct.sprint_textio import *
from comm_utils import pointAfterRotated
from kicad_pcb import sexpr

class PcbRule:
    def __init__(self):
        self.trackWidth = 0.3 #最小布线宽度
        self.minViaDiameter = 0.4 #最小过孔外径
        self.minViaDrill = 0.3 #最小钻孔内径
        self.clearance = 0.25 #最小孔间隙
        self.viaDiameter = 0.8
        self.viaDrill = 0.4

    #根据过孔大小返回过孔名字
    def viaName(self):
        return 'Via_{}x{}'.format(self.viaDiameter, self.viaDrill)


class SprintExportDsn:
    VIA_NAME = 'Sprint_Via'
    def __init__(self, textIo, pcbWidth: float=0, pcbHeight: float=0):
        self.rules = []
        self.name = ''
        self.pcbWidth = pcbWidth
        self.pcbHeight = pcbHeight
        self.viaDiameter = 0.3 #过孔直径
        self.textIo = textIo
        self.padDict = {} #键为焊盘名字，值为焊盘列表
        self.pcbRule = PcbRule()

    def export(self, fileName: str):
        se = sexpr.SexprBuilder("PCB")
        textIo = self.textIo

        #头部的说明性内容
        se.addItem(self.name or 'NoName', newline=False)
        se.startGroup('parser', indent=True)
        se.addItem({'string_quote': '"'}, indent=True)
        se.addItem({'space_in_quoted_tokens': 'on'})
        se.addItem({'host_cad': 'Sprint-Layout'})
        se.addItem({'host_version': 'v6.0'})
        se.endGroup(newline=True) #parser end
        se.addItem({'resolution': ['mm', '10000']})
        se.addItem({'unit': 'mm'})

        #structure段
        self.buildStructure(se)

        #library段
        self.buildPadLibrary(se)

        se.endGroup(True) #文件结束

        with open(fileName, 'w', encoding='utf-8') as f:
            f.write(se.output)

    #构建Structure段
    def buildStructure(self, se):
        se.startGroup('structure')
        self.buildBoundary(se)
        se.addItem({'snap_angle': 'fortyfive_degree'})
        se.addItem({'via': self.VIA_NAME})
        se.addItem({'control': {'via_at_smd': 'off'}})
        se.addItem({'rule': [{'width': self.pcbRule.trackWidth}, {'clear': self.pcbRule.clearance}]})
        se.addItem({'layer': ['F.Cu', {'type': 'signal'}]})
        se.addItem({'layer': ['B.Cu', {'type': 'signal'}]})
        se.startGroup('autoroute_settings')
        se.addItem({'fanout': 'off'}, indent=True)
        se.addItem({'app.freerouting.autoroute': 'on'})
        se.addItem({'postroute': 'on'})
        se.addItem({'vias': 'on'})
        se.addItem({'via_costs': '50'})
        se.addItem({'plane_via_costs': '5'})
        se.addItem({'start_ripup_costs': '100'})
        se.addItem({'start_pass_no': '34'})
        se.startGroup('layer_rule')
        se.addItem('F.Cu', newline=False)
        se.addItem({'active': 'off'}, indent=True)
        se.addItem({'preferred_direction': 'horizontal'})
        se.addItem({'preferred_direction_trace_costs': '1.0'})
        se.addItem({'against_preferred_direction_trace_costs': '2.4'})
        se.endGroup(newline=True) #layer_rule end
        se.startGroup('layer_rule')
        se.addItem('B.Cu', newline=False)
        se.addItem({'active': 'on'}, indent=True)
        se.addItem({'preferred_direction': 'vertical'})
        se.addItem({'preferred_direction_trace_costs': '1.0'})
        se.addItem({'against_preferred_direction_trace_costs': '1.7'})
        se.endGroup(newline=True) #layer_rule end
        se.endGroup(newline=True) #autoroute_settings end
        se.endGroup(newline=True) #structure end

    #填写线路板外框
    def buildBoundary(self, se):
        #PCB大小范围
        se.addItems({'boundary': {'rect': ['pcb', 0, 0, self.pcbWidth, self.pcbHeight]}}, indent=True)
        
        #找到第一个LAYER_U的元素，在调用此函数前，应该要提前确认只有一个LAYER_U元素
        uElems = textIo.getAllElementsInLayer(LAYER_U)
        if len(uElems) < 1:
            return 'The boundary of the board is not defined'

        uElem = uElems[0]
        bbPath = ['signal', '0', ] #第一个参数是信号层，第二个参数是线宽
        if isinstance(uElem, (SprintTrack, SprintPolygon)):
            for (x, y) in uElem.points:
                bbPath.append(str(x))
                bbPath.append(str(y))
        elif isinstance(uElem, SprintCircle):
            points = cutCircle(uElem.center[0], uElem.center[1], uElem.radius, 36)
            for (x, y) in points:
                bbPath.append(str(x))
                bbPath.append(str(y))
        else:
            return

        se.addItem({'boundary': {'polygon': bbPath}})

    #生成焊盘库
    def buildPadLibrary(self, se):
        self.padDict = padDict = textIo.categorizePads()
        se.startGroup('library')
        firstIndent = True
        for name in self.padDict:
            pad = padDict[name][0]
            se.startGroup('padstack', indent=firstIndent)
            firstIndent = False
            se.addItem(name, newline=False)
            if (pad.padType == 'PAD'):
                form = pad.form
                size = pad.size
                rotation = pad.rotation
                if (form in (PAD_FORM_ROUND, PAD_FORM_OCTAGON)): #则两种焊盘当作一种
                    se.addItem({'shape': {'path': ['F.Cu', size, 0, 0, 0, 0]}}, indent=True)
                    se.addItem({'shape': {'path': ['B.Cu', size, 0, 0, 0, 0]}})
                elif (form in (PAD_FORM_SQUARE, PAD_FORM_RECT_H, PAD_FORM_RECT_V)):
                    width = (size * 2) if (form == PAD_FORM_RECT_H) else size
                    height = (size * 2) if (form == PAD_FORM_RECT_V) else size
                    if not rotation:
                        se.addItem({'shape': {'rect': ['F.Cu', 0, 0, width, height]}}, indent=True)
                        se.addItem({'shape': {'rect': ['B.Cu', 0, 0, width, height]}})
                    else:
                        #假定中心坐标为(0, 0)，则如果不旋转，左下角坐标为(-width/2, -height/2)，右上角坐标为(width/2, height/2)
                        #将左下角和右上角绕中心逆时针选择一个rotation角度
                        (x1, y1) = pointAfterRotated(-width/2, -height/2, 0, 0, rotation, clockwise=0)
                        (x2, y2) = pointAfterRotated(width/2, height/2, 0, 0, rotation, clockwise=0)
                        se.addItem({'shape': {'rect': ['F.Cu', x1, y1, x2, y2]}}, indent=True)
                        se.addItem({'shape': {'rect': ['B.Cu', x1, y1, x2, y2]}})
                else:
                    if form in (PAD_FORM_RECT_ROUND_H, PAD_FORM_RECT_OCTAGON_H): #横长条
                        (x1, y1) = size, 0
                    else: #竖长条
                        (x1, y1) = 0, size

                    if rotation:
                        (x1, y1) = pointAfterRotated(x1, y1, 0, 0, rotation, clockwise=0)

                    se.addItem({'shape': {'path': ['F.Cu', size, 0, 0, x1, y1]}}, indent=True)
                    se.addItem({'shape': {'path': ['B.Cu', size, 0, 0, x1, y1]}})
            else: #SMDPAD
                width = pad.sizeX
                height = pad.sizeY
                if not rotation:
                    se.addItem({'shape': {'rect': ['F.Cu', 0, 0, width, height]}}, indent=True)
                    se.addItem({'shape': {'rect': ['B.Cu', 0, 0, width, height]}})
                else:
                    #假定中心坐标为(0, 0)，则如果不旋转，左下角坐标为(-width/2, -height/2)，右上角坐标为(width/2, height/2)
                    #将左下角和右上角绕中心逆时针选择一个rotation角度
                    (x1, y1) = pointAfterRotated(-width/2, -height/2, 0, 0, rotation, clockwise=0)
                    (x2, y2) = pointAfterRotated(width/2, height/2, 0, 0, rotation, clockwise=0)
                    se.addItem({'shape': {'rect': ['F.Cu', x1, y1, x2, y2]}}, indent=True)
                    se.addItem({'shape': {'rect': ['B.Cu', x1, y1, x2, y2]}})
            se.addItem({'attach': 'off'})
            se.endGroup(newline=True) #padstack end

        #添加过孔信息
        se.startGroup('padstack', indent=False)
        se.addItem(self.pcbRule.viaName(), newline=False)
        se.addItem({'shape': {'circle': ['F.Cu', self.pcbRule.viaDiameter]}}, indent=True)
        se.addItem({'shape': {'circle': ['B.Cu', self.pcbRule.viaDiameter]}})
        se.endGroup(newline=True) #padstack end
        se.endGroup(newline=True) #library end

from sprint_struct.sprint_textio_parser import SprintTextIoParser
p = SprintTextIoParser()
textIo = p.parse(r'C:\Users\su\Desktop\testSprint\1.txt')
if textIo:
    #判断是否所有的元件都有名字了
    for elem in textIo.elements:
        if isinstance(elem, SprintComponent) and not elem.name:
            print('There are some unnamed components')
            break

s = SprintExportDsn(textIo, 160, 100)
s.export(r'C:\Users\su\Desktop\testSprint\dsnex.dsn')
