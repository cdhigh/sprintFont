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
from utils.comm_utils import *
from utils.widget_right_click import rightClicker
import sprint_struct.sprint_textio as sprint_textio
from conversion.lceda_to_sprint import LcComponent
from sprint_struct.sprint_export_dsn import PcbRule, SprintExportDsn
from app.config_manager import ConfigManager
from app.font_operations import FontOperations
from app.footprint_svg_handler import FootprintSvgHandler
from app.autorouter_handler import AutorouterHandler
from app.pcb_enhancements import PcbEnhancements

__Version__ = "1.8.1"
__DATE__ = "20251225"
__AUTHOR__ = "cdhigh"

DEBUG_IN_FILE = r'G:/Downloads/Example1.txt'

#在Windows10及以上系统，用户字体目录为：C:\Users\%USERNAME%\AppData\Local\Microsoft\Windows\Fonts
WIN_DIR = os.getenv('WINDIR')
FONT_DIR = os.path.join(WIN_DIR if WIN_DIR else "c:/windows", "fonts")

if getattr(sys, 'frozen', False): #在cxFreeze打包后
    MODULE_PATH = os.path.dirname(sys.executable)
    #basePath = sys._MEIPASS #for pyinstaller
    #os.environ['TCL_LIBRARY'] = os.path.join(basePath, 'tcl', 'tcl8.6')
    #os.environ['TK_LIBRARY'] = os.path.join(basePath, 'tk', 'tk8.6')
else:
    MODULE_PATH = os.path.dirname(os.path.abspath(__file__))

CFG_FILENAME = "config.json"
I18N_PATH = os.path.join(MODULE_PATH, 'i18n')

#目前支持的语种，语种代码全部为小写
SUPPORTED_LANGUAGES = ('en', 'zh_cn', 'de', 'es', 'pt', 'fr', 'ru', 'tr')

