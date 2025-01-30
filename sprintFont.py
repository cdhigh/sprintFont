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
import os, sys, locale, json, threading, queue, datetime, pickle, math, gettext
# Fix Tcl/Tk folder for windows xp
os.environ["TCL_LIBRARY"] = os.path.join(sys.base_prefix, "tcl", "tcl8.6")
os.environ["TK_LIBRARY"] = os.path.join(sys.base_prefix, "tcl", "tk8.6")
os.environ["PATH"] += ';' + sys.base_prefix
from functools import partial
from tkinter import *
from tkinter.font import Font, families
from tkinter.ttk import *
#Usage:showinfo/warning/error,askquestion/okcancel/yesno/retrycancel
from tkinter.messagebox import *
#Usage:f=tkFileDialog.askopenfilename(initialdir='E:/Python')
import tkinter.filedialog as tkFileDialog
import tkinter.simpledialog as tkSimpleDialog  #askstring()
from fontTools.ttLib import ttFont, ttCollection
from comm_utils import *
from widget_right_click import rightClicker
from sprint_struct.sprint_textio import SprintTextIO
from lceda_to_sprint import LcComponent
from sprint_struct.sprint_export_dsn import PcbRule, SprintExportDsn

__Version__ = "1.6.1"
__DATE__ = "20241124"
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

