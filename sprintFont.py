#!/usr/bin/env python
#-*- coding:utf-8 -*-
"""
Sprint-layout v6 2022版的插件，在电路板插入其他字体（包括中文字体）的文字
Author: cdhigh <https://github.com/cdhigh>
==========================
使用cx_freeze打包
cxfreeze --base-name=Win32GUI --icon=app.ico sprintFont.py
==========================
使用pyinstaller打包
-F: 打包单文件
-w: windows执行系统，不弹出cmd命令行
-i: 图标
pyinstaller.exe -F -w -i app.ico sprintFont.py
"""
import os, sys, locale, json
from tkinter import *
from tkinter.font import Font, families
from tkinter.ttk import *
#Usage:showinfo/warning/error,askquestion/okcancel/yesno/retrycancel
from tkinter.messagebox import *
#Usage:f=tkFileDialog.askopenfilename(initialdir='E:/Python')
import tkinter.filedialog as tkFileDialog
#import tkinter.simpledialog as tkSimpleDialog  #askstring()
from fontTools.ttLib.ttFont import TTFont
from i18n import Language
from font_to_polygon import str_to_int, str_to_float, isHexString, singleWordPolygon

__VERSION__ = "v1.0"
__DATE__ = "20220514"
__AUTHOR__ = "cdhigh"

WIN_DIR = os.environ['WINDIR']
FONT_DIR = os.path.join(WIN_DIR if WIN_DIR else "c:/windows", "fonts")

if getattr(sys, 'frozen', False): #在cxFreeze打包后
    MODULE_PATH = os.path.dirname(sys.executable)
else:
    MODULE_PATH = os.path.dirname(__file__)

CFG_FILENAME = os.path.join(MODULE_PATH, "config.json")

class Statusbar(Frame):
    """A Simple Statusbar
    Usage:self.status = Statusbar(self.top, panelwidths=(15,5,))
          self.status.pack(side=BOTTOM, fill=X)
          self.status.set(0,'Demo mode')
          self.status.text('Demo mode')
    """
    def __init__(self, master, **kw):
        """Options:
        panelwidths - a tuple of width of panels, atual number of panels is len(panelwidths)+1.
        """
        Frame.__init__(self, master)
        panelwidths = kw['panelwidths'] if 'panelwidths' in kw else []
        self.lbls = []
        for pnlwidth in panelwidths:
            lbl = Label(self, width=pnlwidth, anchor=W, relief=SUNKEN)
            self.lbls.append(lbl)
            lbl.pack(side=LEFT, fill=Y)
        lbl = Label(self, anchor=W, relief=SUNKEN)
        self.lbls.append(lbl)
        lbl.pack(fill=BOTH, expand=1)

    def set(self, panel, format, *args):
        if panel >= len(self.lbls): raise IndexError
        self.lbls[panel]['text'] = format % args
        self.lbls[panel].update_idletasks()

    text = lambda self,format,*args : self.set(0,format,*args)

    def panelwidth(self, panel, width=None):
        if panel >= len(self.lbls): raise IndexError
        if width is None:
            panelwidth = self.lbls[panel]['width']
        else:
            self.lbls[panel]['width'] = width

    def clear(self):
        for panel in self.lbls:
            panel.config(text='')
            panel.update_idletasks()

