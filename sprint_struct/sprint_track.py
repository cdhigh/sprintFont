#!/usr/bin/env python
#-*- coding:utf-8 -*-
"""
Track定义
Author: cdhigh <https://github.com/cdhigh>
"""

from .sprint_component import SprintComponent

#里面的长度单位都是mm
class SprintTrack(SprintComponent):
    def __init__(self, layerIdx: int=1, width: float=0):
        super().__init__(layerIdx)
        self.width = width
        self.points = [] #元素为(x,y)元祖
        self.clearance = None
        self.cutout = None
        self.soldermask = None
        self.flatstart = None
        self.flatend = None
    
    #增加一个点
    def addPoint(self, x: float, y: float):
        self.updateLimit(x, y)
        self.points.append((x, y))

    def __str__(self):
        if (len(self.points) < 2):
            return ''

        outStr = ['TRACK,LAYER={},WIDTH={:0.0f}'.format(self.layerIdx, self.width * 10000)]
        if self.clearance:
            outStr.append('CLEAR={:0.0f}'.format(self.clearance * 10000))
        if self.cutout is not None:
            outStr.append('CUTOUT={}'.format('true' if self.cutout else 'false'))
        if self.soldermask is not None:
            outStr.append('SOLDERMASK={}'.format('true' if self.soldermask else 'false'))
        if self.flatstart is not None:
            outStr.append('FLATSTART={}'.format('true' if self.flatstart else 'false'))
        if self.flatend is not None:
            outStr.append('FLATEND={}'.format('true' if self.flatend else 'false'))
        
        #点列表
        for idx, (x, y) in enumerate(self.points):
            outStr.append('P{}={:0.0f}/{:0.0f}'.format(idx, x * 10000, y * 10000))

        return ','.join(outStr) + ';'
