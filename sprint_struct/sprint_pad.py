#!/usr/bin/env python
#-*- coding:utf-8 -*-
"""
焊盘定义
Author: cdhigh <https://github.com/cdhigh>
"""
from .sprint_element import *

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
class SprintPad(SprintElement):
    def __init__(self, padType: str='PAD', layerIdx: int=1):
        super().__init__(layerIdx)
        self.padType = padType # 'PAD'/'SMDPAD'
        self.pos = (0, 0)
        self.size = 0
        self.sizeX = 0
        self.sizeY = 0
        self.drill = 0
        self.form = PAD_FORM_ROUND
        self.clearance = None
        self.soldermask = None
        self.rotation = None
        self.via = None
        self.thermal = None
        self.thermalTracksWidth = 0
        self.thermalTracksIndividual = None
        self.thermalTracks = 0
        self.padId = None
        self.connectToOtherPads = [] #从此焊盘到特定其他焊盘的网络连线
    
    def isValid(self):
        return (self.size > 0) if (self.padType == 'PAD') else ((self.sizeX > 0) and (self.sizeY > 0))
        
    def updateSelfBbox(self):
        if (self.padType == 'PAD'):
            size2 = self.size / 2
            self.updateBbox(self.pos[0] - size2, self.pos[1] - size2)
            self.updateBbox(self.pos[0] + size2, self.pos[1] + size2)
        else:
            self.updateBbox(self.pos[0] - self.sizeX / 2, self.pos[1] - self.sizeY / 2)
            self.updateBbox(self.pos[0] + self.sizeX / 2, self.pos[1] + self.sizeY / 2)

    def __str__(self):
        return self.toStr()

    def toStr(self, overwritePadId=None):
        return self.toStrPad(overwritePadId) if self.padType == 'PAD' else self.toStrSmdPad(overwritePadId)

    #生成通孔焊盘的字符串
    def toStrPad(self, overwritePadId=None):
        outStr = ['PAD,LAYER={},POS={:0.0f}/{:0.0f},SIZE={:0.0f},DRILL={:0.0f},FORM={}'.format(
            self.layerIdx, self.pos[0] * 10000, self.pos[1] * 10000, self.size * 10000, self.drill * 10000, self.form)]
        if self.clearance is not None:
            outStr.append('CLEAR={:0.0f}'.format(self.clearance * 10000))
        if self.soldermask is not None:
            outStr.append('SOLDERMASK={}'.format(self.booleanStr(self.soldermask)))
        if (self.form != PAD_FORM_ROUND) and (self.rotation is not None):
            outStr.append('ROTATION={:0.0f}'.format(self.rotation * 100)) #焊盘的旋转单位为0.01度
        if self.via is not None:
            outStr.append('VIA={}'.format(self.booleanStr(self.via)))
        if self.thermal is not None:
            outStr.append('THERMAL={}'.format(self.booleanStr(self.thermal)))
        if self.thermalTracksWidth:
            outStr.append('THERMAL_TRACKS_WIDTH={:0.0f}'.format(self.thermalTracksWidth * 10000))
        if self.thermalTracksIndividual is not None:
            outStr.append('THERMAL_TRACKS_INDIVIDUAL={}'.format(self.booleanStr(self.thermalTracksIndividual)))
        if self.thermalTracks:
            outStr.append('THERMAL_TRACKS={:0.0f}'.format(self.thermalTracks * 10000))
        if overwritePadId is not None:
            outStr.append('PAD_ID={}'.format(overwritePadId))
        else:
            if self.padId is not None:
                outStr.append('PAD_ID={}'.format(self.padId))
            for conIdx, con in enumerate(self.connectToOtherPads):
                outStr.append('CON{}={}'.format(conIdx, con))

        return ','.join(outStr) + ';'

    #生成贴片焊盘的字符串
    def toStrSmdPad(self, overwritePadId=None):
        outStr = ['SMDPAD,LAYER={},POS={:0.0f}/{:0.0f},SIZE_X={:0.0f},SIZE_Y={:0.0f}'.format(
            self.layerIdx, self.pos[0] * 10000, self.pos[1] * 10000, self.sizeX * 10000, self.sizeY * 10000)]
        if self.clearance:
            outStr.append('CLEAR={:0.0f}'.format(self.clearance * 10000))
        if self.soldermask is not None:
            outStr.append('SOLDERMASK={}'.format(self.booleanStr(self.soldermask)))
        if self.rotation is not None:
            outStr.append('ROTATION={:0.0f}'.format(self.rotation * 100))
        if self.thermal is not None:
            outStr.append('THERMAL={}'.format(self.booleanStr(self.thermal)))
        if self.thermalTracksWidth:
            outStr.append('THERMAL_TRACKS_WIDTH={:0.0f}'.format(self.thermalTracksWidth * 10000))
        if self.thermalTracks:
            outStr.append('THERMAL_TRACKS={:0.0f}'.format(self.thermalTracks * 10000))
        if overwritePadId is not None:
            outStr.append('PAD_ID={}'.format(overwritePadId))
        else:
            if self.padId is not None:
                outStr.append('PAD_ID={}'.format(self.padId))
            for conIdx, con in enumerate(self.connectToOtherPads):
                outStr.append('CON{}={}'.format(conIdx, con))

        return ','.join(outStr) + ';'
        
    
    #重载等号运算符，用于导出DSN时将所有相同类型的焊盘归类并给一个名字
    def __eq__(self, other):
        if not isinstance(other, SprintPad):
            return False

        if ((self.layerIdx != other.layerIdx) or (self.padType != other.padType) or (self.size != other.size)
            or (self.sizeX != other.sizeX) or (self.sizeY != other.sizeY) or (self.drill != other.drill)
            or (self.form != other.form) or (self.rotation != other.rotation) or (self.clearance != other.clearance)
            or (self.soldermask != other.soldermask) or (self.via != other.via) or (self.thermal != other.thermal)
            or (self.thermalTracksWidth != other.thermalTracksWidth) or (self.thermalTracksIndividual != other.thermalTracksIndividual)
            or (self.thermalTracks != other.thermalTracks)):
            return False
        else:
            return True
    
    #给焊盘起一个名字，用于DSN导出
    def generateDsnName(self):
        rotation = self.rotation if self.rotation else 0
        if self.padType == 'PAD':
            name = 'PAD_{}_{}_{:0.3f}_{:0.3f}_{:0.0f}_{}'.format(self.layerIdx, self.form, self.size, self.drill, rotation, ('1' if self.via else '0'))
        else:
            name = 'SMDPAD_{}_{:0.3f}x{:0.3f}_{:0.0f}'.format(self.layerIdx, self.sizeX, self.sizeY, rotation)

        return name.replace('.', '_')

    #复制一个自身，并且将坐标相对某个新原点进行移动，
    #ox/oy: 新的原点坐标
    def cloneToNewOrigin(self, ox: float, oy: float, overwritePadId=None):
        ins = SprintPad(self.padType, self.layerIdx)
        ins.pos = (round(self.pos[0] - ox, 2), round(self.pos[1] - oy, 2))
        ins.size = self.size
        ins.sizeX = self.sizeX
        ins.sizeY = self.sizeY
        ins.drill = self.drill
        ins.form = self.form
        ins.clearance = self.clearance
        ins.soldermask = self.soldermask
        ins.rotation = self.rotation
        ins.via = self.via
        ins.thermal = self.thermal
        ins.thermalTracksWidth = self.thermalTracksWidth
        ins.thermalTracksIndividual = self.thermalTracksIndividual
        ins.thermalTracks = self.thermalTracks
        ins.padId = overwritePadId if overwritePadId is not None else self.padId
        ins.connectToOtherPads = self.connectToOtherPads[:]
        ins.updateSelfBbox()
        return ins
