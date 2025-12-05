#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
字体操作 - 文本转多边形、字体处理
Author: cdhigh <https://github.com/cdhigh>
"""
import os, math, queue
from fontTools.ttLib import ttFont, ttCollection
from utils.comm_utils import str_to_float, isHexString, cutCircle
import sprint_struct.sprint_textio as sprint_textio

#处理字体相关操作，包括文本转多边形、字体扫描等
class FontOperations:
    #初始化字体操作类
    # app: sprintFont应用对象
    # modulePath: 模块路径
    # fontDir: 系统字体目录
    def __init__(self, app, modulePath, fontDir):
        self.app = app
        self.modulePath = modulePath
        self.fontDir = fontDir
    
    # 将字符串转换为Sprint-Layout多边形
    # txt: 要转换的文本
    # fontNameMap: 字体名到文件的映射字典
    # fontName: 字体名称
    # layerIdx: 板层索引(1-based)
    # fontHeight: 字体高度(mm)
    # wordSpacing: 字间距(mm)
    # lineSpacing: 行间距(mm)
    # smooth: 平滑度索引
    # invert: 是否反转背景
    # padding: 反转背景时的边距(mm)
    # capLeft: 左侧封口形状
    # capRight: 右侧封口形状
    # pcbWidth: PCB宽度
    # pcbHeight: PCB高度
    # Returns: SprintTextIO实例或空字符串
    def generatePolygons(self, txt, fontNameMap, fontName, layerIdx, fontHeight, 
                        wordSpacing, lineSpacing, smooth, invert, padding, capLeft, capRight, 
                        pcbWidth, pcbHeight):
        from sprint_struct.font_to_polygon import singleWordPolygon

        if not txt:
            return ''
        
        if fontHeight <= 0.0:
            fontHeight = 1.0
        if padding < 0.01:
            padding = 0.0
        
        fontFileName, fontIdx = fontNameMap.get(fontName, ('', 0))
        if not fontFileName or not os.path.exists(fontFileName):
            return ''
        
        if (fontFileName.endswith(('.ttc', '.otc'))):
            try:
                ttCol = ttCollection.TTCollection(fontFileName)
                if (fontIdx < len(ttCol.fonts)):
                    font = ttCol.fonts[fontIdx]
                else:
                    return ''
            except:
                return ''
        else:
            try:
                font = ttFont.TTFont(fontFileName)
            except:
                return ''
        
        # 开始逐字转换
        txt = self.translateUnicodeSymbol(txt)
        offsetY = 0.0
        prevWidth = 0
        polygons = []
        for line in txt.split('\n'):
            offsetX = 0.0  # 每一行都从最左边开始
            maxHeight = 0
            for word in line:
                ret = singleWordPolygon(fontName, font, code=ord(word), layerIdx=layerIdx, fontHeight=fontHeight,
                    offsetX=offsetX, offsetY=offsetY, smooth=smooth)
                if not ret or isinstance(ret, str):
                    font.close()
                    return ret
                    
                prevWidth = ret['width']
                polygons.extend(ret['polygons'])
                inc = prevWidth + wordSpacing
                offsetX += inc if (inc > 0) else prevWidth
                if ret['height'] > maxHeight:
                    maxHeight = ret['height']
            # 新行
            inc = maxHeight + lineSpacing
            offsetY += inc if (inc > 0) else maxHeight

        font.close()

        textIo = sprint_textio.SprintTextIO(pcbWidth, pcbHeight)
        if invert:  # 生成负像
            textIo.add(self.invertFontBackground(polygons, padding, capLeft, capRight, smooth))
        else:
            textIo.addAll(polygons)

        # 返回字符串
        return textIo
    
    # 反转字体的背景（镂空字）
    # 原理：创建一个包含所有多边形的大四边形，形成一个负像
    # polygons: 多边形列表
    # padding: 大四边形边线到字体外框的距离(mm)
    # capLeft: 四边形左侧形状
    # capRight: 四边形右侧形状
    # smooth: 平滑度索引
    # Returns: SprintPolygon实例
    def invertFontBackground(self, polygons, padding, capLeft, capRight, smooth):
        from sprint_struct.sprint_polygon import SprintPolygon
        extPoly = SprintPolygon(polygons[0].layerIdx)

        # 计算包含所有多边形的最小外接矩形
        minX = min(point[0] for poly in polygons for point in poly) - padding
        minY = min(point[1] for poly in polygons for point in poly) - padding
        maxX = max(point[0] for poly in polygons for point in poly) + padding
        maxY = max(point[1] for poly in polygons for point in poly) + padding
        slashAngle = math.radians(70)  # 斜边的角度: 70度
        tipAngle = math.radians(60)  # 尖角的角度：120度
        slashOffX = (maxY - minY) / math.tan(slashAngle)  # 斜杠和反斜杠的X偏移
        tipOffX = ((maxY - minY) / 2) / math.tan(tipAngle)  # 尖角的X偏移
        midY = (maxY - minY) / 2
        cutNumMap = {0: 50, 1: 20, 2: 10, 3: 5, 4: 2}  # 一个圆要切割的份数
        
        # 逆时针添加外框坐标，先添加左侧
        if capLeft == '/':
            extPoly.addPoint(minX, minY)
            extPoly.addPoint(minX - slashOffX, maxY)
        elif capLeft == '\\':
            extPoly.addPoint(minX - slashOffX, minY)
            extPoly.addPoint(minX, maxY)
        elif capLeft == '<':
            extPoly.addPoint(minX, minY)
            extPoly.addPoint(minX - tipOffX, maxY - midY)
            extPoly.addPoint(minX, maxY)
        elif capLeft == '>':
            extPoly.addPoint(minX - tipOffX, minY)
            extPoly.addPoint(minX, maxY - midY)
            extPoly.addPoint(minX - tipOffX, maxY)
        elif capLeft == '(':
            extPoly.addPoint(minX, minY)
            cutNum = cutNumMap.get(smooth, 10)
            extPoly.addAllPoints(cutCircle(center=(minX, maxY-midY), radius=midY, cutNum=cutNum,
                start=180, stop=360))
            extPoly.addPoint(minX, maxY)
        else:  # |
            extPoly.addPoint(minX, minY)
            extPoly.addPoint(minX, maxY)
            
        if capRight == '/':
            extPoly.addPoint(maxX, maxY)
            extPoly.addPoint(maxX + slashOffX, minY)
        elif capRight == '\\':
            extPoly.addPoint(maxX + slashOffX, maxY)
            extPoly.addPoint(maxX, minY)
        elif capRight == '<':
            extPoly.addPoint(maxX + tipOffX, maxY)
            extPoly.addPoint(maxX, maxY - midY)
            extPoly.addPoint(maxX + tipOffX, minY)
        elif capRight == '>':
            extPoly.addPoint(maxX, maxY)
            extPoly.addPoint(maxX + tipOffX, maxY - midY)
            extPoly.addPoint(maxX, minY)
        elif capRight == ')':
            extPoly.addPoint(maxX, maxY)
            cutNum = cutNumMap.get(smooth, 10)
            extPoly.addAllPoints(cutCircle(center=(maxX, maxY-midY), radius=midY, cutNum=cutNum,
                start=0, stop=180))
            extPoly.addPoint(maxX, minY)
        else:  # |
            extPoly.addPoint(maxX, maxY)
            extPoly.addPoint(maxX, minY)
        
        # 合并多边形  
        for poly in polygons:
            extPoly.devour(poly)
            poly.reset()
        
        return extPoly
    
    #将字符串里面的\\u1234转换为对应的字符
    #txt: 输入文本
    #Returns: 转换后的文本
    def translateUnicodeSymbol(self, txt):
        strLen = len(txt)
        if strLen < 6:
            return txt

        idx = 0
        newTxt = []
        while (idx < (strLen - 5)):
            ch = txt[idx]
            digStr = txt[idx + 2:idx + 6]
            # u后面需要四个数字
            if ((ch == '\\') and (txt[idx + 1] == 'u') and isHexString(digStr)):
                try:
                    code = int(digStr, 16)
                except:
                    code = 0
                newTxt.append(chr(code))
                idx += 6
            else:
                newTxt.append(ch)
                idx += 1

        if (idx < strLen):
            newTxt.extend(txt[idx:])
        return ''.join(newTxt)
    
    #生成需要扫描的字体目录列表
    def _getFontSearchDirs(self):
        dirs = [self.fontDir, self.modulePath]

        # 支持Windows10及以上系统的用户字体目录
        localDir = os.getenv('LOCALAPPDATA')
        if localDir:
            userFontDir = os.path.join(localDir, 'Microsoft', 'Windows', 'Fonts')
            if os.path.exists(userFontDir):
                dirs.append(userFontDir)
        return dirs

    #从 fontTools 对象中提取最佳显示名称
    def _extractFontName(self, font):
        nameTable = font.get('name')
        if not nameTable:
            return ''

        # 尝试获取中文名称 (Windows, Unicode BMP, 简体中文 0x804)
        nameRec = nameTable.getName(nameID=4, platformID=3, platEncID=1, langID=0x804)
        if not nameRec: # 如果没有中文，尝试获取默认英文 (Windows, Unicode BMP)
            nameRec = nameTable.getName(nameID=4, platformID=3, platEncID=1)

        try:
            name = nameRec.toUnicode() if nameRec else ''
        except UnicodeDecodeError:
            name = ''

        # 如果上述方式都失败，使用 fontTools 的兜底策略
        if not name:
            name = nameTable.getBestFullName() or \
                   nameTable.getBestSubFamilyName() or \
                   nameTable.getBestFamilyName()
        
        return name
        
    #将字体文件和字体名字对应起来，关键字为字体名字，值为(文件名, 字体索引)
    #除了系统的字体目录，本软件同一目录下的ttf也可以做为选择
    #如果fontQueue传入值，也通过queue传出给子线程使用
    def generateFontFileNameMap(self, fontQueue=None):
        fontNameMap = {}
        supportedExts = ('.ttf', '.otf', '.ttc', '.otc')
        searchDirs = self._getFontSearchDirs()
        
        for folder in searchDirs:
            try:
                files = [f for f in os.listdir(folder) if f.lower().endswith(supportedExts)]
            except OSError:
                continue

            for filename in files:
                fullPath = os.path.join(folder, filename)
                fontsInFile = []

                try: # 加载字体文件（区分集合和单体）
                    if filename.lower().endswith(('.ttc', '.otc')):
                        ttCol = ttCollection.TTCollection(fullPath)
                        fontsInFile = ttCol.fonts
                    else:
                        # lazy=True 很重要，只读取头部信息，提高速度
                        fontsInFile = [ttFont.TTFont(fullPath, lazy=True)]
                except Exception as e:
                    print(f'Load font failed ({fullPath}) : {e}')
                    continue

                # 遍历文件内的字体（处理 TTC/OTC 包含多个字体的情况）
                for fontIdx, font in enumerate(fontsInFile):
                    name = self._extractFontName(font)
                    if name:
                        fontNameMap[name] = (fullPath, fontIdx)

        if fontQueue:
            fontQueue.put_nowait(fontNameMap)
        return fontNameMap
    
    # 更新字体列表组合框，可能直接调用，也可能会使用after延时调用
    # fontNameMap: 字体名映射字典，如果为None则从queue获取
    # fontQueue: 字体Queue，用于异步获取字体列表
    # Returns: 如果字体还没准备好，返回False以便after继续等待
    def populateFontCombox(self, fontNameMap, fontQueue):
        app = self.app
        if fontNameMap is None:  # 使用after延时调用
            if fontQueue.empty():  # 还没有从磁盘里面读取到字体
                return False  # 需要继续等待
            else:
                fontNameMap = fontQueue.get_nowait()

        if fontNameMap:
            app.fontNameMap = fontNameMap
            cmbFontList = sorted(fontNameMap.keys())
            app.cmbFont.configure(value=cmbFontList)
            app.cmbFontList = cmbFontList  # 保存列表供后续使用
            
            lastFont = app.cfg.get('font', '')
            fontNameList = cmbFontList or ['']
            if lastFont and (lastFont in fontNameList):
                app.cmbFont.current(fontNameList.index(lastFont))
            elif (app.sysLanguge.startswith('zh')):  # 中文字体一般在最后，所以默认选择最后一个，保证开箱即用
                app.cmbFont.setText(fontNameList[-1])
            elif 'Calibri' in fontNameList:  # 英文或拉丁文字体也是为了保证开箱即用
                app.cmbFont.setText('Calibri')
            else:
                app.cmbFont.setText(fontNameList[0])
        
        return True  # 字体已加载完成
