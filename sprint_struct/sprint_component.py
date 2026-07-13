#!/usr/bin/env python
#-*- coding:utf-8 -*-
"""
表示一个元件
Author: cdhigh <https://github.com/cdhigh>
"""
from operator import itemgetter
from .sprint_element import *
from .sprint_pad import SprintPad
from .sprint_text import SprintText

class SprintComponent(SprintElement):
    def __init__(self):
        super().__init__(self)
        self.pos = (0, 0) #用于导出DSN使用，默认使用第一个焊盘的坐标，如果没有焊盘，使用第一个元素的坐标
        self.idText = SprintText()
        self.valueText = SprintText()
        self.comment = '' #元件注释
        self.package = '' #封装名字
        self.usePickplace = None #如果为None，则根据是否存在封装名字来自动确定
        self.pickRotation = None #仅适用于贴片机的旋转，不是真实元件的旋转，单位为度
        self.elements = [] #各种绘图元素，都是SprintElement的子类

    @property
    def compName(self):
        return self.idText.text

    #元件的板层需要计算获取
    @property
    def layerIdx(self):
        padLayer = LAYER_C1
        hasVia = False
        for pad in self.getPads():
            padLayer = pad.layerIdx
            if pad.padType == 'SMDPAD':
                return pad.layerIdx #如果有贴片焊盘，则贴片焊盘的板层就是贴片元件的板层
            elif pad.via:
                hasVia = True

        #插件元件需要区分对待
        if hasVia: #双面焊盘就使用名字的丝印板层对应的铜层
            return LAYER_C1 if (self.idText.layerIdx == LAYER_S1) else LAYER_C2
        else: #如果是单面插件焊盘，则使用焊盘所在层对面的板层做为元件面
            return LAYER_C2 if (padLayer == LAYER_S1) else LAYER_C1

    #返回此元件的安装类型, 是SMD还是通孔, 返回"through_hole"/"smd"
    def getMountingType(self):
        for pad in self.getPads(): #有任何一个单面或双面插件焊盘就是插件元件
            if pad.via or (pad.padType == 'PAD'):
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
        self.comment = self.sanitizeText(self.comment)
        self.package = self.sanitizeText(self.package)

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

        if forCompare: #用于比较两个元件是否是同一种,忽略焊盘ID和连接/名字等信息
            padId = 1
            for obj in self.baseDrawElements(forCompare=True):
                if isinstance(obj, SprintPad):
                    outStr.append(obj.toStr(padId=padId))
                    padId += 1
                else:
                    outStr.append(str(obj))
        else: #正常输出
            #ID_TEXT/VALUE_TEXT
            #如果没有预定义名字和值的位置，则将名字和值放在元件上方
            namePos = (self.xMin + (self.xMax - self.xMin) / 2 - 1, self.yMin - 2)
            valuePos = (namePos[0], namePos[1] + 1)
            outStr.append(self.idText.toComponentText('ID_TEXT', namePos))
            outStr.append(self.valueText.toComponentText('VALUE_TEXT', valuePos))

            #逐个添加里面的绘图元素
            outStr.extend([str(obj) for obj in self.elements])

        outStr.append('END_COMPONENT;')
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
        self.xMin = min(elem.xMin, self.xMin)
        self.xMax = max(elem.xMax, self.xMax)
        self.yMin = min(elem.yMin, self.yMin)
        self.yMax = max(elem.yMax, self.yMax)

    #更新元件所占的外框
    def updateSelfBbox(self):
        self.xMin = self.yMin = float('inf')
        self.xMax = self.yMax = float('-inf')
        for elem in self.elements:
            elem.updateSelfBbox()
            self.updateBbox(elem)

    #返回此元件的几何中心 (x, y)
    def centroid(self):
        return (self.xMin + self.xMax) / 2, (self.yMin + self.yMax) / 2
        
    #获取特定板层的所有元素，返回一个列表
    def getAllElementsInLayer(self, layerIdx: int):
        elems = []
        if self.idText.layerIdx == layerIdx:
            elems.append(self.idText)
        if self.valueText.layerIdx == layerIdx:
            elems.append(self.valueText)
        elems.extend([e for e in self.elements if e.layerIdx == layerIdx])
        return elems
    
    #获取所有的下层基本绘图元素，返回一个列表
    #forCompare: 用于比较两个元件是否是同一种,忽略名字/值信息
    def baseDrawElements(self, forCompare=False):
        from .sprint_group import SprintGroup
        elems = [] if forCompare else [self.idText, self.valueText]
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
        if x is None or y is None:
            x, y = self.pos

        self.updateSelfBbox()
        ins = SprintComponent()
        ins.idText = self.idText.cloneToNewOrigin(x, y)
        ins.valueText = self.valueText.cloneToNewOrigin(x, y)
        ins.comment = self.comment
        ins.package = self.package
        ins.usePickplace = self.usePickplace
        ins.pickRotation = self.pickRotation
        ins.name = self.name
        self.updatePos()
            
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