STABAR_INFO_INPUT_FILE = 0
STABAR_INFO_RELEASES = 1
STABAR_INFO_ISSUES = 2
STABAR_INFO_NUM = 3

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
    def __init__(self, master=None):
        Application_ui.__init__(self, master)
        
        # 初始化配置管理器
        self.configManager = ConfigManager(self, MODULE_PATH, CFG_FILENAME, I18N_PATH, SUPPORTED_LANGUAGES)
        self.configManager.loadConfig()
        self.configManager.initI18n()
        self.cfg = self.configManager.cfg
        self.language = self.configManager.language
        self.sysLanguge = self.configManager.sysLanguge
        
        self.retranslateUi()
        self.master.title('sprintFont v{}'.format(__Version__))

        #width = str_to_int(self.master.geometry().split('x')[0])
        #if (width > 16): #状态栏仅使用一个分栏，占满全部空间
        self.staBar.panelwidth(0, 100) #Label的width的单位为字符个数
        self.txtFontSize = 14
        self.fontTryTime = 0

        #当前版本信息
        self.versionJson = None
        self.lastCheckUpdate = 0 #最后一次检查更新的时间戳
        self.checkUpdateFrequency = 30
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

        #分析Sprint-Layout传入的参数
        self.getSprintApiData()

        self.populateWidgets()
        self.configManager.restoreConfig()
        
        #TODO
        if globals().get('DEBUG_IN_FILE') and not self.inFileName:
            self.inFileName = DEBUG_IN_FILE
        
        self.setWidgetsState()
            
        #显示输入文件名或显示单独执行模式字符串
        self.statusBarInfoIdx = 0
        self.updateStatusBar()

        #版本更新检查，启动5s后检查一次更新
        self.master.after(5000, self.periodicCheckUpdate)
        #self.txtMain.focus_set()

    #安全退出程序，确保焦点正确返回给Sprint-Layout
    def safeExit(self, returnCode=RETURN_CODE_NONE):
        self.master.update()
        self.master.quit()
        self.destroy()
        sys.exit(returnCode)
    
    #分析Sprint-Layout传入的参数
    def getSprintApiData(self):
        realArgs = sys.argv[1:]
        self.inFileName = realArgs[0] if realArgs else '' #第二个参数为临时文件名
        self.outFileName = ''
        if self.inFileName and not os.path.isfile(self.inFileName):
            self.inFileName = ''

        w = next((a[3:] for a in realArgs if a.startswith('/W:')), '0')
        h = next((a[3:] for a in realArgs if a.startswith('/H:')), '0')
        self.pcbWidth = str_to_int(w) / 10000
        self.pcbHeight = str_to_int(h) / 10000
        self.pcbAll = ('/A' in realArgs) #如果是整板导出，则有此参数

    #初始化时设置各控件使能状态
    def setWidgetsState(self):
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
        else: #单独执行, 禁止一些功能
            self.cmdOk.configure(state='disabled')
            self.cmdOkFootprint.configure(state='disabled')
            self.cmdExport.configure(state='disabled')
            self.cmdOkSvg.configure(state='disabled')
            self.cmdImportSes.configure(state='disabled')
            self.cmdExportDsn.configure(state='disabled')
            self.lblSaveAsAutoRouter.configure(state='disabled')
            self.cmdAddTeardrops.configure(state='disabled')
            self.cmdRemoveTeardrops.configure(state='disabled')
            self.cmdRoundedTrackConvert.configure(state='disabled')
            self.lblSaveAsRoundedTrack.configure(state='disabled')
            self.cmdOpenWirePairTuner.configure(state='disabled')
            self.cmdOkWirePair.configure(state='disabled')
            self.lblSaveAsWirePair.configure(state='disabled')
        
    #多页控件的当前页面发生改变，初始化对应页面的控件
    def tabStrip_NotebookTabChanged(self, event):
        TAB_FONT = 0
        TAB_FOOTPRINT = 1
        TAB_EXPORT = 2
        TAB_SVG = 3
        TAB_AUTOROUTER = 4
        TAB_TEARDROP = 5
        TAB_ROUNDEDTRACK = 6
        TAB_WIREPAIR = 7
        try:
            tabNo = self.getCurrentTabStripTab()
            if tabNo == TAB_FONT:
                self.txtMain.focus_set()
            elif tabNo == TAB_FOOTPRINT:
                self.txtFootprintFile.focus_set()
            elif tabNo == TAB_EXPORT:
                self.txtExportFile.focus_set()
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
        self.fontOps = FontOperations(self, MODULE_PATH, FONT_DIR)
        self.footprintSvgHandler = FootprintSvgHandler()
        self.autorouterHandler = AutorouterHandler()
        self.pcbEnhancements = PcbEnhancements(self.pcbWidth, self.pcbHeight)
        
        #获取系统已安装的字体列表
        #启动一个新的线程在后台更新字体列表，避免启动过慢
        self.fontNameMap = {}
        try:
            self.fontNameQueue = queue.Queue(5)
            #daemon=True 可以让子线程在主线程退出后自动销毁
            self.fontThread = threading.Thread(target=self.fontOps.generateFontFileNameMap, args=(self.fontNameQueue,), daemon=True)
            self.fontThread.start()
            #启动after方法，每隔500ms确认一次是否已经获取到字体列表
            self.master.after(500, self.populateFontCombox)
        except Exception as e: #如果启动线程失败，就直接在这里更新
            print('create thread failed: {}'.format(str(e)))
            self.populateFontCombox(self.fontOps.generateFontFileNameMap())
            
        #字体板层
        self.cmbLayerList = [_("C1 (Front copper)"), _("S1 (Front silkscreen)"), _("C2 (Back copper)"), 
            _("S2 (Back silkscreen)"), _("I1 (Inner copper1)"), _("I2 (Inner copper2)"), _("U (Edge.cuts)"), ]
        self.cmbLayer.configure(values=self.cmbLayerList)
        self.cmbLayer.current(1) #默认为顶层丝印层

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

        #导出板层设置
        self.cmbExportLayerList = [_("All layers"), _("C1 (Front copper)"), _("S1 (Front silkscreen)"), _("C2 (Back copper)"), 
            _("S2 (Back silkscreen)"), _("I1 (Inner copper1)"), _("I2 (Inner copper2)"), _("U (Edge.cuts)"), ]
        self.cmbExportLayer.configure(values=self.cmbExportLayerList)
        self.cmbExportLayer.current(0)

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

        #SVG板层
        self.cmbSvgLayerList = self.cmbLayerList[:]
        self.cmbSvgLayer.configure(values=self.cmbSvgLayerList)
        self.cmbSvgLayer.current(1)

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
        
    #更新字体列表组合框 - 委托给FontOperations
    def populateFontCombox(self, fontMap=None):
        completed = self.fontOps.populateFontCombox(fontMap, self.fontNameQueue)
        if not completed and self.fontTryTime < 10:  # 字体还没准备好
            self.fontTryTime += 1
            self.master.after(500, self.populateFontCombox)  # 延时500ms再试, 最多5s
    
    #保存当前配置数据 - 委托给ConfigManager
    def saveConfig(self):
        # 如果检查到版本更新，则第二天再检查一次
        if self.versionJson:
            self.lastCheckUpdate = datetime.datetime.now() - datetime.timedelta(days=29)
        self.configManager.saveConfig(self.lastCheckUpdate)

    def cmbFont_ComboboxSelected(self, event=None):
        self.txtMain.configure(font=Font(family=self.cmbFont.text(), size=self.txtFontSize))
        
    #选择一个封装文件
    def cmdFootprintFile_Cmd(self, event=None):
        ret = filedialog.askopenfilename(filetypes=[(_("Kicad footprint"), "*.kicad_mod"), 
            (_("easyEDA footprint"), "*.json"), (_("All files"), "*.*")])
        if ret:
            self.txtFootprintFile.setText(ret)

    #选择一个导出文件
    def cmdChooseExportFile_Cmd(self, event=None):
        selectedFilter = StringVar()
        FILE_TYPES_MAP = {
            _("KiCad PCB files"): ".kicad_pcb",
            _("OpenSCAD files"): ".scad",
            _("SVG files"): ".svg",
        }
        ret = filedialog.asksaveasfilename(filetypes=[
            (_("All supported files"), "*.kicad_pcb;*.scad;*.svg"),
            (_("KiCad PCB files"), "*.kicad_pcb"),
            (_("OpenSCAD files"), "*.scad"),
            (_("SVG files"), "*.svg"),
            (_("All files"), "*.*")
        ], typevariable=selectedFilter)
        if ret:
            rootName, ext = os.path.splitext(ret)
            if not ext:
                choiceName = selectedFilter.get()
                targetExt = FILE_TYPES_MAP.get(choiceName)
                if targetExt:
                    ret = rootName + targetExt
            self.txtExportFile.setText(ret)

    #选择一个SVG文件
    def cmdSvgFile_Cmd(self, event=None):
        ret = filedialog.askopenfilename(filetypes=[(_("SVG files"),"*.svg"), (_("All files"), "*.*")])
        if ret:
            self.txtSvgFile.setText(ret)

    #选择一个DSN文件
    def cmdDsnFile_Cmd(self, event=None):
        retFile = filedialog.asksaveasfilename(filetypes=[(_("Specctra DSN files"), '*.dsn'), (_("All files"), '*.*')])
        if retFile:
            if not retFile.lower().endswith('.dsn'):
                retFile = retFile + '.dsn'
            self.txtDsnFile.setText(retFile)
            self.txtSesFile.setText(os.path.splitext(retFile)[0] + '.ses')

    #选择一个SES文件
    def cmdSesFile_Cmd(self, event=None):
        retFile = filedialog.askopenfilename(filetypes=[(_("Specctra session files"),"*.ses"), (_("All files"), "*.*")])
        if retFile:
            self.txtSesFile.setText(retFile)
    
    #取消退出
    def cmdCancel_Cmd(self, event=None):
        self.safeExit(RETURN_CODE_NONE)

    def cmdCancelFootprint_Cmd(self, event=None):
        self.cmdCancel_Cmd(event)

    def cmdCancelExport_Cmd(self, event=None):
        self.cmdCancel_Cmd(event)

    def cmdCancelSvg_Cmd(self, event=None):
        self.cmdCancel_Cmd(event)

    def cmdCancelAutoRouter_Cmd(self, event=None):
        self.cmdCancel_Cmd(event)

    def cmdCancelTeardrops_Cmd(self, event=None):
        self.cmdCancel_Cmd(event)

    def cmdRoundedTrackCancel_Cmd(self, event=None):
        self.cmdCancel_Cmd(event)

    def cmdCancelWirePair_Cmd(self, event=None):
        self.cmdCancel_Cmd(event)

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
        
        textIo = self.fontOps.generatePolygons(txt, self.fontNameMap, fontName, layerIdx, fontHeight,
            wordSpacing, lineSpacing, smooth, invert, padding, capLeft, capRight,
            self.pcbWidth, self.pcbHeight)

        if not textIo:
            showwarning(_('info'), _('Failed to generate text'))
        elif isinstance(textIo, str): #出错，返回的是错误提示文本
            showwarning(_('info'), textIo)
        elif saveas:
            self.saveTextFile(str(textIo))
        else: #写输出文件
            self.saveOutputFile(str(textIo))
            self.safeExit(RETURN_CODE_INSERT_STICKY)

    #在封装文件文本框中回车，根据情况自动执行响应的命令
    #因为可以在文本框中输入easyEDA的元件编码然后回车, 所以需要一个快捷方式比较好
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
        #fileName = self.footprintSvgHandler.autoAddKicadPath(fileName)

        if (not self.verifyFileName(fileName, LcComponent.isLcedaComponent)):
            return
        
        importText = self.chkImportFootprintText.value()
        errStr, retStr = self.footprintSvgHandler.generateFootprint(fileName, 
            importText, self.easyEdaSite, self.sysLanguge)
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
            self.safeExit(RETURN_CODE_INSERT_STICKY)

    #点击了导出按钮
    def cmdExport_Cmd(self, event=None):
        from conversion.sprint_to_kicad import KicadGenerator
        from conversion.sprint_to_openscad import OpenSCADGenerator
        from conversion.sprint_to_svg import SVGGenerator

        self.saveConfig()
        outFileName = self.txtExportFile.text().strip()
        if not outFileName:
            showwarning(_('info'), _('Input is empty'))
            return
        elif not outFileName.lower().endswith(('.kicad_pcb', '.scad', '.svg')):
            showwarning(_('info'), _('Cannot detect export type. Please add a file extension'))
            return

        textIo = self.createTextIoFromInFile()
        if not textIo:
            return False

        if outFileName.lower().endswith('.kicad_pcb'):
            generator = KicadGenerator(textIo)
        elif outFileName.lower().endswith('.svg'):
            layer = self.cmbExportLayer.current()
            generator = SVGGenerator(textIo, layers=layer)
        else:
            layer = self.cmbExportLayer.current()
            layered = self.chkLayeredScad.value()
            generator = OpenSCADGenerator(textIo, layers=layer, layered=layered)
        errStr = generator.generate(outFileName)
        if errStr:
            showwarning(_('info'), errStr)
        else:
            showinfo(_("info"), _("Export file successfully"))
    
    #转换SVG结果保存为单独一个文本文件
    def lblSaveAsSvg_Button_1(self, event):
        self.cmdOkSvg_Cmd(saveas=True)
        
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
            fileName = self.footprintSvgHandler.textToQrcodeStr(fileName)
        elif not self.verifyFileName(fileName):
            return
        elif not fileName.lower().endswith('.svg'):
            showwarning(_('info'), _('The file format is not supported'))
            return
        
        #生成二维码
        layerIdx = self.cmbSvgLayer.current() + 1
        svgHeight = str_to_float(self.cmbSvgHeight.text(), 1.0)
        svgSmooth = self.cmbSvgSmooth.current()
        svgMode = self.cmbSvgMode.current()

        try:
            retStr = self.footprintSvgHandler.generateFromSvg(fileName, layerIdx, svgHeight, 
                svgSmooth, svgMode, isQrcode)
        except Exception as e:
            showwarning(_('info'), str(e))
            return
        
        if not retStr:
            showwarning(_('info'), _('Convert svg image failed'))
        elif saveas:
            self.saveTextFile(retStr)
        else:
            self.saveOutputFile(retStr)
            self.safeExit(RETURN_CODE_INSERT_STICKY)
        
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

        retFile = filedialog.asksaveasfilename(title=_("Save to a text file"), filetypes=[(_('Text files'), '*.txt'), (_("All files"), '*.*')])
        if retFile:
            if ('.' not in retFile): #自动添加后缀
                retFile += '.txt'
            try:
                with open(retFile, 'w', encoding='utf-8') as f:
                    f.write(txt)
            except Exception as e:
                showwarning(_('info'), _('Failed to save file.\n{}').format(str(e)))
    
    #根据情况确定状态栏的双击响应方式
    def staBar_Double_Button_1(self, event=None):
        import webbrowser
        if self.versionJson:
            from utils.version_check import openNewVersionDialog
            ret = openNewVersionDialog(self.master, __Version__, self.versionJson)
            if (ret == 'skip'):
                self.skipVersion = self.versionJson.get('lastest', '')

            self.saveConfig()
            self.versionJson = {} #只允许点击一次，双击后清空版本字典
            self.statusBarInfoIdx = 0 #恢复正常的显示
            self.displayInputFileOrStandalone()
        elif (self.statusBarInfoIdx == STABAR_INFO_RELEASES):
            webbrowser.open_new_tab(URI_RELEASES)
        elif (self.statusBarInfoIdx == STABAR_INFO_ISSUES):
            webbrowser.open_new_tab(URI_ISSUES)

    #联网检查更新线程
    def versionCheckThread(self, arg=None):
        #print('versionCheckThread')
        from utils.version_check import checkUpdate
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

        ret = simpledialog.askfloat(_("Edit parameter"), msg, initialvalue=str_to_float(record[1]))
        if ret and ret >= 0.01:
            if itemName == _("Track width"):
                self.pcbRule.trackWidth = ret
            elif itemName == _("Via diameter"):
                self.pcbRule.viaDiameter = ret
            elif itemName == _("Via drill"):
                self.pcbRule.viaDrill = ret
            elif itemName == _("Clearance"):
                self.pcbRule.clearance = ret
            elif itemName == _("Smd-Smd Clearance"):
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

    #导出布线到DSN文件 - 委托给AutorouterHandler
    def exportDsn(self, dsnFile):
        self.saveConfig()
        textIo = self.createTextIoFromInFile()
        return self.autorouterHandler.exportDsn(dsnFile, textIo, self.pcbRule)

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

    #菜单项“导入SES”的点击响应函数
    def cmdmnuImportSes(self, trimRatsnestMode: str='trimRouted', trackOnly: bool=False):
        self.saveConfig()
        sesFile = self.txtSesFile.text().strip()
        dsnPickleFile = os.path.splitext(sesFile)[0] + '.pickle'
        
        if ((not self.verifyFileName(sesFile)) or (not self.verifyFileName(dsnPickleFile))):
            return
        
        ret = self.autorouterHandler.importSes(sesFile, dsnPickleFile, trimRatsnestMode, trackOnly)
        if ret:
            self.saveOutputFile(ret)
            self.safeExit(RETURN_CODE_INSERT_STICKY if trackOnly else RETURN_CODE_REPLACE_ALL)

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

        ret = self.autorouterHandler.generateTextIoFromSes(sesFile, dsnPickleFile, 
            trimRatsnestMode='trimRouted', trackOnly=False)
        if not ret:
            return
        elif isinstance(ret, str):
            showwarning(_("info"), ret)
            return
        else:
            self.saveTextFile(str(ret))

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
        if self.versionJson: #检测到新版本后,外部代码设置状态栏显示,这里不再更新
            self.master.after(10000, self.updateStatusBar)
            return

        if (self.statusBarInfoIdx == STABAR_INFO_INPUT_FILE):
            self.displayInputFileOrStandalone()
        elif (self.statusBarInfoIdx == STABAR_INFO_RELEASES):
            self.staBar.text(_("  Releases: ") + "https://github.com/cdhigh/sprintFontRelease/releases")
        else:
            self.staBar.text(_("  Report bugs: ") + "https://github.com/cdhigh/sprintFontRelease/issues")

        self.statusBarInfoIdx = (self.statusBarInfoIdx + 1) % STABAR_INFO_NUM

        self.master.after(10000, self.updateStatusBar)

    #添加泪滴焦盘按钮事件 - 委托给PcbEnhancements
    def cmdAddTeardrops_Cmd(self, event=None):
        self.saveConfig()
        textIo = self.createTextIoFromInFile()
        hPercent = str_to_int(self.cmbhPercent.text())
        vPercent = str_to_int(self.cmbvPercent.text())
        segs = str_to_int(self.cmbTeardropSegs.text())
        padType = self.cmbTeardropPadType.current()
        
        result = self.pcbEnhancements.addTeardrops(textIo, hPercent, vPercent, segs, padType)
        if result:
            self.saveOutputFile(result)
            self.safeExit(RETURN_CODE_INSERT_ALL)

    #删除泪滴焦盘按钮事件 - 委托给PcbEnhancements
    def cmdRemoveTeardrops_Cmd(self, event=None):
        self.saveConfig()
        textIo = self.createTextIoFromInFile()
        padType = self.cmbTeardropPadType.current()
        
        result = self.pcbEnhancements.removeTeardrops(textIo, padType)
        if result:
            self.saveOutputFile(result)
            self.safeExit(RETURN_CODE_REPLACE_ALL)

    #从输入文件创建一个TextIo
    def createTextIoFromInFile(self):
        from sprint_struct.sprint_textio_parser import SprintTextIoParser

        inFileSize = 0
        try:
            inFileSize = os.path.getsize(self.inFileName)
        except Exception as e:
            showwarning(_("info"), str(e))
            return None

        if (inFileSize <= 0):
            showwarning(_("info"), _("No components on the board"))
            return None

        parser = SprintTextIoParser(self.pcbWidth, self.pcbHeight)
        try:
            textIo = parser.parse(self.inFileName)
        except Exception as e:
            showwarning(_("info"), _("Error parsing input file:\n{}").format(str(e)))
            return None

        if not textIo:
            showwarning(_("info"), _("Failed to parse input file"))
        
        return textIo

    #转换走线为弧形走线
    def cmdRoundedTrackConvert_Cmd(self, event=None):
        textIo = self.convertRounedTrack()
        if textIo:
            self.saveOutputFile(str(textIo))
            self.safeExit(RETURN_CODE_REPLACE_ALL)

    #将弧形走线的转换结果保存为文本文件
    def lblSaveAsRoundedTrack_Button_1(self, event=None):
        if str(self.lblSaveAsRoundedTrack.cget('state')) == 'disabled':
            return

        textIo = self.convertRounedTrack()
        if textIo:
            self.saveTextFile(str(textIo))

    #转换弧形走线 - 委托给PcbEnhancements
    def convertRounedTrack(self):
        self.saveConfig()
        textIo = self.createTextIoFromInFile()
        bigDistance = str_to_float(self.cmbRoundedTrackBigDistance.text())
        smallDistance = str_to_float(self.cmbRoundedTrackSmallDistance.text())
        segs = str_to_int(self.cmbRoundedTrackSegs.text())
        rtType = {0: 'tangent', 1: '3Points', 2: 'bezier'}.get(self.cmbRoundedTrackType.current(), 'tangent')
        if textIo and self.chkMergeConnectedTracks.value():
            textIo.mergeConnectedTracks()
        return self.pcbEnhancements.convertRoundedTrack(textIo, rtType, bigDistance, smallDistance, segs)

    #导线对调整长度，确认
    def cmdOkWirePair_Cmd(self, event=None):
        if self.wirePairTextIo:
            self.saveConfig()
            self.saveOutputFile(str(self.wirePairTextIo))
            self.safeExit(RETURN_CODE_REPLACE_ALL)
        else:
            showinfo(_("info"), _("Please click the Adjust button first to match the trace length"))

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
        params = {
            'type': self.cmbWirePairType.current(),
            'aMin': str_to_float(self.txtWirePairAmin.text()) or 0.1,
            'aMax': str_to_float(self.txtWirePairAmax.text()) or 1,
            'spacing': str_to_float(self.txtWirePairSpacing.text()) or 0.6,
            'skew': str_to_float(self.txtWirePairSkew.text()),
        }
        if len(tracks) > 1:
            self.wirePairTuner = WirePairTuner(self, self.wirePairTextIo, params)
        else:
            self.wirePairTextIo = None
            showinfo(_("info"), _("At least two traces must be selected"))

    #切换导线对调整的类型
    def cmbWirePairType_ComboboxSelected(self, event):
        self.initWirePair()

    #初始化导线对调整器
    def initWirePair(self):
        if not self.singleWirePairImage or not self.doubleWirePairImage:
            from ui.wire_pair_image import singleWirePairImageData, doubleWirePairImageData
            self.singleWirePairImage = PhotoImage(data=singleWirePairImageData)
            self.doubleWirePairImage = PhotoImage(data=doubleWirePairImageData)

        image = self.singleWirePairImage if self.cmbWirePairType.current() == 0 else self.doubleWirePairImage
        self.picWirePair.delete('all')
        self.picWirePair.create_image(0, 0, image=image, anchor=NW)

if __name__ == "__main__":
    top = Tk()
    Application(top).mainloop()
