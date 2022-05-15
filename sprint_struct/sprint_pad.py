#!/usr/bin/env python
#-*- coding:utf-8 -*-
"""
焊盘定义
Author: cdhigh <https://github.com/cdhigh>
"""

#Pad的形状
PAD_FORM_ROUND = 1
PAD_FORM_OCTAGON = 2
PAD_FORM_SQUARE = 3
PAD_FORM_RECT_ROUND_H = 4
PAD_FORM_RECT_OCTAGON_H = 5
PAD_FORM_RECT_H = 6
PAD_FORM_RECT_ROUND_V = 7
PAD_FORM_RECT_OCTAGON_V = 8
PAD_FORM_RECT_V = 9


#sprint的Pad类
class SprintPad:
    def __init__(self, padType: str='PAD', layerIdx: int=1):
        self.padType = padType # 'PAD'/'SMDPAD'
        self.layerIdx = layerIdx
        self.pos = (0, 0)
        self.size = 0
        self.sizeX = 0
        self.sizeY = 0
        self.drill = 0
        self.form = PAD_FORM_ROUND
        self.clearance = 0
        self.soldermask = None
        self.rotation = None
        self.via = None
        self.thermal = None
        self.thermalTracksWidth = 0
        self.thermalTracksIndividual = None
        self.thermalTracks = 0
        self.padId = None
        self.connectToOtherPads = [] #从此焊盘到特定其他焊盘的直线

    def __str__(self):
        return self._toStrPad() if self.padType == 'PAD' else self._toStrSmdPad()

    #生成通孔焊盘的字符串
    def _toStrPad(self):
        outStr = ['PAD,LAYER={},POS={:0.0f}/{:0.0f},SIZE={:0.0f},DRILL={:0.0f},FORM={}'.format(
            self.layerIdx, self.pos[0], self.pos[1], self.size, self.drill, self.form)]
        if self.clearance:
            outStr.append('CLEAR={:0.0f}'.format(self.clearance))
        if self.soldermask is not None:
            outStr.append('SOLDERMASK={}'.format('true' if self.soldermask else 'false'))
        if self.rotation is not None:
            outStr.append('ROTATION={:0.0f}'.format(self.rotation))
        if self.via is not None:
            outStr.append('VIA={}'.format('true' if self.via else 'false'))
        if self.thermal is not None:
            outStr.append('THERMAL={}'.format('true' if self.thermal else 'false'))
        if self.thermalTracksWidth:
            outStr.append('THERMAL_TRACKS_WIDTH={:0.0f}'.format(self.thermalTracksWidth))
        if self.thermalTracksIndividual is not None:
            outStr.append('THERMAL_TRACKS_INDIVIDUAL={}'.format('true' if self.thermalTracksIndividual else 'false'))
        if self.thermalTracks:
            outStr.append('THERMAL_TRACKS={:0.0f}'.format(self.thermalTracks))
        if self.padId is not None:
            outStr.append('PAD_ID={:0.0f}'.format(self.padId))
        for conIdx, con in enumerate(self.connectToOtherPads):
            outStr.append('CON{}={}'.format(conIdx, con))

        return ','.join(outStr) + ';'

    #生成贴片焊盘的字符串
    def _toStrSmdPad(self):
        outStr = ['SMDPAD,LAYER={},POS={:0.0f}/{:0.0f},SIZE_X={:0.0f},SIZE_Y={:0.0f}'.format(
            self.layerIdx, self.pos[0], self.pos[1], self.sizeX, self.sizeY)]
        if self.clearance:
            outStr.append('CLEAR={:0.0f}'.format(self.clearance))
        if self.soldermask is not None:
            outStr.append('SOLDERMASK={}'.format('true' if self.soldermask else 'false'))
        if self.rotation is not None:
            outStr.append('ROTATION={:0.0f}'.format(self.rotation))
        if self.thermal is not None:
            outStr.append('THERMAL={}'.format('true' if self.thermal else 'false'))
        if self.thermalTracksWidth:
            outStr.append('THERMAL_TRACKS_WIDTH={:0.0f}'.format(self.thermalTracksWidth))
        if self.thermalTracks:
            outStr.append('THERMAL_TRACKS={:0.0f}'.format(self.thermalTracks))
        if self.padId is not None:
            outStr.append('PAD_ID={}'.format(self.padId))
        for conIdx, con in enumerate(self.connectToOtherPads):
            outStr.append('CON{}={}'.format(conIdx, con))

        return ','.join(outStr) + ';'
        
        



