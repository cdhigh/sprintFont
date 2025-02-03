#!/usr/bin/env python3
#-*- coding:utf-8 -*-
"""
Sprint-Layout v6 2022及以上版本的插件
Author: cdhigh <https://github.com/cdhigh>
==========================
使用cx_freeze打包
cxfreeze --base-name=Win32GUI --icon=app.ico sprintFont.py
==========================
使用pyinstaller打包
-F: 打包为单文件模式
-D: 打包为文件夹模式
-w: windows执行系统，不弹出cmd命令行
-i: 图标
pyinstaller.exe -F -w -i app.ico sprintFont.py
==========================
使用Nuitka打包，Nuitka打包时目录不能有中文名，打包完成后可以
python -m nuitka --standalone --onefile --windows-disable-console --show-progress --plugin-enable=tk-inter --windows-icon-from-ico=./app.ico  sprintFont.py
python -m nuitka --standalone --windows-disable-console --show-progress --plugin-enable=tk-inter --windows-icon-from-ico=./app.ico sprintFont.py
"""
import os, sys, locale, json, threading, queue, datetime, pickle, math, gettext, itertools
from functools import partial
from fontTools.ttLib import ttFont, ttCollection
from ui.sprint_font_ui import *
from comm_utils import *
from widget_right_click import rightClicker
import sprint_struct.sprint_textio as sprint_textio
from lceda_to_sprint import LcComponent
from sprint_struct.sprint_export_dsn import PcbRule, SprintExportDsn

__Version__ = "1.7"
__DATE__ = "20250203"
__AUTHOR__ = "cdhigh"

#DEBUG_IN_FILE = r'd:\1.txt'
DEBUG_IN_FILE = ""

#在Windows10及以上系统，用户字体目录为：C:\Users\%USERNAME%\AppData\Local\Microsoft\Windows\Fonts
WIN_DIR = os.getenv('WINDIR')
FONT_DIR = os.path.join(WIN_DIR if WIN_DIR else "c:/windows", "fonts")

if getattr(sys, 'frozen', False): #在cxFreeze打包后
    MODULE_PATH = os.path.dirname(sys.executable)
else:
    MODULE_PATH = os.path.dirname(__file__)

CFG_FILENAME = os.path.join(MODULE_PATH, "config.json")
I18N_PATH = os.path.join(MODULE_PATH, 'i18n')

#目前支持的语种，语种代码全部为小写
SUPPORTED_LANGUAGES = ('en', 'zh_cn', 'de', 'es', 'pt', 'fr', 'ru', 'tr')

STABAR_INFO_INPUT_FILE = 0
STABAR_INFO_RELEASES = 1
STABAR_INFO_ISSUES = 2
STABAR_MAX_INFO_IDX = STABAR_INFO_ISSUES

#Sprint-Layout的插件返回码定义
#0: = 中止/无动作
#1: = 完全替换元素，Sprint-Layout删除选中的项目并将其替换为插件输出文件中的新项目。
#2: = 绝对添加元素，Sprint-Layout从插件输出文件中插入新元素。不会删除任何项目。
#3: = 相对替换元素，Sprint-Layout从插件输出文件中删除标记的元素和新元素“粘”到鼠标上，并且可以由用户放置。
#4: = 相对添加元素，插件输出文件中的新元素“粘”在鼠标上，并且可以由用户放置。不会删除任何项目。
RETURN_CODE_NONE = 0
RETURN_CODE_REPLACE_ALL = 1
RETURN_CODE_INSERT_ALL = 2
RETURN_CODE_REPLACE_STICKY = 3
RETURN_CODE_INSERT_STICKY = 4

URI_RELEASES = 'https://github.com/cdhigh/sprintFontRelease/releases'
URI_ISSUES = 'https://github.com/cdhigh/sprintFontRelease/issues'

