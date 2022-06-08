#!/usr/bin/env python
#-*- coding:utf-8 -*-
"""
Sprint-Layout v6 2022版的插件，在电路板插入其他字体（包括中文字体）的文字
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
==========================
使用Nuitka打包，Nuitka打包时目录不能有中文名，打包完成后可以
python -m nuitka --standalone --onefile --windows-disable-console --show-progress --plugin-enable=tk-inter --windows-icon-from-ico=./app.ico  sprintFont.py
python -m nuitka --standalone --windows-disable-console --show-progress --plugin-enable=tk-inter --windows-icon-from-ico=./app.ico sprintFont.py
"""
import os, sys, locale, json, threading, queue, datetime, pickle
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
from i18n import I18n
from comm_utils import *
from widget_right_click import rightClicker
from sprint_struct.sprint_textio import SprintTextIO
from lceda_to_sprint import LcComponent
from sprint_struct.sprint_export_dsn import PcbRule, SprintExportDsn

__VERSION__ = "1.3"
__DATE__ = "20220603"
__AUTHOR__ = "cdhigh"

#特定用户的字体目录为：C:\Users\%USERNAME%\AppData\Local\Microsoft\Windows\Fonts
#这里先直接使用系统字体，暂不考虑用户字体
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
        # To center the window on the screen.
        ws = self.master.winfo_screenwidth()
        hs = self.master.winfo_screenheight()
        x = (ws / 2) - (624 / 2)
        y = (hs / 2) - (359 / 2)
        self.master.geometry('%dx%d+%d+%d' % (624,359,x,y))
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
            UPqUXXOWKSRmV7OqORwVcBoUXI68lrRSjcI59OReiKpIQHARZavtttx26y1DAQEAOw="""
        self.iconimg = PhotoImage(data=self.icondata)
        self.master.tk.call('wm', 'iconphoto', self.master._w, self.iconimg)
        self.createWidgets()

    def createWidgets(self):
        self.top = self.winfo_toplevel()

        self.style = Style()

        self.tabStrip = Notebook(self.top)
        self.tabStrip.place(relx=0.026, rely=0.045, relwidth=0.95, relheight=0.872)
        self.tabStrip.bind('<<NotebookTabChanged>>', self.tabStrip_NotebookTabChanged)

        self.tabStrip__Tab1 = Frame(self.tabStrip)
        self.VScroll1 = Scrollbar(self.tabStrip__Tab1, orient='vertical')
        self.VScroll1.place(relx=0.917, rely=0.128, relwidth=0.029, relheight=0.182)
        self.cmbLayerList = ['',]
        self.cmbLayerVar = StringVar(value='')
        self.cmbLayer = Combobox(self.tabStrip__Tab1, state='readonly', textvariable=self.cmbLayerVar, values=self.cmbLayerList, font=('微软雅黑',10))
        self.cmbLayer.setText = lambda x: self.cmbLayerVar.set(x)
        self.cmbLayer.text = lambda : self.cmbLayerVar.get()
        self.cmbLayer.place(relx=0.162, rely=0.511, relwidth=0.352)
        self.txtMainFont = Font(font=('微软雅黑',10))
        self.txtMain = Text(self.tabStrip__Tab1, yscrollcommand=self.VScroll1.set, font=self.txtMainFont)
        self.txtMain.place(relx=0.162, rely=0.128, relwidth=0.757, relheight=0.182)
        self.txtMain.insert('1.0','')
        self.VScroll1['command'] = self.txtMain.yview
        self.cmbSmoothList = ['',]
        self.cmbSmoothVar = StringVar(value='')
        self.cmbSmooth = Combobox(self.tabStrip__Tab1, state='readonly', textvariable=self.cmbSmoothVar, values=self.cmbSmoothList, font=('微软雅黑',10))
        self.cmbSmooth.setText = lambda x: self.cmbSmoothVar.set(x)
        self.cmbSmooth.text = lambda : self.cmbSmoothVar.get()
        self.cmbSmooth.place(relx=0.162, rely=0.639, relwidth=0.352)
        self.cmdOkVar = StringVar(value='Ok')
        self.style.configure('TcmdOk.TButton', font=('微软雅黑',10))
        self.cmdOk = Button(self.tabStrip__Tab1, text='Ok', textvariable=self.cmdOkVar, command=self.cmdOk_Cmd, style='TcmdOk.TButton')
        self.cmdOk.setText = lambda x: self.cmdOkVar.set(x)
        self.cmdOk.text = lambda : self.cmdOkVar.get()
        self.cmdOk.place(relx=0.135, rely=0.818, relwidth=0.245, relheight=0.096)
        self.cmdCancelVar = StringVar(value='Cancel')
        self.style.configure('TcmdCancel.TButton', font=('微软雅黑',10))
        self.cmdCancel = Button(self.tabStrip__Tab1, text='Cancel', textvariable=self.cmdCancelVar, command=self.cmdCancel_Cmd, style='TcmdCancel.TButton')
        self.cmdCancel.setText = lambda x: self.cmdCancelVar.set(x)
        self.cmdCancel.text = lambda : self.cmdCancelVar.get()
        self.cmdCancel.place(relx=0.499, rely=0.818, relwidth=0.245, relheight=0.096)
        self.cmbWordSpacingList = ['',]
        self.cmbWordSpacingVar = StringVar(value='')
        self.cmbWordSpacing = Combobox(self.tabStrip__Tab1, textvariable=self.cmbWordSpacingVar, values=self.cmbWordSpacingList, font=('微软雅黑',10))
        self.cmbWordSpacing.setText = lambda x: self.cmbWordSpacingVar.set(x)
        self.cmbWordSpacing.text = lambda : self.cmbWordSpacingVar.get()
        self.cmbWordSpacing.place(relx=0.782, rely=0.511, relwidth=0.177)
        self.cmbLineSpacingList = ['',]
        self.cmbLineSpacingVar = StringVar(value='')
        self.cmbLineSpacing = Combobox(self.tabStrip__Tab1, textvariable=self.cmbLineSpacingVar, values=self.cmbLineSpacingList, font=('微软雅黑',10))
        self.cmbLineSpacing.setText = lambda x: self.cmbLineSpacingVar.set(x)
        self.cmbLineSpacing.text = lambda : self.cmbLineSpacingVar.get()
        self.cmbLineSpacing.place(relx=0.782, rely=0.639, relwidth=0.177)
        self.cmbFontHeightList = ['',]
        self.cmbFontHeightVar = StringVar(value='')
        self.cmbFontHeight = Combobox(self.tabStrip__Tab1, textvariable=self.cmbFontHeightVar, values=self.cmbFontHeightList, font=('微软雅黑',10))
        self.cmbFontHeight.setText = lambda x: self.cmbFontHeightVar.set(x)
        self.cmbFontHeight.text = lambda : self.cmbFontHeightVar.get()
        self.cmbFontHeight.place(relx=0.782, rely=0.383, relwidth=0.177)
        self.cmbFontList = ['',]
        self.cmbFontVar = StringVar(value='')
        self.cmbFont = Combobox(self.tabStrip__Tab1, state='readonly', textvariable=self.cmbFontVar, values=self.cmbFontList, font=('微软雅黑',10))
        self.cmbFont.setText = lambda x: self.cmbFontVar.set(x)
        self.cmbFont.text = lambda : self.cmbFontVar.get()
        self.cmbFont.place(relx=0.162, rely=0.383, relwidth=0.352)
        self.lblTxtVar = StringVar(value='Text')
        self.style.configure('TlblTxt.TLabel', anchor='e', font=('微软雅黑',10))
        self.lblTxt = Label(self.tabStrip__Tab1, text='Text', textvariable=self.lblTxtVar, style='TlblTxt.TLabel')
        self.lblTxt.setText = lambda x: self.lblTxtVar.set(x)
        self.lblTxt.text = lambda : self.lblTxtVar.get()
        self.lblTxt.place(relx=0.027, rely=0.128, relwidth=0.11, relheight=0.08)
        self.lblLayerVar = StringVar(value='Layer')
        self.style.configure('TlblLayer.TLabel', anchor='e', font=('微软雅黑',10))
        self.lblLayer = Label(self.tabStrip__Tab1, text='Layer', textvariable=self.lblLayerVar, style='TlblLayer.TLabel')
        self.lblLayer.setText = lambda x: self.lblLayerVar.set(x)
        self.lblLayer.text = lambda : self.lblLayerVar.get()
        self.lblLayer.place(relx=0.027, rely=0.511, relwidth=0.11, relheight=0.08)
        self.lblSmoothVar = StringVar(value='Smooth')
        self.style.configure('TlblSmooth.TLabel', anchor='e', font=('微软雅黑',10))
        self.lblSmooth = Label(self.tabStrip__Tab1, text='Smooth', textvariable=self.lblSmoothVar, style='TlblSmooth.TLabel')
        self.lblSmooth.setText = lambda x: self.lblSmoothVar.set(x)
        self.lblSmooth.text = lambda : self.lblSmoothVar.get()
        self.lblSmooth.place(relx=0.027, rely=0.639, relwidth=0.11, relheight=0.08)
        self.lblWordSpacingVar = StringVar(value='Word spacing (mm)')
        self.style.configure('TlblWordSpacing.TLabel', anchor='e', font=('微软雅黑',10))
        self.lblWordSpacing = Label(self.tabStrip__Tab1, text='Word spacing (mm)', textvariable=self.lblWordSpacingVar, style='TlblWordSpacing.TLabel')
        self.lblWordSpacing.setText = lambda x: self.lblWordSpacingVar.set(x)
        self.lblWordSpacing.text = lambda : self.lblWordSpacingVar.get()
        self.lblWordSpacing.place(relx=0.526, rely=0.511, relwidth=0.245, relheight=0.08)
        self.LblLineSpacingVar = StringVar(value='Line spacing (mm)')
        self.style.configure('TLblLineSpacing.TLabel', anchor='e', font=('微软雅黑',10))
        self.LblLineSpacing = Label(self.tabStrip__Tab1, text='Line spacing (mm)', textvariable=self.LblLineSpacingVar, style='TLblLineSpacing.TLabel')
        self.LblLineSpacing.setText = lambda x: self.LblLineSpacingVar.set(x)
        self.LblLineSpacing.text = lambda : self.LblLineSpacingVar.get()
        self.LblLineSpacing.place(relx=0.526, rely=0.639, relwidth=0.245, relheight=0.08)
        self.lblSaveAsVar = StringVar(value='Save as')
        self.style.configure('TlblSaveAs.TLabel', anchor='w', foreground='#0000FF', font=('微软雅黑',10,'underline'))
        self.lblSaveAs = Label(self.tabStrip__Tab1, text='Save as', textvariable=self.lblSaveAsVar, style='TlblSaveAs.TLabel')
        self.lblSaveAs.setText = lambda x: self.lblSaveAsVar.set(x)
        self.lblSaveAs.text = lambda : self.lblSaveAsVar.get()
        self.lblSaveAs.place(relx=0.877, rely=0.843, relwidth=0.11, relheight=0.08)
        self.lblSaveAs.bind('<Button-1>', self.lblSaveAs_Button_1)
        self.lblFontVar = StringVar(value='Font')
        self.style.configure('TlblFont.TLabel', anchor='e', font=('微软雅黑',10))
        self.lblFont = Label(self.tabStrip__Tab1, text='Font', textvariable=self.lblFontVar, style='TlblFont.TLabel')
        self.lblFont.setText = lambda x: self.lblFontVar.set(x)
        self.lblFont.text = lambda : self.lblFontVar.get()
        self.lblFont.place(relx=0.027, rely=0.383, relwidth=0.11, relheight=0.08)
        self.lblFontHeightVar = StringVar(value='Height (mm)')
        self.style.configure('TlblFontHeight.TLabel', anchor='e', font=('微软雅黑',10))
        self.lblFontHeight = Label(self.tabStrip__Tab1, text='Height (mm)', textvariable=self.lblFontHeightVar, style='TlblFontHeight.TLabel')
        self.lblFontHeight.setText = lambda x: self.lblFontHeightVar.set(x)
        self.lblFontHeight.text = lambda : self.lblFontHeightVar.get()
        self.lblFontHeight.place(relx=0.526, rely=0.383, relwidth=0.245, relheight=0.08)
        self.tabStrip.add(self.tabStrip__Tab1, text='Font')

        self.tabStrip__Tab2 = Frame(self.tabStrip)
        self.chkImportFootprintTextVar = IntVar(value=1)
        self.style.configure('TchkImportFootprintText.TCheckbutton', font=('微软雅黑',10))
        self.chkImportFootprintText = Checkbutton(self.tabStrip__Tab2, text='Import text', variable=self.chkImportFootprintTextVar, style='TchkImportFootprintText.TCheckbutton')
        self.chkImportFootprintText.setValue = lambda x: self.chkImportFootprintTextVar.set(x)
        self.chkImportFootprintText.value = lambda : self.chkImportFootprintTextVar.get()
        self.chkImportFootprintText.place(relx=0.175, rely=0.613, relwidth=0.339, relheight=0.08)
        self.cmdFootprintFileVar = StringVar(value='...')
        self.style.configure('TcmdFootprintFile.TButton', font=('Arial',9))
        self.cmdFootprintFile = Button(self.tabStrip__Tab2, text='...', textvariable=self.cmdFootprintFileVar, command=self.cmdFootprintFile_Cmd, style='TcmdFootprintFile.TButton')
        self.cmdFootprintFile.setText = lambda x: self.cmdFootprintFileVar.set(x)
        self.cmdFootprintFile.text = lambda : self.cmdFootprintFileVar.get()
        self.cmdFootprintFile.place(relx=0.917, rely=0.46, relwidth=0.056, relheight=0.08)
        self.txtFootprintFileVar = StringVar(value='')
        self.txtFootprintFile = Entry(self.tabStrip__Tab2, textvariable=self.txtFootprintFileVar, font=('微软雅黑',10))
        self.txtFootprintFile.setText = lambda x: self.txtFootprintFileVar.set(x)
        self.txtFootprintFile.text = lambda : self.txtFootprintFileVar.get()
        self.txtFootprintFile.place(relx=0.175, rely=0.46, relwidth=0.73, relheight=0.089)
        self.cmdOkFootprintVar = StringVar(value='Ok')
        self.style.configure('TcmdOkFootprint.TButton', font=('微软雅黑',10))
        self.cmdOkFootprint = Button(self.tabStrip__Tab2, text='Ok', textvariable=self.cmdOkFootprintVar, command=self.cmdOkFootprint_Cmd, style='TcmdOkFootprint.TButton')
        self.cmdOkFootprint.setText = lambda x: self.cmdOkFootprintVar.set(x)
        self.cmdOkFootprint.text = lambda : self.cmdOkFootprintVar.get()
        self.cmdOkFootprint.place(relx=0.135, rely=0.818, relwidth=0.245, relheight=0.096)
        self.cmdCancelFootprintVar = StringVar(value='Cancel')
        self.style.configure('TcmdCancelFootprint.TButton', font=('微软雅黑',10))
        self.cmdCancelFootprint = Button(self.tabStrip__Tab2, text='Cancel', textvariable=self.cmdCancelFootprintVar, command=self.cmdCancelFootprint_Cmd, style='TcmdCancelFootprint.TButton')
        self.cmdCancelFootprint.setText = lambda x: self.cmdCancelFootprintVar.set(x)
        self.cmdCancelFootprint.text = lambda : self.cmdCancelFootprintVar.get()
        self.cmdCancelFootprint.place(relx=0.499, rely=0.818, relwidth=0.245, relheight=0.096)
        self.lblFootprintFileVar = StringVar(value='Input')
        self.style.configure('TlblFootprintFile.TLabel', anchor='e', font=('微软雅黑',10))
        self.lblFootprintFile = Label(self.tabStrip__Tab2, text='Input', textvariable=self.lblFootprintFileVar, style='TlblFootprintFile.TLabel')
        self.lblFootprintFile.setText = lambda x: self.lblFootprintFileVar.set(x)
        self.lblFootprintFile.text = lambda : self.lblFootprintFileVar.get()
        self.lblFootprintFile.place(relx=0.027, rely=0.46, relwidth=0.11, relheight=0.08)
        self.lblFootprintTipsVar = StringVar(value='Footprint_features_tips')
        self.style.configure('TlblFootprintTips.TLabel', anchor='w', font=('微软雅黑',10))
        self.lblFootprintTips = Label(self.tabStrip__Tab2, text='Footprint_features_tips', textvariable=self.lblFootprintTipsVar, style='TlblFootprintTips.TLabel')
        self.lblFootprintTips.setText = lambda x: self.lblFootprintTipsVar.set(x)
        self.lblFootprintTips.text = lambda : self.lblFootprintTipsVar.get()
        self.lblFootprintTips.place(relx=0.175, rely=0.077, relwidth=0.771, relheight=0.335)
        self.lblSaveAsFootprintVar = StringVar(value='Save as')
        self.style.configure('TlblSaveAsFootprint.TLabel', anchor='w', foreground='#0000FF', font=('微软雅黑',10,'underline'))
        self.lblSaveAsFootprint = Label(self.tabStrip__Tab2, text='Save as', textvariable=self.lblSaveAsFootprintVar, style='TlblSaveAsFootprint.TLabel')
        self.lblSaveAsFootprint.setText = lambda x: self.lblSaveAsFootprintVar.set(x)
        self.lblSaveAsFootprint.text = lambda : self.lblSaveAsFootprintVar.get()
        self.lblSaveAsFootprint.place(relx=0.877, rely=0.843, relwidth=0.11, relheight=0.08)
        self.lblSaveAsFootprint.bind('<Button-1>', self.lblSaveAsFootprint_Button_1)
        self.tabStrip.add(self.tabStrip__Tab2, text='Footprint')

        self.tabStrip__Tab3 = Frame(self.tabStrip)
        self.cmbSvgQrcodeList = ['',]
        self.cmbSvgQrcodeVar = StringVar(value='')
        self.cmbSvgQrcode = Combobox(self.tabStrip__Tab3, state='readonly', justify='right', textvariable=self.cmbSvgQrcodeVar, values=self.cmbSvgQrcodeList, font=('微软雅黑',10))
        self.cmbSvgQrcode.setText = lambda x: self.cmbSvgQrcodeVar.set(x)
        self.cmbSvgQrcode.text = lambda : self.cmbSvgQrcodeVar.get()
        self.cmbSvgQrcode.place(relx=0.013, rely=0.319, relwidth=0.164)
        self.cmbSvgModeList = ['',]
        self.cmbSvgModeVar = StringVar(value='')
        self.cmbSvgMode = Combobox(self.tabStrip__Tab3, state='readonly', textvariable=self.cmbSvgModeVar, values=self.cmbSvgModeList, font=('微软雅黑',10))
        self.cmbSvgMode.setText = lambda x: self.cmbSvgModeVar.set(x)
        self.cmbSvgMode.text = lambda : self.cmbSvgModeVar.get()
        self.cmbSvgMode.place(relx=0.175, rely=0.46, relwidth=0.352)
        self.cmbSvgHeightList = ['',]
        self.cmbSvgHeightVar = StringVar(value='')
        self.cmbSvgHeight = Combobox(self.tabStrip__Tab3, textvariable=self.cmbSvgHeightVar, values=self.cmbSvgHeightList, font=('微软雅黑',10))
        self.cmbSvgHeight.setText = lambda x: self.cmbSvgHeightVar.set(x)
        self.cmbSvgHeight.text = lambda : self.cmbSvgHeightVar.get()
        self.cmbSvgHeight.place(relx=0.728, rely=0.46, relwidth=0.245)
        self.cmbSvgSmoothList = ['',]
        self.cmbSvgSmoothVar = StringVar(value='')
        self.cmbSvgSmooth = Combobox(self.tabStrip__Tab3, state='readonly', textvariable=self.cmbSvgSmoothVar, values=self.cmbSvgSmoothList, font=('微软雅黑',10))
        self.cmbSvgSmooth.setText = lambda x: self.cmbSvgSmoothVar.set(x)
        self.cmbSvgSmooth.text = lambda : self.cmbSvgSmoothVar.get()
        self.cmbSvgSmooth.place(relx=0.728, rely=0.588, relwidth=0.245)
        self.cmbSvgLayerList = ['',]
        self.cmbSvgLayerVar = StringVar(value='')
        self.cmbSvgLayer = Combobox(self.tabStrip__Tab3, state='readonly', textvariable=self.cmbSvgLayerVar, values=self.cmbSvgLayerList, font=('微软雅黑',10))
        self.cmbSvgLayer.setText = lambda x: self.cmbSvgLayerVar.set(x)
        self.cmbSvgLayer.text = lambda : self.cmbSvgLayerVar.get()
        self.cmbSvgLayer.place(relx=0.175, rely=0.588, relwidth=0.352)
        self.cmdCancelSvgVar = StringVar(value='Cancel')
        self.style.configure('TcmdCancelSvg.TButton', font=('微软雅黑',10))
        self.cmdCancelSvg = Button(self.tabStrip__Tab3, text='Cancel', textvariable=self.cmdCancelSvgVar, command=self.cmdCancelSvg_Cmd, style='TcmdCancelSvg.TButton')
        self.cmdCancelSvg.setText = lambda x: self.cmdCancelSvgVar.set(x)
        self.cmdCancelSvg.text = lambda : self.cmdCancelSvgVar.get()
        self.cmdCancelSvg.place(relx=0.499, rely=0.818, relwidth=0.245, relheight=0.096)
        self.cmdOkSvgVar = StringVar(value='Ok')
        self.style.configure('TcmdOkSvg.TButton', font=('微软雅黑',10))
        self.cmdOkSvg = Button(self.tabStrip__Tab3, text='Ok', textvariable=self.cmdOkSvgVar, command=self.cmdOkSvg_Cmd, style='TcmdOkSvg.TButton')
        self.cmdOkSvg.setText = lambda x: self.cmdOkSvgVar.set(x)
        self.cmdOkSvg.text = lambda : self.cmdOkSvgVar.get()
        self.cmdOkSvg.place(relx=0.135, rely=0.818, relwidth=0.245, relheight=0.096)
        self.txtSvgFileVar = StringVar(value='')
        self.txtSvgFile = Entry(self.tabStrip__Tab3, textvariable=self.txtSvgFileVar, font=('微软雅黑',10))
        self.txtSvgFile.setText = lambda x: self.txtSvgFileVar.set(x)
        self.txtSvgFile.text = lambda : self.txtSvgFileVar.get()
        self.txtSvgFile.place(relx=0.175, rely=0.319, relwidth=0.73, relheight=0.089)
        self.cmdSvgFileVar = StringVar(value='...')
        self.style.configure('TcmdSvgFile.TButton', font=('Arial',9))
        self.cmdSvgFile = Button(self.tabStrip__Tab3, text='...', textvariable=self.cmdSvgFileVar, command=self.cmdSvgFile_Cmd, style='TcmdSvgFile.TButton')
        self.cmdSvgFile.setText = lambda x: self.cmdSvgFileVar.set(x)
        self.cmdSvgFile.text = lambda : self.cmdSvgFileVar.get()
        self.cmdSvgFile.place(relx=0.917, rely=0.319, relwidth=0.056, relheight=0.08)
        self.lblSvgHeightVar = StringVar(value='Height (mm)')
        self.style.configure('TlblSvgHeight.TLabel', anchor='e', font=('微软雅黑',10))
        self.lblSvgHeight = Label(self.tabStrip__Tab3, text='Height (mm)', textvariable=self.lblSvgHeightVar, style='TlblSvgHeight.TLabel')
        self.lblSvgHeight.setText = lambda x: self.lblSvgHeightVar.set(x)
        self.lblSvgHeight.text = lambda : self.lblSvgHeightVar.get()
        self.lblSvgHeight.place(relx=0.526, rely=0.46, relwidth=0.191, relheight=0.08)
        self.lblSvgModeVar = StringVar(value='Mode')
        self.style.configure('TlblSvgMode.TLabel', anchor='e', font=('微软雅黑',10))
        self.lblSvgMode = Label(self.tabStrip__Tab3, text='Mode', textvariable=self.lblSvgModeVar, style='TlblSvgMode.TLabel')
        self.lblSvgMode.setText = lambda x: self.lblSvgModeVar.set(x)
        self.lblSvgMode.text = lambda : self.lblSvgModeVar.get()
        self.lblSvgMode.place(relx=0.04, rely=0.46, relwidth=0.11, relheight=0.08)
        self.lblSvgSmoothVar = StringVar(value='Smooth')
        self.style.configure('TlblSvgSmooth.TLabel', anchor='e', font=('微软雅黑',10))
        self.lblSvgSmooth = Label(self.tabStrip__Tab3, text='Smooth', textvariable=self.lblSvgSmoothVar, style='TlblSvgSmooth.TLabel')
        self.lblSvgSmooth.setText = lambda x: self.lblSvgSmoothVar.set(x)
        self.lblSvgSmooth.text = lambda : self.lblSvgSmoothVar.get()
        self.lblSvgSmooth.place(relx=0.526, rely=0.588, relwidth=0.191, relheight=0.08)
        self.lblSvgLayerVar = StringVar(value='Layer')
        self.style.configure('TlblSvgLayer.TLabel', anchor='e', font=('微软雅黑',10))
        self.lblSvgLayer = Label(self.tabStrip__Tab3, text='Layer', textvariable=self.lblSvgLayerVar, style='TlblSvgLayer.TLabel')
        self.lblSvgLayer.setText = lambda x: self.lblSvgLayerVar.set(x)
        self.lblSvgLayer.text = lambda : self.lblSvgLayerVar.get()
        self.lblSvgLayer.place(relx=0.04, rely=0.588, relwidth=0.11, relheight=0.08)
        self.lblSaveAsSvgVar = StringVar(value='Save as')
        self.style.configure('TlblSaveAsSvg.TLabel', anchor='w', foreground='#0000FF', font=('微软雅黑',10,'underline'))
        self.lblSaveAsSvg = Label(self.tabStrip__Tab3, text='Save as', textvariable=self.lblSaveAsSvgVar, style='TlblSaveAsSvg.TLabel')
        self.lblSaveAsSvg.setText = lambda x: self.lblSaveAsSvgVar.set(x)
        self.lblSaveAsSvg.text = lambda : self.lblSaveAsSvgVar.get()
        self.lblSaveAsSvg.place(relx=0.877, rely=0.843, relwidth=0.11, relheight=0.08)
        self.lblSaveAsSvg.bind('<Button-1>', self.lblSaveAsSvg_Button_1)
        self.lblSvgTipsVar = StringVar(value='svg_features_tips')
        self.style.configure('TlblSvgTips.TLabel', anchor='w', font=('微软雅黑',10))
        self.lblSvgTips = Label(self.tabStrip__Tab3, text='svg_features_tips', textvariable=self.lblSvgTipsVar, style='TlblSvgTips.TLabel')
        self.lblSvgTips.setText = lambda x: self.lblSvgTipsVar.set(x)
        self.lblSvgTips.text = lambda : self.lblSvgTipsVar.get()
        self.lblSvgTips.place(relx=0.175, rely=0.077, relwidth=0.771, relheight=0.208)
        self.tabStrip.add(self.tabStrip__Tab3, text='SVG')

        self.tabStrip__Tab4 = Frame(self.tabStrip)
        self.VSrlRules = Scrollbar(self.tabStrip__Tab4, orient='vertical')
        self.VSrlRules.place(relx=0.904, rely=0.46, relwidth=0.029, relheight=0.31)
        self.style.configure('TtreRules.Treeview', font=('微软雅黑',10))
        self.treRules = Treeview(self.tabStrip__Tab4, show='tree', yscrollcommand=self.VSrlRules.set, style='TtreRules.Treeview')
        self.treRules.place(relx=0.175, rely=0.46, relwidth=0.73, relheight=0.31)
        self.treRules.bind('<Double-Button-1>', self.treRules_Double_Button_1)
        self.VSrlRules['command'] = self.treRules.yview
        self.cmdImportSesVar = StringVar(value='Import')
        self.style.configure('TcmdImportSes.TButton', font=('微软雅黑',10))
        self.cmdImportSes = Button(self.tabStrip__Tab4, text='Import', textvariable=self.cmdImportSesVar, command=self.cmdImportSes_Cmd, style='TcmdImportSes.TButton')
        self.cmdImportSes.setText = lambda x: self.cmdImportSesVar.set(x)
        self.cmdImportSes.text = lambda : self.cmdImportSesVar.get()
        self.cmdImportSes.place(relx=0.31, rely=0.818, relwidth=0.204, relheight=0.096)
        self.txtSesFileVar = StringVar(value='')
        self.txtSesFile = Entry(self.tabStrip__Tab4, textvariable=self.txtSesFileVar, font=('微软雅黑',10))
        self.txtSesFile.setText = lambda x: self.txtSesFileVar.set(x)
        self.txtSesFile.text = lambda : self.txtSesFileVar.get()
        self.txtSesFile.place(relx=0.175, rely=0.358, relwidth=0.73, relheight=0.089)
        self.cmdSesFileVar = StringVar(value='...')
        self.style.configure('TcmdSesFile.TButton', font=('Arial',9))
        self.cmdSesFile = Button(self.tabStrip__Tab4, text='...', textvariable=self.cmdSesFileVar, command=self.cmdSesFile_Cmd, style='TcmdSesFile.TButton')
        self.cmdSesFile.setText = lambda x: self.cmdSesFileVar.set(x)
        self.cmdSesFile.text = lambda : self.cmdSesFileVar.get()
        self.cmdSesFile.place(relx=0.917, rely=0.358, relwidth=0.056, relheight=0.08)
        self.cmdCancelAutoRouterVar = StringVar(value='Cancel')
        self.style.configure('TcmdCancelAutoRouter.TButton', font=('微软雅黑',10))
        self.cmdCancelAutoRouter = Button(self.tabStrip__Tab4, text='Cancel', textvariable=self.cmdCancelAutoRouterVar, command=self.cmdCancelAutoRouter_Cmd, style='TcmdCancelAutoRouter.TButton')
        self.cmdCancelAutoRouter.setText = lambda x: self.cmdCancelAutoRouterVar.set(x)
        self.cmdCancelAutoRouter.text = lambda : self.cmdCancelAutoRouterVar.get()
        self.cmdCancelAutoRouter.place(relx=0.58, rely=0.818, relwidth=0.204, relheight=0.096)
        self.cmdExportDsnVar = StringVar(value='Export')
        self.style.configure('TcmdExportDsn.TButton', font=('微软雅黑',10))
        self.cmdExportDsn = Button(self.tabStrip__Tab4, text='Export', textvariable=self.cmdExportDsnVar, command=self.cmdExportDsn_Cmd, style='TcmdExportDsn.TButton')
        self.cmdExportDsn.setText = lambda x: self.cmdExportDsnVar.set(x)
        self.cmdExportDsn.text = lambda : self.cmdExportDsnVar.get()
        self.cmdExportDsn.place(relx=0.04, rely=0.818, relwidth=0.204, relheight=0.096)
        self.txtDsnFileVar = StringVar(value='')
        self.txtDsnFile = Entry(self.tabStrip__Tab4, textvariable=self.txtDsnFileVar, font=('微软雅黑',10))
        self.txtDsnFile.setText = lambda x: self.txtDsnFileVar.set(x)
        self.txtDsnFile.text = lambda : self.txtDsnFileVar.get()
        self.txtDsnFile.place(relx=0.175, rely=0.256, relwidth=0.73, relheight=0.089)
        self.cmdDsnFileVar = StringVar(value='...')
        self.style.configure('TcmdDsnFile.TButton', font=('Arial',9))
        self.cmdDsnFile = Button(self.tabStrip__Tab4, text='...', textvariable=self.cmdDsnFileVar, command=self.cmdDsnFile_Cmd, style='TcmdDsnFile.TButton')
        self.cmdDsnFile.setText = lambda x: self.cmdDsnFileVar.set(x)
        self.cmdDsnFile.text = lambda : self.cmdDsnFileVar.get()
        self.cmdDsnFile.place(relx=0.917, rely=0.256, relwidth=0.056, relheight=0.08)
        self.lblRulesVar = StringVar(value='Rules')
        self.style.configure('TlblRules.TLabel', anchor='e', font=('微软雅黑',10))
        self.lblRules = Label(self.tabStrip__Tab4, text='Rules', textvariable=self.lblRulesVar, style='TlblRules.TLabel')
        self.lblRules.setText = lambda x: self.lblRulesVar.set(x)
        self.lblRules.text = lambda : self.lblRulesVar.get()
        self.lblRules.place(relx=0.027, rely=0.511, relwidth=0.11, relheight=0.08)
        self.lblSesFileVar = StringVar(value='Ses file')
        self.style.configure('TlblSesFile.TLabel', anchor='e', font=('微软雅黑',10))
        self.lblSesFile = Label(self.tabStrip__Tab4, text='Ses file', textvariable=self.lblSesFileVar, style='TlblSesFile.TLabel')
        self.lblSesFile.setText = lambda x: self.lblSesFileVar.set(x)
        self.lblSesFile.text = lambda : self.lblSesFileVar.get()
        self.lblSesFile.place(relx=0.027, rely=0.358, relwidth=0.11, relheight=0.08)
        self.lblSaveAsAutoRouterVar = StringVar(value='Save as')
        self.style.configure('TlblSaveAsAutoRouter.TLabel', anchor='w', foreground='#0000FF', font=('微软雅黑',10,'underline'))
        self.lblSaveAsAutoRouter = Label(self.tabStrip__Tab4, text='Save as', textvariable=self.lblSaveAsAutoRouterVar, style='TlblSaveAsAutoRouter.TLabel')
        self.lblSaveAsAutoRouter.setText = lambda x: self.lblSaveAsAutoRouterVar.set(x)
        self.lblSaveAsAutoRouter.text = lambda : self.lblSaveAsAutoRouterVar.get()
        self.lblSaveAsAutoRouter.place(relx=0.877, rely=0.843, relwidth=0.11, relheight=0.08)
        self.lblSaveAsAutoRouter.bind('<Button-1>', self.lblSaveAsAutoRouter_Button_1)
        self.lblAutoRouterTipsVar = StringVar(value='AutoRouter_features_tips')
        self.style.configure('TlblAutoRouterTips.TLabel', anchor='w', font=('微软雅黑',10))
        self.lblAutoRouterTips = Label(self.tabStrip__Tab4, text='AutoRouter_features_tips', textvariable=self.lblAutoRouterTipsVar, style='TlblAutoRouterTips.TLabel')
        self.lblAutoRouterTips.setText = lambda x: self.lblAutoRouterTipsVar.set(x)
        self.lblAutoRouterTips.text = lambda : self.lblAutoRouterTipsVar.get()
        self.lblAutoRouterTips.place(relx=0.175, rely=0.051, relwidth=0.771, relheight=0.182)
        self.lblDsnFileVar = StringVar(value='Dsn file')
        self.style.configure('TlblDsnFile.TLabel', anchor='e', font=('微软雅黑',10))
        self.lblDsnFile = Label(self.tabStrip__Tab4, text='Dsn file', textvariable=self.lblDsnFileVar, style='TlblDsnFile.TLabel')
        self.lblDsnFile.setText = lambda x: self.lblDsnFileVar.set(x)
        self.lblDsnFile.text = lambda : self.lblDsnFileVar.get()
        self.lblDsnFile.place(relx=0.027, rely=0.256, relwidth=0.11, relheight=0.08)
        self.tabStrip.add(self.tabStrip__Tab4, text='AutoRouter')

        self.staBar = Statusbar(self.top, panelwidths=(16,))
        self.staBar.pack(side=BOTTOM, fill=X)

class Application(Application_ui):
    #这个类实现具体的事件处理回调函数。界面生成代码在Application_ui中。
    def __init__(self, master=None):
        Application_ui.__init__(self, master)
        self.master.title('sprintFont v{} [github.com/cdhigh]'.format(__VERSION__))
        width = str_to_int(self.master.geometry().split('x')[0])
        if (width > 16): #状态栏仅使用一个分栏，占满全部空间
            self.staBar.panelwidth(0, width)

        self.versionJson = {} #用来更新版本使用
        self.checkUpdateFrequency = 30
        self.lastCheckUpdate = None
        self.skipVersion = ''
        self.easyEdaSite = ''

        self.txtDsnFile.setText(r'C:/Users/su/Desktop/testSprint/dsnex.dsn') #TODO

        #这三行代码是修正python3.7的treeview颜色设置不生效的BUG，其他版本可能不需要
        #fixed_map = lambda op: [elm for elm in style.map("Treeview", query_opt=op) if elm[:2] != ("!disabled", "!selected")]
        #style = Style() #in ttk package
        #style.map("Treeview", foreground=fixed_map("foreground"), background=fixed_map("background"))

        self.treRules.configure(columns=['Item', 'Value'])
        self.treRules.configure(show='') #'headings'
        self.treRules.configure(selectmode='browse') #只允许单行选择
        #self.treRules.tag_configure('gray_row', background='#cccccc')

        #初始化多语种支持
        self.sysLanguge = locale.getdefaultlocale()[0]
        I18n.init()
        I18n.setLanguage(self.sysLanguge)
        self.language = ''

        self.pcbRule = PcbRule()

        #读取配置文件到内存
        self.cfg = {}
        if os.path.exists(CFG_FILENAME):
            try:
                with open(CFG_FILENAME, 'r', encoding='utf-8') as f:
                    self.cfg = json.loads(f.read())
            except:
                pass

        #支持手动选择语种，语种配置需要在填充控件前完成
        if isinstance(self.cfg, dict):
            lang = self.cfg.get('language', '')
            if lang and I18n.langIsSupported(lang):
                self.language = lang
                I18n.setLanguage(lang)
        
        #绑定额外的事件处理函数
        self.bindWidgetEvents()
        
        self.populateWidgets()
        self.restoreConfig()
        self.translateWidgets()

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
        
        #self.inFileName = self.inFileName.replace('su', 'Adminstrator') #TODO

        #输出文件名为输入文件名加一个 "_out"
        if self.inFileName:
            inExts = os.path.splitext(self.inFileName)
            self.outFileName = '{}_out{}'.format(inExts[0], inExts[1] if (len(inExts) > 1) else '')
            if not self.pcbAll:
                self.cmdExportDsn.configure(state='disabled')
                self.cmdImportSes.configure(state='disabled')
                self.lblAutoRouterTips.setText(_("Please deselect all items before launching the plugin"))
        else: #单独执行
            self.cmdOk.configure(state='disabled')
            self.cmdOkFootprint.configure(state='disabled')
            self.cmdOkSvg.configure(state='disabled')
            #self.cmdExportDsn.configure(state='disabled') TODO
            self.cmdImportSes.configure(state='disabled')
            
        #显示输入文件名或显示单独执行模式字符串
        self.setStaBarByMode()

        #版本更新检查，启动5s后检查一次更新
        self.master.after(5000, self.periodicCheckUpdate)

        self.txtMain.focus_set()

    #显示输入文件名或显示单独执行模式字符串
    def setStaBarByMode(self):
        self.staBar.text(_("  In: {}").format(self.inFileName) if self.inFileName else _("  Standalone mode"))

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
        except:
            pass

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

        #导入SES时如果安装Shift则仅导入布线
        #self.cmdImportSes.bind('<Shift-Button-1>', self.cmdImportSes_Shift_Button_1)
        self.mnuImportSes = Menu(self.master, tearoff=0)
        self.mnuImportSes.add_command(label=_("Import all (without RATSNEST)"), command=partial(self.cmdmnuImportSes, withRatsnest=False, trackOnly=False))
        self.mnuImportSes.add_command(label=_("Import all (with RATSNEST)"), command=partial(self.cmdmnuImportSes, withRatsnest=True, trackOnly=False))
        self.mnuImportSes.add_command(label=_("Import auto-routed tracks only"), command=partial(self.cmdmnuImportSes, withRatsnest=False, trackOnly=True))

    #翻译界面字符串，为了能方便修改界面，等界面初始化完成后再统一修改
    def translateWidgets(self):
        self.cmdOk.setText(_("Ok"))
        self.cmdOkFootprint.setText(_("Ok"))
        self.cmdOkSvg.setText(_("Ok"))
        self.cmdCancel.setText(_("Cancel"))
        self.cmdCancelFootprint.setText(_("Cancel"))
        self.cmdCancelSvg.setText(_("Cancel"))
        self.lblSaveAs.setText(_("Save as"))
        self.lblSaveAsFootprint.setText(_("Save as"))
        self.lblSaveAsSvg.setText(_("Save as"))
        self.lblFont.setText(_("Font"))
        self.lblTxt.setText(_("Text"))
        self.lblLayer.setText(_("Layer"))
        self.lblSmooth.setText(_("Smooth"))
        self.lblFontHeight.setText(_("Height (mm)"))
        self.lblWordSpacing.setText(_("Word spacing (mm)"))
        self.LblLineSpacing.setText(_("Line spacing (mm)"))
        self.lblFootprintFile.setText(_("Input"))
        self.tabStrip.tab(0, text=_("TabFont"))
        self.tabStrip.tab(1, text=_("TabFootprint"))
        self.tabStrip.tab(2, text=_("TabSVG"))
        self.tabStrip.tab(3, text=_("TabAutoRouter"))
        self.lblFootprintTips.setText(_("Footprint_features_tips"))
        self.chkImportFootprintText.configure(text=_("Import text"))
        self.lblSvgTips.setText(_("svg_features_tips"))
        self.lblSvgMode.setText(_("Mode"))
        self.lblSvgHeight.setText(_("svgHeight"))
        self.lblSvgLayer.setText(_("Layer"))
        self.lblSvgSmooth.setText(_("Smooth"))
        self.lblAutoRouterTips.setText(_("autorouter_features_tips"))
        self.lblDsnFile.setText(_("DSN file"))
        self.lblSesFile.setText(_("SES file"))
        self.lblRules.setText(_("Rules"))
        self.cmdExportDsn.setText(_("Export"))
        self.cmdImportSes.setText(_("Import"))
        self.cmdCancelAutoRouter.setText(_("Cancel"))
        self.lblSaveAsAutoRouter.setText(_("Save as"))

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
            
        #填充板层
        self.cmbLayerList = [_("C1 (Front copper)"), _("S1 (Front silkscreen)"), _("C2 (Back copper)"), 
            _("S2 (Back silkscreen)"), _("I1 (Inner copper1)"), _("I2 (Inner copper2)"), _("U (Edge.cuts)"), ]
        self.cmbLayer.configure(values=self.cmbLayerList)
        self.cmbLayer.current(1) #默认为顶层丝印层
        self.cmbSvgLayer.configure(values=self.cmbLayerList)
        self.cmbSvgLayer.current(1)

        #字高
        self.cmbFontHeightList = [1.0, 2.0, 3.0, 4.0]
        self.cmbFontHeight.configure(values=self.cmbFontHeightList)
        self.cmbFontHeight.current(1) #字高默认2mm
        
        #字间距
        self.cmbWordSpacingList = [-0.8, -0.5, -0.2, 0, 0.2, 0.5]
        self.cmbWordSpacing.configure(values=self.cmbWordSpacingList)
        self.cmbWordSpacing.current(0) #默认-0.8，电路板空间比较宝贵，文字可以相互靠近一些
        
        #行间距
        self.cmbLineSpacingList = [-0.5, -0.2, 0, 0.2, 0.5]
        self.cmbLineSpacing.configure(values=self.cmbLineSpacingList)
        self.cmbLineSpacing.current(2)
        
        #平滑程度
        self.cmbSmoothList = [_("Super fine (super slow)"), _("Fine (slow)"), _("Normal"), _("Rough"), _("Super Rough"), ]
        self.cmbSmooth.configure(values=self.cmbSmoothList)
        self.cmbSmooth.current(2)
        self.cmbSvgSmooth.configure(values=self.cmbSmoothList)
        self.cmbSvgSmooth.current(2)

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
            self.cmbFontList = sorted(self.fontNameMap.keys())
            self.cmbFont.configure(value=self.cmbFontList)
            lastFont = self.cfg.get('font', '')
            if lastFont and (lastFont in self.cmbFontList):
                self.cmbFont.current(self.cmbFontList.index(lastFont))
            else:
                fontNameList = self.cmbFontList if self.cmbFontList else ['',]
                if (self.sysLanguge.startswith('zh')): #中文字体一般在最后，所以默认选择最后一个，保证开箱即用
                    self.cmbFont.setText(fontNameList[-1])
                elif 'Calibri' in fontNameList: #英文或拉丁文字体也是为了保证开箱即用
                    self.cmbFont.setText('Calibri')
                else:
                    self.cmbFont.setText(fontNameList[0])
        
    #从配置文件中恢复以前的配置数据
    def restoreConfig(self):
        cfg = self.cfg
        if isinstance(cfg, dict):
            #字体界面
            lastFont = cfg.get('font', '')
            if lastFont and (lastFont in self.cmbFontList):
                self.cmbFont.current(self.cmbFontList.index(lastFont))

            lastHeight = str_to_float(cfg.get('height', ''))
            if lastHeight:
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
            clearance = str_to_float(cfg.get('clearance', '0.2'))
            smdSmdClearance = str_to_float(cfg.get('smdSmdClearance', '0.06'))
            self.pcbRule.trackWidth = trackWidth if (trackWidth > 0.1) else 0.3
            self.pcbRule.viaDiameter = viaDiameter if (viaDiameter > 0.1) else 0.7
            self.pcbRule.viaDrill = viaDrill if (viaDrill > 0.1) else 0.3
            self.pcbRule.clearance = clearance if (clearance > 0.1) else 0.2
            self.pcbRule.smdSmdClearance = smdSmdClearance if (smdSmdClearance > 0.01) else 0.06
            if (self.pcbRule.viaDiameter <= self.pcbRule.viaDrill):
                self.pcbRule.viaDiameter = self.pcbRule.viaDrill + 0.1
            self.updateRuleView()

    #保存当前配置数据
    def saveConfig(self):
        if self.versionJson: #如果检查到版本更新，则明天再检查一次
            self.lastCheckUpdate = datetime.datetime.now() - datetime.timedelta(days=29)

        cfg = {'language': self.language, 'font': self.cmbFont.text(), 'height': self.cmbFontHeight.text(), 
            'layer': str(self.cmbLayer.current()), 'wordSpacing': self.cmbWordSpacing.text(), 
            'lineSpacing': self.cmbLineSpacing.text(), 'smooth': str(self.cmbSmooth.current()), 
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
            'smdSmdClearance': str(self.pcbRule.smdSmdClearance)}
        
        if (cfg != self.cfg):  #有变化再写配置文件
            self.cfg = cfg
            cfgStr = json.dumps(cfg, indent=2)
            try:
                with open(CFG_FILENAME, 'w', encoding='utf-8') as f:
                    f.write(cfgStr)
            except:
                pass
    
    #选择一个封装文件
    def cmdFootprintFile_Cmd(self, event=None):
        ret = tkFileDialog.askopenfilename(filetypes=[(_("Kicad footprint"), "*.kicad_mod"), 
            (_("easyEDA footprint"), "*.json"), (_("All Files"), "*.*")])
        if ret:
            self.txtFootprintFile.setText(ret)

    #选择一个SVG文件
    def cmdSvgFile_Cmd(self, event=None):
        ret = tkFileDialog.askopenfilename(filetypes=[(_("SVG files"),"*.svg"), (_("All Files"), "*.*")])
        if ret:
            self.txtSvgFile.setText(ret)

    #选择一个DSN文件
    def cmdDsnFile_Cmd(self, event=None):
        retFile = tkFileDialog.asksaveasfilename(filetypes=[(_("Specctra DSN files"), '*.dsn'), (_("All files"), '*.*')])
        if retFile:
            self.txtDsnFile.setText(retFile)
            self.txtSesFile.setText(os.path.splitext(retFile)[0] + '.ses')

    #选择一个SES文件
    def cmdSesFile_Cmd(self, event=None):
        retFile = tkFileDialog.askopenfilename(filetypes=[(_("Specctra session files"),"*.ses"), (_("All Files"), "*.*")])
        if retFile:
            self.txtSesFile.setText(retFile)
            
    #取消退出
    def cmdCancel_Cmd(self, event=None):
        self.destroy()
        sys.exit(0)

    #取消退出
    def cmdCancelFootprint_Cmd(self, event=None):
        self.destroy()
        sys.exit(0)

    #取消退出
    def cmdCancelSvg_Cmd(self, event=None):
        self.destroy()
        sys.exit(0)

    #取消退出
    def cmdCancelAutoRouter_Cmd(self, event=None):
        self.destroy()
        sys.exit(0)

    #保存为单独一个文本文件
    def lblSaveAs_Button_1(self, event):
        self.saveConfig()
        txt = self.txtMain.get('1.0', END).strip()
        if not txt:
            showwarning(_('info'), _('Text is empty'))
            return

        textIo = self.generatePolygons(txt)
        if not textIo:
            showwarning(_('info'), _('Failed to generate text'))
        elif isinstance(textIo, str):
            showwarning(_('info'), textIo)
        else:
            self.saveTextFile(str(textIo))
        
    #转换封装结果保存为单独一个文本文件
    def lblSaveAsFootprint_Button_1(self, event):
        self.saveConfig()
        fileName = self.txtFootprintFile.text().strip()
        #TODO, for test
        #fileName = self.autoAddKicadPath(fileName)

        if (not self.verifyFileName(fileName, LcComponent.isLcedaComponent)):
            return
        
        errStr, retStr = self.generateFootprint(fileName)
        if (errStr):
            showwarning(_('info'), errStr)
        elif not retStr:
            if LcComponent.isLcedaComponent(fileName):
                showwarning(_('info'), _('Failed to parse content\nMaybe Id error or Internet disconnected?'))
            else:
                showwarning(_('info'), _('Failed to parse file content'))
        else:
            self.saveTextFile(retStr)

    #开始转换文本为多边形
    def cmdOk_Cmd(self, event=None):
        self.saveConfig()

        txt = self.txtMain.get('1.0', END).strip()
        if not txt:
            showwarning(_('info'), _('Text is empty'))
            return

        textIo = self.generatePolygons(txt)
        if not textIo:
            showwarning(_('info'), _('Failed to generate text'))
            return
        elif isinstance(textIo, str):
            showwarning(_('info'), textIo)
            return
        else: #写输出文件
            try:
                with open(self.outFileName, 'w', encoding='utf-8') as f:
                    f.write(str(textIo))
            except:
                pass
            
        self.destroy()
        #Sprint-Layout的插件返回码定义
        #0: = 中止/无动作
        #1: = 完全替换元素，Sprint-Layout删除选中的项目并将其替换为插件输出文件中的新项目。
        #2: = 绝对添加元素，Sprint-Layout从插件输出文件中插入新元素。不会删除任何项目。
        #3: = 相对替换元素，Sprint-Layout从插件输出文件中删除标记的元素和新元素“粘”到鼠标上，并且可以由用户放置。
        #4: = 相对添加元素，插件输出文件中的新元素“粘”在鼠标上，并且可以由用户放置。不会删除任何项目。
        sys.exit(4)

    #在封装文件文本框中回车，根据情况自动执行响应的命令
    def txtFootprintFile_Return(self, event=None):
        if (str(self.cmdOkFootprint['state']) == 'disabled') or (not self.txtFootprintFile.text().strip()):
            return

        self.cmdOkFootprint_Cmd()

    #点击了将封装文件转换为Sprint-Layout的按钮
    def cmdOkFootprint_Cmd(self, event=None):
        self.saveConfig()
        fileName = self.txtFootprintFile.text().strip()
        #TODO, for test
        #fileName = self.autoAddKicadPath(fileName)

        if (not self.verifyFileName(fileName, LcComponent.isLcedaComponent)):
            return
        
        errStr, retStr = self.generateFootprint(fileName)
        if (errStr):
            showwarning(_('info'), errStr)
        elif not retStr:
            if LcComponent.isLcedaComponent(fileName):
                showwarning(_('info'), _('Failed to parse content\nMaybe Id error or Internet disconnected?'))
            else:
                showwarning(_('info'), _('Failed to parse file content'))
        else:
            try:
                with open(self.outFileName, 'w', encoding='utf-8') as f:
                    f.write(retStr)
            except:
                pass

            self.destroy()
            sys.exit(4)
    
    #转换SVG结果保存为单独一个文本文件
    def lblSaveAsSvg_Button_1(self, event):
        self.saveConfig()
        fileName = self.txtSvgFile.text().strip()
        isQrcode = self.cmbSvgQrcode.current()
        
        #如果是SVG模式，校验文件，否则直接使用文本
        if (not self.verifyFileName(fileName, (lambda x: isQrcode) if isQrcode else None)):
            return

        #生成二维码
        if isQrcode:
            retStr = self.generateSvg(self.textToQrcodeStr(fileName), 1)
        elif fileName.lower().endswith('.svg'):
            retStr = self.generateSvg(fileName, 0)
        else:
            showwarning(_('info'), _('The file format is not supported'))
            return

        if not retStr:
            showwarning(_('info'), _('Convert svg image failed'))
        else:
            self.saveTextFile(retStr)
    
    #将输入的文本转换为二维码文本
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
    def cmdOkSvg_Cmd(self, event=None):
        self.saveConfig()
        fileName = self.txtSvgFile.text().strip()
        isQrcode = self.cmbSvgQrcode.current()
        
        #如果是SVG模式，校验文件，否则直接使用文本
        if (not self.verifyFileName(fileName, (lambda x: isQrcode) if isQrcode else None)):
            return

        #生成二维码
        if isQrcode:
            retStr = self.generateSvg(self.textToQrcodeStr(fileName), 1)
        elif fileName.lower().endswith('.svg'):
            retStr = self.generateSvg(fileName, 0)
        else:
            showwarning(_('info'), _('The file format is not supported'))
            return

        if not retStr:
            showwarning(_('info'), _('Convert svg image failed'))
        else:
            try:
                with open(self.outFileName, 'w', encoding='utf-8') as f:
                    f.write(retStr)
            except:
                pass

            self.destroy()
            sys.exit(4)

    #校验文件是否存在或是否合法，不合法则做出提示
    #fileName: 文件名
    #extraVeriFunc: 额外的校验函数，接受一个字符串参数
    def verifyFileName(self, fileName: str, extraVeriFunc=None):
        if not fileName:
            showwarning(_('info'), _('Input is empty'))
            return False

        if (extraVeriFunc and extraVeriFunc(fileName)):
            return True

        if (not os.path.isfile(fileName)) or (not os.path.exists(fileName)):
            showwarning(_('info'), _("File does not exist\n{}").format(fileName))
            return False
        
        return True

    #将字符串保存到文本文件
    def saveTextFile(self, txt: str):
        if not txt:
            return

        retFile = tkFileDialog.asksaveasfilename(title=_("Save to a text file"), filetypes=[(_('Text files'), '*.txt'), (_("All files"), '*.*')])
        if retFile:
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
        if fontHeight <= 0.0:
            fontHeight = 1.0
        
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
        textIo = SprintTextIO()
        offsetY = 0.0
        prevWidth = 0
        for line in txt.split('\n'):
            offsetX = 0.0 #每一行都从最左边开始
            maxHeight = 0
            for word in line:
                ret = singleWordPolygon(font, code=ord(word), layerIdx=layerIdx, fontHeight=fontHeight,
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
                textIo.addAll(ret['polygons'])
                inc = prevWidth + (wordSpacing * 10000)
                offsetX += inc if (inc > 0) else prevWidth
                if ret['height'] > maxHeight:
                    maxHeight = ret['height']
            #新行
            inc = maxHeight + (lineSpacing * 10000)
            offsetY += inc if (inc > 0) else maxHeight

        font.close()

        #返回字符串
        return textIo
        
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
        try:
            fontFileList = [os.path.join(FONT_DIR, f) for f in os.listdir(FONT_DIR) if f.lower().endswith(supportedFontExts)]
        except:
            fontFileList = {}
            
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
                except:
                    continue
            else:
                try:
                    insList = [ttFont.TTFont(fontFileName, lazy=True),]
                except:
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
            textIo = ins.createSprintTextIo(importText) if ins else None
        elif LcComponent.isLcedaComponent(fileName): #在线立创EDA
            easyEdaSite = self.easyEdaSite
            if not easyEdaSite:
                easyEdaSite = 'cn' if self.sysLanguge.startswith('zh') else 'global'
                
            ins = LcComponent.fromLcId(fileName, easyEdaSite)
            if isinstance(ins, LcComponent):
                textIo = ins.createSprintTextIo(importText)
            elif ins:
                msg = str(ins)
        else:
            msg = _("This file format is not supported")

        return (msg, str(textIo) if (textIo and textIo.isValid()) else '')

    #将SVG文件转换为Sprint-Layout格式
    #fileName: SVG文件名或二维码文本
    #isQrcode: True则为生成二维码
    #返回：生成的textIo字符串
    def generateSvg(self, fileName: str, isQrcode: bool):
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
        if self.versionJson:
            from version_check import openNewVersionDialog
            ret = openNewVersionDialog(self.master, __VERSION__, self.versionJson)
            if (ret == 'skip'):
                self.skipVersion = self.versionJson.get('lastest', '')

            self.saveConfig()
            self.versionJson = {} #只允许点击一次
            self.setStaBarByMode() #恢复正常的状态栏显示

    #联网检查更新线程
    def versionCheckThread(self, arg=None):
        #print('versionCheckThread')
        from version_check import checkUpdate
        self.versionJson = checkUpdate(__VERSION__, self.skipVersion)
        #为了简单，直接在子线程里面设置状态栏显示，因为状态栏目前仅在启动时设置一次，所以应该不会有资源冲突
        if self.versionJson:
            self.staBar.text(_('  New version found, double-click to show details'))

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

        #TODO
        inFile = self.inFileName if self.inFileName else r'C:\Users\su\Desktop\testSprint\1.txt'
        inFileSize = 0
        try:
            inFileSize = os.path.getsize(inFile)
        except Exception as e:
            showwarning(_("info"), str(e))
            return False

        if (inFileSize <= 0):
            showwarning(_("info"), _("No components on the board"))
            return False

        parser = SprintTextIoParser()
        try:
            textIo = parser.parse(inFile)
        except Exception as e:
            showwarning(_("info"), _("Error parsing input file:\n{}").format(str(e)))
            return False

        if not textIo:
            showwarning(_("info"), _("Failed to parse input file"))
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
    def cmdImportSes_Cmd(self, event=None, trackOnly=False):
        try:         
            x = self.master.winfo_pointerx() # - self.master.winfo_vrootx()
            y = self.master.winfo_pointery() # - self.master.winfo_vrooty()
            self.mnuImportSes.tk_popup(x, y + 10, 0)
        finally:
            self.mnuImportSes.grab_release()

    #菜单项“导入...”的点击响应函数
    def cmdmnuImportSes(self, withRatsnest: bool=False, trackOnly: bool=False):
        if (self.importSes(withRatsnest, trackOnly)):
            self.destroy()
            #Sprint-Layout的插件返回码定义
            #0: = 中止/无动作
            #1: = 完全替换元素，Sprint-Layout删除选中的项目并将其替换为插件输出文件中的新项目。
            #2: = 绝对添加元素，Sprint-Layout从插件输出文件中插入新元素。不会删除任何项目。
            #3: = 相对替换元素，Sprint-Layout从插件输出文件中删除标记的元素和新元素“粘”到鼠标上，并且可以由用户放置。
            #4: = 相对添加元素，插件输出文件中的新元素“粘”在鼠标上，并且可以由用户放置。不会删除任何项目。
            sys.exit(4 if trackOnly else 1)

    #导入自动布线的SES到输出文件
    #withRatsnest: 是否包含网络连线（鼠线）
    #trackOnly: 是否仅导入布线
    #成功返回True
    def importSes(self, withRatsnest: bool, trackOnly: bool):
        self.saveConfig()
        sesFile = self.txtSesFile.text().strip()
        dsnPickleFile = os.path.splitext(sesFile)[0] + '.pickle'
        
        if ((not self.verifyFileName(sesFile)) or (not self.verifyFileName(dsnPickleFile))):
            return False
        
        if not sesFile.lower().endswith('.ses'):
            showwarning(_("info"), _("The file format is not supported"))
            return False

        if not trackOnly:
            ret = askyesno(_("info"), _("This operation will completely replace the existing components and wiring on the board.\nDo you want to continue?"))
            if not ret:
                return False

        ret = self.generateTextIoFromSes(sesFile, dsnPickleFile, withRatsnest=withRatsnest, trackOnly=trackOnly)
        if not ret:
            return False
        elif isinstance(ret, str):
            showwarning(_("info"), ret)
            return False
        else:
            try:
                with open(self.outFileName, 'w', encoding='utf-8') as f:
                    f.write(str(ret))
            except Exception as e:
                showwarning(_("info"), str(e))
                return False
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

        ret = self.generateTextIoFromSes(sesFile, dsnPickleFile, withRatsnest=False, trackOnly=False)
        if not ret:
            return
        elif isinstance(ret, str):
            showwarning(_("info"), ret)
            return
        else:
            self.saveTextFile(str(ret))

    #从SES中生成TextIo实例对象
    def generateTextIoFromSes(self, sesFile: str, dsnPickleFile: str, withRatsnest: bool, trackOnly: bool):
        from sprint_struct.sprint_import_ses import SprintImportSes
        try:
            with open(dsnPickleFile, 'rb') as f:
                dsn = pickle.load(f)
        except Exception as e:
            return str(e)
            
        ses = SprintImportSes(sesFile, dsn)
        try:
            textIo = ses.importSes(withRatsnest=withRatsnest, trackOnly=trackOnly)
            return textIo
        except Exception as e:
            return str(e)

if __name__ == "__main__":
    top = Tk()
    Application(top).mainloop()

