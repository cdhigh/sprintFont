#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PCB增强 - 泪滴、圆弧走线
Author: cdhigh <https://github.com/cdhigh>
"""
import sys
from tkinter.messagebox import showinfo, showwarning, askyesno
import sprint_struct.sprint_textio as sprint_textio
from utils.comm_utils import str_to_int, str_to_float


# 返回码常量（需要从主模块传入）
RETURN_CODE_INSERT_ALL = 11
RETURN_CODE_REPLACE_ALL = 12

#处理PCB增强功能：泪滴焊盘和圆角走线
class PcbEnhancements:
    #初始化PCB增强处理类
    #pcbWidth: PCB宽度
    #pcbHeight: PCB高度
    def __init__(self, pcbWidth, pcbHeight):
        self.pcbWidth = pcbWidth
        self.pcbHeight = pcbHeight
    
    #添加泪滴焊盘
    # textIo: SprintTextIO实例
    # hPercent: 水平百分比
    # vPercent: 垂直百分比
    # segs: 分段数
    # padType: 焊盘类型(0-PTH, 1-SMD, 2-Both)
    # Returns: 成功返回新的textIo字符串，失败返回None
    def addTeardrops(self, textIo, hPercent, vPercent, segs, padType):
        from sprint_struct.teardrop import createTeardrops
        
        if not textIo:
            return None
            
        if ((hPercent <= 0) or (vPercent <= 0) or (segs <= 0)):
            showwarning(_("info"), _("Wrong parameter value"))
            return None

        usePth = True if padType in (0, 2) else False
        useSmd = True if padType in (1, 2) else False
        polys = createTeardrops(textIo, hPercent=hPercent, vPercent=vPercent, segs=segs, 
            usePth=usePth, useSmd=useSmd)
        if polys:
            newTextIo = sprint_textio.SprintTextIO(self.pcbWidth, self.pcbHeight)
            newTextIo.addAll(polys)
            showinfo(_("info"), _("Successfully added [{}] teardrop pads").format(len(polys)))
            return str(newTextIo)
        else:
            showinfo(_("info"), _("No teardrop pads are generated"))
            return None
    
    # 删除泪滴焊盘
    # textIo: SprintTextIO实例
    # padType: 焊盘类型(0-PTH, 1-SMD, 2-Both)
    # Returns: 成功返回修改后的textIo字符串，失败返回None
    def removeTeardrops(self, textIo, padType):
        from sprint_struct.teardrop import getTeardrops
        if not textIo:
            return None
            
        ret = askyesno(_("info"), _("Dangerous operation:\\nThis operation may delete some small polygons by mistake or not delete the desired polygons\\nDo you want to continue?"))
        if not ret:
            return None

        # 搜集焊盘
        pads = textIo.getPads('PAD') if padType in (0, 2) else []
        if padType in (1, 2):
            pads.extend(textIo.getPads('SMDPAD'))
        
        # 搜集走线
        tracks = textIo.getTracks()

        # 搜集已有的泪滴焊盘，每个泪滴焊盘就是一个多边形
        oldTeardrops = getTeardrops(textIo, pads, tracks) if pads and tracks else None
        if oldTeardrops:
            for t in oldTeardrops:
                textIo.remove(t)

            showinfo(_("info"), _("Successfully removed [{}] teardrop pads").format(len(oldTeardrops)))
            return str(textIo)
        else:
            showinfo(_("info"), _("No teardrop pads found"))
            return None
    
    #转换弧形走线
    #textIo: SprintTextIO实例
    #roundedTrackType: 圆角类型(0-大圆角, 1-小圆角, 2-自动)
    #bigDistance: 大圆角距离
    #smallDistance: 小圆角距离
    #segs: 分段数
    #Returns: 成功返回textIo对象，失败返回None
    def convertRoundedTrack(self, textIo, roundedTrackType, bigDistance, smallDistance, segs):
        from sprint_struct.rounded_track import createArcTracksInTextIo
        
        if not textIo:
            return None

        ret = createArcTracksInTextIo(textIo, roundedTrackType, bigDistance, smallDistance, segs)
        if not ret:
            showinfo(_("info"), _("No suitable track found"))
            return None
        else:
            return textIo
