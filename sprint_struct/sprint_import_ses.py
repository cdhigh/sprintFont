#!/usr/bin/env python
#-*- coding:utf-8 -*-
"""
将Specctra SES格式转换为Sprint-Layout的TextIO对象
Author: cdhigh <https://github.com/cdhigh>
"""
import os, sys, pickle

#测试
if __name__ == '__main__':
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from comm_utils import pointAfterRotated, cutCircle, ComputePolygonArea, str_to_float, str_to_int
from kicad_pcb import sexpr
from sprint_struct.sprint_textio import *
from sprint_struct.sprint_export_dsn import SprintExportDsn, mm2um, PcbRule

#微米转换为毫米
def um2mm(value: int):
    return round(str_to_float(value) / 1000, 2)

class SprintImportSes:
    #sesFile: ses文件名
    #dsn: 对应ses的SprintExportDsn实例，可以从pickle文件里面恢复
    def __init__(self, sesFile: str, dsn: SprintExportDsn):
        self.sesFile = sesFile
        self.ses = None #分析过后的ses文件内容，为嵌套的列表字典结构
        self.dsn = dsn
        self.resolution = 1000 #默认为 (resolution um 1)
        
    #将ses文件内的数值转换为mm为单位
    def scale(self, value: float):
        return round(str_to_float(value) / self.resolution, 2)

    #开始导入，生成一个SprintTextIO对象
    #trackOnly: True-仅导入布线，False-导入全部
    def importSes(self, trackOnly=False):
        try:
            with open(self.sesFile, 'r', encoding='utf-8') as f:
                sexprData = "".join(f.readlines())
        except UnicodeDecodeError:
            try:
                with open(self.sesFile, 'r', encoding=locale.getpreferredencoding()) as f:
                    sexprData = "".join(f.readlines())
            except UnicodeDecodeError:  #如果还失败，则让其抛出异常，在外面捕获
                with open(self.sesFile, 'r', encoding='latin-1') as f:
                    sexprData = "".join(f.readlines())

        self.ses = sexpr.parse_sexp(sexprData)
        textIo = SprintTextIO() if trackOnly else self.dsn.textIo
        
        #先分析ses内使用的单位
        self.analyzeResolution(self.ses)

        wires = self._getArray(self.ses, 'wire')
        
        #添加走线
        #[['wire', ['path', 'B.Cu', '2500', 1504097, '-1037700', 1517848, '-1061517']],...]
        for wire in wires:
            if (len(wire) < 2) or (len(wire[1]) < 7):
                continue

            path = wire[1]
            pathLen = len(path)
            layer = path[1]
            width = self.scale(path[2])
            track = SprintTrack(sprintLayerMapSes.get(layer, LAYER_C1), width)
            for idx in range(3, pathLen, 2):
                if (idx + 1 >= pathLen):
                    break

                x = self.scale(path[idx])
                y = self.scale(path[idx + 1])
                track.addPoint(x, -y)
            textIo.add(track)
            
        #添加过孔
        #(via Via_800x400 21946 -13811)
        vias = self._getArray(self.ses, 'via')
        pcbRule = self.dsn.pcbRule
        viaDiameter = pcbRule.viaDiameter
        viaDrill = pcbRule.viaDrill
        for via in vias:
            if (len(via) < 4):
                continue

            viaPad = SprintPad('PAD', LAYER_C1)
            viaPad.size = viaDiameter
            viaPad.drill = viaDrill
            viaPad.via = True
            viaPad.pos = (self.scale(via[2]), -self.scale(via[3]))
            textIo.add(viaPad)

        #如果有元件位置移动，则需要更新到TextIo
        #(place r1 15362 -19807 front 0)
        placements = self._getArray(self.ses, 'place')
        compList = self.dsn.compList
        for place in placements:
            if len(place) < 6:
                continue

            name = place[1]
            x = self.scale(place[2])
            y = -self.scale(place[3])
            for comp in compList:
                if ((comp.name == name) and (abs(x - round(comp.xMin, 2)) > 0.01) 
                    and (abs(y - round(comp.yMin, 2)) > 0.01)):
                    #print(f'{name}, {x}, {comp.xMin}, {y}, {comp.yMin}') #TODO
                    comp.moveByOffset(comp.xMin - x, comp.yMin - y)

        #将textIo里面的网络连线删除
        pads = [elem for elem in textIo.baseDrawElements() if isinstance(elem, SprintPad)]
        for pad in pads:
            pad.connectToOtherPads.clear()
            
        return textIo

    def analyzeResolution(self, ses):
        res = self._getArray(ses, 'resolution')
        #为简单起见，就直接使用最后一个做为单位
        if ((not res) or (len(res[-1]) < 3)):
            return

        unit = res[-1][1]
        unitValue = str_to_int(res[-1][2])
        if (unit == 'um'):
            self.resolution = 1000 * unitValue
        elif (unit == 'mm'):
            self.resolution = unitValue
        elif (unit == 'cm'):
            self.resolution = unitValue / 100
        elif (unit == 'inch'):
            self.resolution = unitValue / 25.4
        elif (unit == 'mil'):
            self.resolution = unitValue / 0.0254
        else:
            return

        if self.resolution == 0:
            self.resolution = 1

    #在sexpr数据结构里面查询一个特定数值的列表
    #data: sexpr结构
    #value: sexpr里面的一个段名，比如 (ses xxx)，则ses就是段名
    #result: 如果传入，则从此列表中返回
    #level: 当前层次
    #maxLevel: 最大遍历层次
    def _getArray(self, data, value, result=None, level: int=0, maxLevel=None):
        if result is None:
            result = []

        if maxLevel and (level >= maxLevel):
            return result

        level += 1

        for i in data:
            if isinstance(i, list):
                self._getArray(i, value, result, level, maxLevel)
            elif (i == value):
                result.append(data)
        return result


if __name__ == '__main__':
    dsnFile = r'C:\Users\su\Desktop\testSprint\dsnex.dsn.pickle'
    sesFile = r'C:\Users\su\Desktop\testSprint\dsnex.ses'
    inputFile = r'C:\Users\su\Desktop\testSprint\1_in.txt'

    with open(dsnFile, 'rb') as f:
        dsn = pickle.load(f)

    ses = SprintImportSes(sesFile, dsn)
    textIo = ses.importSes()
    with open(inputFile, 'w', encoding='utf-8') as f:
        f.write(str(textIo))

