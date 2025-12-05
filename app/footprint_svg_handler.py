#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
封装和SVG处理 - 封装导入、SVG转换
Author: cdhigh <https://github.com/cdhigh>
"""
import os
from conversion.lceda_to_sprint import LcComponent
from utils.comm_utils import str_to_float

#处理封装导入和SVG/二维码转换
class FootprintSvgHandler:
    def __init__(self):
        pass
    
    #方便进行测试的一个函数，可以仅输入kicad封装文件名，自动添加路径
    def autoAddKicadPath(self, fileName):
        if fileName and ('\\' not in fileName) and (not LcComponent.isLcedaComponent(fileName)):
            for root, subdirs, files in os.walk('C:/Program Files/KiCad/9.0/share/kicad/footprints'):
                if fileName + '.kicad_mod' in files:
                    fileName = os.path.join(root, fileName + '.kicad_mod')
        return fileName
    
    #将封装文件转换为Sprint-Layout格式
    #fileName: 封装文件名
    #importText: 是否导入文本
    #easyEdaSite: EasyEDA站点(cn/global)
    #sysLanguge: 系统语言
    #Returns: (错误信息, 生成的文本) 元组
    def generateFootprint(self, fileName, importText, easyEdaSite, sysLanguge):
        msg = ''
        textIo = None
        fileName = fileName.lower()
        
        if (fileName.endswith('.kicad_mod')):  # Kicad封装文件
            from conversion.kicad_to_sprint import kicadModToTextIo
            textIo = kicadModToTextIo(fileName, importText)
        elif (fileName.endswith('.json')):  # 立创EDA离线封装文件
            ins = LcComponent.fromFile(fileName)
            textIo = ins if not ins or isinstance(ins, str) else ins.createSprintTextIo(importText)
        elif LcComponent.isLcedaComponent(fileName):  # 在线立创EDA
            if not easyEdaSite:
                easyEdaSite = 'cn' if sysLanguge.startswith('zh') else 'global'
                
            ins = LcComponent.fromLcId(fileName, easyEdaSite)
            if isinstance(ins, LcComponent):
                textIo = ins.createSprintTextIo(importText)
            else:
                textIo = str(ins)
        else:
            msg = _("The file format is not supported")

        if not msg and isinstance(textIo, str):
            msg = textIo

        return (msg, str(textIo))
    
    #将SVG文件转换为Sprint-Layout格式
    # fileName: SVG文件名或二维码文本
    # layerIdx: 板层索引(1-based)
    # svgHeight: SVG图像高度(mm)
    # svgSmooth: 平滑度索引
    # svgMode: SVG生成模式(0-线条, 1-多边形)
    # isQrcode: True则为生成二维码
    # Returns: 生成的textIo字符串
    def generateFromSvg(self, fileName, layerIdx, svgHeight, svgSmooth, svgMode, isQrcode):
        from conversion.svg_to_polygon import svgToPolygon

        usePolygon = 1 if isQrcode else svgMode  # 0-线条, 1-多边形，二维码固定为多边形
        textIo = svgToPolygon(fileName, layerIdx=layerIdx, height=max(svgHeight, 1.0), 
            smooth=svgSmooth, usePolygon=usePolygon)

        return str(textIo) if (textIo and textIo.isValid()) else ''
    
    #将文本转换为二维码字符串(SVG格式)
    #txt: 要转换的文本
    #Returns: 二维码SVG字符串
    def textToQrcodeStr(self, txt):
        from qrcode import QRCode
        from qrcode.image.svg import SvgPathImage
        qr = QRCode(image_factory=SvgPathImage)
        qr.add_data(txt)
        qr.make(fit=True)
        img = qr.make_image()
        return img.to_string().decode('utf-8')
        
