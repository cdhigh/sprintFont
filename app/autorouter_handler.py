#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
自动布线 - DSN导出、SES导入
Author: cdhigh <https://github.com/cdhigh>
"""
import os, pickle
from tkinter.messagebox import showwarning, showinfo
from sprint_struct.sprint_export_dsn import SprintExportDsn

#处理自动布线的DSN导出和SES导入
class AutorouterHandler:
    def __init__(self):
        pass
    
    # 导出布线到DSN文件
    # dsnFile: DSN文件路径
    # textIo: SprintTextIO实例
    # pcbRule: PCB规则对象
    # Returns: 成功返回True，失败返回False
    def exportDsn(self, dsnFile, textIo, pcbRule):
        if not textIo:
            return False

        if not dsnFile.lower().endswith('.dsn'):
            showwarning(_("info"), _('The file format is not supported'))
            return False

        dsnPickleFile = os.path.splitext(dsnFile)[0] + '.pickle'

        exporter = SprintExportDsn(textIo, pcbRule, dsnFile)
        ret = exporter.export()
        if isinstance(ret, str):  # 错误信息
            showwarning(_("info"), ret if ret else _("Unknown error"))
            return False
        else:
            try:
                with open(dsnFile, 'w', encoding='utf-8') as f:
                    f.write(ret.output)
                
                with open(dsnPickleFile, 'wb') as f:
                    pickle.dump(exporter, f)
                showinfo(_("info"), _("Export Specctra DSN file successfully"))
            except Exception as e:
                showwarning(_("info"), str(e))
                return False

        return True
    
    # 导入自动布线的SES文件
    # sesFile: SES文件路径
    # dsnFile: DSN文件路径
    # trimRatsnestMode: 修剪飞线模式
    # trackOnly: 是否仅导入走线
    # Returns: 成功返回textIo字符串，失败返回False或错误信息    
    def importSes(self, sesFile, dsnFile, trimRatsnestMode, trackOnly):
        if not sesFile.lower().endswith('.ses'):
            showwarning(_("info"), _("The file format is not supported"))
            return False

        ret = self.generateTextIoFromSes(sesFile, dsnFile, trimRatsnestMode, trackOnly)
        if not ret:
            return False
        elif isinstance(ret, str):
            showwarning(_("info"), ret)
            return False
        else:
            return str(ret)
    
    # 从SES中生成TextIo实例对象
    # sesFile: SES文件路径
    # dsnPickleFile: DSN pickle文件路径
    # trimRatsnestMode: 修剪飞线模式
    # trackOnly: 是否仅导入走线
    # Returns: 成功返回SprintTextIO实例，失败返回错误信息字符串
    def generateTextIoFromSes(self, sesFile, dsnPickleFile, trimRatsnestMode, trackOnly):
        from sprint_struct.sprint_import_ses import SprintImportSes
        try:
            with open(dsnPickleFile, 'rb') as f:
                dsn = pickle.load(f)
        except Exception as e:
            return str(e)
            
        ses = SprintImportSes(sesFile, dsn)
        try:
            return ses.importSes(trimRatsnestMode=trimRatsnestMode, trackOnly=trackOnly)
        except Exception as e:
            return str(e)
