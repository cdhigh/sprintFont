#!/usr/bin/env python
#-*- coding:utf-8 -*-
"""
表示一个元件
Author: cdhigh <https://github.com/cdhigh>
"""
from .sprint_element import *

class SprintComponent(SprintElement):
    def __init__(self):
        super().__init__(self)
        self.name = '' #用于元件的名字，比如R1
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
        self.pickRotation = None #仅适用于贴片机的旋转，不是真实元件的旋转，单位为度
        self.elements = [] #各种绘图元素，都是SprintElement的子类
        
    #复制一个自身，并且将内部的坐标都相对自己外框的左下角做为新原点进行移动，
    #并且为了避免小数点误差，方便计算两个对象是否相等，单位转换为不带小数点的微米/度
    def cloneToSelfOrigin(self):
        ins = SprintComponent()
        ins.name = self.name
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
        ins.elements = [elem.cloneToNewOrigin(self.xMin, self.yMin) for elem in self.elements]
        ins.updateSelfBbox()
        return ins

    def isValid(self):
        return (len(self.elements) > 0)

    #转换为字符串TextIO
    def __str__(self):
        if not self.isValid():
            return ''

        outStr = []

        #先生成元件的描述头
        self.name = str(self.name).replace(';', '_').replace(',', '_').replace('|', '_')
        self.value = str(self.value).replace(';', '_').replace(',', '_').replace('|', '_')
        self.comment = str(self.comment).replace(';', '_').replace(',', '_').replace('|', '_')
        self.package = str(self.package).replace(';', '_').replace(',', '_').replace('|', '_')

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
        nameVisible = 'true' if (self.nameVisible and self.name) else 'false'
        idText = ['ID_TEXT,VISIBLE={},LAYER={},POS={:0.0f}/{:0.0f},HEIGHT={:0.0f}'.format(
            nameVisible, self.nameLayer, namePos[0] * 10000, namePos[1] * 10000, self.txtHeight * 10000)]
        if (self.txtThickness != 1):
            idText.append('THICKNESS={}'.format(self.txtThickness))
        if (self.txtStyle != 1):
            idText.append('STYLE={}'.format(self.txtStyle))
        if (self.nameLayer in (LAYER_C2, LAYER_S2)):
            idText.append('MIRROR_HORZ=true')
        idText.append('TEXT=|{}|;'.format(self.name)) #注意最后有一个分号
        outStr.append(','.join(idText))

        #数值
        valueVisible = 'true' if (self.valueVisible and self.value) else 'false'
        valueText = ['VALUE_TEXT,VISIBLE={},LAYER={},POS={:0.0f}/{:0.0f},HEIGHT={:0.0f}'.format(
            valueVisible, self.valueLayer, valuePos[0] * 10000, valuePos[1] * 10000, self.txtHeight * 10000)]
        if (self.txtThickness != 1):
            valueText.append('THICKNESS={}'.format(self.txtThickness))
        if (self.txtStyle != 1):
            valueText.append('STYLE={}'.format(self.txtStyle))
        if (self.valueLayer in (LAYER_C2, LAYER_S2)):
            valueText.append('MIRROR_HORZ=true')
        valueText.append('TEXT=|{}|;'.format(self.value)) #注意最后有一个分号
        outStr.append(','.join(valueText))

        #逐个添加里面的绘图元素
        outStr.extend([str(obj) for obj in self.elements])
        
        outStr.append('END_COMPONENT;')
        
        #合并绘图元素，并去掉可能的空字符串
        return '\n'.join([s for s in outStr if s])

    #统一的添加绘图元素接口
    def add(self, elem: SprintElement):
        if elem:
            #print('component add ', elem)
            elem.updateSelfBbox()
            self.updateBbox(elem)
            self.elements.append(elem)

    #添加列表中所有元素
    def addAll(self, elemList: list):
        for elem in elemList:
            self.add(elem)

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
        for elem in self.elements:
            elem.updateSelfBbox()
    
    #获取特定板层的所有元素，返回一个列表
    def getAllElementsInLayer(self, layerIdx: int):
        return [elem for elem in self.elements if elem.layerIdx == layerIdx]
    
    #获取所有的下层绘图元素，返回一个列表
    def children(self):
        from .sprint_group import SprintGroup
        elems = []
        for elem in self.elements:
            if isinstance(elem, (SprintComponent, SprintGroup)):
                elems.extend(elem.children())
            else:
                elems.append(elem)
        return elems

