#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
配置管理 - 配置加载/保存、国际化
Author: cdhigh <https://github.com/cdhigh>
"""
import os, json, locale, gettext, datetime
from utils.comm_utils import str_to_int, str_to_float

#管理应用程序的配置加载、保存和恢复
class ConfigManager:
    #初始化配置管理器
    #app: sprintFont应用实例
    #modulePath: 模块路径
    #cfgFilename: 配置文件名
    #i18nPath: 国际化文件路径
    #supportedLanguages: 支持的语言列表
    def __init__(self, app, modulePath, cfgFilename='config.json', i18nPath=None, supportedLanguages=None):
        self.app = app
        self.modulePath = modulePath
        self.cfgFilename = cfgFilename
        self.i18nPath = i18nPath or os.path.join(modulePath, 'i18n')
        self.supportedLanguages = supportedLanguages or ('en',)
        
        self.appDataDir = self.getAppDataDir()
        self.cfg = {}
        self.sysLanguge = locale.getdefaultlocale()[0]
        self.language = ''
    
    #获取用户配置数据目录
    #appName: 应用名称
    #useRoaming: 是否使用漫游目录
    #Returns: 配置目录路径
    def getAppDataDir(self, appName="sprintFont", useRoaming=True):
        if useRoaming:
            baseDir = os.getenv('APPDATA')  # C:\Users\<user>\AppData\Roaming
        else:
            baseDir = os.getenv('LOCALAPPDATA')  # C:\Users\<user>\AppData\Local

        if not baseDir:
            baseDir = os.path.expanduser('~\\AppData\\Roaming' if useRoaming else '~\\AppData\\Local')
        if baseDir:
            appDir = os.path.join(baseDir, appName)
            os.makedirs(appDir, exist_ok=True)
            return appDir
        else:
            return self.modulePath
    
    #初始化多语种支持
    #tr.install()会设置全局翻译函数 _()
    def initI18n(self):
        self.language = lang = self.cfg.get('language', '')
        lang = self.getSupportedLanguage(lang or self.sysLanguge)
        tr = gettext.translation('messages', localedir=self.i18nPath, languages=[lang], fallback=True)
        tr.install()
    
    #获取一个支持的语言代码
    #lang: 语言代码
    #Returns: 支持的语言代码
    def getSupportedLanguage(self, lang):
        lang = lang.lower().replace('-', '_')
        if lang in self.supportedLanguages:
            return lang

        # 同一语种的其他可选语言
        baseLang = lang.split('_')[0]
        return next((item for item in self.supportedLanguages if item.startswith(baseLang)), 'en')
    
    #读取配置文件到内存
    def loadConfig(self):
        self.cfg = {}
        cfgFile = os.path.join(self.appDataDir, self.cfgFilename)
        if os.path.isfile(cfgFile):
            try:
                with open(cfgFile, 'r', encoding='utf-8') as f:
                    self.cfg = json.load(f)
                if not isinstance(self.cfg, dict):
                    self.cfg = {}
            except Exception as e:
                print(str(e))
    
    #保存当前配置数据
    #lastCheckUpdate: 上次检查更新时间
    def saveConfig(self, lastCheckUpdate=None):
        app = self.app
        cfg = {
            'language': self.language, 
            'font': app.cmbFont.text(), 
            'txtFontSize': str(app.txtFontSize), 
            'height': app.cmbFontHeight.text(), 
            'layer': str(app.cmbLayer.current()), 
            'wordSpacing': app.cmbWordSpacing.text(), 
            'lineSpacing': app.cmbLineSpacing.text(), 
            'smooth': str(app.cmbSmooth.current()), 
            'invertBackground': str(app.chkInvertedBackground.value()), 
            'padding': app.cmbPadding.text(),
            'capLeft': str(app.cmbCapLeft.current()), 
            'capRight': str(app.cmbCapRight.current()),
            'importFootprintText': str(app.chkImportFootprintText.value()),
            'exportLayer': str(app.cmbExportLayer.current()),
            'svgQrcode': str(app.cmbSvgQrcode.current()),
            'svgMode': str(app.cmbSvgMode.current()), 
            'svgLayer': str(app.cmbSvgLayer.current()),
            'svgHeight': app.cmbSvgHeight.text(), 
            'svgSmooth': str(app.cmbSvgSmooth.current()),
            'easyEdaSite': app.easyEdaSite, 
            'lastTab': str(app.getCurrentTabStripTab()),
            'checkUpdateFrequency': str(app.checkUpdateFrequency),
            'lastCheckUpdate': lastCheckUpdate.strftime('%Y-%m-%d') if lastCheckUpdate else '',
            'skipVersion': str(app.skipVersion), 
            'trackWidth': str(app.pcbRule.trackWidth), 
            'viaDiameter': str(app.pcbRule.viaDiameter),
            'viaDrill': str(app.pcbRule.viaDrill), 
            'clearance': str(app.pcbRule.clearance),
            'smdSmdClearance': str(app.pcbRule.smdSmdClearance),
            'teardropHPercent': app.cmbhPercent.text(), 
            'teardropVPercent': app.cmbvPercent.text(),
            'teardropSegs': app.cmbTeardropSegs.text(), 
            'teardropPadType': str(app.cmbTeardropPadType.current()),
            'roundedTrackType': str(app.cmbRoundedTrackType.current()), 
            'roundedTrackBigDistance': app.cmbRoundedTrackBigDistance.text(),
            'roundedTrackSmallDistance': app.cmbRoundedTrackSmallDistance.text(),
            'roundedTrackSegs': app.cmbRoundedTrackSegs.text(),
            'mergeConnectedTracks': str(app.chkMergeConnectedTracks.value()),
            'wirePairType': str(app.cmbWirePairType.current()), 
            'wirePairAmin': app.txtWirePairAmin.text(),
            'wirePairAmax': app.txtWirePairAmax.text(), 
            'wirePairSpacing': app.txtWirePairSpacing.text(),
            'wirePairSkew': app.txtWirePairSkew.text(),
        }
        
        if cfg != self.cfg:  # 有变化再写配置文件
            self.cfg = cfg
            cfgFile = os.path.join(self.appDataDir, self.cfgFilename)
            try:
                with open(cfgFile, 'w', encoding='utf-8') as f:
                    json.dump(cfg, f, indent=2)
            except:
                pass
    
    #从配置文件中恢复以前的配置数据
    def restoreConfig(self):
        app = self.app
        cfg = self.cfg
        if not isinstance(cfg, dict):
            return

        # 字体界面, cmbFontList由FontOperations设置
        lastFont = cfg.get('font', '')
        if lastFont and (lastFont in app.cmbFontList):
            app.cmbFont.current(app.cmbFontList.index(lastFont))

        app.txtFontSize = str_to_int(cfg.get('txtFontSize', '14'))

        lastHeight = str_to_float(cfg.get('height', ''))
        if lastHeight:
            app.cmbFontHeight.setText(str(lastHeight))

        lastLayer = str_to_int(cfg.get('layer', '1'), 100)
        if 0 <= lastLayer < len(app.cmbLayerList):
            app.cmbLayer.current(lastLayer)
        smooth = str_to_int(cfg.get('smooth', '2'), 100)
        if 0 <= smooth < len(app.cmbSmoothList):
            app.cmbSmooth.current(smooth)

        ws = str_to_float(cfg.get('wordSpacing', "0"))
        app.cmbWordSpacing.setText(str(ws))
        ls = str_to_float(cfg.get('lineSpacing', "0"))
        app.cmbLineSpacing.setText(str(ls))

        if (str_to_int(cfg.get('invertBackground', '0'))):
            app.chkInvertedBackground.setValue(1)
            app.cmbPadding.configure(state='normal')
            app.cmbCapLeft.configure(state='readonly')
            app.cmbCapRight.configure(state='readonly')
        padding = cfg.get('padding', '')
        if padding:
            app.cmbPadding.setText(padding)
        capLeft = str_to_int(cfg.get('capLeft', '0'))
        if 0 <= capLeft < len(app.cmbCapLeftList):
            app.cmbCapLeft.current(capLeft)
        capRight = str_to_int(cfg.get('capRight', '0'))
        if 0 <= capRight < len(app.cmbCapRightList):
            app.cmbCapRight.current(capRight)

        # 封装导入页面
        if (str_to_int(cfg.get('importFootprintText', '0'))):
            app.chkImportFootprintText.setValue(1)

        # 导出页面
        lastExportLayer = str_to_int(cfg.get('exportLayer', '0'), 100)
        if 0 <= lastExportLayer < len(app.cmbExportLayerList):
            app.cmbExportLayer.current(lastExportLayer)
        
        # SVG页面
        svgQrcode = str_to_int(cfg.get('svgQrcode', '0'), 100)
        if 0 <= svgQrcode < len(app.cmbSvgQrcodeList):
            app.cmbSvgQrcode.current(svgQrcode)
        svgMode = str_to_int(cfg.get('svgMode', '2'), 100)
        if 0 <= svgMode < len(app.cmbSvgModeList):
            app.cmbSvgMode.current(svgMode)
        smooth = str_to_int(cfg.get('svgSmooth', '2'), 100)
        if 0 <= smooth < len(app.cmbSmoothList):
            app.cmbSvgSmooth.current(smooth)
        svgLayer = str_to_int(cfg.get('svgLayer', '2'), 100)
        if 0 <= svgLayer < len(app.cmbSvgLayerList):
            app.cmbSvgLayer.current(svgLayer)
        lastHeight = str_to_float(cfg.get('svgHeight', ''))
        if lastHeight:
            app.cmbSvgHeight.setText(str(lastHeight))

        lastTab = str_to_int(cfg.get('lastTab', '0'))
        if (lastTab > 0):
            app.setCurrentTabStripTab(lastTab)

        # 立创EDA的服务器节点
        easyEdaSite = cfg.get('easyEdaSite', '').lower()
        if (easyEdaSite in ('cn', 'global')):
            app.easyEdaSite = easyEdaSite
        else:
            app.easyEdaSite = ''

        # 版本更新检查
        app.checkUpdateFrequency = str_to_int(cfg.get('checkUpdateFrequency', '30'))
        if (app.checkUpdateFrequency < 0):
            app.checkUpdateFrequency = 0
        lastCheck = cfg.get('lastCheckUpdate', '')
        try:
            app.lastCheckUpdate = datetime.datetime.strptime(lastCheck, '%Y-%m-%d')
        except:
            app.lastCheckUpdate = None
        app.skipVersion = cfg.get('skipVersion', '')

        # 自动布线规则和其他配置
        trackWidth = str_to_float(cfg.get('trackWidth', '0.3'))
        viaDiameter = str_to_float(cfg.get('viaDiameter', '0.6'))
        viaDrill = str_to_float(cfg.get('viaDrill', '0.3'))
        clearance = str_to_float(cfg.get('clearance', '0.2'))
        smdSmdClearance = str_to_float(cfg.get('smdSmdClearance', '0.2'))
        app.pcbRule.trackWidth = trackWidth if (trackWidth > 0.1) else 0.3
        app.pcbRule.viaDiameter = viaDiameter if (viaDiameter > 0.1) else 0.6
        app.pcbRule.viaDrill = viaDrill if (viaDrill > 0.1) else 0.3
        app.pcbRule.clearance = clearance if (clearance > 0.1) else 0.2
        app.pcbRule.smdSmdClearance = smdSmdClearance if (smdSmdClearance > 0.01) else 0.2
        if (app.pcbRule.viaDiameter <= app.pcbRule.viaDrill):
            app.pcbRule.viaDiameter = app.pcbRule.viaDrill + 0.1
        app.updateRuleView()

        # 泪滴焊盘
        hPercent = str_to_int(cfg.get('teardropHPercent', '50'))
        vPercent = str_to_int(cfg.get('teardropVPercent', '90'))
        segs = str_to_int(cfg.get('teardropSegs', '10'))
        padTypeIdx = str_to_int(cfg.get('teardropPadType', '0'))
        app.cmbhPercent.setText(str(hPercent))
        app.cmbvPercent.setText(str(vPercent))
        if segs:
            app.cmbTeardropSegs.setText(str(segs))
        if 0 <= padTypeIdx <= 2:
            app.cmbTeardropPadType.current(padTypeIdx)

        # 弧形走线
        rtType = str_to_int(cfg.get('roundedTrackType', '0'))
        if 0 <= rtType <= 2:
            app.cmbRoundedTrackType.current(rtType)
        
        distance = str_to_float(cfg.get('roundedTrackBigDistance', ''))
        if distance > 0:
            app.cmbRoundedTrackBigDistance.setText('{:.1f}'.format(distance))
        distance = str_to_float(cfg.get('roundedTrackSmallDistance', ''))
        if distance > 0:
            app.cmbRoundedTrackSmallDistance.setText('{:.1f}'.format(distance))
        segs = str_to_int(cfg.get('roundedTrackSegs', '10'))
        if segs:
            app.cmbRoundedTrackSegs.setText(segs)
        if (str_to_int(cfg.get('mergeConnectedTracks', '0'))):
            app.chkMergeConnectedTracks.setValue(1)

        # 导线对长度调整
        wType = str_to_int(cfg.get('wirePairType', '0'))
        if 0 <= wType <= 1:
            app.cmbWirePairType.current(wType)
        a = str_to_float(cfg.get('wirePairAmin', ''))
        if a > 0:
            app.txtWirePairAmin.setText('{:.1f}'.format(a))
        a = str_to_float(cfg.get('wirePairAmax', ''))
        if a > 0:
            app.txtWirePairAmax.setText('{:.1f}'.format(a))
        s = str_to_float(cfg.get('wirePairSpacing', ''))
        if s > 0:
            app.txtWirePairSpacing.setText('{:.1f}'.format(s))
        app.txtWirePairSkew.setText('{:.1f}'.format(str_to_float(cfg.get('wirePairSkew', ''))))
