#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PCB增强 - 泪滴、圆弧走线
Author: cdhigh <https://github.com/cdhigh>
"""
import sys
from tkinter.messagebox import showinfo, showwarning, askyesno
import sprint_struct.sprint_textio as sprint_textio
from utils.comm_utils import str_to_int, str_to_float, evalCondition


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
    
    # 批量修改文本属性的底层实现
    # elem: SprintText 实例
    # applyToAll: 是否忽略条件直接应用修改
    # ifCfg: 条件配置字典, 每个条目元祖的第一个元素为是否使用此条件
    # thenCfg: 目标配置字典, 每个条目元祖的第一个元素为是否修改此属性
    def _bulkEditText(self, elem, applyToAll, ifCfg, thenCfg):
        if not applyToAll:
            if ifCfg.get('Layer')[0] and elem.layerIdx != ifCfg['Layer'][1]:
                return 0
            if ifCfg.get('Thickness')[0]:
                thickness = elem.thickness if elem.thickness is not None else 1
                if thickness != ifCfg['Thickness'][1]:
                    return 0
            if ifCfg.get('Style')[0]:
                style = elem.style if elem.style is not None else 1
                if style != ifCfg['Style'][1]:
                    return 0
            if ifCfg.get('Height')[0] and not evalCondition(elem.height, ifCfg['Height'][1], ifCfg['Height'][2]):
                return 0
            if ifCfg.get('Rotation')[0] and not evalCondition(elem.rotation, '==', ifCfg['Rotation'][1]):
                return 0
            
        # apply overrides
        if thenCfg.get('Layer')[0]:
            elem.layerIdx = thenCfg['Layer'][1]
        if thenCfg.get('Thickness')[0]:
            elem.thickness = thenCfg['Thickness'][1]
        if thenCfg.get('Style')[0]:
            elem.style = thenCfg['Style'][1]
        if thenCfg.get('Height')[0]:
            elem.height = thenCfg['Height'][1]
        if thenCfg.get('Rotation')[0]:
            elem.rotation = thenCfg['Rotation'][1]
        return 1

    # 批量修改导线属性的底层实现
    # elem: SprintTrack 实例
    # applyToAll: 是否忽略条件直接应用修改
    # ifCfg: 条件配置字典, 每个条目元祖的第一个元素为是否使用此条件
    # thenCfg: 目标配置字典, 每个条目元祖的第一个元素为是否修改此属性
    def _bulkEditTrack(self, elem, applyToAll, ifCfg, thenCfg):
        if not applyToAll:
            if ifCfg.get('Layer')[0] and elem.layerIdx != ifCfg['Layer'][1]:
                return 0
            if ifCfg.get('Width')[0] and not evalCondition(elem.width, ifCfg['Width'][1], ifCfg['Width'][2]):
                return 0
        
        if thenCfg.get('Layer')[0]:
            elem.layerIdx = thenCfg['Layer'][1]
        if thenCfg.get('Width')[0]:
            elem.width = thenCfg['Width'][1]
        return 1

    # 批量修改通孔焊盘属性的底层实现
    # elem: SprintPad 实例 (仅限 PAD)
    # applyToAll: 是否忽略条件直接应用修改
    # ifCfg: 条件配置字典, 每个条目元祖的第一个元素为是否使用此条件
    # thenCfg: 目标配置字典, 每个条目元祖的第一个元素为是否修改此属性
    def _bulkEditPad(self, elem, applyToAll, ifCfg, thenCfg):
        if not applyToAll:
            if ifCfg.get('Layer')[0] and elem.layerIdx != ifCfg['Layer'][1]:
                return 0
            if ifCfg.get('Size')[0] and not evalCondition(elem.size, ifCfg['Size'][1], ifCfg['Size'][2]):
                return 0
            if ifCfg.get('Drill')[0] and not evalCondition(elem.drill, ifCfg['Drill'][1], ifCfg['Drill'][2]):
                return 0
            if ifCfg.get('Form')[0] and elem.form != ifCfg['Form'][1]:
                return 0
            if ifCfg.get('Rotation')[0] and not evalCondition(elem.rotation, '==', ifCfg['Rotation'][1]):
                return 0
        
        if thenCfg.get('Layer')[0]:
            elem.layerIdx = thenCfg['Layer'][1]
        if thenCfg.get('Size')[0]:
            elem.size = thenCfg['Size'][1]
        if thenCfg.get('Drill')[0]:
            elem.drill = thenCfg['Drill'][1]
        if thenCfg.get('Form')[0]:
            elem.form = thenCfg['Form'][1]
        if thenCfg.get('Rotation')[0]:
            elem.rotation = thenCfg['Rotation'][1]
        return 1

    # 批量修改贴片焊盘属性的底层实现
    # elem: SprintPad 实例 (仅限 SMDPAD)
    # applyToAll: 是否忽略条件直接应用修改
    # ifCfg: 条件配置字典, 每个条目元祖的第一个元素为是否使用此条件
    # thenCfg: 目标配置字典, 每个条目元祖的第一个元素为是否修改此属性
    def _bulkEditSmdPad(self, elem, applyToAll, ifCfg, thenCfg):
        if not applyToAll:
            if ifCfg.get('Layer')[0] and elem.layerIdx != ifCfg['Layer'][1]:
                return 0
            if ifCfg.get('SizeX')[0] and not evalCondition(elem.sizeX, ifCfg['SizeX'][1], ifCfg['SizeX'][2]):
                return 0
            if ifCfg.get('SizeY')[0] and not evalCondition(elem.sizeY, ifCfg['SizeY'][1], ifCfg['SizeY'][2]):
                return 0
            if ifCfg.get('Rotation')[0] and not evalCondition(elem.rotation, '==', ifCfg['Rotation'][1]):
                return 0
        
        if thenCfg.get('Layer')[0]:
            elem.layerIdx = thenCfg['Layer'][1]
        if thenCfg.get('SizeX')[0]:
            elem.sizeX = thenCfg['SizeX'][1]
        if thenCfg.get('SizeY')[0]:
            elem.sizeY = thenCfg['SizeY'][1]
        if thenCfg.get('Rotation')[0]:
            elem.rotation = thenCfg['Rotation'][1]
        return 1

    # 将批量修改结果保存为文本文件按钮事件
    # textIo: SprintTextIO实例
    # cfg: 批量修改的配置字典
    # Returns: 返回(目标字符串, 修改元素个数)
    def doBulkEdit(self, textIo, cfg):
        if not textIo:
            return ('', 0)

        targetName = cfg.get('targetName', 'Text')
        applyToAll = cfg.get('applyToAll', False)
        ifCfg = cfg.get('If', {})
        thenCfg = cfg.get('Then', {})

        editedCount = 0

        if targetName == 'Text':
            editedCount = sum(self._bulkEditText(elem, applyToAll, ifCfg, thenCfg) for elem in textIo.getTexts())
        elif targetName == 'Track':
            editedCount = sum(self._bulkEditTrack(elem, applyToAll, ifCfg, thenCfg) for elem in textIo.getTracks())
        elif targetName == 'Pad':
            editedCount = sum(self._bulkEditPad(elem, applyToAll, ifCfg, thenCfg) for elem in textIo.getPads('PAD'))
        elif targetName == 'SmdPad':
            editedCount = sum(self._bulkEditSmdPad(elem, applyToAll, ifCfg, thenCfg) for elem in textIo.getPads('SMDPAD'))

        if editedCount == 0:
            return ('', 0)

        return str(textIo), editedCount

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
