#!/usr/bin/env python
#-*- coding:utf-8 -*-
"""
文本定义
Author: cdhigh <https://github.com/cdhigh>
"""

#sprint的Text类
class SprintText:
    def __init__(self, layerIdx: int=1):
        self.layerIdx = layerIdx
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

    def __str__(self):
        outStr = ['TEXT,LAYER={},POS={:0.0f}/{:0.0f},TEXT=|{}|,HEIGHT={:0.0f}'.format(
            self.layerIdx, self.pos[0], self.pos[1], self.text, self.height)]
        if self.clearance:
            outStr.append('CLEAR={:0.0f}'.format(self.clearance))
        if self.cutout is not None:
            outStr.append('CUTOUT={}'.format('true' if self.cutout else 'false'))
        if self.soldermask is not None:
            outStr.append('SOLDERMASK={}'.format('true' if self.soldermask else 'false'))
        if self.style is not None:
            outStr.append('STYLE={}'.format(self.style))
        if self.thickness is not None:
            outStr.append('THICKNESS={}'.format(self.thickness))
        if self.rotation is not None:
            outStr.append('ROTATION={:0.0f}'.format(self.rotation))
        if self.mirrorH is not None:
            outStr.append('MIRROR_HORZ={:0.0f}'.format(self.mirrorH))
        if self.mirrorV is not None:
            outStr.append('MIRROR_VERT={:0.0f}'.format(self.mirrorV))

        return ','.join(outStr) + ';'