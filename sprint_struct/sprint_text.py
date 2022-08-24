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
        self.clearance = None
        self.cutout = None
        self.soldermask = None
        self.style = None
        self.thickness = None
        self.rotation = None
        self.mirrorH = None
        self.mirrorV = None

    #多边形是否合法，至少要求为两个点
    def isValid(self):
        return (self.height > 0)

    #文本比较特殊，很难确定其确切的外框，所以使用中心点
    def updateSelfBbox(self):
        self.xMin = self.xMax = self.pos[0]
        self.yMin = self.yMax = self.pos[1]

    def __str__(self):
        self.text = self.justifiedText(self.text)

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
            outStr.append('ROTATION={:0.0f}'.format(self.rotation)) #文本的旋转单位就是度，手册上是错的
        if self.mirrorH is not None:
            outStr.append('MIRROR_HORZ={}'.format(self.booleanStr(self.mirrorH)))
        if self.mirrorV is not None:
            outStr.append('MIRROR_VERT={}'.format(self.booleanStr(self.mirrorV)))
        outStr.append('TEXT=|{}|'.format(self.justifiedText(self.text)))
        if self.name:
            outStr.append('NAME=|{}|'.format(self.justifiedText(self.name)))

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
        ins.updateSelfBbox()
        return ins

    #移动自身的位置
    def moveByOffset(self, offsetX: float, offsetY: float):
        self.pos = (round(self.pos[0] - offsetX, 4), round(self.pos[1] - offsetY, 4))
        self.updateSelfBbox()
