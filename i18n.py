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
    "Inverted Background": ("Inverted Background (slow)", "反转背景 (慢)"),
    "Padding": ("", "内边距"),
    "Cap left": ("", "左侧形状"),
    "Cap right": ("", "右侧形状"),
    "info": ("", "信息"),
    "Text is empty": ("", "文本为空"),
    "File does not exist\n{}": ("", "文件不存在\n{}"),
    "Failed to generate text": ("", "创建文本失败"),
    "Failed to save file.\n{}": ("", "保存文件失败\n{}"),
    "Save to a text file": ("", "保存为一个文本文件"),
    "Text files": ("", "文本文件"),
    "All files": ("", "所有文件"),
    "  Standalone mode": ("", "  单独执行模式"),
    "  In [{}] : {}": ("", "  输入 [{}]：{}"),
    "whole board": ("", "整板"),
    "partial": ("", "部分"),
    "Input is empty": ("", "输入为空"),
    "Failed to parse file content": ("", "分析文件内容错误"),
    "Failed to parse content\nMaybe Id error or Internet disconnected?": ("", "分析内容错误：\n可能是ID错误或网络不通？"),
    "Input": ("", "输入"),
    "TabFont":         ("     Font     ", "       字体      "),    
    "TabFootprint":    ("   Footprint  ", "       封装      "),
    "TabSVG":          ("  SVG/Qrcode  ", "    SVG/二维码   "),
    "TabAutoRouter":   ("  Autorouter  ", "    自动布线     "),
    "TabTeardrops":    ("  Teardrop    ", "    泪滴焊盘     "),
    "TabRoundedTrack": (" RoundedTrack ", "    圆弧走线     "),
    "Import text": ("", "导入封装库中的文本"),
    "Kicad footprint": ("", "Kicad封装文件"),
    "easyEDA footprint": ("", "力创封装文件"),
    "SVG files": ("", "SVG矢量图像文件"),
    "All Files": ("", "所有文件"),
    " Cut": ("", " 剪切"),
    " Copy": ("", " 复制"),
    " Paste": ("", " 粘贴"),
    "Footprint_features_tips": ("Currently supports:\n1. Kicad footprint Library : *.kicad_mod\n2. EasyEDA part ID: C + number (C can be omitted)",
        "当前支持：\n1. Kicad 封装库文件：*.kicad_mod\n2. 力创商城元件编号：C + 若干位数字 (C可省略)"),
    "The content is not json format": ("", "内容不是json格式"),
    "The content is not a valid json format": ("", "内容不是正确的json格式"),
    "Error from easyEDA:\n{}": ("", "来自立创的错误信息：\n{}"),
    "Convert svg image failed": ("", "转换SVG图像失败"),
    "Enter the desired image height (mm)": ("", "输入要生成的图像高度 (mm)"),
    "The image height is invalid": ("", "图像高度数值非法"),
    "Polygon": ("", "多边形"),
    "Track": ("", "线条"),
    "svg_features_tips": ("Note:\nOnly for simple images, may fail to convert complex images", "注意：\n仅适用于简单的图像，复杂的图像可能会转换失败"),
    "File": ("", "文件"),
    "Mode": ("", "模式"),
    "svgHeight": ("Height (mm)", "高度 (mm)"),
    "The file format is not supported": ("", "此文件格式暂不支持"),
    "  New version found, double-click to show details": ("", "  发现新版本，双击显示详情"),
    "New version found": ("", "发现新版本"),
    "Current version: v{}": ("", "当前版本：v{}"),
    "Lastest version: v{}": ("", "最新版本：v{}"),
    "Download": ("", "下载"),
    "Skip this version": ("", "跳过此版本"),
    "Later": ("", "稍后"),
    "Qrcode": ("", "二维码"),
    "Please deselect all items before launching the plugin": ("", "请取消全部选择然后再执行此插件"),
    "autorouter_features_tips": (
        "Open the exported DSN file with Freerouting for autorouting\nCurrently only supports all components placed on the front side", 
        "使用 Freerouting 打开导出后的DSN文件进行自动布线\n当前仅支持在板子正面放置元件"),
    "DSN file": ("", "DSN文件"),
    "SES file": ("", "SES文件"),
    "Specctra DSN files": ("", "自动布线DSN文件"),
    "Specctra session files": ("", "自动布线session文件"),
    "Rules": ("", "布线规则"),
    "Export DSN": ("", "导出DSN"),
    "Import SES": ("", "导入SES"),
    "Item": ("", "项目"),
    "Value": ("", "数值"),
    "Track width": ("", "走线宽度"),
    "Via diameter": ("", "过孔外径"),
    "Via drill": ("", "过孔内径"),
    "Clearance": ("", "最小走线间隙"),
    "Smd-Smd Clearance": ("", "最小贴片到贴片间隙"),
    "\nPlease enter a new value for the parameter '{}'\nThe unit is mm\n": ("", "\n请输入一个新的“{}”配置值\n单位为毫米\n"),
    "Edit parameter": ("", "修改参数"),
    "Error parsing input file:\n{}": ("", "分析输入文件时出错:\n{}"),
    "The boundary (layer U) of the board is not defined": ("", "未定义电路板的边框（板层U）"),
    "Unknown error": ("", "未知错误"),
    "Export Specctra DSN file successfully": ("", "导出自动布线DSN文件成功"),
    "This operation will completely replace the existing components and wiring on the board.\nDo you want to continue?": 
            ("", "这个操作将会全部替换电路板上的已有元件和布线。\n需要继续吗？"),
    "DSN file is empty": ("", "DSN文件为空"),
    "There are some components with the same name: {}": ("", "存在重名的元件：{}"),
    "Failed to get glyph set from the font file you selected": ("", "无法从您选择的字体文件中提取字形集"),
    "No suitable character map found in the font file you selected": ("", "在您选择的字体文件中找不到合适的字符表"),
    "The glyph for the character was not found in the font file you selected.\n\n{}": ("", "在您选择的字体文件中找不到这个字符的字形\n\n{}"),
    "Failed to get glyph for the character.\n\n{}": ("", "获取这个字符串的字形失败\n\n{}"),
    "Currently only supports all components placed on the front side\n\n{}": ("", "当前仅支持在电路板正面放置元件\n\n{}"),
    "Import all (remove routed ratsnests)": ("", "导入全部（删除已经布线成功的网络连接线）"),
    "Import all (remove all ratsnests)": ("", "导入全部（删除所有网络连接线）"),
    "Import all (keep all ratsnests)": ("", "导入全部（保留所有网络连接线）"),
    "Import auto-routed tracks only": ("", "仅导入自动布线的铜箔走线"),
    "No components on the board": ("", "电路板上没有元件"),
    "Failed to parse input file": ("", "分析输入文件失败"),
    "  Releases: ": ("", "  版本库： "),
    "  Report bugs: ": ("", "  报告Bug： "),
    "teardrops_features_tips": (
        "Apply to all pads when deselecting all, otherwise apply to selected pads AND tracks only",
        "取消全部选择时应用到所有焊盘，否则仅应用到您选择的焊盘和对应的走线"),
    "Horizontal percent": ("", "水平比例 (H)"),
    "Vertical percent": ("", "垂直比例 (W)"),
    "Number of segments": ("", "线段数量"),
    "Pad type": ("", "焊盘类型"),
    "PTH pad": ("", "通孔焊盘"),
    "SMD pad": ("", "贴片焊盘"),
    "PTH/SMD": ("", "通孔/贴片"),
    "Add": ("", "添加"),
    "Remove": ("", "删除"),
    "Dangerous operation:\nThis operation may delete some small polygons by mistake or not delete the desired polygons\nDo you want to continue?":
        ("", "危险操作：\n这个操作可能会误删一些小多边形或没能完全删除需要的多边形。\n需要继续吗？"),
    "No teardrop pads are generated": ("", "没有生成任何泪滴焊盘"),
    "Wrong parameter value": ("", "参数值错误"),
    "Successfully added [{}] teardrop pads": ("", "成功添加 [{}] 个泪滴焊盘"),
    "Successfully removed [{}] teardrop pads": ("", "成功删除 [{}] 个泪滴焊盘"),
    "No teardrop pads found": ("", "没有找到泪滴焊盘"),
    "rounded_track_features_tips": (
        "Apply to all tracks when deselecting all, otherwise apply to selected tracks only",
        "取消全部选择时应用到所有走线，否则仅应用到您选择的走线"),
    "Type": ("", "类型"),
    "Tangent": ("", "切线圆弧"),
    "Three-point": ("", "三点圆弧"),
    "Bezier": ("", "贝塞尔曲线"),
    "big d(mm)": ("", "大 d(mm)"),
    "small d(mm)": ("", "小 d(mm)"),
    "Convert": ("", "转换"),
    "No suitable track found": ("", "没有找到符合条件的走线"),
    "The file contains no components.": ("", "此文件没有包含任何元件。"),
    "The ID is empty.": ("", "ID为空。"),
    "The content of this file is not in valid JSON format.": ("", "此文件的内容不是合法的json格式。"),
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
        cls._langIndex = idx if ((idx >= 0) and (idx < len(cls._supported_languages))) else 0

    #查询当前使用的语种，比如：zh-cn
    @classmethod
    def getLanguage(cls):
        idx = cls._langIndex if ((cls._langIndex >= 0) and (cls._langIndex < len(cls._supported_languages))) else 0
        return cls._supported_languages[idx]
        
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

    #获取翻译字符串
    @classmethod
    def tr(cls, txt: str):
        ret = cls._translations.get(txt, '')
        if (ret and (cls._langIndex < len(ret))):
            return ret[cls._langIndex] or txt
        else:
            return txt
