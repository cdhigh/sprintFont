#!/usr/bin/env python
#-*- coding:utf-8 -*-
"""
表示一个元件
Author: cdhigh <https://github.com/cdhigh>
"""
from operator import itemgetter
from .sprint_element import *
from .sprint_pad import SprintPad

class SprintComponent(SprintElement):
    def __init__(self):
        super().__init__(self)
        self.pos = (0, 0) #用于导出DSN使用，默认使用第一个焊盘的坐标，如果没有焊盘，使用第一个元素的坐标
        self.compName = '' #用于元件的名字，比如R1
        self.value = '' #用于元件的值，比如10k
        self.comment = '' #元件注释
        self.package = '' #封装名字
        self.usePickplace = None #如果为None，则根据是否存在封装名字来自动确定
        self.txtHeight = 1.3 #单位为毫米
        self.txtThickness = 1  #0-细体，1-正常，2-粗体
        self.txtStyle = 1  #0-窄体，1-正常，2-宽体
        self.namePos = None #如果存在，则为 (x,y) 元祖，单位为毫米
        self.valuePos = None #如果存在，则为 (x,y) 元祖，单位为毫米
        self.nameLayer = LAYER_S1
        self.valueLayer = LAYER_S1
        self.nameVisible = True
        self.valueVisible = True
        self.nameRotation = 0
        self.valueRotation = 0
        self.pickRotation = None #仅适用于贴片机的旋转，不是真实元件的旋转，单位为度
        self.elements = [] #各种绘图元素，都是SprintElement的子类

    #元件的板层不能直接使用layerIdx属性，需要使用此函数获取
    def getLayer(self):
        padLayer = LAYER_C1
        padVia = False
        for pad in self.getPads():
            padLayer = pad.layerIdx
            if (pad.padType == 'SMDPAD'):
                return pad.layerIdx #如果有贴片焊盘，则贴片焊盘的板层就是贴片元件的板层
            elif pad.via:
                padVia = True

        #插件元件需要区分对待，双面焊盘就使用名字的丝印板层对应的铜层
        if padVia:
            return LAYER_C1 if (self.nameLayer == LAYER_S1) else LAYER_C2
        else: #如果是单面插件焊盘，则使用焊盘所在层对面的板层做为元件面
            return LAYER_C2 if (padLayer == LAYER_S1) else LAYER_C1

    #返回此元件的安装类型, 是SMD还是通孔, 返回"through_hole"/"smd"
    def getMountingType(self):
        for pad in self.getPads(): #有任何一个单面或双面插件焊盘就是插件元件
            if (pad.via or (pad.padType == 'PAD')):
                return 'through_hole'
        return 'smd'
        
    def isValid(self):
        return (len(self.elements) > 0)

    #转换为字符串TextIO
    def __str__(self):
        return self.toStr(forCompare=False)

    #转换为字符串
    #forCompare: 是否用于比较两个元件是否相等，忽略焊盘ID和连接/名字等信息
    def toStr(self, forCompare=False):
        if not self.isValid():
            return ''

        outStr = []

        #先生成元件的描述头
        self.compName = self.justifiedText(self.compName)
        self.value = self.justifiedText(self.value)
        self.comment = self.justifiedText(self.comment)
        self.package = self.justifiedText(self.package)

        compHeadStrList = ['BEGIN_COMPONENT',]
        if self.comment:
            compHeadStrList.append('COMMENT=|{}|'.format(self.comment))
        if self.package:
            usePickplace = self.usePickplace
            if usePickplace is None:
                usePickplace = 'true'
            compHeadStrList.append('USE_PICKPLACE={},PACKAGE=|{}|'.format(usePickplace, self.package))
            if self.pickRotation:
                compHeadStrList.append('ROTATION={:0.0f}'.format(self.pickRotation))
        compHead = ','.join(compHeadStrList) + ';'

        outStr.append(compHead)

        #如果没有预定义名字和值的位置，则将名字和值放在元件上方
        #Example: ID_TEXT,LAYER=2,POS=408300/370050,HEIGHT=13000,THICKNESS=2,TEXT=|R1|;
        namePos = self.namePos
        if not namePos:
            namePos = (self.xMin + (self.xMax - self.xMin) / 2 - 1, self.yMin - 2)
        valuePos = self.valuePos
        if not valuePos:
            valuePos = (self.xMin + (self.xMax - self.xMin) / 2 - 1, self.yMin - 1)
        
        #名字
        if not forCompare:
            nameVisible = 'true' if (self.nameVisible and self.compName) else 'false'
            idText = ['ID_TEXT,VISIBLE={},LAYER={},POS={}/{},HEIGHT={}'.format(nameVisible, self.nameLayer, 
                self.mm2um01(namePos[0]), self.mm2um01(namePos[1]), self.mm2um01(self.txtHeight))]
            if (self.txtThickness != 1):
                idText.append('THICKNESS={}'.format(self.txtThickness))
            if (self.txtStyle != 1):
                idText.append('STYLE={}'.format(self.txtStyle))
            if (self.nameLayer in (LAYER_C2, LAYER_S2)):
                idText.append('MIRROR_HORZ=true')
            idText.append('TEXT=|{}|'.format(self.compName))
            if self.name:
                idText.append('NAME=|{}|'.format(self.justifiedText(self.name)))
            outStr.append(','.join(idText) + ';')

            #数值
            valueVisible = 'true' if (self.valueVisible and self.value) else 'false'
            valueText = ['VALUE_TEXT,VISIBLE={},LAYER={},POS={}/{},HEIGHT={}'.format(valueVisible, self.valueLayer, 
                self.mm2um01(valuePos[0]), self.mm2um01(valuePos[1]), self.mm2um01(self.txtHeight))]
            if (self.txtThickness != 1):
                valueText.append('THICKNESS={}'.format(self.txtThickness))
            if (self.txtStyle != 1):
                valueText.append('STYLE={}'.format(self.txtStyle))
            if (self.valueLayer in (LAYER_C2, LAYER_S2)):
                valueText.append('MIRROR_HORZ=true')
            valueText.append('TEXT=|{}|'.format(self.value))
            if self.name:
                valueText.append('NAME=|{}|'.format(self.justifiedText(self.name)))
            outStr.append(','.join(valueText) + ';')

            #逐个添加里面的绘图元素
            outStr.extend([str(obj) for obj in self.elements])
        else: #用于比较为目的的转换字符串
            padId = 1
            for obj in self.baseDrawElements():
                if isinstance(obj, SprintPad):
                    outStr.append(obj.toStr(overwritePadId=padId))
                    padId += 1
                else:
                    outStr.append(str(obj))
        
        outStr.append('END_COMPONENT;')
        
        #合并绘图元素，并去掉可能的空字符串
        return '\n'.join([s for s in outStr if s])

    #统一的添加绘图元素接口
    def add(self, elem: SprintElement):
        if elem:
            elem.updateSelfBbox()
            self.updateBbox(elem)
            self.elements.append(elem)
            self.updatePos()
            
    #添加列表中所有元素
    def addAll(self, elemList: list):
        for elem in elemList:
            self.add(elem)

    #删除某一个对象，成功返回True
    def remove(self, obj):
        from .sprint_group import SprintGroup
        for elem in self.elements:
            if elem is obj:
                self.elements.remove(obj)
                self.updateSelfBbox()
                return True
                
        for elem in self.elements:
            if isinstance(elem, (SprintComponent, SprintGroup)):
                if elem.remove(obj):
                    self.updateSelfBbox()
                    return True
                    
        return False

    #根据绘图元素，更新元件自己的外框
    def updateBbox(self, elem):
        if elem.xMin < self.xMin:
            self.xMin = elem.xMin
        if elem.xMax > self.xMax:
            self.xMax = elem.xMax
        if elem.yMin < self.yMin:
            self.yMin = elem.yMin
        if elem.yMax > self.yMax:
            self.yMax = elem.yMax

    #更新元件所占的外框
    def updateSelfBbox(self):
        self.xMin = self.yMin = 100000.0
        self.xMax = self.yMax = -100000.0
        for elem in self.elements:
            elem.updateSelfBbox()
            self.updateBbox(elem)

    #返回此元件的几何中心 (x, y)
    def centroid(self):
        return (self.xMin + self.xMax) / 2, (self.yMin + self.yMax) / 2
        
    #获取特定板层的所有元素，返回一个列表
    def getAllElementsInLayer(self, layerIdx: int):
        return [elem for elem in self.elements if elem.layerIdx == layerIdx]
    
    #获取所有的下层基本绘图元素，返回一个列表
    def baseDrawElements(self):
        from .sprint_group import SprintGroup
        elems = []
        for elem in self.elements:
            if isinstance(elem, SprintGroup):
                elems.extend(elem.baseDrawElements())
            else:
                elems.append(elem)
        return elems

    #返回此元件的所有焊盘
    def getPads(self):
        return [elem for elem in self.baseDrawElements() if isinstance(elem, SprintPad)]

    #刷新元件的定位点，以最左边的焊盘中心为元件定位点
    def updatePos(self):
        padsSize = sorted([pad.pos for pad in self.getPads()], key=itemgetter(0))
        if padsSize:
            self.pos = padsSize[0]
        else:
            self.pos = (self.elements[0].xMin, self.elements[0].yMin)

    #复制一个自身，
    #x/y: 新的原点
    #如果不提供原点，则将内部的坐标都相对自己的定位点做为新原点进行移动
    def cloneToOrigin(self, x: float=None, y: float=None):
        ins = SprintComponent()
        self.updateSelfBbox()
        ins.compName = self.compName
        ins.value = self.value
        ins.comment = self.comment
        ins.package = self.package
        ins.usePickplace = self.usePickplace
        ins.txtHeight = self.txtHeight
        ins.txtThickness = self.txtThickness
        ins.txtStyle = self.txtStyle
        ins.namePos = self.namePos
        ins.valuePos = self.valuePos
        ins.nameLayer = self.nameLayer
        ins.valueLayer = self.valueLayer
        ins.nameVisible = self.nameVisible
        ins.valueVisible = self.valueVisible
        ins.pickRotation = self.pickRotation
        ins.name = self.name
        self.updatePos()
        if x is None or y is None:
            x, y = self.pos
            
        padId = 1
        for elem in self.elements:
            #元件内的焊盘重新编号，从1开始
            if isinstance(elem, SprintPad):
                ins.elements.append(elem.cloneToNewOrigin(x, y, padId))
                padId += 1
            else:
                ins.elements.append(elem.cloneToNewOrigin(x, y))
        ins.updateSelfBbox()
        return ins

    #移动自身的位置
    def moveByOffset(self, offsetX: float, offsetY: float):
        for elem in self.elements:
            elem.moveByOffset(offsetX, offsetY)
        self.updateSelfBbox()