#界面使用作者自己的工具 tkinter-designer <https://github.com/cdhigh/tkinter-designer> 自动生成
class Application_ui(Frame):
    #这个类仅实现界面生成功能，具体事件处理代码在子类Application中。
    def __init__(self, master=None):
        Frame.__init__(self, master)
        self.master.title('sprintFont')
        self.master.geometry('570x289')
        self.master.resizable(0,0)
        self.icondata = """
            R0lGODlhMAAwAPcAAD6KKP///z6KJ//8///+//v6+/n4+f77//37/vz6/fv6/Pr5+/v9
            +/3+/fz9/PX29e/27ufx5fP48t/s3Ojx5jmIIz2KKD6KKT+LKkeQM2ShU2ymXG+nYH6x
            cH+ycY27gZO+h5K9hprCj6jLn7bTrr7Yt8bdwMXcv87iyc/iytLkzdjn1Nno1eHt3uDs
            3ez06uvz6fb69Sh9Dyl9ES2AFS+BFzCBGC+BGDGCGTKCGjGCGjKDGzOEHDODHDSEHTWF
            HjeGHzaFHzeGIDiGITmHIjqIIzqHIzuIJDyJJT2KJj6LJzyIJj6JJz2JJz6JKECLKUCL
            KkKNK0GMK0GMLEOOLUKNLUSOLkONLkWOMEePMUiRMkePMkmRNEuSNUuSNkyTN02TOU6U
            OlKXPVGWPVOXPlSXQFWYQViaRViZRVubSFycSV6dS2CfTWGfT2KgUGahVGeiVWmkWGym
            W26nXW+oX3CpYG+nX3KpYnetZnWrZXquanitaXyvbYCycYKzc4Gzc4a3d4O0dYa1eIi3
            eoe2eYy6fou5foy5f4+7gZG7hJS9h5W/iZjBi5fAipS9iJzDkZvCkJ/FlKPHmKfKnarL
            oKvMoazMoq7OpbDPp7HPqLjUsLrVsrzWtL/YuLzUtcLau8HZusPavMrfxMfbwcncw87h
            yM3eyNbm0dDgy9zq2Nvp19/p3Obw4+Xv4uzz6jOEGWWiUWijVXSqYn6wbom4eYu5fJfA
            iZzDj5/Ek7LOqbnTsL7XtsHYucnewtHiy9jn09Lhzeny5ujx5fH37+/17fj79/f69vb5
            9fL18fH08O/y7sTavNPjzeTv4OLt3t7o2uXt4uTs4fP48e3x6/r8+fn7+Pz9+/7+/f//
            /wAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
            AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
            AAAAAAAAAAAAAAAAAAAAACH5BAEAANgALAAAAAAwADAAAAj/ALEJHEiwoMGDCBMqXMiw
            ocOHECF6+ALklZCLGDEGwUGDxg4gGS8GGfmDiBY8DhlB8VEEgAAAMGMCsMDjiBs+e8z4
            ECKzJwAkPqAgWoioxhKfMgX8mIUqAYEBD3S54ZH0JcyXS2wUUljDglekMIU4CnBgwYAB
            Bgggg8UTbEwatxBSOeLVAlgfeQIYGDDN06gFChIo+9LSLYAjUQ4yyjHzq08BREidXdYl
            h4830AoQSETVMIActQyKMdLYrs8KZwwUSCbmB0waggYcAEbE82EuBpE0KY00CAfZplzD
            rCDmQQJoUZB4bgIFUEEhF3j7FKIBQYJVApQD+AGnQIJnSpII/xhv1WVPgwKiG0ZiJVqC
            AYdoBOHxg9fTXFTJly/v0mAS9YbpoEgAAThgSSyylEJgAW605ZkA/gHolg6PEGjhhcwQ
            wZ9bEBb0n2dFhEHMhSRKE0ZhD0boWQ4jXGhNixeGoINL5IHVIUEfuoWEFMFcmIoQolxI
            jBdH2HbjQDmC1YMhJPYxwx4kNsJYih5K2BMSWMBw4S9DHHFFBBeqcsRuhh0pUJI+9cAH
            iSHsAMAOgZBIyA7jxVTjVSoi1cQRKlxIQQZFIvEEKxe28NN+deJZ5V0dkPjBjDDtIAmJ
            cghnY54++aCghcaAgeIRXLhyYQpDbJgUpjIJ0QY1F17SWUw6RP9CYh1BcIgqTEwEYcKF
            EoBRQU9EqNHAhZrg0FONSdwKwBBqkEjCDUhEKy0SOGByYTVrOEjjS8ku2tMOk1xIDR0Y
            bGGuuVlkIQUbxlzIiaXbAtAtjlYSgQarFjrgCgTE9OsvMRC8wMCFxpyI1LxIWokDJSQ2
            7DCJkkDaUxOoHpEFBQ9n3LAEZfzaE8JnSriDCCT20gkoKKesMiglpEDiIsbGCzI2SR6x
            xTAXrrDDDjz07PPPPeggBAsXtlKFcshiysMfJB7iw4MA+ADlhYvkV+fMOSKBgQsXTvCT
            bT9hIMyFzTQh3tXoqbfDIHJOCXYPIJC4h9XyGgREdAIIgcKFEHjLCjZMSFThTJhQaOeE
            mdjott0dJIrg9t84QEJiHk8DwJxBZFQgwBCn8J1FkX/DVMQYMVz4CQ/jHaGFQbbkIAQb
            DlyYSQ+hy7QDLhc2MIdrONByUBQ6bHLhMWcMUXtMxOFL4Ak1JXaQLc1eWEnMRibqkg8l
            EFyGDIwk5AuJcGh7/BBpFHMhJn4wZGEoPzTh/vvwxy+/+zjskrtDBWpgxBRS9O///wAM
            oBSGkIdrECgi2PDABjjAwAY68IEQtIMc4qCHYiDwghjMoAYNEhAAOw="""
        self.iconimg = PhotoImage(data=self.icondata)
        self.master.tk.call('wm', 'iconphoto', self.master._w, self.iconimg)
        self.createWidgets()

    def createWidgets(self):
        self.top = self.winfo_toplevel()

        self.style = Style()

        self.cmbFontList = ['Add items in designer or code!',]
        self.cmbFontVar = StringVar(value='Add items in designer or code!')
        self.cmbFont = Combobox(self.top, state='readonly', text='Add items in designer or code!', textvariable=self.cmbFontVar, values=self.cmbFontList, font=('微软雅黑',10))
        self.cmbFont.setText = lambda x: self.cmbFontVar.set(x)
        self.cmbFont.text = lambda : self.cmbFontVar.get()
        self.cmbFont.place(relx=0.14, rely=0.304, relwidth=0.367)

        self.cmbFontHeightList = ['Add items in designer or code!',]
        self.cmbFontHeightVar = StringVar(value='Add items in designer or code!')
        self.cmbFontHeight = Combobox(self.top, text='Add items in designer or code!', textvariable=self.cmbFontHeightVar, values=self.cmbFontHeightList, font=('微软雅黑',10))
        self.cmbFontHeight.setText = lambda x: self.cmbFontHeightVar.set(x)
        self.cmbFontHeight.text = lambda : self.cmbFontHeightVar.get()
        self.cmbFontHeight.place(relx=0.758, rely=0.304, relwidth=0.212)

        self.cmbLineSpacingList = ['Add items in designer or code!',]
        self.cmbLineSpacingVar = StringVar(value='Add items in designer or code!')
        self.cmbLineSpacing = Combobox(self.top, text='Add items in designer or code!', textvariable=self.cmbLineSpacingVar, values=self.cmbLineSpacingList, font=('微软雅黑',10))
        self.cmbLineSpacing.setText = lambda x: self.cmbLineSpacingVar.set(x)
        self.cmbLineSpacing.text = lambda : self.cmbLineSpacingVar.get()
        self.cmbLineSpacing.place(relx=0.758, rely=0.581, relwidth=0.212)

        self.cmbWordSpacingList = ['Add items in designer or code!',]
        self.cmbWordSpacingVar = StringVar(value='Add items in designer or code!')
        self.cmbWordSpacing = Combobox(self.top, text='Add items in designer or code!', textvariable=self.cmbWordSpacingVar, values=self.cmbWordSpacingList, font=('微软雅黑',10))
        self.cmbWordSpacing.setText = lambda x: self.cmbWordSpacingVar.set(x)
        self.cmbWordSpacing.text = lambda : self.cmbWordSpacingVar.get()
        self.cmbWordSpacing.place(relx=0.758, rely=0.443, relwidth=0.212)

        self.cmdCancelVar = StringVar(value='Cancel')
        self.style.configure('TcmdCancel.TButton', font=('微软雅黑',10))
        self.cmdCancel = Button(self.top, text='Cancel', textvariable=self.cmdCancelVar, command=self.cmdCancel_Cmd, style='TcmdCancel.TButton')
        self.cmdCancel.setText = lambda x: self.cmdCancelVar.set(x)
        self.cmdCancel.text = lambda : self.cmdCancelVar.get()
        self.cmdCancel.place(relx=0.491, rely=0.775, relwidth=0.254, relheight=0.087)

        self.cmdOkVar = StringVar(value='Ok')
        self.style.configure('TcmdOk.TButton', font=('微软雅黑',10))
        self.cmdOk = Button(self.top, text='Ok', textvariable=self.cmdOkVar, command=self.cmdOk_Cmd, style='TcmdOk.TButton')
        self.cmdOk.setText = lambda x: self.cmdOkVar.set(x)
        self.cmdOk.text = lambda : self.cmdOkVar.get()
        self.cmdOk.place(relx=0.112, rely=0.775, relwidth=0.254, relheight=0.087)

        self.cmbSmoothList = ['Add items in designer or code!',]
        self.cmbSmoothVar = StringVar(value='Add items in designer or code!')
        self.cmbSmooth = Combobox(self.top, state='readonly', text='Add items in designer or code!', textvariable=self.cmbSmoothVar, values=self.cmbSmoothList, font=('微软雅黑',10))
        self.cmbSmooth.setText = lambda x: self.cmbSmoothVar.set(x)
        self.cmbSmooth.text = lambda : self.cmbSmoothVar.get()
        self.cmbSmooth.place(relx=0.14, rely=0.581, relwidth=0.367)

        self.VScroll1 = Scrollbar(self.top, orient='vertical')
        self.VScroll1.place(relx=0.926, rely=0.028, relwidth=0.03, relheight=0.197)

        self.cmbLayerList = ['Add items in designer or code!',]
        self.cmbLayerVar = StringVar(value='Add items in designer or code!')
        self.cmbLayer = Combobox(self.top, state='readonly', text='Add items in designer or code!', textvariable=self.cmbLayerVar, values=self.cmbLayerList, font=('微软雅黑',10))
        self.cmbLayer.setText = lambda x: self.cmbLayerVar.set(x)
        self.cmbLayer.text = lambda : self.cmbLayerVar.get()
        self.cmbLayer.place(relx=0.14, rely=0.443, relwidth=0.367)

        self.txtMainFont = Font(font=('微软雅黑',10))
        self.txtMain = Text(self.top, yscrollcommand=self.VScroll1.set, font=self.txtMainFont)
        self.txtMain.place(relx=0.14, rely=0.028, relwidth=0.788, relheight=0.197)
        self.txtMain.insert('1.0','')
        self.VScroll1['command'] = self.txtMain.yview

        self.lblFontHeightVar = StringVar(value='Height (mm)')
        self.style.configure('TlblFontHeight.TLabel', anchor='e', font=('微软雅黑',10))
        self.lblFontHeight = Label(self.top, text='Height (mm)', textvariable=self.lblFontHeightVar, style='TlblFontHeight.TLabel')
        self.lblFontHeight.setText = lambda x: self.lblFontHeightVar.set(x)
        self.lblFontHeight.text = lambda : self.lblFontHeightVar.get()
        self.lblFontHeight.place(relx=0.505, rely=0.304, relwidth=0.24, relheight=0.087)

        self.lblFontVar = StringVar(value='Font')
        self.style.configure('TlblFont.TLabel', anchor='e', font=('微软雅黑',10))
        self.lblFont = Label(self.top, text='Font', textvariable=self.lblFontVar, style='TlblFont.TLabel')
        self.lblFont.setText = lambda x: self.lblFontVar.set(x)
        self.lblFont.text = lambda : self.lblFontVar.get()
        self.lblFont.place(relx=0., rely=0.304, relwidth=0.114, relheight=0.087)

        self.lblSaveAsVar = StringVar(value='Save as')
        self.style.configure('TlblSaveAs.TLabel', anchor='w', foreground='#0000FF', font=('微软雅黑',10,'underline'))
        self.lblSaveAs = Label(self.top, text='Save as', textvariable=self.lblSaveAsVar, style='TlblSaveAs.TLabel')
        self.lblSaveAs.setText = lambda x: self.lblSaveAsVar.set(x)
        self.lblSaveAs.text = lambda : self.lblSaveAsVar.get()
        self.lblSaveAs.place(relx=0.884, rely=0.803, relwidth=0.114, relheight=0.087)
        self.lblSaveAs.bind('<Button-1>', self.lblSaveAs_Button_1)

        self.LblLineSpacingVar = StringVar(value='Line spacing (mm)')
        self.style.configure('TLblLineSpacing.TLabel', anchor='e', font=('微软雅黑',10))
        self.LblLineSpacing = Label(self.top, text='Line spacing (mm)', textvariable=self.LblLineSpacingVar, style='TLblLineSpacing.TLabel')
        self.LblLineSpacing.setText = lambda x: self.LblLineSpacingVar.set(x)
        self.LblLineSpacing.text = lambda : self.LblLineSpacingVar.get()
        self.LblLineSpacing.place(relx=0.505, rely=0.581, relwidth=0.24, relheight=0.087)

        self.lblWordSpacingVar = StringVar(value='Word spacing (mm)')
        self.style.configure('TlblWordSpacing.TLabel', anchor='e', font=('微软雅黑',10))
        self.lblWordSpacing = Label(self.top, text='Word spacing (mm)', textvariable=self.lblWordSpacingVar, style='TlblWordSpacing.TLabel')
        self.lblWordSpacing.setText = lambda x: self.lblWordSpacingVar.set(x)
        self.lblWordSpacing.text = lambda : self.lblWordSpacingVar.get()
        self.lblWordSpacing.place(relx=0.505, rely=0.443, relwidth=0.24, relheight=0.087)

        self.lblSmoothVar = StringVar(value='Smooth')
        self.style.configure('TlblSmooth.TLabel', anchor='e', font=('微软雅黑',10))
        self.lblSmooth = Label(self.top, text='Smooth', textvariable=self.lblSmoothVar, style='TlblSmooth.TLabel')
        self.lblSmooth.setText = lambda x: self.lblSmoothVar.set(x)
        self.lblSmooth.text = lambda : self.lblSmoothVar.get()
        self.lblSmooth.place(relx=0., rely=0.581, relwidth=0.114, relheight=0.087)

        self.lblLayerVar = StringVar(value='Layer')
        self.style.configure('TlblLayer.TLabel', anchor='e', font=('微软雅黑',10))
        self.lblLayer = Label(self.top, text='Layer', textvariable=self.lblLayerVar, style='TlblLayer.TLabel')
        self.lblLayer.setText = lambda x: self.lblLayerVar.set(x)
        self.lblLayer.text = lambda : self.lblLayerVar.get()
        self.lblLayer.place(relx=0., rely=0.443, relwidth=0.114, relheight=0.087)

        self.lblTxtVar = StringVar(value='Text')
        self.style.configure('TlblTxt.TLabel', anchor='e', font=('微软雅黑',10))
        self.lblTxt = Label(self.top, text='Text', textvariable=self.lblTxtVar, style='TlblTxt.TLabel')
        self.lblTxt.setText = lambda x: self.lblTxtVar.set(x)
        self.lblTxt.text = lambda : self.lblTxtVar.get()
        self.lblTxt.place(relx=0., rely=0.028, relwidth=0.114, relheight=0.087)

        self.staBar = Statusbar(self.top, panelwidths=(16,))
        self.staBar.pack(side=BOTTOM, fill=X)