#界面使用作者自己的工具 vb6tkinter <https://github.com/cdhigh/vb6tkinter> 自动生成
class Application_ui(Frame):
    def __init__(self, master):
        super().__init__(master)
        # To center the window on the screen.
        ws = self.master.winfo_screenwidth()
        hs = self.master.winfo_screenheight()
        x = (ws / 2) - (626 / 2)
        y = (hs / 2) - (412 / 2)
        self.master.geometry('%dx%d+%d+%d' % (626,412,x,y))
        self.master.title('sprintFont')
        self.master.resizable(0,0)
        self.icondata = """
            R0lGODlhMAAwAPcAAP///z6KKPf39z6KJz6JJz2KKP78/vz7/Pv6+/f69/r8+v7//v3+
            /fz9/PH38Ja6j8XWwvP48vL38Yiwf5G4iJK3iqTGnJ/Al6bEn6jGobHOqqzHprHLq7XL
            sL3SuNXm0dLgz9Th0d/s3N7r2+ny5+jx5kOOL0ySOVGWPlOXQFOVQVeaRViaRliYR1yZ
            TGWiVWSeVWumW2mkWmqhXGyiXnWsZnWrZnanaYW2eH6scoe3eom2fYKud426gY+8g5G8
            hZW/ipW9iqnLoKrMobHQqbTSrLXQrr3XtsbdwMXcv8LWvczgx8/iytLkzczcyNno1eLu
            3+Ht3uPu4Ovz6fX59O7y7e3x7DiHH0CLKT+KKUCLKkGMK0KMLEONLUONLkaOL0SOL0WO
            MEaPMUeQMkiQM0mQNEqRNUuSNkyRNkySN02TOU6TOVCVO0+UO1CVPFKWPlSXQFWYQVWY
            QlaZQ1eZRFiaRVubR1ubSFycSV2dS16dS1+eTGGfT2KgUGWhU2aiVWijVmqlWGmkWGym
            W22mXG6nXXCoX2+oX26nXnGpYXSrZHOqY3esZ3itaXuva3uvbHywbX6xb32wboCycX2v
            b3+xcYKzc4Gzc4KzdIa2eIW1d4q4fY26f4u5foy5f467gY+7gpC8g5O9hpW/iZS+iJfA
            i5rCjpnBjZ3EkpzDkZvCkJ/FlJ7Ek6HGlqDFlaPHmKXImqfKnabJnK3No67OpbDPp6/O
            prPRqrjUsLfTr7rVsrvWs7zWtMDZub/YuMPbvMLau8Tbvcvfxc/iyc7hyNTlz9Pkztfn
            0tbm0dXl0Nzq2Nvp193n2ubw4+Xv4u306+Tr4jGFFTSGGT6MJUKOKHSsYYe1eJrBjanL
            nrPQqbbSrb/Yt8newszgxdDiytLjzNjn0+Ds3ODp3ejx5efw5O/17eju5vj79/b59S2E
            Cy2DDOXv4ery5/H27yiCADCGCfT48vr8+fn7+PT28/7+/vj4+P///wAAAAAAAAAAAAAA
            AAAAAAAAAAAAAAAAAAAAACH5BAEAAPYALAAAAAAwADAAAAj/AO0JHEiwoMGDCBMqXMiw
            ocOHECFKCxAgGoECFDNSLIBRo8eP6Rxe2fhxY8doLa4MKOmRAEV3C0tezNjRioCbNxGM
            1EhgZQCXLgNcSTiRY4COJRHgXCrAHUWfHzvuQGjyJ0tpSw0oxclSI8YCB9WZxBjUI04K
            Ga/g3Nk140GaHAu4jPuVq0YONw20PXoUbEG4ckuqFaBXo7qcbeNSNAiY5QDEGifkDbBy
            AFSrXwMwpkigbFQB9QSwDYBzA+Wfly9r/itzZkZzAAAgmKdODIPYAvZ63OwRKd8CsYML
            ByBEt0beGYMaNTq8uXG3rHU/Gx5geJ8BLi1nt3o8evLfG507/3+OnPPH8X2ok/duVTnF
            4Qw6jtddvuQI9ZRfDX/TM2h2z/Wdh997A3YVoEYnFFidgiUdmNF8GkHI0oFBDTcGTRkB
            w+Bu7HnlHFJISUiZZSuV59twMXzU0wDwDLfiaeatRlBXDWz4oHA/dEWAg8316GNsHpHo
            0oE/FjkcHSzt2OFRRjYJJGUrdibjQCVR4WSTimREYolLDhfPXmWN11l/Uwr0ETE2Bklg
            cGA8RWKZ9ggonGtRyRmcm9jB6REoLnqlmxnDWcZTec111hGIXUmo5IwRCufFc9hlh6Zw
            I0qJXKEkVZWpnQDIo9EABu20yHCM0NlbWwkEih2oby1I6W+Hkjzk26fDKUMiQiMNx8Jz
            UPqUXXOWKSRmV7OqORwVcBoUXI68lrRSjcI59OReiKpIQHARZavtttx26y1DAQEAOw==
            ==="""
        self.iconimg = PhotoImage(data=self.icondata)
        self.master.tk.call('wm', 'iconphoto', self.master._w, self.iconimg)
        self.createWidgets()

    def createWidgets(self):
        self.top = self.winfo_toplevel()

        self.style = Style()

        self.tabStrip = Notebook(self.top)
        self.tabStrip.place(relx=0.026, rely=0.039, relwidth=0.947, relheight=0.876)
        self.tabStrip.bind('<<NotebookTabChanged>>', self.tabStrip_NotebookTabChanged)

        self.tabStrip__Tab1 = Frame(self.tabStrip)
        self.style.configure('TfrmInvertedBg.TFrame', background='#C0C0C0')
        self.frmInvertedBg = Frame(self.tabStrip__Tab1, style='TfrmInvertedBg.TFrame')
        self.frmInvertedBg.place(relx=0., rely=0.593, relwidth=1., relheight=0.264)
        self.chkInvertedBackgroundTextVar = StringVar(value='Inverted Background')
        self.chkInvertedBackgroundVar = IntVar(value=0)
        self.style.configure('TchkInvertedBackground.TCheckbutton', foreground='#000000', background='#C0C0C0', font=('微软雅黑',10,'bold'))
        self.chkInvertedBackground = Checkbutton(self.frmInvertedBg, text='Inverted Background', textvariable=self.chkInvertedBackgroundTextVar, variable=self.chkInvertedBackgroundVar, command=self.chkInvertedBackground_Cmd, style='TchkInvertedBackground.TCheckbutton')
        self.chkInvertedBackground.setText = lambda x: self.chkInvertedBackgroundTextVar.set(x)
        self.chkInvertedBackground.text = lambda : self.chkInvertedBackgroundTextVar.get()
        self.chkInvertedBackground.setValue = lambda x: self.chkInvertedBackgroundVar.set(x)
        self.chkInvertedBackground.value = lambda : self.chkInvertedBackgroundVar.get()
        self.chkInvertedBackground.place(relx=0.162, rely=0.09, relwidth=0.352, relheight=0.281)
        self.cmbPaddingList = ['',]
        self.cmbPaddingVar = StringVar(value='')
        self.style.configure('TcmbPadding.TCombobox', background='#808080')
        self.cmbPadding = Combobox(self.frmInvertedBg, exportselection=0, textvariable=self.cmbPaddingVar, values=self.cmbPaddingList, font=('微软雅黑',10), style='TcmbPadding.TCombobox')
        self.cmbPadding.setText = lambda x: self.cmbPaddingVar.set(x)
        self.cmbPadding.text = lambda : self.cmbPaddingVar.get()
        self.cmbPadding.place(relx=0.175, rely=0.539, relwidth=0.339)
        self.cmbCapLeftList = ['',]
        self.cmbCapLeftVar = StringVar(value='')
        self.style.configure('TcmbCapLeft.TCombobox', background='#808080')
        self.cmbCapLeft = Combobox(self.frmInvertedBg, exportselection=0, state='readonly', textvariable=self.cmbCapLeftVar, values=self.cmbCapLeftList, font=('Times New Roman',12,'bold'), style='TcmbCapLeft.TCombobox')
        self.cmbCapLeft.setText = lambda x: self.cmbCapLeftVar.set(x)
        self.cmbCapLeft.text = lambda : self.cmbCapLeftVar.get()
        self.cmbCapLeft.place(relx=0.782, rely=0.09, relwidth=0.177)
        self.cmbCapRightList = ['',]
        self.cmbCapRightVar = StringVar(value='')
        self.style.configure('TcmbCapRight.TCombobox', background='#808080')
        self.cmbCapRight = Combobox(self.frmInvertedBg, exportselection=0, state='readonly', textvariable=self.cmbCapRightVar, values=self.cmbCapRightList, font=('Times New Roman',12,'bold'), style='TcmbCapRight.TCombobox')
        self.cmbCapRight.setText = lambda x: self.cmbCapRightVar.set(x)
        self.cmbCapRight.text = lambda : self.cmbCapRightVar.get()
        self.cmbCapRight.place(relx=0.782, rely=0.539, relwidth=0.177)
        self.lblBkPaddingVar = StringVar(value='Padding')
        self.style.configure('TlblBkPadding.TLabel', anchor='e', foreground='#000000', background='#C0C0C0', font=('微软雅黑',10))
        self.lblBkPadding = Label(self.frmInvertedBg, text='Padding', textvariable=self.lblBkPaddingVar, style='TlblBkPadding.TLabel')
        self.lblBkPadding.setText = lambda x: self.lblBkPaddingVar.set(x)
        self.lblBkPadding.text = lambda : self.lblBkPaddingVar.get()
        self.lblBkPadding.place(relx=0.027, rely=0.539, relwidth=0.137, relheight=0.281)
        self.lblCapLeftVar = StringVar(value='Cap left')
        self.style.configure('TlblCapLeft.TLabel', anchor='e', foreground='#000000', background='#C0C0C0', font=('微软雅黑',10))
        self.lblCapLeft = Label(self.frmInvertedBg, text='Cap left', textvariable=self.lblCapLeftVar, style='TlblCapLeft.TLabel')
        self.lblCapLeft.setText = lambda x: self.lblCapLeftVar.set(x)
        self.lblCapLeft.text = lambda : self.lblCapLeftVar.get()
        self.lblCapLeft.place(relx=0.526, rely=0.09, relwidth=0.245, relheight=0.281)
        self.lblCapRightVar = StringVar(value='Cap right')
        self.style.configure('TlblCapRight.TLabel', anchor='e', foreground='#000000', background='#C0C0C0', font=('微软雅黑',10))
        self.lblCapRight = Label(self.frmInvertedBg, text='Cap right', textvariable=self.lblCapRightVar, style='TlblCapRight.TLabel')
        self.lblCapRight.setText = lambda x: self.lblCapRightVar.set(x)
        self.lblCapRight.text = lambda : self.lblCapRightVar.get()
        self.lblCapRight.place(relx=0.526, rely=0.539, relwidth=0.245, relheight=0.281)
        self.VScroll1 = Scrollbar(self.tabStrip__Tab1, orient='vertical')
        self.VScroll1.place(relx=0.931, rely=0.071, relwidth=0.029, relheight=0.169)
        self.cmbLayerList = ['',]
        self.cmbLayerVar = StringVar(value='')
        self.cmbLayer = Combobox(self.tabStrip__Tab1, exportselection=0, state='readonly', textvariable=self.cmbLayerVar, values=self.cmbLayerList, font=('微软雅黑',10))
        self.cmbLayer.setText = lambda x: self.cmbLayerVar.set(x)
        self.cmbLayer.text = lambda : self.cmbLayerVar.get()
        self.cmbLayer.place(relx=0.175, rely=0.38, relwidth=0.339)
        self.txtMainFont = Font(font=('微软雅黑',14))
        self.txtMain = Text(self.tabStrip__Tab1, yscrollcommand=self.VScroll1.set, font=self.txtMainFont)
        self.txtMain.place(relx=0.175, rely=0.071, relwidth=0.754, relheight=0.169)
        self.txtMain.insert('1.0','')
        self.VScroll1['command'] = self.txtMain.yview
        self.cmbSmoothList = ['',]
        self.cmbSmoothVar = StringVar(value='')
        self.cmbSmooth = Combobox(self.tabStrip__Tab1, exportselection=0, state='readonly', textvariable=self.cmbSmoothVar, values=self.cmbSmoothList, font=('微软雅黑',10))
        self.cmbSmooth.setText = lambda x: self.cmbSmoothVar.set(x)
        self.cmbSmooth.text = lambda : self.cmbSmoothVar.get()
        self.cmbSmooth.place(relx=0.175, rely=0.499, relwidth=0.339)
        self.cmdOkVar = StringVar(value='Ok')
        self.style.configure('TcmdOk.TButton', font=('微软雅黑',10))
        self.cmdOk = Button(self.tabStrip__Tab1, text='Ok', textvariable=self.cmdOkVar, command=self.cmdOk_Cmd, style='TcmdOk.TButton')
        self.cmdOk.setText = lambda x: self.cmdOkVar.set(x)
        self.cmdOk.text = lambda : self.cmdOkVar.get()
        self.cmdOk.place(relx=0.135, rely=0.878, relwidth=0.245, relheight=0.089)
        self.cmdCancelVar = StringVar(value='Cancel')
        self.style.configure('TcmdCancel.TButton', font=('微软雅黑',10))
        self.cmdCancel = Button(self.tabStrip__Tab1, text='Cancel', textvariable=self.cmdCancelVar, command=self.cmdCancel_Cmd, style='TcmdCancel.TButton')
        self.cmdCancel.setText = lambda x: self.cmdCancelVar.set(x)
        self.cmdCancel.text = lambda : self.cmdCancelVar.get()
        self.cmdCancel.place(relx=0.499, rely=0.878, relwidth=0.245, relheight=0.089)
        self.cmbWordSpacingList = ['',]
        self.cmbWordSpacingVar = StringVar(value='')
        self.cmbWordSpacing = Combobox(self.tabStrip__Tab1, exportselection=0, textvariable=self.cmbWordSpacingVar, values=self.cmbWordSpacingList, font=('微软雅黑',10))
        self.cmbWordSpacing.setText = lambda x: self.cmbWordSpacingVar.set(x)
        self.cmbWordSpacing.text = lambda : self.cmbWordSpacingVar.get()
        self.cmbWordSpacing.place(relx=0.782, rely=0.38, relwidth=0.177)
        self.cmbLineSpacingList = ['',]
        self.cmbLineSpacingVar = StringVar(value='')
        self.cmbLineSpacing = Combobox(self.tabStrip__Tab1, exportselection=0, textvariable=self.cmbLineSpacingVar, values=self.cmbLineSpacingList, font=('微软雅黑',10))
        self.cmbLineSpacing.setText = lambda x: self.cmbLineSpacingVar.set(x)
        self.cmbLineSpacing.text = lambda : self.cmbLineSpacingVar.get()
        self.cmbLineSpacing.place(relx=0.782, rely=0.499, relwidth=0.177)
        self.cmbFontHeightList = ['',]
        self.cmbFontHeightVar = StringVar(value='')
        self.cmbFontHeight = Combobox(self.tabStrip__Tab1, exportselection=0, textvariable=self.cmbFontHeightVar, values=self.cmbFontHeightList, font=('微软雅黑',10))
        self.cmbFontHeight.setText = lambda x: self.cmbFontHeightVar.set(x)
        self.cmbFontHeight.text = lambda : self.cmbFontHeightVar.get()
        self.cmbFontHeight.place(relx=0.782, rely=0.261, relwidth=0.177)
        self.cmbFontList = ['',]
        self.cmbFontVar = StringVar(value='')
        self.cmbFont = Combobox(self.tabStrip__Tab1, exportselection=0, state='readonly', textvariable=self.cmbFontVar, values=self.cmbFontList, font=('微软雅黑',10))
        self.cmbFont.setText = lambda x: self.cmbFontVar.set(x)
        self.cmbFont.text = lambda : self.cmbFontVar.get()
        self.cmbFont.place(relx=0.175, rely=0.261, relwidth=0.339)
        self.cmbFont.bind('<<ComboboxSelected>>', self.cmbFont_ComboboxSelected)
        self.lblTxtVar = StringVar(value='Text')
        self.style.configure('TlblTxt.TLabel', anchor='e', font=('微软雅黑',10))
        self.lblTxt = Label(self.tabStrip__Tab1, text='Text', textvariable=self.lblTxtVar, style='TlblTxt.TLabel')
        self.lblTxt.setText = lambda x: self.lblTxtVar.set(x)
        self.lblTxt.text = lambda : self.lblTxtVar.get()
        self.lblTxt.place(relx=0.054, rely=0.071, relwidth=0.11, relheight=0.074)
        self.lblLayerVar = StringVar(value='Layer')
        self.style.configure('TlblLayer.TLabel', anchor='e', font=('微软雅黑',10))
        self.lblLayer = Label(self.tabStrip__Tab1, text='Layer', textvariable=self.lblLayerVar, style='TlblLayer.TLabel')
        self.lblLayer.setText = lambda x: self.lblLayerVar.set(x)
        self.lblLayer.text = lambda : self.lblLayerVar.get()
        self.lblLayer.place(relx=0.027, rely=0.38, relwidth=0.137, relheight=0.074)
        self.lblSmoothVar = StringVar(value='Smooth')
        self.style.configure('TlblSmooth.TLabel', anchor='e', font=('微软雅黑',10))
        self.lblSmooth = Label(self.tabStrip__Tab1, text='Smooth', textvariable=self.lblSmoothVar, style='TlblSmooth.TLabel')
        self.lblSmooth.setText = lambda x: self.lblSmoothVar.set(x)
        self.lblSmooth.text = lambda : self.lblSmoothVar.get()
        self.lblSmooth.place(relx=0.027, rely=0.499, relwidth=0.137, relheight=0.074)
        self.lblWordSpacingVar = StringVar(value='Word spacing (mm)')
        self.style.configure('TlblWordSpacing.TLabel', anchor='e', font=('微软雅黑',10))
        self.lblWordSpacing = Label(self.tabStrip__Tab1, text='Word spacing (mm)', textvariable=self.lblWordSpacingVar, style='TlblWordSpacing.TLabel')
        self.lblWordSpacing.setText = lambda x: self.lblWordSpacingVar.set(x)
        self.lblWordSpacing.text = lambda : self.lblWordSpacingVar.get()
        self.lblWordSpacing.place(relx=0.526, rely=0.38, relwidth=0.245, relheight=0.074)
        self.LblLineSpacingVar = StringVar(value='Line spacing (mm)')
        self.style.configure('TLblLineSpacing.TLabel', anchor='e', font=('微软雅黑',10))
        self.LblLineSpacing = Label(self.tabStrip__Tab1, text='Line spacing (mm)', textvariable=self.LblLineSpacingVar, style='TLblLineSpacing.TLabel')
        self.LblLineSpacing.setText = lambda x: self.LblLineSpacingVar.set(x)
        self.LblLineSpacing.text = lambda : self.LblLineSpacingVar.get()
        self.LblLineSpacing.place(relx=0.526, rely=0.499, relwidth=0.245, relheight=0.074)
        self.lblSaveAsVar = StringVar(value='Save as')
        self.style.configure('TlblSaveAs.TLabel', anchor='e', foreground='#0000FF', font=('微软雅黑',10,'underline'))
        self.lblSaveAs = Label(self.tabStrip__Tab1, text='Save as', textvariable=self.lblSaveAsVar, style='TlblSaveAs.TLabel')
        self.lblSaveAs.setText = lambda x: self.lblSaveAsVar.set(x)
        self.lblSaveAs.text = lambda : self.lblSaveAsVar.get()
        self.lblSaveAs.place(relx=0.782, rely=0.902, relwidth=0.204, relheight=0.074)
        self.lblSaveAs.bind('<Button-1>', self.lblSaveAs_Button_1)
        self.lblFontVar = StringVar(value='Font')
        self.style.configure('TlblFont.TLabel', anchor='e', font=('微软雅黑',10))
        self.lblFont = Label(self.tabStrip__Tab1, text='Font', textvariable=self.lblFontVar, style='TlblFont.TLabel')
        self.lblFont.setText = lambda x: self.lblFontVar.set(x)
        self.lblFont.text = lambda : self.lblFontVar.get()
        self.lblFont.place(relx=0.027, rely=0.261, relwidth=0.137, relheight=0.074)
        self.lblFontHeightVar = StringVar(value='Height (mm)')
        self.style.configure('TlblFontHeight.TLabel', anchor='e', font=('微软雅黑',10))
        self.lblFontHeight = Label(self.tabStrip__Tab1, text='Height (mm)', textvariable=self.lblFontHeightVar, style='TlblFontHeight.TLabel')
        self.lblFontHeight.setText = lambda x: self.lblFontHeightVar.set(x)
        self.lblFontHeight.text = lambda : self.lblFontHeightVar.get()
        self.lblFontHeight.place(relx=0.526, rely=0.261, relwidth=0.245, relheight=0.074)
        self.tabStrip.add(self.tabStrip__Tab1, text='     Font     ')

        self.tabStrip__Tab2 = Frame(self.tabStrip)
        self.chkImportFootprintTextTextVar = StringVar(value='Import text')
        self.chkImportFootprintTextVar = IntVar(value=1)
        self.style.configure('TchkImportFootprintText.TCheckbutton', font=('微软雅黑',10))
        self.chkImportFootprintText = Checkbutton(self.tabStrip__Tab2, text='Import text', textvariable=self.chkImportFootprintTextTextVar, variable=self.chkImportFootprintTextVar, style='TchkImportFootprintText.TCheckbutton')
        self.chkImportFootprintText.setText = lambda x: self.chkImportFootprintTextTextVar.set(x)
        self.chkImportFootprintText.text = lambda : self.chkImportFootprintTextTextVar.get()
        self.chkImportFootprintText.setValue = lambda x: self.chkImportFootprintTextVar.set(x)
        self.chkImportFootprintText.value = lambda : self.chkImportFootprintTextVar.get()
        self.chkImportFootprintText.place(relx=0.175, rely=0.57, relwidth=0.339, relheight=0.074)
        self.cmdFootprintFileVar = StringVar(value='...')
        self.style.configure('TcmdFootprintFile.TButton', font=('Arial',9))
        self.cmdFootprintFile = Button(self.tabStrip__Tab2, text='...', textvariable=self.cmdFootprintFileVar, command=self.cmdFootprintFile_Cmd, style='TcmdFootprintFile.TButton')
        self.cmdFootprintFile.setText = lambda x: self.cmdFootprintFileVar.set(x)
        self.cmdFootprintFile.text = lambda : self.cmdFootprintFileVar.get()
        self.cmdFootprintFile.place(relx=0.917, rely=0.427, relwidth=0.056, relheight=0.074)
        self.txtFootprintFileVar = StringVar(value='')
        self.txtFootprintFile = Entry(self.tabStrip__Tab2, textvariable=self.txtFootprintFileVar, font=('微软雅黑',10))
        self.txtFootprintFile.setText = lambda x: self.txtFootprintFileVar.set(x)
        self.txtFootprintFile.text = lambda : self.txtFootprintFileVar.get()
        self.txtFootprintFile.place(relx=0.175, rely=0.427, relwidth=0.73, relheight=0.083)
        self.cmdOkFootprintVar = StringVar(value='Ok')
        self.style.configure('TcmdOkFootprint.TButton', font=('微软雅黑',10))
        self.cmdOkFootprint = Button(self.tabStrip__Tab2, text='Ok', textvariable=self.cmdOkFootprintVar, command=self.cmdOkFootprint_Cmd, style='TcmdOkFootprint.TButton')
        self.cmdOkFootprint.setText = lambda x: self.cmdOkFootprintVar.set(x)
        self.cmdOkFootprint.text = lambda : self.cmdOkFootprintVar.get()
        self.cmdOkFootprint.place(relx=0.135, rely=0.878, relwidth=0.245, relheight=0.089)
        self.cmdCancelFootprintVar = StringVar(value='Cancel')
        self.style.configure('TcmdCancelFootprint.TButton', font=('微软雅黑',10))
        self.cmdCancelFootprint = Button(self.tabStrip__Tab2, text='Cancel', textvariable=self.cmdCancelFootprintVar, command=self.cmdCancelFootprint_Cmd, style='TcmdCancelFootprint.TButton')
        self.cmdCancelFootprint.setText = lambda x: self.cmdCancelFootprintVar.set(x)
        self.cmdCancelFootprint.text = lambda : self.cmdCancelFootprintVar.get()
        self.cmdCancelFootprint.place(relx=0.499, rely=0.878, relwidth=0.245, relheight=0.089)
        self.lblFootprintFileVar = StringVar(value='Input')
        self.style.configure('TlblFootprintFile.TLabel', anchor='e', font=('微软雅黑',10))
        self.lblFootprintFile = Label(self.tabStrip__Tab2, text='Input', textvariable=self.lblFootprintFileVar, style='TlblFootprintFile.TLabel')
        self.lblFootprintFile.setText = lambda x: self.lblFootprintFileVar.set(x)
        self.lblFootprintFile.text = lambda : self.lblFootprintFileVar.get()
        self.lblFootprintFile.place(relx=0.027, rely=0.427, relwidth=0.11, relheight=0.074)
        self.lblFootprintTipsVar = StringVar(value='Currently supports:\n1. Kicad footprint Library : *.kicad_mod\n2. EasyEDA part ID: C + number (C can be omitted)')
        self.style.configure('TlblFootprintTips.TLabel', anchor='w', font=('微软雅黑',10))
        self.lblFootprintTips = Label(self.tabStrip__Tab2, text='Currently supports:\n1. Kicad footprint Library : *.kicad_mod\n2. EasyEDA part ID: C + number (C can be omitted)', textvariable=self.lblFootprintTipsVar, style='TlblFootprintTips.TLabel')
        self.lblFootprintTips.setText = lambda x: self.lblFootprintTipsVar.set(x)
        self.lblFootprintTips.text = lambda : self.lblFootprintTipsVar.get()
        self.lblFootprintTips.place(relx=0.175, rely=0.071, relwidth=0.771, relheight=0.312)
        self.lblSaveAsFootprintVar = StringVar(value='Save as')
        self.style.configure('TlblSaveAsFootprint.TLabel', anchor='e', foreground='#0000FF', font=('微软雅黑',10,'underline'))
        self.lblSaveAsFootprint = Label(self.tabStrip__Tab2, text='Save as', textvariable=self.lblSaveAsFootprintVar, style='TlblSaveAsFootprint.TLabel')
        self.lblSaveAsFootprint.setText = lambda x: self.lblSaveAsFootprintVar.set(x)
        self.lblSaveAsFootprint.text = lambda : self.lblSaveAsFootprintVar.get()
        self.lblSaveAsFootprint.place(relx=0.782, rely=0.902, relwidth=0.191, relheight=0.074)
        self.lblSaveAsFootprint.bind('<Button-1>', self.lblSaveAsFootprint_Button_1)
        self.tabStrip.add(self.tabStrip__Tab2, text='   Footprint  ')

        self.tabStrip__Tab3 = Frame(self.tabStrip)
        self.cmbSvgQrcodeList = ['',]
        self.cmbSvgQrcodeVar = StringVar(value='')
        self.cmbSvgQrcode = Combobox(self.tabStrip__Tab3, exportselection=0, state='readonly', justify='right', textvariable=self.cmbSvgQrcodeVar, values=self.cmbSvgQrcodeList, font=('微软雅黑',10))
        self.cmbSvgQrcode.setText = lambda x: self.cmbSvgQrcodeVar.set(x)
        self.cmbSvgQrcode.text = lambda : self.cmbSvgQrcodeVar.get()
        self.cmbSvgQrcode.place(relx=0.013, rely=0.297, relwidth=0.164)
        self.cmbSvgModeList = ['',]
        self.cmbSvgModeVar = StringVar(value='')
        self.cmbSvgMode = Combobox(self.tabStrip__Tab3, exportselection=0, state='readonly', textvariable=self.cmbSvgModeVar, values=self.cmbSvgModeList, font=('微软雅黑',10))
        self.cmbSvgMode.setText = lambda x: self.cmbSvgModeVar.set(x)
        self.cmbSvgMode.text = lambda : self.cmbSvgModeVar.get()
        self.cmbSvgMode.place(relx=0.175, rely=0.451, relwidth=0.352)
        self.cmbSvgHeightList = ['',]
        self.cmbSvgHeightVar = StringVar(value='')
        self.cmbSvgHeight = Combobox(self.tabStrip__Tab3, exportselection=0, textvariable=self.cmbSvgHeightVar, values=self.cmbSvgHeightList, font=('微软雅黑',10))
        self.cmbSvgHeight.setText = lambda x: self.cmbSvgHeightVar.set(x)
        self.cmbSvgHeight.text = lambda : self.cmbSvgHeightVar.get()
        self.cmbSvgHeight.place(relx=0.728, rely=0.451, relwidth=0.245)
        self.cmbSvgSmoothList = ['',]
        self.cmbSvgSmoothVar = StringVar(value='')
        self.cmbSvgSmooth = Combobox(self.tabStrip__Tab3, exportselection=0, state='readonly', textvariable=self.cmbSvgSmoothVar, values=self.cmbSvgSmoothList, font=('微软雅黑',10))
        self.cmbSvgSmooth.setText = lambda x: self.cmbSvgSmoothVar.set(x)
        self.cmbSvgSmooth.text = lambda : self.cmbSvgSmoothVar.get()
        self.cmbSvgSmooth.place(relx=0.728, rely=0.57, relwidth=0.245)
        self.cmbSvgLayerList = ['',]
        self.cmbSvgLayerVar = StringVar(value='')
        self.cmbSvgLayer = Combobox(self.tabStrip__Tab3, exportselection=0, state='readonly', textvariable=self.cmbSvgLayerVar, values=self.cmbSvgLayerList, font=('微软雅黑',10))
        self.cmbSvgLayer.setText = lambda x: self.cmbSvgLayerVar.set(x)
        self.cmbSvgLayer.text = lambda : self.cmbSvgLayerVar.get()
        self.cmbSvgLayer.place(relx=0.175, rely=0.57, relwidth=0.352)
        self.cmdCancelSvgVar = StringVar(value='Cancel')
        self.style.configure('TcmdCancelSvg.TButton', font=('微软雅黑',10))
        self.cmdCancelSvg = Button(self.tabStrip__Tab3, text='Cancel', textvariable=self.cmdCancelSvgVar, command=self.cmdCancelSvg_Cmd, style='TcmdCancelSvg.TButton')
        self.cmdCancelSvg.setText = lambda x: self.cmdCancelSvgVar.set(x)
        self.cmdCancelSvg.text = lambda : self.cmdCancelSvgVar.get()
        self.cmdCancelSvg.place(relx=0.499, rely=0.878, relwidth=0.245, relheight=0.089)
        self.cmdOkSvgVar = StringVar(value='Ok')
        self.style.configure('TcmdOkSvg.TButton', font=('微软雅黑',10))
        self.cmdOkSvg = Button(self.tabStrip__Tab3, text='Ok', textvariable=self.cmdOkSvgVar, command=self.cmdOkSvg_Cmd, style='TcmdOkSvg.TButton')
        self.cmdOkSvg.setText = lambda x: self.cmdOkSvgVar.set(x)
        self.cmdOkSvg.text = lambda : self.cmdOkSvgVar.get()
        self.cmdOkSvg.place(relx=0.135, rely=0.878, relwidth=0.245, relheight=0.089)
        self.txtSvgFileVar = StringVar(value='')
        self.txtSvgFile = Entry(self.tabStrip__Tab3, textvariable=self.txtSvgFileVar, font=('微软雅黑',10))
        self.txtSvgFile.setText = lambda x: self.txtSvgFileVar.set(x)
        self.txtSvgFile.text = lambda : self.txtSvgFileVar.get()
        self.txtSvgFile.place(relx=0.175, rely=0.297, relwidth=0.73, relheight=0.083)
        self.cmdSvgFileVar = StringVar(value='...')
        self.style.configure('TcmdSvgFile.TButton', font=('Arial',9))
        self.cmdSvgFile = Button(self.tabStrip__Tab3, text='...', textvariable=self.cmdSvgFileVar, command=self.cmdSvgFile_Cmd, style='TcmdSvgFile.TButton')
        self.cmdSvgFile.setText = lambda x: self.cmdSvgFileVar.set(x)
        self.cmdSvgFile.text = lambda : self.cmdSvgFileVar.get()
        self.cmdSvgFile.place(relx=0.917, rely=0.297, relwidth=0.056, relheight=0.074)
        self.lblSvgHeightVar = StringVar(value='Height (mm)')
        self.style.configure('TlblSvgHeight.TLabel', anchor='e', font=('微软雅黑',10))
        self.lblSvgHeight = Label(self.tabStrip__Tab3, text='Height (mm)', textvariable=self.lblSvgHeightVar, style='TlblSvgHeight.TLabel')
        self.lblSvgHeight.setText = lambda x: self.lblSvgHeightVar.set(x)
        self.lblSvgHeight.text = lambda : self.lblSvgHeightVar.get()
        self.lblSvgHeight.place(relx=0.526, rely=0.451, relwidth=0.191, relheight=0.074)
        self.lblSvgModeVar = StringVar(value='Mode')
        self.style.configure('TlblSvgMode.TLabel', anchor='e', font=('微软雅黑',10))
        self.lblSvgMode = Label(self.tabStrip__Tab3, text='Mode', textvariable=self.lblSvgModeVar, style='TlblSvgMode.TLabel')
        self.lblSvgMode.setText = lambda x: self.lblSvgModeVar.set(x)
        self.lblSvgMode.text = lambda : self.lblSvgModeVar.get()
        self.lblSvgMode.place(relx=0.04, rely=0.451, relwidth=0.11, relheight=0.074)
        self.lblSvgSmoothVar = StringVar(value='Smooth')
        self.style.configure('TlblSvgSmooth.TLabel', anchor='e', font=('微软雅黑',10))
        self.lblSvgSmooth = Label(self.tabStrip__Tab3, text='Smooth', textvariable=self.lblSvgSmoothVar, style='TlblSvgSmooth.TLabel')
        self.lblSvgSmooth.setText = lambda x: self.lblSvgSmoothVar.set(x)
        self.lblSvgSmooth.text = lambda : self.lblSvgSmoothVar.get()
        self.lblSvgSmooth.place(relx=0.526, rely=0.57, relwidth=0.191, relheight=0.074)
        self.lblSvgLayerVar = StringVar(value='Layer')
        self.style.configure('TlblSvgLayer.TLabel', anchor='e', font=('微软雅黑',10))
        self.lblSvgLayer = Label(self.tabStrip__Tab3, text='Layer', textvariable=self.lblSvgLayerVar, style='TlblSvgLayer.TLabel')
        self.lblSvgLayer.setText = lambda x: self.lblSvgLayerVar.set(x)
        self.lblSvgLayer.text = lambda : self.lblSvgLayerVar.get()
        self.lblSvgLayer.place(relx=0.04, rely=0.57, relwidth=0.11, relheight=0.074)
        self.lblSaveAsSvgVar = StringVar(value='Save as')
        self.style.configure('TlblSaveAsSvg.TLabel', anchor='e', foreground='#0000FF', font=('微软雅黑',10,'underline'))
        self.lblSaveAsSvg = Label(self.tabStrip__Tab3, text='Save as', textvariable=self.lblSaveAsSvgVar, style='TlblSaveAsSvg.TLabel')
        self.lblSaveAsSvg.setText = lambda x: self.lblSaveAsSvgVar.set(x)
        self.lblSaveAsSvg.text = lambda : self.lblSaveAsSvgVar.get()
        self.lblSaveAsSvg.place(relx=0.782, rely=0.902, relwidth=0.191, relheight=0.074)
        self.lblSaveAsSvg.bind('<Button-1>', self.lblSaveAsSvg_Button_1)
        self.lblSvgTipsVar = StringVar(value='Note:\nOnly for simple images, may fail to convert complex images')
        self.style.configure('TlblSvgTips.TLabel', anchor='w', font=('微软雅黑',10))
        self.lblSvgTips = Label(self.tabStrip__Tab3, text='Note:\nOnly for simple images, may fail to convert complex images', textvariable=self.lblSvgTipsVar, style='TlblSvgTips.TLabel')
        self.lblSvgTips.setText = lambda x: self.lblSvgTipsVar.set(x)
        self.lblSvgTips.text = lambda : self.lblSvgTipsVar.get()
        self.lblSvgTips.place(relx=0.175, rely=0.071, relwidth=0.771, relheight=0.193)
        self.tabStrip.add(self.tabStrip__Tab3, text='  SVG/Qrcode  ')

        self.tabStrip__Tab4 = Frame(self.tabStrip)
        self.VSrlRules = Scrollbar(self.tabStrip__Tab4, orient='vertical')
        self.VSrlRules.place(relx=0.904, rely=0.427, relwidth=0.029, relheight=0.359)
        self.style.configure('TtreRules.Treeview', font=('微软雅黑',10))
        self.treRules = Treeview(self.tabStrip__Tab4, show='tree', yscrollcommand=self.VSrlRules.set, style='TtreRules.Treeview')
        self.treRules.place(relx=0.175, rely=0.427, relwidth=0.73, relheight=0.359)
        self.treRules.bind('<Double-Button-1>', self.treRules_Double_Button_1)
        self.VSrlRules['command'] = self.treRules.yview
        self.cmdImportSesVar = StringVar(value='Import SES')
        self.style.configure('TcmdImportSes.TButton', font=('微软雅黑',10))
        self.cmdImportSes = Button(self.tabStrip__Tab4, text='Import SES', textvariable=self.cmdImportSesVar, command=self.cmdImportSes_Cmd, style='TcmdImportSes.TButton')
        self.cmdImportSes.setText = lambda x: self.cmdImportSesVar.set(x)
        self.cmdImportSes.text = lambda : self.cmdImportSesVar.get()
        self.cmdImportSes.place(relx=0.31, rely=0.878, relwidth=0.204, relheight=0.089)
        self.txtSesFileVar = StringVar(value='')
        self.txtSesFile = Entry(self.tabStrip__Tab4, textvariable=self.txtSesFileVar, font=('微软雅黑',10))
        self.txtSesFile.setText = lambda x: self.txtSesFileVar.set(x)
        self.txtSesFile.text = lambda : self.txtSesFileVar.get()
        self.txtSesFile.place(relx=0.175, rely=0.332, relwidth=0.73, relheight=0.083)
        self.cmdSesFileVar = StringVar(value='...')
        self.style.configure('TcmdSesFile.TButton', font=('Arial',9))
        self.cmdSesFile = Button(self.tabStrip__Tab4, text='...', textvariable=self.cmdSesFileVar, command=self.cmdSesFile_Cmd, style='TcmdSesFile.TButton')
        self.cmdSesFile.setText = lambda x: self.cmdSesFileVar.set(x)
        self.cmdSesFile.text = lambda : self.cmdSesFileVar.get()
        self.cmdSesFile.place(relx=0.917, rely=0.332, relwidth=0.056, relheight=0.074)
        self.cmdCancelAutoRouterVar = StringVar(value='Cancel')
        self.style.configure('TcmdCancelAutoRouter.TButton', font=('微软雅黑',10))
        self.cmdCancelAutoRouter = Button(self.tabStrip__Tab4, text='Cancel', textvariable=self.cmdCancelAutoRouterVar, command=self.cmdCancelAutoRouter_Cmd, style='TcmdCancelAutoRouter.TButton')
        self.cmdCancelAutoRouter.setText = lambda x: self.cmdCancelAutoRouterVar.set(x)
        self.cmdCancelAutoRouter.text = lambda : self.cmdCancelAutoRouterVar.get()
        self.cmdCancelAutoRouter.place(relx=0.58, rely=0.878, relwidth=0.204, relheight=0.089)
        self.cmdExportDsnVar = StringVar(value='Export DSN')
        self.style.configure('TcmdExportDsn.TButton', font=('微软雅黑',10))
        self.cmdExportDsn = Button(self.tabStrip__Tab4, text='Export DSN', textvariable=self.cmdExportDsnVar, command=self.cmdExportDsn_Cmd, style='TcmdExportDsn.TButton')
        self.cmdExportDsn.setText = lambda x: self.cmdExportDsnVar.set(x)
        self.cmdExportDsn.text = lambda : self.cmdExportDsnVar.get()
        self.cmdExportDsn.place(relx=0.04, rely=0.878, relwidth=0.204, relheight=0.089)
        self.txtDsnFileVar = StringVar(value='')
        self.txtDsnFile = Entry(self.tabStrip__Tab4, textvariable=self.txtDsnFileVar, font=('微软雅黑',10))
        self.txtDsnFile.setText = lambda x: self.txtDsnFileVar.set(x)
        self.txtDsnFile.text = lambda : self.txtDsnFileVar.get()
        self.txtDsnFile.place(relx=0.175, rely=0.237, relwidth=0.73, relheight=0.083)
        self.cmdDsnFileVar = StringVar(value='...')
        self.style.configure('TcmdDsnFile.TButton', font=('Arial',9))
        self.cmdDsnFile = Button(self.tabStrip__Tab4, text='...', textvariable=self.cmdDsnFileVar, command=self.cmdDsnFile_Cmd, style='TcmdDsnFile.TButton')
        self.cmdDsnFile.setText = lambda x: self.cmdDsnFileVar.set(x)
        self.cmdDsnFile.text = lambda : self.cmdDsnFileVar.get()
        self.cmdDsnFile.place(relx=0.917, rely=0.237, relwidth=0.056, relheight=0.074)
        self.lblRulesVar = StringVar(value='Rules')
        self.style.configure('TlblRules.TLabel', anchor='e', font=('微软雅黑',10))
        self.lblRules = Label(self.tabStrip__Tab4, text='Rules', textvariable=self.lblRulesVar, style='TlblRules.TLabel')
        self.lblRules.setText = lambda x: self.lblRulesVar.set(x)
        self.lblRules.text = lambda : self.lblRulesVar.get()
        self.lblRules.place(relx=0.027, rely=0.475, relwidth=0.11, relheight=0.074)
        self.lblSesFileVar = StringVar(value='Ses file')
        self.style.configure('TlblSesFile.TLabel', anchor='e', font=('微软雅黑',10))
        self.lblSesFile = Label(self.tabStrip__Tab4, text='Ses file', textvariable=self.lblSesFileVar, style='TlblSesFile.TLabel')
        self.lblSesFile.setText = lambda x: self.lblSesFileVar.set(x)
        self.lblSesFile.text = lambda : self.lblSesFileVar.get()
        self.lblSesFile.place(relx=0.027, rely=0.332, relwidth=0.11, relheight=0.074)
        self.lblSaveAsAutoRouterVar = StringVar(value='Save as')
        self.style.configure('TlblSaveAsAutoRouter.TLabel', anchor='e', foreground='#0000FF', font=('微软雅黑',10,'underline'))
        self.lblSaveAsAutoRouter = Label(self.tabStrip__Tab4, text='Save as', textvariable=self.lblSaveAsAutoRouterVar, style='TlblSaveAsAutoRouter.TLabel')
        self.lblSaveAsAutoRouter.setText = lambda x: self.lblSaveAsAutoRouterVar.set(x)
        self.lblSaveAsAutoRouter.text = lambda : self.lblSaveAsAutoRouterVar.get()
        self.lblSaveAsAutoRouter.place(relx=0.809, rely=0.902, relwidth=0.164, relheight=0.074)
        self.lblSaveAsAutoRouter.bind('<Button-1>', self.lblSaveAsAutoRouter_Button_1)
        self.lblAutoRouterTipsVar = StringVar(value='Open the exported DSN file with Freerouting for autorouting\nCurrently only supports all components placed on the front side')
        self.style.configure('TlblAutoRouterTips.TLabel', anchor='w', font=('微软雅黑',10))
        self.lblAutoRouterTips = Label(self.tabStrip__Tab4, text='Open the exported DSN file with Freerouting for autorouting\nCurrently only supports all components placed on the front side', textvariable=self.lblAutoRouterTipsVar, style='TlblAutoRouterTips.TLabel')
        self.lblAutoRouterTips.setText = lambda x: self.lblAutoRouterTipsVar.set(x)
        self.lblAutoRouterTips.text = lambda : self.lblAutoRouterTipsVar.get()
        self.lblAutoRouterTips.place(relx=0.175, rely=0.047, relwidth=0.771, relheight=0.169)
        self.lblDsnFileVar = StringVar(value='Dsn file')
        self.style.configure('TlblDsnFile.TLabel', anchor='e', font=('微软雅黑',10))
        self.lblDsnFile = Label(self.tabStrip__Tab4, text='Dsn file', textvariable=self.lblDsnFileVar, style='TlblDsnFile.TLabel')
        self.lblDsnFile.setText = lambda x: self.lblDsnFileVar.set(x)
        self.lblDsnFile.text = lambda : self.lblDsnFileVar.get()
        self.lblDsnFile.place(relx=0.027, rely=0.237, relwidth=0.11, relheight=0.074)
        self.tabStrip.add(self.tabStrip__Tab4, text='  AutoRouter  ')

        self.tabStrip__Tab5 = Frame(self.tabStrip)
        self.cmbTeardropPadTypeList = ['',]
        self.cmbTeardropPadTypeVar = StringVar(value='')
        self.cmbTeardropPadType = Combobox(self.tabStrip__Tab5, exportselection=0, state='readonly', textvariable=self.cmbTeardropPadTypeVar, values=self.cmbTeardropPadTypeList, font=('微软雅黑',10))
        self.cmbTeardropPadType.setText = lambda x: self.cmbTeardropPadTypeVar.set(x)
        self.cmbTeardropPadType.text = lambda : self.cmbTeardropPadTypeVar.get()
        self.cmbTeardropPadType.place(relx=0.31, rely=0.617, relwidth=0.137)
        self.picTeardrops = Canvas(self.tabStrip__Tab5, takefocus=1, highlightthickness=0)
        self.picTeardrops.place(relx=0.499, rely=0.237, relwidth=0.447, relheight=0.478)
        self.cmdRemoveTeardropsVar = StringVar(value='Remove')
        self.style.configure('TcmdRemoveTeardrops.TButton', font=('微软雅黑',10))
        self.cmdRemoveTeardrops = Button(self.tabStrip__Tab5, text='Remove', textvariable=self.cmdRemoveTeardropsVar, command=self.cmdRemoveTeardrops_Cmd, style='TcmdRemoveTeardrops.TButton')
        self.cmdRemoveTeardrops.setText = lambda x: self.cmdRemoveTeardropsVar.set(x)
        self.cmdRemoveTeardrops.text = lambda : self.cmdRemoveTeardropsVar.get()
        self.cmdRemoveTeardrops.place(relx=0.31, rely=0.878, relwidth=0.204, relheight=0.089)
        self.cmbhPercentList = ['',]
        self.cmbhPercentVar = StringVar(value='')
        self.cmbhPercent = Combobox(self.tabStrip__Tab5, exportselection=0, textvariable=self.cmbhPercentVar, values=self.cmbhPercentList, font=('微软雅黑',10))
        self.cmbhPercent.setText = lambda x: self.cmbhPercentVar.set(x)
        self.cmbhPercent.text = lambda : self.cmbhPercentVar.get()
        self.cmbhPercent.place(relx=0.31, rely=0.261, relwidth=0.137)
        self.cmdCancelTeardropsVar = StringVar(value='Cancel')
        self.style.configure('TcmdCancelTeardrops.TButton', font=('微软雅黑',10))
        self.cmdCancelTeardrops = Button(self.tabStrip__Tab5, text='Cancel', textvariable=self.cmdCancelTeardropsVar, command=self.cmdCancelTeardrops_Cmd, style='TcmdCancelTeardrops.TButton')
        self.cmdCancelTeardrops.setText = lambda x: self.cmdCancelTeardropsVar.set(x)
        self.cmdCancelTeardrops.text = lambda : self.cmdCancelTeardropsVar.get()
        self.cmdCancelTeardrops.place(relx=0.58, rely=0.878, relwidth=0.204, relheight=0.089)
        self.cmdAddTeardropsVar = StringVar(value='Add')
        self.style.configure('TcmdAddTeardrops.TButton', font=('微软雅黑',10))
        self.cmdAddTeardrops = Button(self.tabStrip__Tab5, text='Add', textvariable=self.cmdAddTeardropsVar, command=self.cmdAddTeardrops_Cmd, style='TcmdAddTeardrops.TButton')
        self.cmdAddTeardrops.setText = lambda x: self.cmdAddTeardropsVar.set(x)
        self.cmdAddTeardrops.text = lambda : self.cmdAddTeardropsVar.get()
        self.cmdAddTeardrops.place(relx=0.04, rely=0.878, relwidth=0.204, relheight=0.089)
        self.cmbTeardropSegsList = ['',]
        self.cmbTeardropSegsVar = StringVar(value='')
        self.cmbTeardropSegs = Combobox(self.tabStrip__Tab5, exportselection=0, textvariable=self.cmbTeardropSegsVar, values=self.cmbTeardropSegsList, font=('微软雅黑',10))
        self.cmbTeardropSegs.setText = lambda x: self.cmbTeardropSegsVar.set(x)
        self.cmbTeardropSegs.text = lambda : self.cmbTeardropSegsVar.get()
        self.cmbTeardropSegs.place(relx=0.31, rely=0.499, relwidth=0.137)
        self.cmbvPercentList = ['',]
        self.cmbvPercentVar = StringVar(value='')
        self.cmbvPercent = Combobox(self.tabStrip__Tab5, exportselection=0, textvariable=self.cmbvPercentVar, values=self.cmbvPercentList, font=('微软雅黑',10))
        self.cmbvPercent.setText = lambda x: self.cmbvPercentVar.set(x)
        self.cmbvPercent.text = lambda : self.cmbvPercentVar.get()
        self.cmbvPercent.place(relx=0.31, rely=0.38, relwidth=0.137)
        self.lblTeardropPadTypeVar = StringVar(value='Pad type')
        self.style.configure('TlblTeardropPadType.TLabel', anchor='e', font=('微软雅黑',10))
        self.lblTeardropPadType = Label(self.tabStrip__Tab5, text='Pad type', textvariable=self.lblTeardropPadTypeVar, style='TlblTeardropPadType.TLabel')
        self.lblTeardropPadType.setText = lambda x: self.lblTeardropPadTypeVar.set(x)
        self.lblTeardropPadType.text = lambda : self.lblTeardropPadTypeVar.get()
        self.lblTeardropPadType.place(relx=0.027, rely=0.617, relwidth=0.258, relheight=0.074)
        self.lblTeardropsTipsVar = StringVar(value='Apply to all pads when deselecting all, otherwise apply to selected pads AND tracks only')
        self.style.configure('TlblTeardropsTips.TLabel', anchor='center', font=('微软雅黑',10))
        self.lblTeardropsTips = Label(self.tabStrip__Tab5, text='Apply to all pads when deselecting all, otherwise apply to selected pads AND tracks only', textvariable=self.lblTeardropsTipsVar, style='TlblTeardropsTips.TLabel')
        self.lblTeardropsTips.setText = lambda x: self.lblTeardropsTipsVar.set(x)
        self.lblTeardropsTips.text = lambda : self.lblTeardropsTipsVar.get()
        self.lblTeardropsTips.place(relx=0.027, rely=0.071, relwidth=0.946, relheight=0.098)
        self.lblhPercentVar = StringVar(value='Horizontal percent')
        self.style.configure('TlblhPercent.TLabel', anchor='e', font=('微软雅黑',10))
        self.lblhPercent = Label(self.tabStrip__Tab5, text='Horizontal percent', textvariable=self.lblhPercentVar, style='TlblhPercent.TLabel')
        self.lblhPercent.setText = lambda x: self.lblhPercentVar.set(x)
        self.lblhPercent.text = lambda : self.lblhPercentVar.get()
        self.lblhPercent.place(relx=0.027, rely=0.261, relwidth=0.258, relheight=0.074)
        self.lblTeardropSegsVar = StringVar(value='Number of segments')
        self.style.configure('TlblTeardropSegs.TLabel', anchor='e', font=('微软雅黑',10))
        self.lblTeardropSegs = Label(self.tabStrip__Tab5, text='Number of segments', textvariable=self.lblTeardropSegsVar, style='TlblTeardropSegs.TLabel')
        self.lblTeardropSegs.setText = lambda x: self.lblTeardropSegsVar.set(x)
        self.lblTeardropSegs.text = lambda : self.lblTeardropSegsVar.get()
        self.lblTeardropSegs.place(relx=0.027, rely=0.499, relwidth=0.258, relheight=0.074)
        self.lblvPercentVar = StringVar(value='Vertical percent')
        self.style.configure('TlblvPercent.TLabel', anchor='e', font=('微软雅黑',10))
        self.lblvPercent = Label(self.tabStrip__Tab5, text='Vertical percent', textvariable=self.lblvPercentVar, style='TlblvPercent.TLabel')
        self.lblvPercent.setText = lambda x: self.lblvPercentVar.set(x)
        self.lblvPercent.text = lambda : self.lblvPercentVar.get()
        self.lblvPercent.place(relx=0.027, rely=0.38, relwidth=0.258, relheight=0.074)
        self.tabStrip.add(self.tabStrip__Tab5, text='  Teardrop    ')

        self.tabStrip__Tab6 = Frame(self.tabStrip)
        self.cmbRoundedTrackTypeList = ['',]
        self.cmbRoundedTrackTypeVar = StringVar(value='')
        self.cmbRoundedTrackType = Combobox(self.tabStrip__Tab6, exportselection=0, state='readonly', textvariable=self.cmbRoundedTrackTypeVar, values=self.cmbRoundedTrackTypeList, font=('微软雅黑',10))
        self.cmbRoundedTrackType.setText = lambda x: self.cmbRoundedTrackTypeVar.set(x)
        self.cmbRoundedTrackType.text = lambda : self.cmbRoundedTrackTypeVar.get()
        self.cmbRoundedTrackType.place(relx=0.27, rely=0.285, relwidth=0.218)
        self.cmbRoundedTrackSmallDistanceList = ['',]
        self.cmbRoundedTrackSmallDistanceVar = StringVar(value='')
        self.cmbRoundedTrackSmallDistance = Combobox(self.tabStrip__Tab6, exportselection=0, textvariable=self.cmbRoundedTrackSmallDistanceVar, values=self.cmbRoundedTrackSmallDistanceList, font=('微软雅黑',10))
        self.cmbRoundedTrackSmallDistance.setText = lambda x: self.cmbRoundedTrackSmallDistanceVar.set(x)
        self.cmbRoundedTrackSmallDistance.text = lambda : self.cmbRoundedTrackSmallDistanceVar.get()
        self.cmbRoundedTrackSmallDistance.place(relx=0.27, rely=0.522, relwidth=0.218)
        self.cmbRoundedTrackSegsList = ['',]
        self.cmbRoundedTrackSegsVar = StringVar(value='')
        self.cmbRoundedTrackSegs = Combobox(self.tabStrip__Tab6, exportselection=0, textvariable=self.cmbRoundedTrackSegsVar, values=self.cmbRoundedTrackSegsList, font=('微软雅黑',10))
        self.cmbRoundedTrackSegs.setText = lambda x: self.cmbRoundedTrackSegsVar.set(x)
        self.cmbRoundedTrackSegs.text = lambda : self.cmbRoundedTrackSegsVar.get()
        self.cmbRoundedTrackSegs.place(relx=0.27, rely=0.641, relwidth=0.218)
        self.cmdRoundedTrackConvertVar = StringVar(value='Convert')
        self.style.configure('TcmdRoundedTrackConvert.TButton', font=('微软雅黑',10))
        self.cmdRoundedTrackConvert = Button(self.tabStrip__Tab6, text='Convert', textvariable=self.cmdRoundedTrackConvertVar, command=self.cmdRoundedTrackConvert_Cmd, style='TcmdRoundedTrackConvert.TButton')
        self.cmdRoundedTrackConvert.setText = lambda x: self.cmdRoundedTrackConvertVar.set(x)
        self.cmdRoundedTrackConvert.text = lambda : self.cmdRoundedTrackConvertVar.get()
        self.cmdRoundedTrackConvert.place(relx=0.135, rely=0.878, relwidth=0.245, relheight=0.089)
        self.cmdRoundedTrackCancelVar = StringVar(value='Cancel')
        self.style.configure('TcmdRoundedTrackCancel.TButton', font=('微软雅黑',10))
        self.cmdRoundedTrackCancel = Button(self.tabStrip__Tab6, text='Cancel', textvariable=self.cmdRoundedTrackCancelVar, command=self.cmdRoundedTrackCancel_Cmd, style='TcmdRoundedTrackCancel.TButton')
        self.cmdRoundedTrackCancel.setText = lambda x: self.cmdRoundedTrackCancelVar.set(x)
        self.cmdRoundedTrackCancel.text = lambda : self.cmdRoundedTrackCancelVar.get()
        self.cmdRoundedTrackCancel.place(relx=0.499, rely=0.878, relwidth=0.245, relheight=0.089)
        self.cmbRoundedTrackBigDistanceList = ['',]
        self.cmbRoundedTrackBigDistanceVar = StringVar(value='')
        self.cmbRoundedTrackBigDistance = Combobox(self.tabStrip__Tab6, exportselection=0, textvariable=self.cmbRoundedTrackBigDistanceVar, values=self.cmbRoundedTrackBigDistanceList, font=('微软雅黑',10))
        self.cmbRoundedTrackBigDistance.setText = lambda x: self.cmbRoundedTrackBigDistanceVar.set(x)
        self.cmbRoundedTrackBigDistance.text = lambda : self.cmbRoundedTrackBigDistanceVar.get()
        self.cmbRoundedTrackBigDistance.place(relx=0.27, rely=0.404, relwidth=0.218)
        self.picRoundedTrack = Canvas(self.tabStrip__Tab6, takefocus=1, highlightthickness=0)
        self.picRoundedTrack.place(relx=0.594, rely=0.261, relwidth=0.379, relheight=0.478)
        self.lblRoundedTrackTypeVar = StringVar(value='Type')
        self.style.configure('TlblRoundedTrackType.TLabel', anchor='e', font=('微软雅黑',10))
        self.lblRoundedTrackType = Label(self.tabStrip__Tab6, text='Type', textvariable=self.lblRoundedTrackTypeVar, style='TlblRoundedTrackType.TLabel')
        self.lblRoundedTrackType.setText = lambda x: self.lblRoundedTrackTypeVar.set(x)
        self.lblRoundedTrackType.text = lambda : self.lblRoundedTrackTypeVar.get()
        self.lblRoundedTrackType.place(relx=0.054, rely=0.285, relwidth=0.204, relheight=0.074)
        self.lblRoundedTrackSmallDVar = StringVar(value='small d(mm)')
        self.style.configure('TlblRoundedTrackSmallD.TLabel', anchor='e', font=('微软雅黑',10))
        self.lblRoundedTrackSmallD = Label(self.tabStrip__Tab6, text='small d(mm)', textvariable=self.lblRoundedTrackSmallDVar, style='TlblRoundedTrackSmallD.TLabel')
        self.lblRoundedTrackSmallD.setText = lambda x: self.lblRoundedTrackSmallDVar.set(x)
        self.lblRoundedTrackSmallD.text = lambda : self.lblRoundedTrackSmallDVar.get()
        self.lblRoundedTrackSmallD.place(relx=0.054, rely=0.522, relwidth=0.204, relheight=0.074)
        self.lblSaveAsRoundedTrackVar = StringVar(value='Save as')
        self.style.configure('TlblSaveAsRoundedTrack.TLabel', anchor='e', foreground='#0000FF', font=('微软雅黑',10,'underline'))
        self.lblSaveAsRoundedTrack = Label(self.tabStrip__Tab6, text='Save as', textvariable=self.lblSaveAsRoundedTrackVar, style='TlblSaveAsRoundedTrack.TLabel')
        self.lblSaveAsRoundedTrack.setText = lambda x: self.lblSaveAsRoundedTrackVar.set(x)
        self.lblSaveAsRoundedTrack.text = lambda : self.lblSaveAsRoundedTrackVar.get()
        self.lblSaveAsRoundedTrack.place(relx=0.782, rely=0.902, relwidth=0.191, relheight=0.074)
        self.lblSaveAsRoundedTrack.bind('<Button-1>', self.lblSaveAsRoundedTrack_Button_1)
        self.lblRoundedTrackBigDVar = StringVar(value='big d(mm)')
        self.style.configure('TlblRoundedTrackBigD.TLabel', anchor='e', font=('微软雅黑',10))
        self.lblRoundedTrackBigD = Label(self.tabStrip__Tab6, text='big d(mm)', textvariable=self.lblRoundedTrackBigDVar, style='TlblRoundedTrackBigD.TLabel')
        self.lblRoundedTrackBigD.setText = lambda x: self.lblRoundedTrackBigDVar.set(x)
        self.lblRoundedTrackBigD.text = lambda : self.lblRoundedTrackBigDVar.get()
        self.lblRoundedTrackBigD.place(relx=0.054, rely=0.404, relwidth=0.204, relheight=0.074)
        self.lblRoundedTrackSegsVar = StringVar(value='Number of segments')
        self.style.configure('TlblRoundedTrackSegs.TLabel', anchor='e', font=('微软雅黑',10))
        self.lblRoundedTrackSegs = Label(self.tabStrip__Tab6, text='Number of segments', textvariable=self.lblRoundedTrackSegsVar, style='TlblRoundedTrackSegs.TLabel')
        self.lblRoundedTrackSegs.setText = lambda x: self.lblRoundedTrackSegsVar.set(x)
        self.lblRoundedTrackSegs.text = lambda : self.lblRoundedTrackSegsVar.get()
        self.lblRoundedTrackSegs.place(relx=0.054, rely=0.641, relwidth=0.204, relheight=0.074)
        self.lblRoundedTrackTipsVar = StringVar(value='Apply to all tracks when deselecting all, otherwise apply to selected tracks only')
        self.style.configure('TlblRoundedTrackTips.TLabel', anchor='center', font=('微软雅黑',10))
        self.lblRoundedTrackTips = Label(self.tabStrip__Tab6, text='Apply to all tracks when deselecting all, otherwise apply to selected tracks only', textvariable=self.lblRoundedTrackTipsVar, style='TlblRoundedTrackTips.TLabel')
        self.lblRoundedTrackTips.setText = lambda x: self.lblRoundedTrackTipsVar.set(x)
        self.lblRoundedTrackTips.text = lambda : self.lblRoundedTrackTipsVar.get()
        self.lblRoundedTrackTips.place(relx=0.027, rely=0.071, relwidth=0.946, relheight=0.098)
        self.tabStrip.add(self.tabStrip__Tab6, text=' RoundedTrack ')

        self.staBar = Statusbar(self.top, panelwidths=(16,))
        self.staBar.pack(side=BOTTOM, fill=X)

    def retranslateUi(self):
        self.master.title(_('sprintFont'))
        self.chkInvertedBackground.setText(_('Inverted Background'))
        self.lblBkPadding.setText(_('Padding'))
        self.lblCapLeft.setText(_('Cap left'))
        self.lblCapRight.setText(_('Cap right'))
        self.cmdOk.setText(_('Ok'))
        self.cmdCancel.setText(_('Cancel'))
        self.lblTxt.setText(_('Text'))
        self.lblLayer.setText(_('Layer'))
        self.lblSmooth.setText(_('Smooth'))
        self.lblWordSpacing.setText(_('Word spacing (mm)'))
        self.LblLineSpacing.setText(_('Line spacing (mm)'))
        self.lblSaveAs.setText(_('Save as'))
        self.lblFont.setText(_('Font'))
        self.lblFontHeight.setText(_('Height (mm)'))
        self.tabStrip.tab(0, text=_('     Font     '))
        self.chkImportFootprintText.setText(_('Import text'))
        self.cmdFootprintFile.setText(_('...'))
        self.cmdOkFootprint.setText(_('Ok'))
        self.cmdCancelFootprint.setText(_('Cancel'))
        self.lblFootprintFile.setText(_('Input'))
        self.lblFootprintTips.setText(_('Currently supports:\n1. Kicad footprint Library : *.kicad_mod\n2. EasyEDA part ID: C + number (C can be omitted)'))
        self.lblSaveAsFootprint.setText(_('Save as'))
        self.tabStrip.tab(1, text=_('   Footprint  '))
        self.cmdCancelSvg.setText(_('Cancel'))
        self.cmdOkSvg.setText(_('Ok'))
        self.cmdSvgFile.setText(_('...'))
        self.lblSvgHeight.setText(_('Height (mm)'))
        self.lblSvgMode.setText(_('Mode'))
        self.lblSvgSmooth.setText(_('Smooth'))
        self.lblSvgLayer.setText(_('Layer'))
        self.lblSaveAsSvg.setText(_('Save as'))
        self.lblSvgTips.setText(_('Note:\nOnly for simple images, may fail to convert complex images'))
        self.tabStrip.tab(2, text=_('  SVG/Qrcode  '))
        self.cmdImportSes.setText(_('Import SES'))
        self.cmdSesFile.setText(_('...'))
        self.cmdCancelAutoRouter.setText(_('Cancel'))
        self.cmdExportDsn.setText(_('Export DSN'))
        self.cmdDsnFile.setText(_('...'))
        self.lblRules.setText(_('Rules'))
        self.lblSesFile.setText(_('Ses file'))
        self.lblSaveAsAutoRouter.setText(_('Save as'))
        self.lblAutoRouterTips.setText(_('Open the exported DSN file with Freerouting for autorouting\nCurrently only supports all components placed on the front side'))
        self.lblDsnFile.setText(_('Dsn file'))
        self.tabStrip.tab(3, text=_('  AutoRouter  '))
        self.cmdRemoveTeardrops.setText(_('Remove'))
        self.cmdCancelTeardrops.setText(_('Cancel'))
        self.cmdAddTeardrops.setText(_('Add'))
        self.lblTeardropPadType.setText(_('Pad type'))
        self.lblTeardropsTips.setText(_('Apply to all pads when deselecting all, otherwise apply to selected pads AND tracks only'))
        self.lblhPercent.setText(_('Horizontal percent'))
        self.lblTeardropSegs.setText(_('Number of segments'))
        self.lblvPercent.setText(_('Vertical percent'))
        self.tabStrip.tab(4, text=_('  Teardrop    '))
        self.cmdRoundedTrackConvert.setText(_('Convert'))
        self.cmdRoundedTrackCancel.setText(_('Cancel'))
        self.lblRoundedTrackType.setText(_('Type'))
        self.lblRoundedTrackSmallD.setText(_('small d(mm)'))
        self.lblSaveAsRoundedTrack.setText(_('Save as'))
        self.lblRoundedTrackBigD.setText(_('big d(mm)'))
        self.lblRoundedTrackSegs.setText(_('Number of segments'))
        self.lblRoundedTrackTips.setText(_('Apply to all tracks when deselecting all, otherwise apply to selected tracks only'))
        self.tabStrip.tab(5, text=_(' RoundedTrack '))

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
        
        self.teardropImage = None
        self.roundedTrackImage = None
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
        
    #多页控件的当前页面发现改变
    def tabStrip_NotebookTabChanged(self, event):
        try:
            tabNo = self.getCurrentTabStripTab()
            if (tabNo == 0):
                self.txtMain.focus_set()
            elif (tabNo == 1):
                self.txtFootprintFile.focus_set()
            elif (tabNo == 2):
                self.txtSvgFile.focus_set()
            elif (tabNo == 3):
                self.txtDsnFile.focus_set()
            elif (tabNo == 4):
                if not self.teardropImage:
                    from teardrop_image import teardropImageData
                    self.teardropImage = PhotoImage(data=teardropImageData)
                    self.picTeardrops.create_image(0, 0, image=self.teardropImage, anchor=NW)
                self.cmbhPercent.focus_set()
            elif (tabNo == 5):
                if not self.roundedTrackImage:
                    from rounded_track_image import roundedTrackImageData, roundedTrackImageDataCn
                    imgData = roundedTrackImageDataCn if self.sysLanguge.startswith('zh') else roundedTrackImageData
                    self.roundedTrackImage = PhotoImage(data=imgData)
                    self.picRoundedTrack.create_image(0, 0, image=self.roundedTrackImage, anchor=NW)
                self.cmbRoundedTrackBigDistance.focus_set()
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
        self.txtMain.bind('<Button-3>', rightClicker, add='')
        self.txtFootprintFile.bind('<Button-3>', rightClicker, add='')
        self.txtSvgFile.bind('<Button-3>', rightClicker, add='')

        #绑定状态栏的双击事件
        self.staBar.lbls[0].bind('<Double-Button-1>', self.staBar_Double_Button_1)

        #导入SES时如果安装Shift点击按钮则弹出菜单，提供更多的导入选择
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

        textIo = SprintTextIO()
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
            extPoly.addAllPoints(cutCircle(cx=minX, cy=maxY-midY, radius=midY, cutNum=cutNum,
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
            extPoly.addAllPoints(cutCircle(cx=maxX, cy=maxY-midY, radius=midY, cutNum=cutNum,
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

    #安装Shift点击导入按钮
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
            newTextIo = SprintTextIO()
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
        tracks = textIo.getConductiveTracks()

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

if __name__ == "__main__":
    top = Tk()
    Application(top).mainloop()

