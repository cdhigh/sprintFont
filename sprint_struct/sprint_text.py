#!/usr/bin/env python
#-*- coding:utf-8 -*-
"""
文本定义
Author: cdhigh <https://github.com/cdhigh>
"""
from .sprint_component import SprintComponent

#里面的长度单位都是mm
class SprintText(SprintComponent):
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
        self.rotation = None #角度乘以100
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
            outStr.append('CUTOUT={}'.format('true' if self.cutout else 'false'))
        if self.soldermask is not None:
            outStr.append('SOLDERMASK={}'.format('true' if self.soldermask else 'false'))
        if self.style is not None:
            outStr.append('STYLE={}'.format(self.style))
        if self.thickness is not None:
            outStr.append('THICKNESS={}'.format(self.thickness * 10000))
        if self.rotation:
            outStr.append('ROTATION={:0.0f}'.format(self.rotation)) #文本的旋转单位就是度
        if self.mirrorH is not None:
            outStr.append('MIRROR_HORZ={}'.format('true' if self.mirrorH else 'false'))
        if self.mirrorV is not None:
            outStr.append('MIRROR_VERT={}'.format('true' if self.mirrorV else 'false'))
        outStr.append('TEXT=|{}|'.format(self.text))

        return ','.join(outStr) + ';'