class Application(Application_ui):
    #这个类实现具体的事件处理回调函数。界面生成代码在Application_ui中。
    def __init__(self, master=None):
        Application_ui.__init__(self, master)
        self.master.title('sprintFont {} by cdhigh [github.com/cdhigh]'.format(__VERSION__))
        width = str_to_int(self.master.geometry().split('x')[0])
        if (width > 16):
            self.staBar.panelwidth(0, width)

        Language.init()
        Language.setLang(locale.getdefaultlocale()[0])
        self.language = None #如果手工在配置文件中添加语种选择，则此变量保存对应语种

        #读取配置文件到内存
        self.cfg = None
        if os.path.exists(CFG_FILENAME):
            try:
                with open(CFG_FILENAME, 'r', encoding='utf-8') as f:
                    self.cfg = json.loads(f.read())
            except:
                pass

        #支持手动选择语种
        if isinstance(self.cfg, dict):
            lang = self.cfg.get('language', '')
            if lang and Language.langIsSupported(lang):
                self.language = lang
                Language.setLang(lang)
        
        self.populateWidgets()
        self.restoreConfig()
        self.translateWidgets()

        #分析sprint-layout传入的参数
        self.inFileName = ''
        self.outFileName = ''
        if (len(sys.argv) >= 2): #第二个参数为临时文件名
            self.inFileName = sys.argv[1]
            if not (os.path.exists(self.inFileName)):
                self.inFileName = ''

        #输出文件名为输入文件名加一个 "_out"        
        if self.inFileName:
            inExts = os.path.splitext(self.inFileName)
            self.outFileName = '{}_out{}'.format(inExts[0], inExts[1] if (len(inExts) > 1) else '')
            self.staBar.text(_("  In: {}").format(self.inFileName))
        else: #单独执行
            self.cmdOk.configure(state='disabled')
            self.staBar.text(_("  Standalone mode"))

        self.txtMain.focus_set()

    #翻译界面字符串，为了能方便修改界面，等界面初始化完成后再统一修改
    def translateWidgets(self):
        self.cmdOk.setText(_("Ok"))
        self.cmdCancel.setText(_("Cancel"))
        self.lblSaveAs.setText(_("Save as"))
        self.lblFont.setText(_("Font"))
        self.lblTxt.setText(_("Text"))
        self.lblLayer.setText(_("Layer"))
        self.lblSmooth.setText(_("Smooth"))
        self.lblFontHeight.setText(_("Height (mm)"))
        self.lblWordSpacing.setText(_("Word spacing (mm)"))
        self.LblLineSpacing.setText(_("Line spacing (mm)"))
        
    #填充界面控件
    def populateWidgets(self):
        #获取系统已安装的字体列表
        self.fontNameMap = self.generateFontFileNameMap()
        self.cmbFontList = sorted(self.fontNameMap.keys())
        self.cmbFont.configure(value=self.cmbFontList)
        self.cmbFont.setText(self.cmbFontList[0] if self.cmbFontList else '')

        #填充板层
        self.cmbLayerList = [_("C1 (Front copper)"), _("S1 (Front silkscreen)"), _("C2 (Back copper)"), 
            _("S2 (Back silkscreen)"), _("I1 (Inner copper1)"), _("I2 (Inner copper2)"), _("U (Edge.cuts)"), ]
        self.cmbLayer.configure(values=self.cmbLayerList)
        self.cmbLayer.current(1) #默认为顶层丝印层

        #字高
        self.cmbFontHeightList = [1.0, 2.0, 3.0]
        self.cmbFontHeight.configure(values=self.cmbFontHeightList)
        self.cmbFontHeight.current(1) #字高默认2mm
        
        #字间距
        self.cmbWordSpacingList = [-0.5, -0.2, 0, 0.2, 0.5]
        self.cmbWordSpacing.configure(values=self.cmbWordSpacingList)
        self.cmbWordSpacing.current(1)
        
        #行间距
        self.cmbLineSpacingList = [-0.5, -0.2, 0, 0.2, 0.5]
        self.cmbLineSpacing.configure(values=self.cmbLineSpacingList)
        self.cmbLineSpacing.current(2)
        
        #平滑程度
        self.cmbSmoothList = [_("Super fine (super slow)"), _("Fine (slow)"), _("Normal"), _("Rough"), _("Super Rough"), ]
        self.cmbSmooth.configure(values=self.cmbSmoothList)
        self.cmbSmooth.current(2)
        
    #从配置文件中恢复以前的配置数据
    def restoreConfig(self):
        cfg = self.cfg
        if isinstance(cfg, dict):
            lastFont = cfg.get('font', '')
            if lastFont and (lastFont in self.cmbFontList):
                self.cmbFont.current(self.cmbFontList.index(lastFont))

            lastHeight = str_to_float(cfg.get('height', ''))
            if lastHeight:
                if (lastHeight in self.cmbFontHeightList):
                    self.cmbFontHeight.current(self.cmbFontHeightList.index(lastHeight))
                else:
                    self.cmbFontHeight.setText(str(lastHeight))

            lastLayer = str_to_int(cfg.get('layer', '1'), 100)
            if 0 <= lastLayer < len(self.cmbLayerList):
                self.cmbLayer.current(lastLayer)
            smooth = str_to_int(cfg.get('smooth', '2'), 100)
            if 0 <= smooth < len(self.cmbSmoothList):
                self.cmbSmooth.current(smooth)

            ws = str_to_float(cfg.get('wordSpacing', "-0.8"))
            self.cmbWordSpacing.setText(str(ws))
            ls = str_to_float(cfg.get('lineSpacing', "0"))
            self.cmbLineSpacing.setText(str(ls))

    #保存当前配置数据
    def saveConfig(self):
        cfg = {'font': self.cmbFont.text(), 'height': self.cmbFontHeight.text(), 
            'layer': str(self.cmbLayer.current()), 'wordSpacing': self.cmbWordSpacing.text(), 
            'lineSpacing': self.cmbLineSpacing.text(), 'smooth': str(self.cmbSmooth.current()), }

        if self.language:
            cfg['language'] = self.language

        cfgStr = json.dumps(cfg, indent=2)
        try:
            with open(CFG_FILENAME, 'w', encoding='utf-8') as f:
                f.write(cfgStr)
        except:
            pass
    
    #取消退出
    def cmdCancel_Cmd(self, event=None):
        #self.saveConfig()
        self.destroy()
        sys.exit(0)
    
    #保存为单独一个文本文件
    def lblSaveAs_Button_1(self, event):
        self.saveConfig()
        txt = self.txtMain.get('1.0', END).strip()
        if not txt:
            showinfo(_('info'), _('Text is empty'))
            return

        newStr = self.generatePolygons(txt)
        if newStr:
            retFile = tkFileDialog.asksaveasfilename(title=_("Save to a text file"), filetypes=[(_('Text files'), '*.txt'), (_("All files"), '*.*')])
            if retFile:
                with open(retFile, 'w') as f:
                    f.write(newStr)
        else:
            showinfo(_('info'), _('Failed to generate text'))
    
    #开始转换文本为多边形
    def cmdOk_Cmd(self, event=None):
        self.saveConfig()

        txt = self.txtMain.get('1.0', END).strip()
        if not txt:
            showinfo(_('info'), _('Text is empty'))
            return

        newStr = self.generatePolygons(txt)
        if newStr:
            with open(self.outFileName, 'w') as f:
                f.write(newStr)
            ret = 4
        else:
            ret = 0

        self.destroy()
        #sprint-layout的插件返回码定义
        #0: = 中止/无动作
        #1: = 完全替换元素，Sprint-layout删除选中的项目并将其替换为插件输出文件中的新项目。
        #2: = 绝对添加元素，Sprint-layout从插件输出文件中插入新元素。不会删除任何项目。
        #3: = 相对替换元素，Sprint-layout从插件输出文件中删除标记的元素和新元素“粘”到鼠标上，并且可以由用户放置。
        #4: = 相对添加元素，插件输出文件中的新元素“粘”在鼠标上，并且可以由用户放置。不会删除任何项目。
        sys.exit(ret)
    
    #将字符串转换为sprint-layout多边形
    def generatePolygons(self, txt: str):
        if not txt:
            return ''
        
        #参数
        fontName = self.cmbFont.text()
        layerIdx = self.cmbLayer.current() + 1 #sprint-layout的板层定义从1开始
        smooth = self.cmbSmooth.current()
        fontHeight = str_to_float(self.cmbFontHeight.text())
        wordSpacing = str_to_float(self.cmbWordSpacing.text())
        lineSpacing = str_to_float(self.cmbLineSpacing.text())
        if fontHeight <= 0.0:
            fontHeight = 1.0
        
        fontFileName = self.fontNameMap.get(fontName, '')
        if not fontFileName or not os.path.exists(fontFileName):
            return ''
            
        try:
            font = TTFont(fontFileName)
        except:
            return ''
        
        #开始逐字转换
        txt = self.translateUnicodeSymbol(txt)
        polygons = []
        offsetY = 0.0
        prevWidth = 0
        for line in txt.split('\n'):
            offsetX = 0.0 #每一行都从最左边开始
            maxHeight = 0
            for word in line:
                ret = singleWordPolygon(font, code=ord(word), layerIdx=layerIdx, fontHeight=fontHeight,
                    offsetX=offsetX, offsetY=offsetY, smooth=smooth)
                #print(ret)
                if not ret: #没有对应的字形，跳过一个空格
                    inc = prevWidth + (wordSpacing * 10000)
                    offsetX += inc if (inc > 0) else prevWidth
                    continue
                    
                prevWidth = ret['width']
                polygons.append(ret['polygon'])
                inc = prevWidth + (wordSpacing * 10000)
                offsetX += inc if (inc > 0) else prevWidth
                if ret['height'] > maxHeight:
                    maxHeight = ret['height']
            #新行
            inc = maxHeight + (lineSpacing * 10000)
            offsetY += inc if (inc > 0) else maxHeight

        font.close()

        #每行一个多边形
        return '\n'.join(polygons)
        
        
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
    
    #将字体文件和字体名字对应起来，关键字为字体名字，值为文件名
    #除了系统的字体目录，本软件同一目录下的ttf也可以做为选择
    def generateFontFileNameMap(self):
        fontNameMap = {}
        fontFileList = [os.path.join(FONT_DIR, f) for f in os.listdir(FONT_DIR) if f.lower().endswith(('.ttf', '.otf'))]
        fontFileList.extend([os.path.join(MODULE_PATH, f) for f in os.listdir(MODULE_PATH) if f.lower().endswith(('.ttf', '.otf'))])
        for fontFileName in fontFileList:
            try:
                font = TTFont(fontFileName, lazy=True)
            except:
                continue
            
            if 'name' in font.keys():
                #nameID:4-比较完整的给人看到名字，包括名称和字体类型，Times New Roman Bold
                #platformID=1: mac平台， 3-windows平台
                #platEncID:1-Unicode BMP
                nameTable = font['name']
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
                    fontNameMap[name] = fontFileName
        return fontNameMap
        

if __name__ == "__main__":
    top = Tk()
    Application(top).mainloop()

