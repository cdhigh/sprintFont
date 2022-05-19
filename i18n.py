#!/usr/bin/env python
#-*- coding:utf-8 -*-
"""
Python通用简单多语种支持模块
不使用python内置的gettext来进行多语种支持，直接使用一个大Map，简单粗暴
Author: cdhigh <https://github.com/cdhigh>
使用方法：
1. 导入此模块的Language类
2. 初始化
   I18n.init()
   I18n.setLanguage(locale.getdefaultlocale()[0])
3. 代码中使用 _("") 或 I18n.tr("") 进行字符串翻译
"""
import builtins

#用于翻译的辅助类，使用时创建一个实例，然后设置对应的语种，即可调用tr()获取翻译字符串
class I18n:
    #目前支持的语种，不支持的语种则使用第一个语言
    #语种代码全部为小写
    _supported_languages = ('en','zh-cn')

    #这个Map的Key是英语，Value是翻译列表，列表中字符串的顺序就是_supported_languages[]的顺序
    #如果翻译字符串列表的第一个元素为空，则使用Key做为翻译字符串
    _translations = {
    "Ok":  ("", "确定"),
    "Cancel":  ("", "取消"),
    "Save as":  ("", "另存为"),
    "Font": ("", "字体"),
    "Text": ("", "文本"),
    "Layer": ("", "板层"),
    "Smooth": ("", "平滑"),
    "C1 (Front copper)": ("", "C1 (顶层覆铜层)"),
    "S1 (Front silkscreen)": ("", "S1 (顶层丝印层)"),
    "C2 (Back copper)": ("", "C2 (底层覆铜层)"),
    "S2 (Back silkscreen)": ("", "S2 (底层丝印层)"),
    "I1 (Inner copper1)": ("", "I1 (内部覆铜层1)"),
    "I2 (Inner copper2)": ("", "I2 (内部覆铜层2)"),
    "U (Edge.cuts)": ("", "U (印刷板边界层)"),
    "Height (mm)": ("", "字高 (mm)"),
    "Word spacing (mm)": ("", "字间距 (mm)"),
    "Line spacing (mm)": ("", "行间距 (mm)"),
    "Super fine (super slow)": ("", "超精细 (超级慢)"),
    "Fine (slow)": ("", "精细 (慢)"),
    "Normal": ("", "正常"),
    "Rough": ("", "稍粗糙"),
    "Super Rough": ("", "比较粗糙"),
    "info": ("", "信息"),
    "Text is empty": ("", "文本为空"),
    "File does not exist": ("", "文件不存在"),
    "Failed to generate text": ("", "创建文本失败"),
    "Failed to save file": ("", "保存文件失败"),
    "Save to a text file": ("", "保存为一个文本文件"),
    "Text files": ("", "文本文件"),
    "All files": ("", "所有文件"),
    "  Standalone mode": ("", "  单独执行模式"),
    "  In: {}": ("", "  输入：{}"),
    "No file selected": ("", "没有选择文件"),
    "Failed to parse file content": ("", "分析文件内容错误"),
    "Input": ("", "输入"),
    "Font": ("            Font            ", "            字体            "),    
    "Footprint": ("            Footprint            ", "            封装            "),
    "Kicad footprint Library Supported": ("", "当前支持Kicad的封装库格式"),
    "Import text": ("", "导入封装库中的文本"),
    "Kicad footprint": ("", "Kicad封装文件"),
    "Easyeda footprint": ("", "力创EDA封装文件"),
    "All Files": ("", "所有文件"),
    "Footprint_features_tips": ("Currently supports:\n1. Kicad footprint Library : *.kicad_mod\n2. EasyEDA component ID: C + number (need Internet)",
        "当前支持：\n1. Kicad封装文件：*.kicad_mod\n2. 力创商城元件编号：C + 若干位数字 (需要网络)"),
    }

    #这个属性是可以在程序执行过程中修改的
    _langIndex = 0

    #初始化多语种支持
    @classmethod
    def init(cls):
        cls._langIndex = 0
        builtins.__dict__['_'] = cls.tr

    #查询一个语种是否支持
    @classmethod
    def langIsSupported(cls, lang: str):
        return True if cls._getLangIndex(lang) >= 0 else False

    #设置语种，比如: zh-cn
    @classmethod
    def setLanguage(cls, lang: str):
        idx = cls._getLangIndex(lang)
        cls._langIndex = idx if (idx >= 0) else 0
        
    #获取语种的内部索引
    @classmethod
    def _getLangIndex(cls, lang: str):
        if not lang:
            return -1
            
        lang = lang.lower().replace('_', '-')
        baselang = lang.split('-')[0]
        
        if lang in cls._supported_languages:
            return cls._supported_languages.index(lang)

        for idx, c in enumerate(cls._supported_languages): #同一语种的其他可选语言
            if c.startswith(baselang):
                return idx

        return -1

    #获取翻译字符串，如果增加了翻译语种种类，则 (txt, txt) 元祖个数需要同步增加
    @classmethod
    def tr(cls, txt: str):
        return cls._translations.get(txt, (txt, txt))[cls._langIndex] or txt