class Application(Application_ui):
    #这个类实现具体的事件处理回调函数。界面生成代码在Application_ui中。
    def __init__(self, master=None):
        Application_ui.__init__(self, master)
        self.loadConfig()
        self.initI18n()
        self.retranslateUi()
        self.master.title('sprintFont v{}'.format(__Version__))
        #width = str_to_int(self.master.geometry().split('x')[0])
        #if (width > 16): #状态栏仅使用一个分栏，占满全部空间
        self.staBar.panelwidth(0, 100) #Label的width的单位为字符个数
        self.txtFontSize = 14
        
        self.versionJson = {} #用来更新版本使用
        self.checkUpdateFrequency = 30
        self.lastCheckUpdate = None
        self.skipVersion = ''
        self.easyEdaSite = ''

        #这三行代码是修正python3.7的treeview颜色设置不生效的BUG，其他版本可能不需要
        #fixed_map = lambda op: [elm for elm in style.map("Treeview", query_opt=op) if elm[:2] != ("!disabled", "!selected")]
        #style = Style() #in ttk package
        #style.map("Treeview", foreground=fixed_map("foreground"), background=fixed_map("background"))

        self.treRules.configure(columns=['Item', 'Value'])
        self.treRules.configure(show='') #'headings'
        self.treRules.configure(selectmode='browse') #只允许单行选择
        #self.treRules.tag_configure('gray_row', background='#cccccc')
        #设置反转字体背景的下拉框字体
        popdown = self.master.tk.call("ttk::combobox::PopdownWindow", self.cmbCapLeft)
        self.master.tk.call(f"{popdown}.f.l", "configure", "-font", '{Times New Roman} 14 bold')
        popdown = self.master.tk.call("ttk::combobox::PopdownWindow", self.cmbCapRight)
        self.master.tk.call(f"{popdown}.f.l", "configure", "-font", '{Times New Roman} 14 bold')
        
        self.wirePairTuner = None
        self.wirePairTextIo = None
        self.teardropImage = None
        self.roundedTrackImage = None
        self.singleWirePairImage = None
        self.doubleWirePairImage = None
        self.pcbRule = PcbRule()

        #绑定额外的事件处理函数
        self.bindWidgetEvents()
        
        self.populateWidgets()
        self.restoreConfig()
        #self.translateWidgets()

        #分析Sprint-Layout传入的参数
        self.inFileName = ''
        self.outFileName = ''
        self.pcbWidth = 0
        self.pcbHeight = 0
        self.pcbAll = False
        if (len(sys.argv) >= 2): #第二个参数为临时文件名
            self.inFileName = sys.argv[1]
            if not (os.path.exists(self.inFileName)):
                self.inFileName = ''
                
            w = [arg for arg in sys.argv if arg.startswith('/W:')] #板子宽度
            h = [arg for arg in sys.argv if arg.startswith('/H:')] #板子高度
            a = [arg for arg in sys.argv if arg == '/A']  #如果是整板导出，则有此参数
            if w and h:
                self.pcbWidth = str_to_int(w[0][3:]) / 10000
                self.pcbHeight = str_to_int(h[0][3:]) / 10000
                
            self.pcbAll = True if a else False
        
        #输出文件名为输入文件名加一个 "_out"
        if self.inFileName:
            inExts = os.path.splitext(self.inFileName)
            self.outFileName = '{}_out{}'.format(inExts[0], inExts[1] if (len(inExts) > 1) else '')
            if not self.pcbAll:
                self.cmdExportDsn.configure(state='disabled')
                self.cmdImportSes.configure(state='disabled')
                self.lblAutoRouterTips.setText(_("Please deselect all items before launching the plugin"))
                self.lblAutoRouterTips.configure(foreground='red')
                #self.cmdRemoveTeardrops.configure(state='disabled')
        else: #单独执行
            self.cmdOk.configure(state='disabled')
            self.cmdOkFootprint.configure(state='disabled')
            self.cmdOkSvg.configure(state='disabled')
            self.cmdImportSes.configure(state='disabled')
            self.cmdExportDsn.configure(state='disabled')
            self.lblSaveAsAutoRouter.configure(state='disabled')
            self.cmdAddTeardrops.configure(state='disabled')
            self.cmdRemoveTeardrops.configure(state='disabled')
            self.cmdRoundedTrackConvert.configure(state='disabled')
            self.lblSaveAsRoundedTrack.configure(state='disabled')
            self.cmdOkWirePair.configure(state='disabled')
            self.lblSaveAsWirePair.configure(state='disabled')
            
        #显示输入文件名或显示单独执行模式字符串
        self.currentStatusBarInfoIdx = STABAR_INFO_INPUT_FILE - 1 #让第一次显示时恢复0
        self.updateStatusBar()

        #版本更新检查，启动5s后检查一次更新
        self.master.after(5000, self.periodicCheckUpdate)

        self.txtMain.focus_set()

    #初始化多语种支持
    def initI18n(self):
        self.sysLanguge = locale.getdefaultlocale()[0]
        self.language = lang = self.cfg.get('language', '')
        lang = self.getSupportedLanguage(lang or self.sysLanguge)
        tr = gettext.translation('messages', localedir=I18N_PATH, languages=[lang], fallback=True)
        tr.install()

    #获取一个支持的语言代码
    def getSupportedLanguage(self, lang):
        lang = lang.lower().replace('-', '_')
        if lang in SUPPORTED_LANGUAGES:
            return lang

        #同一语种的其他可选语言
        baseLang = lang.split('_')[0]
        return next((item for item in SUPPORTED_LANGUAGES if item.startswith(baseLang)), 'en')
        
    #多页控件的当前页面发生改变，初始化对应页面的控件
    def tabStrip_NotebookTabChanged(self, event):
        TAB_FONT = 0
        TAB_FOOTPRINT = 1
        TAB_SVG = 2
        TAB_AUTOROUTER = 3
        TAB_TEARDROP = 4
        TAB_ROUNDEDTRACK = 5
        TAB_WIREPAIR = 6
        try:
            tabNo = self.getCurrentTabStripTab()
            if tabNo == TAB_FONT:
                self.txtMain.focus_set()
            elif tabNo == TAB_FOOTPRINT:
                self.txtFootprintFile.focus_set()
            elif tabNo == TAB_SVG:
                self.txtSvgFile.focus_set()
            elif tabNo == TAB_AUTOROUTER:
                self.txtDsnFile.focus_set()
            elif tabNo == TAB_TEARDROP:
                if not self.teardropImage:
                    from ui.teardrop_image import teardropImageData
                    self.teardropImage = PhotoImage(data=teardropImageData)
                    self.picTeardrops.create_image(0, 0, image=self.teardropImage, anchor=NW)
                self.cmbhPercent.focus_set()
            elif tabNo == TAB_ROUNDEDTRACK:
                if not self.roundedTrackImage:
                    from ui.rounded_track_image import roundedTrackImageData, roundedTrackImageDataCn
                    lang = self.language or self.sysLanguge
                    imgData = roundedTrackImageDataCn if lang.startswith('zh') else roundedTrackImageData
                    self.roundedTrackImage = PhotoImage(data=imgData)
                    self.picRoundedTrack.create_image(0, 0, image=self.roundedTrackImage, anchor=NW)
                self.cmbRoundedTrackType.focus_set()
            elif tabNo == TAB_WIREPAIR:
                self.initWirePair()
                self.cmbWirePairType.focus_set()
        except Exception as e:
            print(str(e))
            #pass

    #获取多页控件的当前页面
    def getCurrentTabStripTab(self):
        try:
            return self.tabStrip.index(self.tabStrip.select())
        except:
            return -1

    #设置多页控件的当前页面, 0-第一个页面
    def setCurrentTabStripTab(self, tabNo: int):
        tabs = self.tabStrip.tabs()
        if 0 <= tabNo < len(tabs):
            self.tabStrip.select(tabs[tabNo])

    #绑定额外的事件处理函数
    def bindWidgetEvents(self):
        #绑定文件文本框的回车事件
        self.txtFootprintFile.bind('<Return>', self.txtFootprintFile_Return)
        self.txtSvgFile.bind('<Return>', self.txtSvgFile_Return)

        #绑定文本控件的右键菜单
        self.txtMain.bind('<Button-3>', rightClicker, add=False)
        self.txtFootprintFile.bind('<Button-3>', rightClicker, add=False)
        self.txtSvgFile.bind('<Button-3>', rightClicker, add=False)

        #绑定状态栏的双击事件
        self.staBar.lbls[0].bind('<Double-Button-1>', self.staBar_Double_Button_1)

        #导入SES时如果按住Shift点击按钮则弹出菜单，提供更多的导入选择
        self.cmdImportSes.bind('<Shift-Button-1>', self.cmdImportSes_Shift_Button_1)
        self.mnuImportSes = Menu(self.master, tearoff=0)
        self.mnuImportSes.add_command(label=_("Import all (remove routed ratsnests)"), command=partial(self.cmdmnuImportSes, trimRatsnestMode='trimRouted', trackOnly=False))
        self.mnuImportSes.add_command(label=_("Import all (remove all ratsnests)"), command=partial(self.cmdmnuImportSes, trimRatsnestMode='trimAll', trackOnly=False))
        self.mnuImportSes.add_command(label=_("Import all (keep all ratsnests)"), command=partial(self.cmdmnuImportSes, trimRatsnestMode='keepAll', trackOnly=False))
        self.mnuImportSes.add_command(label=_("Import auto-routed tracks only"), command=partial(self.cmdmnuImportSes, trimRatsnestMode='trimRouted', trackOnly=True))

    #判断是否需要检查更新，如果需要，另外开一个线程进行后台检查
    #此函数在程序启动后5s才会得到执行
    def periodicCheckUpdate(self):
        if (self.checkUpdateFrequency <= 0):
            return

        #一个月检查一个更新
        now = datetime.datetime.now()
        if ((not self.lastCheckUpdate) or ((now - self.lastCheckUpdate).days >= self.checkUpdateFrequency)):
            self.lastCheckUpdate = now
            try:
                self.thVersionCheck = threading.Thread(target=self.versionCheckThread, daemon=True)
                self.thVersionCheck.start()
            except:
                pass

    #初始化填充界面控件
    def populateWidgets(self):
        #获取系统已安装的字体列表
        #启动一个新的线程在后台更新字体列表，避免启动过慢
        self.fontNameMap = {}
        try:
            self.fontNameQueue = queue.Queue(5)
            #daemon=True 可以让子线程在主线程退出后自动销毁
            self.fontThread = threading.Thread(target=self.generateFontFileNameMap, args=(self.fontNameQueue,), daemon=True)
            self.fontThread.start()
            #启动after方法，每隔200ms确认一次是否已经获取到字体列表
            self.master.after(200, self.populateFontCombox)
        except Exception as e: #如果启动线程失败，就直接在这里更新
            print('create thread failed: {}'.format(str(e)))
            self.populateFontCombox(self.generateFontFileNameMap())
            
        #字体板层
        self.cmbLayerList = [_("C1 (Front copper)"), _("S1 (Front silkscreen)"), _("C2 (Back copper)"), 
            _("S2 (Back silkscreen)"), _("I1 (Inner copper1)"), _("I2 (Inner copper2)"), _("U (Edge.cuts)"), ]
        self.cmbLayer.configure(values=self.cmbLayerList)
        self.cmbLayer.current(1) #默认为顶层丝印层
        self.cmbSvgLayer.configure(values=self.cmbLayerList)
        self.cmbSvgLayer.current(1)

        #字体字高
        self.cmbFontHeightList = [1.0, 2.0, 3.0, 4.0]
        self.cmbFontHeight.configure(values=self.cmbFontHeightList)
        self.cmbFontHeight.current(1) #字高默认2mm
        
        #字间距
        self.cmbWordSpacingList = [-0.5, -0.2, 0, 0.2, 0.5, 0.8, 1.0]
        self.cmbWordSpacing.configure(values=self.cmbWordSpacingList)
        self.cmbWordSpacing.current(2)
        
        #字体行间距
        self.cmbLineSpacingList = [-0.5, -0.2, 0, 0.2, 0.5, 1.0, 2.0]
        self.cmbLineSpacing.configure(values=self.cmbLineSpacingList)
        self.cmbLineSpacing.current(2)
        
        #字体平滑程度
        self.cmbSmoothList = [_("Super fine (super slow)"), _("Fine (slow)"), _("Normal"), _("Rough"), _("Super Rough"), ]
        self.cmbSmooth.configure(values=self.cmbSmoothList)
        self.cmbSmooth.current(2)
        self.cmbSvgSmooth.configure(values=self.cmbSmoothList)
        self.cmbSvgSmooth.current(2)

        #字体反转背景
        self.cmbPaddingList = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0]
        self.cmbPadding.configure(values=self.cmbPaddingList)
        self.cmbPadding.current(0)
        self.cmbPadding.configure(state='disabled')
        self.cmbCapLeftList = ['  [', '  \\', '  /', '  (', '  <', '  >']
        self.cmbCapLeft.configure(values=self.cmbCapLeftList)
        self.cmbCapLeft.current(0)
        self.cmbCapLeft.configure(state='disabled')
        self.cmbCapRightList = ['  ]', '  \\', '  /', '  )', '  <', '  >']
        self.cmbCapRight.configure(values=self.cmbCapRightList)
        self.cmbCapRight.current(0)
        self.cmbCapRight.configure(state='disabled')

        #SVG/QRCODE选择
        self.cmbSvgQrcodeList = [_("SVG"), _("Qrcode")]
        self.cmbSvgQrcode.configure(values=self.cmbSvgQrcodeList)
        self.cmbSvgQrcode.current(0)

        #SVG生成方法
        self.cmbSvgModeList = [_("Track"), _("Polygon")]
        self.cmbSvgMode.configure(values=self.cmbSvgModeList)
        self.cmbSvgMode.current(0)

        #SVG图像高度
        self.cmbSvgHeightList = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 20.0, 30.0, 40.0, 50.0]
        self.cmbSvgHeight.configure(values=self.cmbSvgHeightList)
        self.cmbSvgHeight.current(9) #SVG图像高度默认10mm

        #泪滴的比例
        self.cmbhPercentList = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
        self.cmbhPercent.configure(values=self.cmbhPercentList)
        self.cmbhPercent.current(4) #水平比例默认50%
        self.cmbvPercentList = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
        self.cmbvPercent.configure(values=self.cmbvPercentList)
        self.cmbvPercent.current(8) #垂直比例默认90%
        self.cmbTeardropSegsList = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        self.cmbTeardropSegs.configure(values=self.cmbTeardropSegsList)
        self.cmbTeardropSegs.current(9) #默认10个线段
        self.cmbTeardropPadTypeList = [_("PTH pad"), _("SMD pad"), _("PTH/SMD")]
        self.cmbTeardropPadType.configure(values=self.cmbTeardropPadTypeList)
        self.cmbTeardropPadType.current(0)

        #弧形走线
        self.cmbRoundedTrackTypeList = [_("Tangent"), _("Three-point"), _("Bezier")]
        self.cmbRoundedTrackType.configure(values=self.cmbRoundedTrackTypeList)
        self.cmbRoundedTrackType.current(0)
        self.cmbRoundedTrackBigDistanceList = [0.5, 1, 2, 3, 4, 5, 6, 7, 8, 9]
        self.cmbRoundedTrackBigDistance.configure(values=self.cmbRoundedTrackBigDistanceList)
        self.cmbRoundedTrackBigDistance.current(3) #默认3mm
        self.cmbRoundedTrackSmallDistanceList = [0.5, 1, 2, 3, 4, 5, 6, 7, 8, 9]
        self.cmbRoundedTrackSmallDistance.configure(values=self.cmbRoundedTrackSmallDistanceList)
        self.cmbRoundedTrackSmallDistance.current(0) #默认0.5mm
        self.cmbRoundedTrackSegsList = [3, 4, 5, 6, 7, 8, 9, 10, 20]
        self.cmbRoundedTrackSegs.configure(values=self.cmbRoundedTrackSegsList)
        self.cmbRoundedTrackSegs.current(7) #默认10个线段

        #导线对长度调整
        self.cmbWirePairTypeList = [_("Single-sided"), _("Double-sided")]
        self.cmbWirePairType.configure(values=self.cmbWirePairTypeList)
        self.cmbWirePairType.current(0)
        
    #更新字体列表组合框，可能直接调用，也可能会使用after延时调用
    def populateFontCombox(self, fontMap: dict=None):
        if fontMap is None: #使用after延时调用
            if self.fontNameQueue.empty(): #还没有从磁盘里面读取到字体
                self.master.after(200, self.populateFontCombox) #延时200ms再试
                return
            else:
                fontMap = self.fontNameQueue.get_nowait()

        if fontMap:
            self.fontNameMap = fontMap
            #with open('d:/fontNameMap.json', 'w', encoding='utf-8') as f: #TODO
            #    f.write(json.dumps(fontMap, ensure_ascii=False, indent=2))
            self.cmbFontList = sorted(self.fontNameMap.keys())
            self.cmbFont.configure(value=self.cmbFontList)
            lastFont = self.cfg.get('font', '')
            fontNameList = self.cmbFontList or ['']
            if lastFont and (lastFont in fontNameList):
                self.cmbFont.current(fontNameList.index(lastFont))
            elif (self.sysLanguge.startswith('zh')): #中文字体一般在最后，所以默认选择最后一个，保证开箱即用
                self.cmbFont.setText(fontNameList[-1])
            elif 'Calibri' in fontNameList: #英文或拉丁文字体也是为了保证开箱即用
                self.cmbFont.setText('Calibri')
            else:
                self.cmbFont.setText(fontNameList[0])
        
    #从配置文件中恢复以前的配置数据
    def restoreConfig(self):
        cfg = self.cfg
        if not isinstance(cfg, dict):
            return

        #字体界面
        lastFont = cfg.get('font', '')
        if lastFont and (lastFont in self.cmbFontList):
            self.cmbFont.current(self.cmbFontList.index(lastFont))

        self.txtFontSize = str_to_int(cfg.get('txtFontSize', '14'))

        lastHeight = str_to_float(cfg.get('height', ''))
        if lastHeight:
            self.cmbFontHeight.setText(str(lastHeight))

        lastLayer = str_to_int(cfg.get('layer', '1'), 100)
        if 0 <= lastLayer < len(self.cmbLayerList):
            self.cmbLayer.current(lastLayer)
        smooth = str_to_int(cfg.get('smooth', '2'), 100)
        if 0 <= smooth < len(self.cmbSmoothList):
            self.cmbSmooth.current(smooth)

        ws = str_to_float(cfg.get('wordSpacing', "0"))
        self.cmbWordSpacing.setText(str(ws))
        ls = str_to_float(cfg.get('lineSpacing', "0"))
        self.cmbLineSpacing.setText(str(ls))

        if (str_to_int(cfg.get('invertBackground', '0'))):
            self.chkInvertedBackground.setValue(1)
            self.cmbPadding.configure(state='normal')
            self.cmbCapLeft.configure(state='readonly')
            self.cmbCapRight.configure(state='readonly')
        padding = cfg.get('padding', '')
        if padding:
            self.cmbPadding.setText(padding)
        capLeft = str_to_int(cfg.get('capLeft', '0'))
        if 0 <= capLeft < len(self.cmbCapLeftList):
            self.cmbCapLeft.current(capLeft)
        capRight = str_to_int(cfg.get('capRight', '0'))
        if 0 <= capRight < len(self.cmbCapRightList):
            self.cmbCapRight.current(capRight)

        #封装导入页面
        if (str_to_int(cfg.get('importFootprintText', '0'))):
            self.chkImportFootprintText.setValue(1)

        #SVG页面
        svgQrcode = str_to_int(cfg.get('svgQrcode', '0'), 100)
        if 0 <= svgQrcode < len(self.cmbSvgQrcodeList):
            self.cmbSvgQrcode.current(svgQrcode)
        svgMode = str_to_int(cfg.get('svgMode', '2'), 100)
        if 0 <= svgMode < len(self.cmbSvgModeList):
            self.cmbSvgMode.current(svgMode)
        smooth = str_to_int(cfg.get('svgSmooth', '2'), 100)
        if 0 <= smooth < len(self.cmbSmoothList):
            self.cmbSvgSmooth.current(smooth)
        svgLayer = str_to_int(cfg.get('svgLayer', '2'), 100)
        if 0 <= svgLayer < len(self.cmbSvgLayerList):
            self.cmbSvgLayer.current(svgLayer)
        lastHeight = str_to_float(cfg.get('svgHeight', ''))
        if lastHeight:
            self.cmbSvgHeight.setText(str(lastHeight))

        lastTab = str_to_int(cfg.get('lastTab', '0'))
        if (lastTab > 0):
            self.setCurrentTabStripTab(lastTab)

        #立创EDA的服务器节点
        easyEdaSite = cfg.get('easyEdaSite', '').lower()
        if (easyEdaSite in ('cn', 'global')):
            self.easyEdaSite = easyEdaSite
        else:
            self.easyEdaSite = ''

        #版本更新检查
        self.checkUpdateFrequency = str_to_int(cfg.get('checkUpdateFrequency', '30'))
        if (self.checkUpdateFrequency < 0):
            self.checkUpdateFrequency = 0
        lastCheck = cfg.get('lastCheckUpdate', '')
        try:
            self.lastCheckUpdate = datetime.datetime.strptime(lastCheck, '%Y-%m-%d')
        except:
            self.lastCheckUpdate = None
        self.skipVersion = cfg.get('skipVersion', '')

        #自动布线规则和其他配置
        trackWidth = str_to_float(cfg.get('trackWidth', '0.3'))
        viaDiameter = str_to_float(cfg.get('viaDiameter', '0.7'))
        viaDrill = str_to_float(cfg.get('viaDrill', '0.3'))
        clearance = str_to_float(cfg.get('clearance', '0.3'))
        smdSmdClearance = str_to_float(cfg.get('smdSmdClearance', '0.06'))
        self.pcbRule.trackWidth = trackWidth if (trackWidth > 0.1) else 0.3
        self.pcbRule.viaDiameter = viaDiameter if (viaDiameter > 0.1) else 0.7
        self.pcbRule.viaDrill = viaDrill if (viaDrill > 0.1) else 0.3
        self.pcbRule.clearance = clearance if (clearance > 0.1) else 0.3
        self.pcbRule.smdSmdClearance = smdSmdClearance if (smdSmdClearance > 0.01) else 0.06
        if (self.pcbRule.viaDiameter <= self.pcbRule.viaDrill):
            self.pcbRule.viaDiameter = self.pcbRule.viaDrill + 0.1
        self.updateRuleView()

        #泪滴焊盘
        hPercent = str_to_int(cfg.get('teardropHPercent', '50'))
        vPercent = str_to_int(cfg.get('teardropVPercent', '90'))
        segs = str_to_int(cfg.get('teardropSegs', '10'))
        padTypeIdx = str_to_int(cfg.get('teardropPadType', '0'))
        self.cmbhPercent.setText(str(hPercent))
        self.cmbvPercent.setText(str(vPercent))
        if segs:
            self.cmbTeardropSegs.setText(str(segs))
        if 0 <= padTypeIdx <= 2:
            self.cmbTeardropPadType.current(padTypeIdx)

        #弧形走线
        rtType = str_to_int(cfg.get('roundedTrackType', '0'))
        if 0 <= rtType <= 2:
            self.cmbRoundedTrackType.current(rtType)
        
        distance = str_to_float(cfg.get('roundedTrackBigDistance', ''))
        if distance > 0:
            self.cmbRoundedTrackBigDistance.setText('{:.1f}'.format(distance))
        distance = str_to_float(cfg.get('roundedTrackSmallDistance', ''))
        if distance > 0:
            self.cmbRoundedTrackSmallDistance.setText('{:.1f}'.format(distance))
        segs = str_to_int(cfg.get('roundedTrackSegs', '10'))
        if segs:
            self.cmbRoundedTrackSegs.setText(segs)

        #导线对长度调整
        wType = str_to_int(cfg.get('wirePairType', '0'))
        if 0 <= wType <= 1:
            self.cmbWirePairType.current(wType)
        a = str_to_float(cfg.get('wirePairAmin', ''))
        if a > 0:
            self.txtWirePairAmin.setText('{:.1f}'.format(a))
        a = str_to_float(cfg.get('wirePairAmax', ''))
        if a > 0:
            self.txtWirePairAmax.setText('{:.1f}'.format(a))
        s = str_to_float(cfg.get('wirePairSpacing', ''))
        if s > 0:
            self.txtWirePairSpacing.setText('{:.1f}'.format(s))
        self.txtWirePairSkew.setText('{:.1f}'.format(str_to_float(cfg.get('wirePairSkew', ''))))
        
    #读取配置文件到内存
    def loadConfig(self):
        self.cfg = {}
        if os.path.isfile(CFG_FILENAME):
            try:
                with open(CFG_FILENAME, 'r', encoding='utf-8') as f:
                    self.cfg = json.load(f)
                if not isinstance(self.cfg, dict):
                    self.cfg = {}
            except:
                pass

    #保存当前配置数据
    def saveConfig(self):
        if self.versionJson: #如果检查到版本更新，则第二天再检查一次
            self.lastCheckUpdate = datetime.datetime.now() - datetime.timedelta(days=29)

        cfg = {'language': self.language, 'font': self.cmbFont.text(), 
            'txtFontSize': str(self.txtFontSize), 'height': self.cmbFontHeight.text(), 
            'layer': str(self.cmbLayer.current()), 'wordSpacing': self.cmbWordSpacing.text(), 
            'lineSpacing': self.cmbLineSpacing.text(), 'smooth': str(self.cmbSmooth.current()), 
            'invertBackground': str(self.chkInvertedBackground.value()), 'padding': self.cmbPadding.text(),
            'capLeft': str(self.cmbCapLeft.current()), 'capRight': str(self.cmbCapRight.current()),
            'importFootprintText': str(self.chkImportFootprintText.value()),
            'svgQrcode': str(self.cmbSvgQrcode.current()),
            'svgMode': str(self.cmbSvgMode.current()), 'svgLayer': str(self.cmbSvgLayer.current()),
            'svgHeight': self.cmbSvgHeight.text(), 'svgSmooth': str(self.cmbSvgSmooth.current()),
            'easyEdaSite': self.easyEdaSite, 'lastTab': str(self.getCurrentTabStripTab()),
            'checkUpdateFrequency': str(self.checkUpdateFrequency),
            'lastCheckUpdate': self.lastCheckUpdate.strftime('%Y-%m-%d') if self.lastCheckUpdate else '',
            'skipVersion': str(self.skipVersion), 
            'trackWidth': str(self.pcbRule.trackWidth), 'viaDiameter': str(self.pcbRule.viaDiameter),
            'viaDrill': str(self.pcbRule.viaDrill), 'clearance': str(self.pcbRule.clearance),
            'smdSmdClearance': str(self.pcbRule.smdSmdClearance),
            'teardropHPercent': self.cmbhPercent.text(), 'teardropVPercent': self.cmbvPercent.text(),
            'teardropSegs': self.cmbTeardropSegs.text(), 'teardropPadType': str(self.cmbTeardropPadType.current()),
            'roundedTrackType': str(self.cmbRoundedTrackType.current()), 'roundedTrackBigDistance': self.cmbRoundedTrackBigDistance.text(),
            'roundedTrackSmallDistance': self.cmbRoundedTrackSmallDistance.text(),
            'roundedTrackSegs': self.cmbRoundedTrackSegs.text(),
            'wirePairType': str(self.cmbWirePairType.current()), 'wirePairAmin': self.txtWirePairAmin.text(),
            'wirePairAmax': self.txtWirePairAmax.text(), 'wirePairSpacing': self.txtWirePairSpacing.text(),
            'wirePairSkew': self.txtWirePairSkew.text(),
        }
        
        if cfg != self.cfg:  #有变化再写配置文件
            self.cfg = cfg
            try:
                with open(CFG_FILENAME, 'w', encoding='utf-8') as f:
                    json.dump(cfg, f, indent=2)
            except:
                pass
    
    def cmbFont_ComboboxSelected(self, event=None):
        self.txtMain.configure(font=Font(family=self.cmbFont.text(), size=self.txtFontSize))
        
    #选择一个封装文件
    def cmdFootprintFile_Cmd(self, event=None):
        ret = tkFileDialog.askopenfilename(filetypes=[(_("Kicad footprint"), "*.kicad_mod"), 
            (_("easyEDA footprint"), "*.json"), (_("All files"), "*.*")])
        if ret:
            self.txtFootprintFile.setText(ret)

    #选择一个SVG文件
    def cmdSvgFile_Cmd(self, event=None):
        ret = tkFileDialog.askopenfilename(filetypes=[(_("SVG files"),"*.svg"), (_("All files"), "*.*")])
        if ret:
            self.txtSvgFile.setText(ret)

    #选择一个DSN文件
    def cmdDsnFile_Cmd(self, event=None):
        retFile = tkFileDialog.asksaveasfilename(filetypes=[(_("Specctra DSN files"), '*.dsn'), (_("All files"), '*.*')])
        if retFile:
            if not retFile.lower().endswith('.dsn'):
                retFile = retFile + '.dsn'
            self.txtDsnFile.setText(retFile)
            self.txtSesFile.setText(os.path.splitext(retFile)[0] + '.ses')

    #选择一个SES文件
    def cmdSesFile_Cmd(self, event=None):
        retFile = tkFileDialog.askopenfilename(filetypes=[(_("Specctra session files"),"*.ses"), (_("All files"), "*.*")])
        if retFile:
            self.txtSesFile.setText(retFile)
            
    #取消退出
    def cmdCancel_Cmd(self, event=None):
        self.destroy()
        sys.exit(RETURN_CODE_NONE)

    #取消退出
    def cmdCancelFootprint_Cmd(self, event=None):
        self.destroy()
        sys.exit(RETURN_CODE_NONE)

    #取消退出
    def cmdCancelSvg_Cmd(self, event=None):
        self.destroy()
        sys.exit(RETURN_CODE_NONE)

    #取消退出
    def cmdCancelAutoRouter_Cmd(self, event=None):
        self.destroy()
        sys.exit(RETURN_CODE_NONE)

    #取消退出
    def cmdCancelTeardrops_Cmd(self, event=None):
        self.destroy()
        sys.exit(RETURN_CODE_NONE)

    #取消退出
    def cmdRoundedTrackCancel_Cmd(self, event=None):
        self.destroy()
        sys.exit(RETURN_CODE_NONE)

    #点击翻转字体背景
    def chkInvertedBackground_Cmd(self, event=None):
        if self.chkInvertedBackground.value():
            self.cmbPadding.configure(state='normal')
            self.cmbCapLeft.configure(state='readonly')
            self.cmbCapRight.configure(state='readonly')
        else:
            self.cmbPadding.configure(state='disabled')
            self.cmbCapLeft.configure(state='disabled')
            self.cmbCapRight.configure(state='disabled')

    #保存字体结果为单独一个文本文件
    def lblSaveAs_Button_1(self, event):
        self.cmdOk_Cmd(saveas=True)
        
    #转换封装结果保存为单独一个文本文件
    def lblSaveAsFootprint_Button_1(self, event):
        self.cmdOkFootprint_Cmd(saveas=True)
        
    #开始转换文本为多边形
    #saveas: 是否保存到其他文件
    def cmdOk_Cmd(self, event=None, saveas=False):
        self.saveConfig()
        txt = self.txtMain.get('1.0', END).strip()
        if not txt:
            showwarning(_('info'), _('Text is empty'))
            return

        textIo = self.generatePolygons(txt)
        if not textIo:
            showwarning(_('info'), _('Failed to generate text'))
        elif isinstance(textIo, str): #出错，返回的是错误提示文本
            showwarning(_('info'), textIo)
        elif saveas:
            self.saveTextFile(str(textIo))
        else: #写输出文件
            self.saveOutputFile(str(textIo))
            self.destroy()
            sys.exit(RETURN_CODE_INSERT_STICKY)

    #在封装文件文本框中回车，根据情况自动执行响应的命令
    def txtFootprintFile_Return(self, event=None):
        if (str(self.cmdOkFootprint['state']) == 'disabled') or (not self.txtFootprintFile.text().strip()):
            return

        self.cmdOkFootprint_Cmd()

    #点击了将封装文件转换为Sprint-Layout的按钮
    #saveas: 是否需要保存到其他文件
    def cmdOkFootprint_Cmd(self, event=None, saveas=False):
        self.saveConfig()
        fileName = self.txtFootprintFile.text().strip()
        #TODO, for test
        #fileName = self.autoAddKicadPath(fileName)

        if (not self.verifyFileName(fileName, LcComponent.isLcedaComponent)):
            return
        
        errStr, retStr = self.generateFootprint(fileName)
        if errStr:
            showwarning(_('info'), errStr)
        elif not retStr:
            if LcComponent.isLcedaComponent(fileName):
                showwarning(_('info'), _('Failed to parse content\nMaybe Id error or Internet disconnected?'))
            else:
                showwarning(_('info'), _('Failed to parse file content'))
        elif saveas:
            self.saveTextFile(retStr)
        else:
            self.saveOutputFile(retStr)
            self.destroy()
            sys.exit(RETURN_CODE_INSERT_STICKY)
    
    #转换SVG结果保存为单独一个文本文件
    def lblSaveAsSvg_Button_1(self, event):
        self.cmdOkSvg_Cmd(saveas=True)
        
    #将输入的文本转换为一系列的二维码SVG绘图指令
    def textToQrcodeStr(self, txt: str):
        from qrcode import QRCode
        from qrcode.image.svg import SvgPathImage
        qr = QRCode(image_factory=SvgPathImage)
        qr.add_data(txt)
        qr.make(fit=True)
        img = qr.make_image()
        return img.to_string().decode('utf-8')

    #在SVG文件文本框中回车，根据情况自动执行响应的命令
    def txtSvgFile_Return(self, event=None):
        if (str(self.cmdOkSvg['state']) == 'disabled') or (not self.txtSvgFile.text().strip()):
            return

        self.cmdOkSvg_Cmd()

    #点击了将SVG文件转换为Sprint-Layout的按钮
    #saveas: 是保存到sprint-layout的输出文件还是另存为
    def cmdOkSvg_Cmd(self, event=None, saveas=False):
        self.saveConfig()
        fileName = self.txtSvgFile.text().strip()
        isQrcode = self.cmbSvgQrcode.current()
        if not fileName:
            showwarning(_('info'), _('Input is empty'))
            return

        #如果是SVG模式，校验文件，否则直接使用文本
        if isQrcode:
            fileName = self.textToQrcodeStr(fileName)
        elif not self.verifyFileName(fileName):
            return
        elif not fileName.lower().endswith('.svg'):
            showwarning(_('info'), _('The file format is not supported'))
            return
        
        #生成二维码
        try:
            retStr = self.generateFromSvg(fileName, isQrcode)
        except Exception as e:
            showwarning(_('info'), str(e))
            return

        if not retStr:
            showwarning(_('info'), _('Convert svg image failed'))
        elif saveas:
            self.saveTextFile(retStr)
        else:
            self.saveOutputFile(retStr)
            self.destroy()
            sys.exit(RETURN_CODE_INSERT_STICKY)
        
    #校验文件是否存在或是否合法，不合法则做出提示
    #fileName: 文件名
    #extraVeriFunc: 额外的校验函数，接受一个字符串参数
    def verifyFileName(self, fileName: str, extraVeriFunc=None):
        if not fileName:
            showwarning(_('info'), _('Input is empty'))
            return False

        if (extraVeriFunc and extraVeriFunc(fileName)):
            return True

        if not os.path.isfile(fileName):
            showwarning(_('info'), _("File does not exist\n{}").format(fileName))
            return False
        
        return True

    #将字符串写到输出文件
    def saveOutputFile(self, txt):
        try:
            with open(self.outFileName, 'w', encoding='utf-8') as f:
                f.write(str(txt))
        except:
            pass

    #将字符串保存到文本文件
    def saveTextFile(self, txt: str):
        if not txt:
            return

        retFile = tkFileDialog.asksaveasfilename(title=_("Save to a text file"), filetypes=[(_('Text files'), '*.txt'), (_("All files"), '*.*')])
        if retFile:
            if ('.' not in retFile): #自动添加后缀
                retFile += '.txt'
            try:
                with open(retFile, 'w', encoding='utf-8') as f:
                    f.write(txt)
            except Exception as e:
                showwarning(_('info'), _('Failed to save file.\n{}').format(str(e)))

    #方便进行测试的一个函数，可以仅输入kicad封装文件名，自动添加路径
    def autoAddKicadPath(self, fileName: str):
        if fileName and ('\\' not in fileName) and (not LcComponent.isLcedaComponent(fileName)):
            for root, subdirs, files in os.walk(r'C:\Program Files\KiCad\share\kicad\modules'):
                if fileName + '.kicad_mod' in files:
                    fileName = os.path.join(root, fileName + '.kicad_mod')
        return fileName

    #将字符串转换为Sprint-Layout多边形，返回一个 SprintTextIO 实例 或空
    def generatePolygons(self, txt: str):
        from sprint_struct.font_to_polygon import singleWordPolygon

        if not txt:
            return ''
        
        #参数
        fontName = self.cmbFont.text()
        layerIdx = self.cmbLayer.current() + 1 #Sprint-Layout的板层定义从1开始
        smooth = self.cmbSmooth.current()
        fontHeight = str_to_float(self.cmbFontHeight.text())
        wordSpacing = str_to_float(self.cmbWordSpacing.text())
        lineSpacing = str_to_float(self.cmbLineSpacing.text())
        invert = self.chkInvertedBackground.value()
        padding = str_to_float(self.cmbPadding.text())
        capLeft = self.cmbCapLeft.text().strip()
        capRight = self.cmbCapRight.text().strip()
        if fontHeight <= 0.0:
            fontHeight = 1.0
        if padding < 0.01:
            padding = 0.0
        
        fontFileName, fontIdx = self.fontNameMap.get(fontName, ('', 0))
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
        
        #开始逐字转换
        txt = self.translateUnicodeSymbol(txt)
        offsetY = 0.0
        prevWidth = 0
        polygons = []
        for line in txt.split('\n'):
            offsetX = 0.0 #每一行都从最左边开始
            maxHeight = 0
            for word in line:
                ret = singleWordPolygon(fontName, font, code=ord(word), layerIdx=layerIdx, fontHeight=fontHeight,
                    offsetX=offsetX, offsetY=offsetY, smooth=smooth)
                #print(ret)
                #if not ret: #没有对应的字形，跳过一个空格位置
                #    inc = prevWidth + (wordSpacing * 10000)
                #    offsetX += inc if (inc > 0) else prevWidth
                #    continue
                if not ret or isinstance(ret, str):
                    font.close()
                    return ret
                    
                prevWidth = ret['width']
                polygons.extend(ret['polygons'])
                inc = prevWidth + wordSpacing
                offsetX += inc if (inc > 0) else prevWidth
                if ret['height'] > maxHeight:
                    maxHeight = ret['height']
            #新行
            inc = maxHeight + lineSpacing
            offsetY += inc if (inc > 0) else maxHeight

        font.close()

        textIo = sprint_textio.SprintTextIO()
        if invert: #生成负像
            textIo.add(self.invertFontBackground(polygons, padding, capLeft, capRight))
        else:
            textIo.addAll(polygons)

        #返回字符串
        return textIo

    #反转字体的背景（镂空字）
    #原理：创建一个包含所有多边形的大四边形，形成一个负像
    #padding: 大四边形边线到字体外框的距离，单位为mm
    #capLeft: 四边形左侧形状
    #capRight: 四边形右侧形状
    def invertFontBackground(self, polygons, padding, capLeft, capRight):
        from sprint_struct.sprint_polygon import SprintPolygon
        extPoly = SprintPolygon(polygons[0].layerIdx)

        # 计算包含所有多边形的最小外接矩形
        minX = min(point[0] for poly in polygons for point in poly) - padding
        minY = min(point[1] for poly in polygons for point in poly) - padding
        maxX = max(point[0] for poly in polygons for point in poly) + padding
        maxY = max(point[1] for poly in polygons for point in poly) + padding
        slashAngle = math.radians(70) #斜边的角度: 70度
        tipAngle = math.radians(60) #尖角的角度：120度
        slashOffX = (maxY - minY) / math.tan(slashAngle) #斜杠和反斜杠的X偏移
        tipOffX = ((maxY - minY) / 2) / math.tan(tipAngle) #尖角的X偏移
        midY = (maxY - minY) / 2
        cutNumMap = {0: 50, 1: 20, 2: 10, 3: 5, 4: 2} #一个圆要切割的份数
        #逆时针添加外框坐标，先添加左侧
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
            cutNum = cutNumMap.get(self.cmbSmooth.current(), 10)
            extPoly.addAllPoints(cutCircle(center=(minX, maxY-midY), radius=midY, cutNum=cutNum,
                start=180, stop=360))
            extPoly.addPoint(minX, maxY)
        else: # |
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
            cutNum = cutNumMap.get(self.cmbSmooth.current(), 10)
            extPoly.addAllPoints(cutCircle(center=(maxX, maxY-midY), radius=midY, cutNum=cutNum,
                start=0, stop=180))
            extPoly.addPoint(maxX, minY)
        else:
            extPoly.addPoint(maxX, maxY)
            extPoly.addPoint(maxX, minY)

        #合并多边形
        for poly in polygons:
            extPoly.devour(poly)
            poly.reset()

        return extPoly
        
    #将字符串里面的\u1234转换为对应的字符
    def translateUnicodeSymbol(self, txt: str):
        strLen = len(txt)
        if strLen < 6:
            return txt

        idx = 0
        newTxt = []
        while (idx < (strLen - 5)):
            ch = txt[idx]
            digStr = txt[idx + 2:idx + 6]
            #u后面需要四个数字
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
    
    #将字体文件和字体名字对应起来，关键字为字体名字，值为(文件名, 字体索引)
    #除了系统的字体目录，本软件同一目录下的ttf也可以做为选择
    #如果fontQueue传入值，也通过queue传出给子线程使用
    def generateFontFileNameMap(self, fontQueue: queue.Queue=None):
        fontNameMap = {}
        supportedFontExts = tuple(('.ttf', '.otf', '.ttc', '.otc'))
        
        #支持Widows10及以上系统的用户字体目录
        localDir = os.getenv('LOCALAPPDATA')
        userFontDir = ''
        if localDir:
            userFontDir = os.path.join(localDir, 'Microsoft', 'Windows', 'Fonts')
            if not os.path.exists(userFontDir):
                userFontDir = ''
                
        try:
            fontFileList = [os.path.join(FONT_DIR, f) for f in os.listdir(FONT_DIR) if f.lower().endswith(supportedFontExts)]
        except:
            fontFileList = {}
        
        if userFontDir:
            try:
                fontFileList.extend([os.path.join(userFontDir, f) for f in os.listdir(userFontDir) if f.lower().endswith(supportedFontExts)])
            except:
                pass
            
        try:
            fontFileList.extend([os.path.join(MODULE_PATH, f) for f in os.listdir(MODULE_PATH) if f.lower().endswith(supportedFontExts)])
        except:
            pass
            
        for fontFileName in fontFileList:
            insList = []
            if (fontFileName.endswith(('.ttc', '.otc'))): #一个字体文件里面包含多个字体
                try:
                    ttCol = ttCollection.TTCollection(fontFileName)
                    insList = ttCol.fonts
                except Exception as e:
                    print('Load ttc/otc failed ({}) : {}'.format(fontFileName, str(e)))
                    continue
            else:
                try:
                    insList = [ttFont.TTFont(fontFileName, lazy=True),]
                except Exception as e:
                    print('Load ttf failed ({}) : {}'.format(fontFileName, str(e)))
                    continue
            
            for fontIdx, font in enumerate(insList):
                if 'name' in font.keys():
                    #nameID:4-比较完整的给人看到名字，包括名称和字体类型，Times New Roman Bold
                    #platformID=1: mac平台， 3-windows平台
                    #platEncID:1-Unicode BMP
                    nameTable = font.get('name', '')
                    if not nameTable:
                        continue

                    name = nameTable.getName(nameID=4, platformID=3, platEncID=1, langID=0x804)
                    if name:
                        try:
                            name = name.toUnicode()
                        except UnicodeDecodeError:
                            name = ""
                            pass

                    if not name:
                        name = nameTable.getName(nameID=4, platformID=3, platEncID=1)
                        if name:
                            try:
                                name = name.toUnicode()
                            except UnicodeDecodeError:
                                name = ""
                                pass

                    if not name:
                        name = nameTable.getBestFullName() or nameTable.getBestSubFamilyName() or nameTable.getBestFamilyName()

                    if name:
                        fontNameMap[name] = (fontFileName, fontIdx)
        if fontQueue:
            fontQueue.put(fontNameMap)
        return fontNameMap

    #将封装文件转换为Sprint-Layout格式
    #返回：("错误信息"，生成的文本)
    def generateFootprint(self, fileName: str):
        importText = self.chkImportFootprintText.value()

        msg = ''
        textIo = None
        fileName = fileName.lower()
        if (fileName.endswith('.kicad_mod')):  #Kicad封装文件
            from kicad_to_sprint import kicadModToTextIo
            textIo = kicadModToTextIo(fileName, importText)
        elif (fileName.endswith('.json')):  #立创EDA离线封装文件
            ins = LcComponent.fromFile(fileName)
            textIo = ins if not ins or isinstance(ins, str) else ins.createSprintTextIo(importText)
        elif LcComponent.isLcedaComponent(fileName): #在线立创EDA
            easyEdaSite = self.easyEdaSite
            if not easyEdaSite:
                easyEdaSite = 'cn' if self.sysLanguge.startswith('zh') else 'global'
                
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
    #fileName: SVG文件名或二维码文本
    #isQrcode: True则为生成二维码
    #返回：生成的textIo字符串
    def generateFromSvg(self, fileName: str, isQrcode: bool):
        from svg_to_polygon import svgToPolygon

        usePolygon = 1 if isQrcode else self.cmbSvgMode.current()  #0-线条, 1-多边形，二维码固定为多边形
        layerIdx = self.cmbSvgLayer.current() + 1 #Sprint-Layout的板层定义从1开始
        smooth = self.cmbSvgSmooth.current()
        height = str_to_float(self.cmbSvgHeight.text())
        if height < 1.0:
            height = 1.0

        textIo = svgToPolygon(fileName, layerIdx=layerIdx, height=height, smooth=smooth, usePolygon=usePolygon)

        return str(textIo) if (textIo and textIo.isValid()) else ''

    #根据情况确定状态栏的双击响应方式
    def staBar_Double_Button_1(self, event=None):
        import webbrowser
        if self.versionJson:
            from version_check import openNewVersionDialog
            ret = openNewVersionDialog(self.master, __Version__, self.versionJson)
            if (ret == 'skip'):
                self.skipVersion = self.versionJson.get('lastest', '')

            self.saveConfig()
            self.versionJson = {} #只允许点击一次，双击后清空版本字典
            self.currentStatusBarInfoIdx = STABAR_INFO_INPUT_FILE - 1 #恢复正常的显示
            self.displayInputFileOrStandalone()
        elif (self.currentStatusBarInfoIdx == STABAR_INFO_RELEASES):
            webbrowser.open_new_tab(URI_RELEASES)
        elif (self.currentStatusBarInfoIdx == STABAR_INFO_ISSUES):
            webbrowser.open_new_tab(URI_ISSUES)

    #联网检查更新线程
    def versionCheckThread(self, arg=None):
        #print('versionCheckThread')
        from version_check import checkUpdate
        self.versionJson = checkUpdate(__Version__, self.skipVersion)
        #为了简单，直接在子线程里面设置状态栏显示，因为状态栏目前仅在启动时设置一次，所以应该不会有资源冲突
        if self.versionJson:
            try:
                self.staBar.text(_('  New version found, double-click to show details'))
            except:
                pass

    #将自动布线参数更新到界面控件
    def updateRuleView(self):
        treRules = self.treRules
        treRules.delete(*treRules.get_children())
        treRules.heading('Item', text=_("Item"))
        treRules.heading('Value', text=_("Value"))
        #treRules.column('Item', width=150)
        treRules.insert('', 'end', values=[_("Track width"), str(self.pcbRule.trackWidth)])
        treRules.insert('', 'end', values=[_("Via diameter"), str(self.pcbRule.viaDiameter)])
        treRules.insert('', 'end', values=[_("Via drill"), str(self.pcbRule.viaDrill)])
        treRules.insert('', 'end', values=[_("Clearance"), str(self.pcbRule.clearance)])
        treRules.insert('', 'end', values=[_("Smd-Smd Clearance"), str(self.pcbRule.smdSmdClearance)])
        
    #双击自动布线参数，弹出对话框修改
    def treRules_Double_Button_1(self, event):
        sel = self.treRules.selection()
        if not sel:
            return

        item = self.treRules.item(sel[0])
        if (not item) or (not item.get('values')) or (len(item.get('values')) < 2):
            return

        record = item.get('values')
        itemName = record[0]
        msg = _("\nPlease enter a new value for the parameter '{}'\nThe unit is mm\n").format(itemName)

        ret = tkSimpleDialog.askfloat(_("Edit parameter"), msg, initialvalue=str_to_float(record[1]))
        if ret and ret > 0.1:
            if (itemName == _("Track width")):
                self.pcbRule.trackWidth = ret
            elif (itemName == _("Via diameter")):
                self.pcbRule.viaDiameter = ret
            elif (itemName == _("Via drill")):
                self.pcbRule.viaDrill = ret
            elif (itemName == _("Clearance")):
                self.pcbRule.clearance = ret
            elif (itemName == _("Smd-Smd Clearance")):
                self.pcbRule.smdSmdClearance = ret

        self.updateRuleView()
        self.saveConfig()
        
    #输出自动布线的DSN文件
    def cmdExportDsn_Cmd(self, event=None):
        dsnFile = self.txtDsnFile.text().strip()
        if not dsnFile:
            showwarning(_('info'), _('DSN file is empty'))
            self.txtDsnFile.focus_set()
        else:            
            self.exportDsn(dsnFile)

    #导出布线到DSN文件，成功返回True
    def exportDsn(self, dsnFile: str):
        from sprint_struct.sprint_textio_parser import SprintTextIoParser
        
        self.saveConfig()
        
        if not dsnFile.lower().endswith('.dsn'):
            showwarning(_("info"), _('The file format is not supported'))
            return False

        dsnPickleFile = os.path.splitext(dsnFile)[0] + '.pickle'

        textIo = self.createTextIoFromInFile()
        if not textIo:
            return False

        exporter = SprintExportDsn(textIo, self.pcbRule, dsnFile)
        ret = exporter.export()
        if isinstance(ret, str): #错误信息
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

    #导入自动布线的SES文件
    def cmdImportSes_Cmd(self, event=None):
        self.cmdmnuImportSes(trimRatsnestMode='trimRouted', trackOnly=False)

    #按住Shift点击导入按钮
    def cmdImportSes_Shift_Button_1(self, event=None):
        try:         
            x = self.master.winfo_pointerx() # - self.master.winfo_vrootx()
            y = self.master.winfo_pointery() # - self.master.winfo_vrooty()
            self.mnuImportSes.tk_popup(x, y + 10, 0)
        finally:
            self.mnuImportSes.grab_release()

    #菜单项“导入...”的点击响应函数
    def cmdmnuImportSes(self, trimRatsnestMode: str='trimRouted', trackOnly: bool=False):
        if (self.importSes(trimRatsnestMode, trackOnly)):
            self.destroy()
            sys.exit(RETURN_CODE_INSERT_STICKY if trackOnly else RETURN_CODE_REPLACE_ALL)

    #导入自动布线的SES到输出文件
    #trimRatsnestMode: 'keepAll'-包含所有鼠线（网络连线），'trimAll'-删除所有鼠线，'trimRouted'-仅删除有铜箔布线连通的焊盘间鼠线
    #trackOnly: 是否仅导入布线
    #成功返回True
    def importSes(self, trimRatsnestMode: str, trackOnly: bool):
        self.saveConfig()
        sesFile = self.txtSesFile.text().strip()
        dsnPickleFile = os.path.splitext(sesFile)[0] + '.pickle'
        
        if ((not self.verifyFileName(sesFile)) or (not self.verifyFileName(dsnPickleFile))):
            return False
        
        if not sesFile.lower().endswith('.ses'):
            showwarning(_("info"), _("The file format is not supported"))
            return False

        if not trackOnly:
            inFileSize = 1
            try:
                inFileSize = os.path.getsize(inFile)
            except Exception as e:
                pass

            if (inFileSize > 0):
                ret = askyesno(_("info"), _("This operation will completely replace the existing components and wiring on the board.\nDo you want to continue?"))
                if not ret:
                    return False

        ret = self.generateTextIoFromSes(sesFile, dsnPickleFile, trimRatsnestMode=trimRatsnestMode, trackOnly=trackOnly)
        if not ret:
            return False
        elif isinstance(ret, str):
            showwarning(_("info"), ret)
            return False
        else:
            self.saveOutputFile(str(ret))

        return True

    #将自动布线结果另存为
    def lblSaveAsAutoRouter_Button_1(self, event=None):
        if str(self.lblSaveAsAutoRouter.cget('state')) == 'disabled':
            return
        self.saveConfig()
        sesFile = self.txtSesFile.text().strip()
        dsnPickleFile = os.path.splitext(sesFile)[0] + '.pickle'
        
        if ((not self.verifyFileName(sesFile)) or (not self.verifyFileName(dsnPickleFile))):
            return
        
        if not sesFile.lower().endswith('.ses'):
            showwarning(_("info"), _("The file format is not supported"))
            return

        ret = self.generateTextIoFromSes(sesFile, dsnPickleFile, trimRatsnestMode='trimRouted', trackOnly=False)
        if not ret:
            return
        elif isinstance(ret, str):
            showwarning(_("info"), ret)
            return
        else:
            self.saveTextFile(str(ret))

    #从SES中生成TextIo实例对象
    def generateTextIoFromSes(self, sesFile: str, dsnPickleFile: str, trimRatsnestMode: str, trackOnly: bool):
        from sprint_struct.sprint_import_ses import SprintImportSes
        try:
            with open(dsnPickleFile, 'rb') as f:
                dsn = pickle.load(f)
        except Exception as e:
            return str(e)
            
        ses = SprintImportSes(sesFile, dsn)
        try:
            textIo = ses.importSes(trimRatsnestMode=trimRatsnestMode, trackOnly=trackOnly)
            return textIo
        except Exception as e:
            return str(e)

    #根据当前执行模式，显示输入文件或独立执行模式字符串
    def displayInputFileOrStandalone(self):
        if self.inFileName:
            selMsg = _("whole board") if self.pcbAll else _("partial")
            msg = _("  In [{}] : {}").format(selMsg, self.inFileName)
        else:
            msg = _("  Standalone mode")
        self.staBar.text(msg)

    #每10s更新一次下部状态栏的显示
    def updateStatusBar(self):
        if self.versionJson:
            self.master.after(10000, self.updateStatusBar)
            return

        self.currentStatusBarInfoIdx += 1
        if (self.currentStatusBarInfoIdx > STABAR_MAX_INFO_IDX):
            self.currentStatusBarInfoIdx = STABAR_INFO_INPUT_FILE
        if (self.currentStatusBarInfoIdx == STABAR_INFO_INPUT_FILE):
            self.displayInputFileOrStandalone()
        elif (self.currentStatusBarInfoIdx == STABAR_INFO_RELEASES):
            self.staBar.text(_("  Releases: ") + "https://github.com/cdhigh/sprintFontRelease/releases")
        else:
            self.staBar.text(_("  Report bugs: ") + "https://github.com/cdhigh/sprintFontRelease/issues")

        self.master.after(10000, self.updateStatusBar)

    #添加泪滴焊盘按钮事件
    def cmdAddTeardrops_Cmd(self, event=None):
        from sprint_struct.teardrop import createTeardrops
        
        self.saveConfig()

        textIo = self.createTextIoFromInFile()
        if not textIo:
            return False

        hPercent = str_to_int(self.cmbhPercent.text())
        vPercent = str_to_int(self.cmbvPercent.text())
        segs = str_to_int(self.cmbTeardropSegs.text())
        padType = self.cmbTeardropPadType.current()
        if ((hPercent <= 0) or (vPercent <= 0) or (segs <= 0)):
            showwarning(_("info"), _("Wrong parameter value"))
            return

        usePth = True if padType in (0, 2) else False
        useSmd = True if padType in (1, 2) else False
        polys = createTeardrops(textIo, hPercent=hPercent, vPercent=vPercent, segs=segs, 
            usePth=usePth, useSmd=useSmd)
        if polys:
            newTextIo = sprint_textio.SprintTextIO()
            newTextIo.addAll(polys)
            showinfo(_("info"), _("Successfully added [{}] teardrop pads").format(len(polys)))

            #写输出文件
            self.saveOutputFile(str(newTextIo))
        else:
            showinfo(_("info"), _("No teardrop pads are generated"))
            return
            
        self.destroy()
        sys.exit(RETURN_CODE_INSERT_ALL)

    #删除泪滴焊盘按钮事件
    def cmdRemoveTeardrops_Cmd(self, event=None):
        from sprint_struct.teardrop import getTeardrops
        self.saveConfig()

        ret = askyesno(_("info"), _("Dangerous operation:\nThis operation may delete some small polygons by mistake or not delete the desired polygons\nDo you want to continue?"))
        if not ret:
            return

        textIo = self.createTextIoFromInFile()
        if not textIo:
            return False

        teardrops = []
        #搜集焊盘
        padType = self.cmbTeardropPadType.current()
        pads = textIo.getPads('PAD') if padType in (0, 2) else []
        if padType in (1, 2):
            pads.extend(textIo.getPads('SMDPAD'))
        
        #搜集走线
        tracks = textIo.getTracks()

        #搜集已有的泪滴焊盘，每个泪滴焊盘就是一个多边形
        oldTeardrops = getTeardrops(textIo, pads, tracks) if pads and tracks else None
        if oldTeardrops:
            for t in oldTeardrops:
                textIo.remove(t)

            showinfo(_("info"), _("Successfully removed [{}] teardrop pads").format(len(oldTeardrops)))

            #写输出文件
            self.saveOutputFile(str(textIo))
            
            self.destroy()
            sys.exit(RETURN_CODE_REPLACE_ALL)
        else:
            showinfo(_("info"), _("No teardrop pads found"))

    #从输入文件创建一个TextIo
    def createTextIoFromInFile(self):
        from sprint_struct.sprint_textio_parser import SprintTextIoParser

        #TODO
        if DEBUG_IN_FILE and not self.inFileName:
            inFile = DEBUG_IN_FILE
        else:
            inFile = self.inFileName
        
        inFileSize = 0
        try:
            inFileSize = os.path.getsize(inFile)
        except Exception as e:
            showwarning(_("info"), str(e))
            return None

        if (inFileSize <= 0):
            showwarning(_("info"), _("No components on the board"))
            return None

        parser = SprintTextIoParser()
        try:
            textIo = parser.parse(inFile)
        except Exception as e:
            showwarning(_("info"), _("Error parsing input file:\n{}").format(str(e)))
            return None

        if not textIo:
            showwarning(_("info"), _("Failed to parse input file"))
        
        return textIo

    #获取当前生成弧形走线方法的函数
    def roundedTrackType(self):
        return {0: 'tangent', 1: '3Points', 2: 'bezier'}.get(self.cmbRoundedTrackType.current(), 'tangent')

    #转换走线为弧形走线
    def cmdRoundedTrackConvert_Cmd(self, event=None):
        textIo = self.convertRounedTrack()
        if textIo:
            self.saveOutputFile(str(textIo))
            self.destroy()
            sys.exit(RETURN_CODE_REPLACE_ALL)

    #将弧形走线的转换结果保存为文本文件
    def lblSaveAsRoundedTrack_Button_1(self, event=None):
        if str(self.lblSaveAsRoundedTrack.cget('state')) == 'disabled':
            return
        textIo = self.convertRounedTrack()
        if textIo:
            self.saveTextFile(str(textIo))

    #转换弧形走线，返回textIo对象
    def convertRounedTrack(self):
        from sprint_struct.rounded_track import createArcTracksInTextIo
        self.saveConfig()
        textIo = self.createTextIoFromInFile()
        if not textIo:
            return None

        bigDistance = str_to_float(self.cmbRoundedTrackBigDistance.text())
        smallDistance = str_to_float(self.cmbRoundedTrackSmallDistance.text())
        segs = str_to_int(self.cmbRoundedTrackSegs.text())
        ret = createArcTracksInTextIo(textIo, self.roundedTrackType(), bigDistance, smallDistance, segs)
        if not ret:
            showinfo(_("info"), _("No suitable track found"))
            return None
        else:
            return textIo

    #初始化导线对调整器
    def initWirePair(self):
        if not self.singleWirePairImage or not self.doubleWirePairImage:
            from ui.wire_pair_image import singleWirePairImageData, doubleWirePairImageData
            self.singleWirePairImage = PhotoImage(data=singleWirePairImageData)
            self.doubleWirePairImage = PhotoImage(data=doubleWirePairImageData)
        image = self.singleWirePairImage if self.cmbWirePairType.current() == 0 else self.doubleWirePairImage
        self.picWirePair.delete('all')
        self.picWirePair.create_image(0, 0, image=image, anchor=NW)

    #给导线对调整器使用的回调函数，用于获取界面上的配置数据，返回字典
    def getWirePairParams(self):
        return {
            'type': self.cmbWirePairType.current(),
            'aMin': str_to_float(self.txtWirePairAmin.text()) or 0.1,
            'aMax': str_to_float(self.txtWirePairAmax.text()) or 1,
            'spacing': str_to_float(self.txtWirePairSpacing.text()) or 0.6,
            'skew': str_to_float(self.txtWirePairSkew.text()),
        }

    #导线对调整长度，确认
    def cmdOkWirePair_Cmd(self, event=None):
        if self.wirePairTextIo:
            self.saveConfig()
            self.saveOutputFile(str(self.wirePairTextIo))
            self.destroy()
            sys.exit(RETURN_CODE_REPLACE_ALL)
        else:
            showinfo(_("info"), _("Please click the Adjust button first to match the trace length"))

    #导线对调整长度，取消
    def cmdCancelWirePair_Cmd(self, event=None):
        self.destroy()
        sys.exit(RETURN_CODE_NONE)

    #导线对调整长度，另存为
    def lblSaveAsWirePair_Button_1(self, event):
        if str(self.lblSaveAsWirePair.cget('state')) == 'disabled':
            return
        if self.wirePairTextIo:
            self.saveConfig()
            self.saveTextFile(str(self.wirePairTextIo))
        else:
            showinfo(_("info"), _("Please click the Adjust button first to match the trace length"))
            
    #在一个新窗口打开导线对长度调整器
    def cmdOpenWirePairTuner_Cmd(self, event=None):
        from sprint_struct.wire_pair_tuner import WirePairTuner
        self.saveConfig()
        self.wirePairTextIo = self.createTextIoFromInFile()
        if not self.wirePairTextIo:
            return

        tracks = self.wirePairTextIo.getTracks()
        if len(tracks) > 1:
            self.wirePairTuner = WirePairTuner(self, self.wirePairTextIo, self.getWirePairParams())
        else:
            self.wirePairTextIo = None

    #切换导线对调整的类型
    def cmbWirePairType_ComboboxSelected(self, event):
        self.initWirePair()

if __name__ == "__main__":
    top = Tk()
    Application(top).mainloop()

