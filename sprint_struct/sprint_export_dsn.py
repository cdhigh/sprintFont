#!/usr/bin/env python
#-*- coding:utf-8 -*-
"""
将Sprint-Layout的TextIO对象转换为Specctra DSN格式
Author: cdhigh <https://github.com/cdhigh>
"""
import os, sys, pickle
if 0:
    from .sprint_textio import *

#测试
if __name__ == '__main__':
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sprint_struct.sprint_textio import *
from comm_utils import pointAfterRotated, cutCircle, ComputePolygonArea, str_to_float
from kicad_pcb import sexpr

#浮点毫米转换为整数微米
def mm2um(value: float):
    return int(str_to_float(value) * 1000)

class PcbRule:
    def __init__(self):
        #单位为mm
        self.trackWidth = 0.3  #最小布线宽度
        self.viaDiameter = 0.7 #过孔外径
        self.viaDrill = 0.3    #过孔内径
        self.clearance = 0.2  #最小孔到孔间隙
        self.smdSmdClearance = 0.06 #贴片贴片间隙
        
    #根据过孔大小返回过孔名字
    def viaName(self):
        return 'Via_{}x{}'.format(mm2um(self.viaDiameter), mm2um(self.viaDrill))


class SprintExportDsn:
    def __init__(self, textIo, pcbRule: PcbRule=None, name: str=''):
        self.name = name
        self.pcbRule = pcbRule if pcbRule else PcbRule()
        self.se = sexpr.SexprBuilder("PCB")
        self.textIo = textIo
        if textIo:
            textIo.ensurePadHasId()
            textIo.ensureComponentHasName()
            self.padDict = textIo.categorizePads() #键为焊盘形状名字，值为焊盘实例列表
            self.compDict = textIo.categorizeComponents() #键为元件名字，值为字典 {'image': SprintComponent, 'instance':[]}
            self.compList = [] #这个列表保存了所有的元件和根据游离焊盘生成的临时元件
            for comps in self.compDict.values():
                self.compList.extend(comps['instance'])
            self.wires = [elem for elem in textIo.children() if (isinstance(elem, SprintTrack) and (elem.layerIdx in (LAYER_C1, LAYER_C2)))]
            self.uElems = self.getAllLayerUAndKeepoutZone()
            self.padIdSeqDict = self.buildPadIdSeqDict() #键为焊盘ID，值为('compName':,'seqNum':)
            self.yMax = mm2um(textIo.yMax)
        
    #转换Y坐标，因为Sprint-Layout的坐标为笛卡尔坐标，freerouting的坐标为屏幕绘图坐标
    def umY(self, y: float):
        return -mm2um(y) #self.yMax

    #开始导出DSN，成功则返回sexpr.SexprBuilder实例，否则返回出错字符串信息
    #如果要保存到文件可以使用sexpr.SexprBuilder实例的output属性获取字符串
    def export(self):
        se = self.se
        textIo = self.textIo
        if not textIo:
            return _("")

        #确认线路板外框有效
        if len([e for e in self.uElems if (e.layerIdx == LAYER_U)]) < 1:
            return _("The boundary (layer U) of the board is not defined")

        #判断是否有重复的元件名
        #并且目前仅允许元件放在正面
        names = set()
        for comp in self.compList:
            if comp.name in names:
                return _("There are some components with the same name: {}").format(comp.name)
            else:
                names.add(comp.name)
            if (comp.getLayer() == LAYER_C2):
                return _("Currently only supports all components placed on the front side\n\n{}").format(comp.name)
        
        #头部的说明性内容
        se.addItem(self.name or 'NoName', newline=False)
        se.startGroup('parser', indent=True)
        se.addItem({'string_quote': '"'}, indent=True)
        se.addItem({'space_in_quoted_tokens': 'on'})
        se.addItem({'host_cad': 'Sprint-Layout'})
        se.addItem({'host_version': 'v6.0'})
        se.endGroup(newline=True) #parser end
        se.addItem({'resolution': ['um', 1]})
        se.addItem({'unit': 'um'})

        #structure段
        self.buildStructure(se)

        #placement段
        self.buildPlacement(se)

        #library段
        se.startGroup('library')
        self.buildImageLibrary(se)
        self.buildPadLibrary(se)
        se.endGroup(newline=True) #library end

        #network段
        self.buildNetwork(se)

        #已有的走线段
        self.buildWiring(se)

        se.endGroup(True) #文件结束
        return se

    #构建Structure段
    def buildStructure(self, se):
        se.startGroup('structure')
        se.addItem({'layer': ['F.Cu', [{'type': 'signal'}, {'property': {'index': 0}}]]}, indent=True)
        se.addItem({'layer': ['B.Cu', [{'type': 'signal'}, {'property': {'index': 1}}]]})
        self.buildBoundary(se)
        #se.addItem({'snap_angle': 'fortyfive_degree'})
        se.addItem({'via': self.pcbRule.viaName()})
        se.addItem({'control': {'via_at_smd': 'off'}})
        se.startGroup('rule')
        se.addItem({'width': mm2um(self.pcbRule.trackWidth)}, indent=True)
        se.addItem({'clearance': mm2um(self.pcbRule.clearance)})
        #pin_pin, pin_smd, smd_smd, pin_wire, smd_wire, wire_wire, smd_via, pin_via, via_wire, via_via 
        se.addItem({'clearance': [mm2um(self.pcbRule.clearance), {'type': 'default_smd'}]})
        se.addItem({'clearance': [mm2um(self.pcbRule.smdSmdClearance), {'type': 'smd_smd'}]})
        se.endGroup()
        #autoroute_settings经过会出现各种奇怪的错误，所以不需要还更好
        """
        se.startGroup('autoroute_settings')
        se.addItem({'fanout': 'off'}, indent=True)
        se.addItem({'app.freerouting.autoroute': 'on'})
        se.addItem({'postroute': 'on'})
        se.addItem({'vias': 'on'})
        se.addItem({'via_costs': 50})
        se.addItem({'plane_via_costs': 5})
        se.addItem({'start_ripup_costs': 100})
        se.addItem({'start_pass_no': 34})
        se.startGroup('layer_rule')
        se.addItem('F.Cu', newline=False)
        se.addItem({'active': 'on'}, indent=True)
        se.addItem({'preferred_direction': 'horizontal'})
        se.addItem({'preferred_direction_trace_costs': 1.0})
        se.addItem({'against_preferred_direction_trace_costs': 2.4})
        se.endGroup(newline=True) #layer_rule end
        se.startGroup('layer_rule')
        se.addItem('B.Cu', newline=False)
        se.addItem({'active': 'on'}, indent=True)
        se.addItem({'preferred_direction': 'vertical'})
        se.addItem({'preferred_direction_trace_costs': 1.0})
        se.addItem({'against_preferred_direction_trace_costs': 1.7})
        se.endGroup(newline=True) #layer_rule end
        se.endGroup(newline=True) #autoroute_settings end
        """
        se.endGroup(newline=True) #structure end

    #填写线路板外框
    def buildBoundary(self, se):
        #寻找一个最大面积的区域做为PCB绝对外框区域
        #这个地方比较麻烦的一点是有时候会使用多个线条组成多边形，而不是直接使用一个多边形做为线路板外框
        #所以规定如果使用线条，则一次画完首位相接（至少需要5个点，第一个点和最后一个点重合）
        areas = [] #每个图像的面积
        for elem in self.uElems:
            if (elem.layerIdx != LAYER_U): #仅计算U层的面积
                areas.append(0.0)
                continue

            if isinstance(elem, SprintPolygon):
                areas.append(ComputePolygonArea(elem.points))
            elif isinstance(elem, SprintCircle):
                areas.append(3.14159 * elem.radius * elem.radius)
            elif isinstance(elem, SprintTrack) and (len(elem.points) >= 5):
                areas.append(ComputePolygonArea(elem.points))
            else:
                areas.append(0.0)

        maxAreaIdx = areas.index(max(areas))

        #将U层最大外框移到第一个元素位置
        maxElem = self.uElems.pop(maxAreaIdx)
        self.uElems.insert(0, maxElem)

        #PCB大小范围
        pcbBoundary = True
        for elem in self.uElems:
            #第一个为线路板轮廓，其他的为禁布区
            bbPath = ['pcb', 0] if pcbBoundary else ['F.Cu', 0] #第一个参数是信号层，第二个参数是线宽
            if isinstance(elem, (SprintTrack, SprintPolygon)):
                for (x, y) in elem.points:
                    bbPath.append(mm2um(x))
                    bbPath.append(self.umY(y))
            elif isinstance(elem, SprintCircle):
                points = cutCircle(elem.center[0], elem.center[1], elem.radius, 36) #将圆切分为36分
                for (x, y) in points:
                    bbPath.append(mm2um(x))
                    bbPath.append(self.umY(y))
            else:
                continue

            if (pcbBoundary):
                se.addItem({'boundary': {'path': bbPath}})
            else:
                se.addItem({'keepout': ["", {'polygon': bbPath}]})
                bbPath[0] = 'B.Cu' #对应禁止布线区，正反面都不允许布线
                se.addItem({'keepout': ["", {'polygon': bbPath}]})

            pcbBoundary = False

    #收集所有U层元素和其他层的禁布区
    def getAllLayerUAndKeepoutZone(self):
        return [elem for elem in self.textIo.baseDrawElements() 
            if ((elem.layerIdx == LAYER_U) or (isinstance(elem, SprintPolygon) and elem.cutout))]

    #生成元件放置位置
    def buildPlacement(self, se):
        compDict = self.compDict
        firstIndent = True
        se.startGroup('placement')
        for name in compDict:
            compList = compDict[name]['instance']
            se.startGroup('component', indent=firstIndent)
            firstIndent = False
            se.addItem(name, newline=False)
            compIndent = True
            for comp in compList:
                if (comp.getLayer() == LAYER_C1):
                    compLayer = 'front'
                    rotation = 0
                    #x = comp.xMin
                else:
                    compLayer = 'back'
                    rotation = 0 #180
                    #x = comp.xMax
                #pn = {'PN': comp.value if comp.value else ''}
                se.addItem({'place': [comp.name, mm2um(comp.pos[0]), 
                    self.umY(comp.pos[1]), compLayer, rotation, {'PN': ''}]}, indent=compIndent)
                compIndent = False
            se.endGroup(newline=True) #component end
        se.endGroup(newline=True) #placement end

    #生成元件图像库
    def buildImageLibrary(self, se):
        compDict = self.compDict
        imageFirstIndent = True
        for name in compDict:
            image = compDict[name]['image']
            #imgyMax = image.yMax
            se.startGroup('image', indent=imageFirstIndent)
            imageFirstIndent = False
            se.addItem(name, newline=False)
            #将Component里面的绘图元素一一翻译出来
            outlineFirstIndent = True
            for elem in image.baseDrawElements():
                if isinstance(elem, SprintTrack):
                    #为避免freerouting将Track封闭，这里两两组成线条
                    for idx in range(len(elem.points) - 1):
                        x1, y1 = elem.points[idx]
                        x2, y2 = elem.points[idx + 1]
                        params = ['signal', mm2um(elem.width), mm2um(x1), self.umY(y1), mm2um(x2), self.umY(y2)]
                        se.addItem({'outline': {'path': params}}, indent=outlineFirstIndent)
                        outlineFirstIndent = False
                elif isinstance(elem, SprintPolygon):
                    params = ['signal', mm2um(elem.width)]
                    for x, y in elem.points:
                        params.append(mm2um(x))
                        params.append(-mm2um(y))
                    se.addItem({'outline': {'path': params}}, indent=outlineFirstIndent)
                    outlineFirstIndent = False
                elif isinstance(elem, SprintCircle):
                    if ((elem.start is None) or (elem.stop is None)): #圆
                        se.addItem({'outline': {'circle': ['signal', mm2um(elem.radius * 2),
                            mm2um(elem.center[0]), -mm2um(elem.center[1])]}}, indent=outlineFirstIndent)
                        outlineFirstIndent = False
                    if 0:  #圆弧
                        pts = cutCircle(elem.center[0], elem.center[1], elem.radius, 10, elem.stop, elem.start)
                        #为避免freerouting将Track封闭，这里两两组成线条
                        for idx in range(len(pts) - 1):
                            x1, y1 = pts[idx]
                            x2, y2 = pts[idx + 1]
                            params = ['signal', mm2um(elem.width), mm2um(x1), self.umY(y1), mm2um(x2), self.umY(y2)]
                            se.addItem({'outline': {'path': params}}, indent=outlineFirstIndent)
                            outlineFirstIndent = False
                elif isinstance(elem, SprintPad):
                    #如果外径和内径相同，则认为是开孔，而不是插件焊盘
                    if ((elem.padType == 'PAD') and (elem.size == elem.drill) and (elem.drill > 0)):
                        cirParams = ['F.Cu', mm2um(elem.drill), mm2um(elem.pos[0]), self.umY(elem.pos[1])]
                        se.addItem({'keepout': ['', {'circle': cirParams}]}, indent=outlineFirstIndent)
                        outlineFirstIndent = False
                        cirParams[0] = 'B.Cu'
                        se.addItem({'keepout': ['', {'circle': cirParams}]})
                    else:
                        pinParams = [elem.generateDsnName(), elem.padId, mm2um(elem.pos[0]), self.umY(elem.pos[1])]
                        if elem.rotation: #很奇怪，在freerouting中插件焊盘和贴片焊盘的旋转方向是相反的
                            #pinParams.insert(1, {'rotate': (360 - elem.rotation) if (elem.padType == 'PAD') else elem.rotation})
                            pinParams.insert(1, {'rotate': 360 - elem.rotation})
                        se.addItem({'pin': pinParams}, indent=outlineFirstIndent)
                        outlineFirstIndent = False

                        #如果是单面焊盘，因为对面没有焊盘占位，所以在钻孔位置添加一个禁止布线区
                        if ((elem.padType == 'PAD') and (elem.size > elem.drill) and (elem.drill > 0) and (not elem.via)):
                            keepoutLayer = 'B.Cu' if (elem.layerIdx == LAYER_C1) else 'F.Cu'
                            cirParams = [keepoutLayer, mm2um(elem.drill), mm2um(elem.pos[0]), self.umY(elem.pos[1])]
                            se.addItem({'keepout': ['', {'circle': cirParams}]}, indent=outlineFirstIndent)
                            outlineFirstIndent = False
                            
            se.endGroup(newline=True) #image end

    #生成焊盘库
    def buildPadLibrary(self, se):
        padDict = self.padDict
        firstIndent = False #上面的Image已经缩进了
        for name in padDict:
            pad = padDict[name][0]
            if (pad.layerIdx not in (LAYER_C1, LAYER_C2)):
                continue

            se.startGroup('padstack', indent=firstIndent)
            firstIndent = False
            se.addItem(name, newline=False)
            rotation = pad.rotation
            form = pad.form
            padIndent = True
            if ((pad.padType == 'PAD') and (form not in (PAD_FORM_SQUARE, PAD_FORM_RECT_H, PAD_FORM_RECT_V))): #插件焊盘
                size = pad.size
                via = pad.via
                if via:
                    layerStrs = ['F.Cu', 'B.Cu']
                elif (pad.layerIdx == LAYER_C1):
                    layerStrs = ['F.Cu']
                else:
                    layerStrs = ['B.Cu']

                if (form == PAD_FORM_ROUND): #圆焊盘
                    for layerStr in layerStrs:
                        se.addItem({'shape': {'circle': [layerStr, mm2um(size)]}}, indent=padIndent)
                        padIndent = False
                elif (form == PAD_FORM_OCTAGON): #八角焊盘
                    for layerStr in layerStrs:
                        se.addItem({'shape': {'path': [layerStr, mm2um(size), 0, 0, 0, 0, {'aperture_type': 'square'}]}}, indent=padIndent)
                        padIndent = False
                else:
                    if (form in (PAD_FORM_RECT_ROUND_H, PAD_FORM_RECT_OCTAGON_H)): #横长条
                        (x1, y1) = -size/2, 0
                        (x2, y2) = size/2, 0
                    else: #竖长条
                        (x1, y1) = 0, -size/2
                        (x2, y2) = 0, size/2

                    for layerStr in layerStrs:
                        se.addItem({'shape': {'path': [layerStr, mm2um(size), mm2um(x1), self.umY(y1), 
                            mm2um(x2), self.umY(y2)]}}, indent=padIndent)
                        padIndent = False
            else: #SMDPAD或方形的插件焊盘
                if (pad.padType == 'SMDPAD'):
                    width, height = pad.sizeX, pad.sizeY
                    layerStrs = ['F.Cu'] if (pad.layerIdx == LAYER_C1) else ['B.Cu']
                else:
                    if (form == PAD_FORM_SQUARE):
                        width, height = pad.size, pad.size
                    elif (form == PAD_FORM_RECT_H):
                        width, height = pad.size * 2, pad.size
                    else: #PAD_FORM_RECT_V
                        width, height = pad.size, pad.size * 2
                    if pad.via:
                        layerStrs = ['F.Cu', 'B.Cu']
                    elif (pad.layerIdx == LAYER_C1):
                        layerStrs = ['F.Cu']
                    else:
                        layerStrs = ['B.Cu']
                
                x1, y1 = -mm2um(width/2), -mm2um(height/2)
                x2, y2 = -x1, -y1
                for layerStr in layerStrs:
                    se.addItem({'shape': {'rect': [layerStr, x1, y1, x2, y2]}}, indent=padIndent)
                    padIndent = False

            se.addItem({'attach': 'off'})
            se.endGroup(newline=True) #padstack end

        #添加过孔信息
        se.startGroup('padstack', indent=False)
        se.addItem(self.pcbRule.viaName(), newline=False)
        se.addItem({'shape': {'circle': ['F.Cu', mm2um(self.pcbRule.viaDiameter)]}}, indent=True)
        se.addItem({'shape': {'circle': ['B.Cu', mm2um(self.pcbRule.viaDiameter)]}})
        se.endGroup(newline=True) #padstack end
    
    #创建网络连接段
    def buildNetwork(self, se):
        compList = self.compList
        netList = [] #元素是一个相互连接的焊盘列表[[1, 7, 8], [2, 3, 4],...]
        #分析相互连接情况
        for comp in compList:
            pads = comp.getPads()
            for pad in pads:
                padId = pad.padId
                #找到对应的焊盘ID所在的index
                foundIdx = -1
                for idx, net in enumerate(netList):
                    if padId in net:
                        foundIdx = idx
                        break

                if (foundIdx >= 0):
                    netList[foundIdx].extend(pad.connectToOtherPads)
                else: #没找到
                    netList.append([padId, *pad.connectToOtherPads])

        #网表里面去掉重复的焊盘ID
        netList = [set(net) for net in netList]
        #print(netList)
        padIdSeqDict = self.padIdSeqDict

        se.startGroup('network')
        firstIndent = True
        netNames = ['sprint_default', '', ]
        idx = 0
        for net in netList:
            #if len(net) <= 1: #如果只有一个管脚，就不输出了
            #    continue
            idx += 1
            name = 'net-{}'.format(idx)
            se.startGroup('net', indent=firstIndent)
            firstIndent = False
            netNames.append(name)
            se.addItem(name, newline=False)
            #将焊盘ID修改为“元件名-焊盘ID”形式
            se.addItem({'pins': [f'{padIdSeqDict[item]["compName"]}-{padIdSeqDict[item]["seqNum"]}' 
                for item in net if item in padIdSeqDict]}, indent=True)
            se.endGroup(newline=True) #net end

        se.startGroup('class', indent=firstIndent)
        se.addItem(netNames, newline=False)
        se.addItem({'circuit': {'use_via': self.pcbRule.viaName()}}, indent=True)
        se.addItem({'rule': [{'width': mm2um(self.pcbRule.trackWidth), 'clearance': mm2um(self.pcbRule.clearance)}]})
        se.endGroup(newline=True) #class end

        se.endGroup(newline=True) #network end

    #生成预先布好的走线，这些走线是不能被覆盖的
    def buildWiring(self, se):
        wires = self.wires
        se.startGroup('wiring')
        if not wires:
            se.endGroup(newline=False) #wiring end
            return

        firstIndent = True
        for wire in wires:
            layerName = 'F.Cu' if (wire.layerIdx == LAYER_C1) else 'B.Cu'
            params = [layerName, mm2um(wire.width)]
            for x, y in wire.points:
                params.append(mm2um(x))
                params.append(self.umY(y))
            
            se.addItem({'wire': [{'path': params}, {'type': 'protect'}]}, indent=firstIndent)
            firstIndent = False
        se.endGroup(newline=True) #wiring end

    #构建一个焊盘ID和元件名的字典对应关系，键为焊盘ID，值为[元件名, 焊盘在元件内的索引(从1开始)]
    def buildPadIdSeqDict(self):
        padIdSeqDict = {}
        for comp in self.compList:
            pads = comp.getPads()
            for idx, pad in enumerate(pads, 1):
                padIdSeqDict[pad.padId] = {'compName': comp.name, 'seqNum': idx}

        return padIdSeqDict

if __name__ == '__main__':
    if 0:
        from sprint_struct.sprint_textio_parser import SprintTextIoParser
        p = SprintTextIoParser()
        textIo = p.parse(r'C:\Users\su\Desktop\testSprint\1.txt')
        dsnFile = r'C:\Users\su\Desktop\testSprint\dsnex.dsn'
        exporter = SprintExportDsn(textIo)
        ret = exporter.export()
        with open(dsnFile, 'w', encoding='utf-8') as f:
            f.write(ret.output)
        with open(dsnFile + '.pickle', 'wb') as f:
            pickle.dump(exporter, f)
