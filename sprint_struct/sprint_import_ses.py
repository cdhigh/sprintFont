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

#整数微米转换为浮点毫米
def um2mm(value: int):
    return round(str_to_float(value) / 1000, 4)

class SprintImportSes:
    #sesFile: ses文件名
    #dsn: 对应ses的SprintExportDsn实例，可以从pickle文件里面恢复
    def __init__(self, sesFile: str, dsn: SprintExportDsn):
        self.sesFile = sesFile
        self.ses = None #分析过后的ses文件内容，为嵌套的列表字典结构
        self.dsn = dsn
        self.resolution = 1000 #默认为 (resolution um 1)
        
    #将ses文件内的数值转换为mm为单位，返回浮点数
    def scale(self, value: float):
        return round(str_to_float(value) / self.resolution, 4)

    #开始导入，生成一个SprintTextIO对象
    #trimRatsnestMode: 'keepAll'-包含所有鼠线（网络连线），'trimAll'-删除所有鼠线，'trimRouted'-仅删除有铜箔布线连通的焊盘间鼠线
    #trackOnly: True-仅导入布线，False-导入全部
    #trackOnly的优先级比withRatsnest高，如果trackOnly=True，则忽略withRatsnest
    def importSes(self, trimRatsnestMode: str, trackOnly: bool):
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

        #如果有元件位置移动，则需要先更新到TextIo
        #(place r1 15362 -19807 front 0)
        if not trackOnly:
            placements = self._getArray(self.ses, 'place')
            compList = self.dsn.compList
            for place in placements:
                if len(place) < 6:
                    continue

                name = place[1]
                x = self.scale(place[2])
                y = -self.scale(place[3])
                for comp in compList:
                    if ((comp.name == name) and (abs(x - round(comp.pos[0], 3)) > 0.01)
                        and (abs(y - round(comp.pos[1], 3)) > 0.01)):
                        #print(f'{name}, {x}, {comp.pos[0]}, {y}, {comp.pos[1]}') #TODO
                        comp.moveByOffset(comp.pos[0] - x, comp.pos[1] - y)

        #添加走线
        wires = self._getArray(self.ses, 'wire')

        #[['wire', ['path', 'B.Cu', '2500', 1504097, '-1037700', 1517848, '-1061517']],...]
        for wire in wires:
            if (len(wire) < 2) or (len(wire[1]) < 7):
                continue

            path = wire[1]
            pathLen = len(path)
            #print(path)
            layer = sprintLayerMapSes.get(path[1], LAYER_C1)
            width = self.scale(path[2])
            if (width <= 0):
                continue
                
            track = SprintTrack(layer, width)
            for idx in range(3, pathLen, 2):
                if (idx + 1 >= pathLen):
                    break

                x = self.scale(path[idx])
                y = self.scale(path[idx + 1])
                track.addPoint(x, -y) #负号是因为两个系统的坐标系Y轴方向相反
            textIo.add(track)
            #print('add track:{},{}'.format(layer, width))
            #time.sleep(0.1)
            
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

        if trimRatsnestMode == 'trimAll':
            #将textIo里面的网络连线删除
            nonePads = [elem.connectToOtherPads.clear() for elem in textIo.baseDrawElements() if isinstance(elem, SprintPad)]
        elif trimRatsnestMode == 'trimRouted':
            self.trimRatsnest(textIo)

        #将自动命名的元件的名字恢复为空
        components = [elem for elem in textIo.children() if isinstance(elem, SprintComponent)]
        for comp in components:
            name = comp.name
            if ((len(name) > 8) and name.startswith('unnamed_') and name[8:].isdigit()):
                comp.name = ''
            
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

    #智能判断铜箔连接情况，将有铜箔连接的焊盘之间的鼠线删除
    #大概原理：首先通过过孔将所有布线转换为(坐标,板层)列表。形成一个字典，键为网表号
    #遍历所有焊盘，先获取焊盘位置，然后逐个布线各端点，如果端点在焊盘范围内并且板层相同，则为连通，
    #记录布线索引对应的字典键值和焊盘ID的对应情况(ID,
    #所有焊盘完成后，同样键的所有焊盘ID为相互连通，再遍历textio，某个ID删除和它相通的其他ID
    def trimRatsnest(self, textIo):
        #所有过孔和铜箔走线
        #round(2)而不是round(4)是为了减小浮点误差导致之后的比较错误
        vias = [(round(elem.pos[0], 2), round(elem.pos[1], 2)) for elem in textIo.baseDrawElements() if (isinstance(elem, SprintPad) and elem.via)]
        tracks = [elem for elem in textIo.baseDrawElements() if (isinstance(elem, SprintTrack) and (elem.layerIdx in (LAYER_C1, LAYER_C2)))]
        trackPoints = []

        #先生成点列表
        for track in tracks:
            ptSet = set()
            points =[(round(x, 2), round(y, 2))  for (x, y) in track.points]
            for (x, y) in points:
                found = True
                for (xv, yv) in vias: #确认一个过孔连通，再找其他有同样这个过孔的走线
                    if ((abs(x - xv) < 0.1) and (abs(y - yv) < 0.1)):
                        ptSet.add((x, y, LAYER_C1))
                        ptSet.add((x, y, LAYER_C2))
                        break
                else:
                    ptSet.add((x, y, track.layerIdx))

            trackPoints.append(ptSet)

        #合并有相同元素的集合
        trackPoints = self.mergeListWithSameElement(trackPoints)
        
        padIdDict = {elem.padId: elem for elem in textIo.baseDrawElements() if (isinstance(elem, SprintPad) and elem.padId is not None)}
        for padId, pad in padIdDict.items():
            connects = pad.connectToOtherPads
            if not connects:
                continue

            #找到和此焊盘相连的布线
            for condutiveIdx, area in enumerate(trackPoints):
                if (self.isPadConnectToArea(pad, area)):
                    break
            else: #此焊盘没有连通任何区域
                continue

            condutiveArea = trackPoints[condutiveIdx]

            #判断和此焊盘有鼠线连接的其他焊盘是否已经有布线连接了
            for otherId in connects[:]:
                otherPad = padIdDict.get(otherId)
                if not otherPad:
                    continue

                if (self.isPadConnectToArea(otherPad, condutiveArea)):
                    connects.remove(otherId)

    #判断一个焊盘是否连接到一个连通区域
    #area: {(x, y, layer),...}
    def isPadConnectToArea(self, pad: SprintPad, area: set):
        for (x, y, layer) in area:
            if ((layer == pad.layerIdx) and pad.enclose(x, y)):
                return True
        return False

    #将列表中有相同元素的集合合并，算法时间复杂度O(n^2)
    #比如对于列表： [{'a', 'b', 'c', 'f'}, {'e', 'g'}, {1, 2, 3}, {'h', 'g', 'f'}, {5, 6, 7}, {3, 4}]
    #输出结果：[{'b', 'a', 'h', 'c', 'g', 'f', 'e'}, {5, 6, 7}, {1, 2, 3, 4}]
    def mergeListWithSameElement(self, srcList: list):
        lenth = len(srcList)
        setForEmpty = {0} #用于将一个集合清空的特殊集合，如果你的数据集里面有这个数，可以将这个集合修改为其他集合
        for i in range(1, lenth):
            for j in range(i):
                if ((srcList[i] == setForEmpty) or (srcList[j] == setForEmpty)):
                    continue

                x = srcList[i].union(srcList[j])
                y = len(srcList[i]) + len(srcList[j])
                if len(x) < y: #合并后的集合长度小于合并前的两个集合长度总和，说明有共同元素
                    srcList[i] = x
                    srcList[j] = setForEmpty

        return [i for i in srcList if (i != setForEmpty)] #筛掉空集合
