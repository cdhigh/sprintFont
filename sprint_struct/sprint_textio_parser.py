#!/usr/bin/env python
#-*- coding:utf-8 -*-
"""
从Sprint-Layout导出的TextIO格式的文本文件生成Sprint-Layout的TextIO对象
保存到里面的参数使用mm为单位，角度单位为度，仅仅在重新输出文本时再转换为0.1微米和0.001度
Author: cdhigh <https://github.com/cdhigh>
"""
import locale
from functools import partial
from operator import itemgetter
from utils.comm_utils import *
from .sprint_element import *
from .sprint_track import SprintTrack
from .sprint_polygon import SprintPolygon
from .sprint_pad import *
from .sprint_text import SprintText
from .sprint_circle import SprintCircle
from .sprint_component import SprintComponent
from .sprint_group import SprintGroup
from .sprint_textio import *

class SprintTextIoParser:
    def __init__(self, pcbWidth=0, pcbHeight=0):
        self.pcbWidth = pcbWidth
        self.pcbHeight = pcbHeight
        self.fileName = ''
        self.textIo = None
        self.containers = [] #这是一个栈结构
        self.handlers = {
            'GROUP': self.handleGroup,
            'END_GROUP': self.handleEndGroup,
            'BEGIN_COMPONENT': self.handleComponent,
            'END_COMPONENT': self.handleEndComponent,
            'TRACK': self.handleTrack,
            'PAD': self.handlePad,
            'SMDPAD': self.handlePad,
            'ZONE': self.handleZone,
            'TEXT': partial(self.handleText, type_='TEXT'),
            'ID_TEXT': partial(self.handleText, type_='ID_TEXT'),
            'VALUE_TEXT': partial(self.handleText, type_='VALUE_TEXT'),
            'CIRCLE': self.handleCircle,
        }

    #分析文本文件，返回一个 SprintTextIO 对象
    def parse(self, fileName: str):
        try:
            with open(fileName, 'r', encoding='latin-1') as f:
                lines = f.read().split('\n')
        except UnicodeDecodeError:
            try:
                with open(fileName, 'r', encoding='utf-8') as f:
                    lines = f.read().split('\n')
            except UnicodeDecodeError:
                try:
                    with open(fileName, 'r', encoding=locale.getpreferredencoding()) as f:
                        lines = f.read().split('\n')
                except:
                    return None

        self.fileName = fileName
        self.textIo = SprintTextIO(self.pcbWidth, self.pcbHeight)
        self.containers = [self.textIo] #这是一个栈结构

        for line in lines:
            elems = line.strip().replace(';', '').split(',')
            if not elems:
                continue

            elemType = elems[0].strip()
            if not elemType:
                continue

            #将后续的字符串分割成(key,value)形式的元祖
            for idx in range(1, len(elems)):
                keyValue = elems[idx].split('=', 1)
                elems[idx] = (keyValue[0], keyValue[1].strip() if (len(keyValue) >= 2) else '')

            self.handlers.get(elemType, self.handleUnknown)(elems)

        self.textIo.updateSelfBbox()

        return self.textIo if self.textIo.isValid() else None

    #字符串转换为电路板层
    @classmethod
    def parseLayerStr(cls, layerStr: str, defaultLayer: int=LAYER_S1):
        layer = str_to_int(layerStr)
        return layer if (LAYER_C1 <= layer <= LAYER_U) else defaultLayer

    #分析 x/y 形式的坐标点格式，返回 (x, y) 元祖，并且将里面的单位转换为毫米
    @classmethod
    def parsePosStr(cls, posStr: str):
        if not posStr or ('/' not in posStr):
            return (0, 0)
        xy = posStr.split('/')
        return (str_to_int(xy[0]) / 10000, str_to_int(xy[1]) / 10000)

    #分析boolean型
    @classmethod
    def parseBooleanStr(cls, booleanStr: str):
        return True if (booleanStr.lower() == 'true') else False

    #未知handler
    def handleUnknown(self, elems: list):
        print('handleUnknown: {}'.format(elems))
        return

    #开始新组
    def handleGroup(self, elems: list):
        group = SprintGroup()
        self.containers[-1].add(group)
        self.containers.append(group)

    #结束组
    def handleEndGroup(self, elems: list):
        if self.containers:
            self.containers.pop(-1)

    #开始新元件
    #BEGIN_COMPONENT,COMMENT=|coment|,USE_PICKPLACE=true,PACKAGE=|SOT32|,ROTATION=270;
    def handleComponent(self, elems: list):
        component = SprintComponent()
        self.containers[-1].add(component)
        self.containers.append(component)
        for key, value in elems[1:]:
            key = key.upper()
            if key == 'COMMENT':
                component.comment = value.replace('|', '')
            elif key == 'USE_PICKPLACE':
                component.usePickplace = True if value.lower() == 'true' else False
            elif key == 'PACKAGE':
                component.package = value.replace('|', '')
            elif key == 'ROTATION':
                component.pickRotation = str_to_int(value)

    #结束新元件
    def handleEndComponent(self, elems: list):
        if self.containers:
            comp = self.containers.pop(-1)
            #comp.updateSelfBbox()

    #分析Track
    #TRACK,LAYER=2,WIDTH=1500,P0=9900/167100,P1=58200/215400;
    def handleTrack(self, elems: list):
        track = SprintTrack()
        pointsList = [] #每个点的定义 (idx, (x, y))
        for key, value in elems[1:]:
            key = key.upper()
            if key == 'LAYER':
                track.layerIdx = self.parseLayerStr(value)
            elif key == 'WIDTH':
                track.width = str_to_int(value) / 10000
            elif key == 'CLEAR':
                track.clearance = str_to_int(value) / 10000
            elif key == 'CUTOUT':
                track.cutout = self.parseBooleanStr(value)
            elif key == 'SOLDERMASK':
                track.soldermask = self.parseBooleanStr(value)
            elif key == 'FLATSTART':
                track.flatstart = self.parseBooleanStr(value)
            elif key == 'FLATEND':
                track.flatend = self.parseBooleanStr(value)
            elif key == 'NAME':
                track.name = value.replace('|', '')
            elif key.startswith('P') and (len(key) > 1): #点列表
                ptIdx = str_to_int(key[1:])
                pointsList.append((ptIdx, self.parsePosStr(value)))

        #将点列表进行排序
        pointsList.sort(key=itemgetter(0))
        for ptIdx, (x, y) in pointsList:
            track.addPoint(x, y)

        self.containers[-1].add(track)

    #分析PAD/SMDPAD
    def handlePad(self, elems: list):
        pad = SprintPad(padType=elems[0].strip())
        for key, value in elems[1:]:
            key = key.upper()
            if key == 'LAYER':
                pad.layerIdx = self.parseLayerStr(value)
            elif key == 'POS':
                pad.pos = self.parsePosStr(value)
            elif key == 'SIZE':
                pad.size = str_to_int(value) / 10000
            elif key == 'SIZE_X':
                pad.sizeX = str_to_int(value) / 10000
            elif key == 'SIZE_Y':
                pad.sizeY = str_to_int(value) / 10000
            elif key == 'DRILL':
                pad.drill = str_to_int(value) / 10000
            elif key == 'FORM':
                pad.form = str_to_int(value)
            elif key == 'CLEAR':
                pad.clearance = str_to_int(value) / 10000
            elif key == 'SOLDERMASK':
                pad.soldermask = self.parseBooleanStr(value)
            elif key == 'ROTATION': #焊盘的旋转单位是0.01度
                pad.rotation = int(str_to_int(value) / 100)
            elif key == 'VIA':
                pad.via = self.parseBooleanStr(value)
            elif key == 'THERMAL':
                pad.thermal = self.parseBooleanStr(value)
            elif key == 'THERMAL_TRACKS_WIDTH':
                pad.thermalTracksWidth = str_to_int(value) / 10000
            elif key == 'THERMAL_TRACKS_INDIVIDUAL':
                pad.thermalTracksIndividual = self.parseBooleanStr(value)
            elif key == 'THERMAL_TRACKS':
                pad.thermalTracks = str_to_int(value)
            elif key == 'PAD_ID':
                pad.padId = str_to_int(value)
            elif key == 'NAME':
                pad.name = value.replace('|', '')
            elif key.startswith('CON') and (len(key) > 3): #网络连接
                pad.connectToOtherPads.append(str_to_int(value))
        self.containers[-1].add(pad)

    #分析ZONE多边形
    def handleZone(self, elems: list):
        poly = SprintPolygon()
        pointsList = [] #每个点的定义 (idx, (x, y))
        for key, value in elems[1:]:
            key = key.upper()
            if key == 'LAYER':
                poly.layerIdx = self.parseLayerStr(value)
            elif key == 'WIDTH':
                poly.width = str_to_int(value) / 10000
            elif key == 'CLEAR':
                poly.clearance = str_to_int(value) / 10000
            elif key == 'CUTOUT':
                poly.cutout = self.parseBooleanStr(value)
            elif key == 'SOLDERMASK':
                poly.soldermask = self.parseBooleanStr(value)
            elif key == 'SOLDERMASK_CUTOUT':
                poly.soldermaskCutout = self.parseBooleanStr(value)
            elif key == 'HATCH':
                poly.hatch = self.parseBooleanStr(value)
            elif key == 'HATCH_AUTO':
                poly.hatchAuto = self.parseBooleanStr(value)
            elif key == 'HATCH_WIDTH':
                poly.hatchWidth = str_to_int(value) / 10000
            elif key == 'NAME':
                poly.name = value.replace('|', '')
            elif key.startswith('P') and (len(key) > 1): #点列表
                ptIdx = str_to_int(key[1:])
                pointsList.append((ptIdx, self.parsePosStr(value)))
        
        #将点列表进行排序
        pointsList.sort(key=itemgetter(0))
        for ptIdx, (x, y) in pointsList:
            poly.addPoint(x, y)

        self.containers[-1].add(poly)

    #Text
    def handleText(self, elems: list, type_: str="TEXT"):
        component = self.containers[-1] #调用到这个函数，containers至少有一个元素
        if type_ != "TEXT" and not isinstance(component, SprintComponent):
            return

        text = SprintText()
        for key, value in elems[1:]:
            key = key.upper()
            if key == 'LAYER':
                text.layerIdx = self.parseLayerStr(value)
            elif key == 'POS':
                text.pos = self.parsePosStr(value)
            elif key == 'HEIGHT':
                text.height = str_to_int(value) / 10000
            elif key == 'TEXT':
                text.text = value.replace('|', '')
            elif key == 'CLEAR':
                text.clearance = str_to_int(value) / 10000
            elif key == 'CUTOUT':
                text.cutout = self.parseBooleanStr(value)
            elif key == 'SOLDERMASK':
                text.soldermask = self.parseBooleanStr(value)
            elif key == 'STYLE':
                text.style = str_to_int(value)
            elif key == 'THICKNESS':
                text.thickness = str_to_int(value)
            elif key == 'ROTATION': #文本的旋转好像很奇怪, 不同版本单位不同
                #IDTEXT/VALUETEXT旋转单位是0.001度, 单独文本的旋转单位为0.01度
                unit = 100 if type_ == 'TEXT' else 1000
                rotation = int(str_to_int(value) / unit)
                text.rotation = int(rotation / 10) if rotation > 359 else rotation
            elif key == 'MIRROR_HORZ':
                text.mirrorH = self.parseBooleanStr(value)
            elif key == 'MIRROR_VERT':
                text.mirrorV = self.parseBooleanStr(value)
            elif key == 'NAME':
                text.name = value.replace('|', '')
            elif key == 'VISIBLE':
                text.visible = self.parseBooleanStr(value)

        if type_ == 'ID_TEXT':
            component.idText = text
        elif type_ == 'VALUE_TEXT':
            component.valueText = text
        else:
            component.add(text)
            
    #Circle
    def handleCircle(self, elems: list):
        cir = SprintCircle()
        for key, value in elems[1:]:
            key = key.upper()
            if (key == 'LAYER'):
                cir.layerIdx = self.parseLayerStr(value)
            elif (key == 'CENTER'):
                cir.center = self.parsePosStr(value)
            elif (key == 'WIDTH'):
                cir.width = str_to_int(value) / 10000
            elif (key == 'RADIUS'):
                cir.radius = str_to_int(value) / 10000
            elif (key == 'CLEAR'):
                cir.clearance = str_to_int(value) / 10000
            elif (key == 'CUTOUT'):
                cir.cutout = self.parseBooleanStr(value)
            elif (key == 'SOLDERMASK'):
                cir.soldermask = self.parseBooleanStr(value)
            elif (key == 'START'):
                cir.start = str_to_int(value) / 1000
                while (cir.start > 360):
                    cir.start -= 360
                while (cir.start < -0.1):
                    cir.start += 360
            elif (key == 'STOP'):
                cir.stop = str_to_int(value) / 1000
                while (cir.stop > 360):
                    cir.stop -= 360
                while (cir.stop < -0.1):
                    cir.stop += 360
            elif (key == 'FILL'):
                cir.fill = self.parseBooleanStr(value)
            elif (key == 'NAME'):
                cir.name = value.replace('|', '')

        self.containers[-1].add(cir)
        
