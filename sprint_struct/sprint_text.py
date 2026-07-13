#!/usr/bin/env python
#-*- coding:utf-8 -*-
"""
文本定义
Author: cdhigh <https://github.com/cdhigh>
"""
from .sprint_element import *

#里面的长度单位都是mm
class SprintText(SprintElement):
    def __init__(self, layerIdx: int=1):
        super().__init__(layerIdx)
        self.pos = (0, 0)
        self.text = ''
        self.height = 0
        self.clearance = 0
        self.cutout = None
        self.soldermask = None
        self.style = None
        self.thickness = None
        self.rotation = 0
        self.mirrorH = None
        self.mirrorV = None
        self.visible = True  #仅用于component的ID_TEXT和VALUE_TEXT

    #多边形是否合法，至少要求为两个点
    def isValid(self):
        return (self.height > 0)

    #文本比较特殊，很难确定其确切的外框，所以使用中心点
    def updateSelfBbox(self):
        self.xMin = self.yMin = float('inf')
        self.xMax = self.yMax = float('-inf')
        self.updateBbox(self.pos[0], self.pos[1], self.height)
        
    def __str__(self):
        self.text = self.sanitizeText(self.text)

        outStr = ['TEXT,LAYER={},POS={}/{},HEIGHT={}'.format(
            self.layerIdx, self.mm2um01(self.pos[0]), self.mm2um01(self.pos[1]), self.mm2um01(self.height))]
        if self.clearance:
            outStr.append('CLEAR={}'.format(self.mm2um01(self.clearance)))
        if self.cutout is not None:
            outStr.append('CUTOUT={}'.format(self.booleanStr(self.cutout)))
        if self.soldermask is not None:
            outStr.append('SOLDERMASK={}'.format(self.booleanStr(self.soldermask)))
        if self.style is not None:
            outStr.append('STYLE={}'.format(self.style))
        if self.thickness is not None:
            outStr.append('THICKNESS={}'.format(self.thickness))
        if self.rotation:
            outStr.append('ROTATION={:0.0f}'.format(self.rotation * 1000))
        if self.mirrorH is not None:
            outStr.append('MIRROR_HORZ={}'.format(self.booleanStr(self.mirrorH)))
        if self.mirrorV is not None:
            outStr.append('MIRROR_VERT={}'.format(self.booleanStr(self.mirrorV)))
        outStr.append('TEXT=|{}|'.format(self.sanitizeText(self.text)))
        if self.name:
            outStr.append('NAME=|{}|'.format(self.sanitizeText(self.name)))

        return ','.join(outStr) + ';'

    #输出为组件的ID_TEXT/VALUE_TEXT字符串
    #prefix: ID_TEXT/VALUE_TEXT
    #fallBackPos: 如果自身没有被设置过位置，则使用传入的参数
    def toComponentText(self, prefix, fallBackPos=(0,0)):
        self.text = self.sanitizeText(self.text)

        pos = self.pos
        if pos is None or pos == (0, 0):
            pos = fallBackPos or (0,0)

        visible = 'true' if (self.visible and self.text) else 'false'
        outStr = ['{},VISIBLE={},LAYER={},POS={}/{},HEIGHT={}'.format(prefix, 
            visible, self.layerIdx, self.mm2um01(pos[0]), self.mm2um01(pos[1]), 
            self.mm2um01(self.height))]
        if self.thickness not in (1, None):
            outStr.append('THICKNESS={}'.format(self.thickness))
        if self.style not in (1, None):
            outStr.append('STYLE={}'.format(self.style))
        if self.layerIdx in (LAYER_C2, LAYER_S2):
            outStr.append('MIRROR_HORZ=true')
        outStr.append('TEXT=|{}|'.format(self.text))
        if self.name:
            outStr.append('NAME=|{}|'.format(self.sanitizeText(self.name)))

        return ','.join(outStr) + ';'


    #重载等号运算符，判断两个是否相等
    def __eq__(self, other):
        if not isinstance(other, SprintText):
            return False

        if ((self.layerIdx != other.layerIdx) or (self.pos != other.pos) or (self.text != other.text)
            or (self.height != other.height) or (self.rotation != other.rotation) or (self.mirrorH != other.mirrorH)
            or (self.mirrorV != other.mirrorV)):
            return False
        else:
            return True

    #复制一个自身，并且将坐标相对某个新原点进行移动，
    #ox/oy: 新的原点坐标
    def cloneToNewOrigin(self, ox: float, oy: float):
        ins = SprintText(self.layerIdx)
        ins.pos = (round(self.pos[0] - ox, 4), round(self.pos[1] - oy, 4))
        ins.text = self.text
        ins.height = self.height
        ins.clearance = self.clearance
        ins.cutout = self.cutout
        ins.soldermask = self.soldermask
        ins.style = self.style
        ins.thickness = self.thickness
        ins.rotation = self.rotation
        ins.mirrorH = self.mirrorH
        ins.mirrorV = self.mirrorV
        ins.name = self.name
        ins.visible = self.visible
        ins.updateSelfBbox()
        return ins

    #移动自身的位置
    def moveByOffset(self, offsetX: float, offsetY: float):
        self.pos = (round(self.pos[0] + offsetX, 4), round(self.pos[1] + offsetY, 4))
        self.updateSelfBbox()
