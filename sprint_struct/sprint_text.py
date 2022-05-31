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

    def __str__(self):
        self.text = str(self.text).replace(';', '_').replace(',', '_').replace('|', '_')

        outStr = ['TEXT,LAYER={},POS={:0.0f}/{:0.0f},HEIGHT={:0.0f}'.format(
            self.layerIdx, self.pos[0] * 10000, self.pos[1] * 10000, self.height * 10000)]
        if self.clearance:
            outStr.append('CLEAR={:0.0f}'.format(self.clearance * 10000))
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
        outStr.append('TEXT=|{}|'.format(self.text))

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
    #并且为了避免小数点误差，方便计算两个对象是否相等，单位转换为不带小数点的微米/度
    #ox/oy: 新的原点坐标
    def cloneToNewOrigin(self, ox: float, oy: float):
        ins = SprintText(self.layerIdx)
        ins.pos = (round((self.pos[0] - ox) * 1000), round((self.pos[1] - oy) * 1000))
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
        return ins