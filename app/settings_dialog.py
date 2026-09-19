#!/usr/bin/env python3
#-*- coding:utf-8 -*-
#设置对话框
#Author: cdhigh <https://github.com/cdhigh>
import os, sys, gettext, builtins
from tkinter import *
from tkinter.font import Font
from tkinter.ttk import *
#Usage:showinfo/warning/error,askquestion/okcancel/yesno/retrycancel
from tkinter.messagebox import *
#from tkinter import filedialog  #.askopenfilename()
#from tkinter import simpledialog  #.askstring()
from utils.comm_utils import str_to_int

#独立运行本文件预览界面时的翻译占位，正常由config_manager安装gettext
if not hasattr(builtins, '_'):
    builtins._ = lambda txt: txt

#界面语种列表(代码, 显示名)，显示名用各自语言的原文，不做翻译
LANGUAGE_DISPLAY_NAMES = [
    ('', 'Auto'), #这个Auto也不翻译, 不管什么语言, 大概率都认得这个单词
    ('en', 'English'),
    ('zh_cn', '简体中文'),
    ('de', 'Deutsch'),
    ('es', 'Español'),
    ('pt', 'Português'),
    ('fr', 'Français'),
    ('ru', 'Русский'),
    ('tr', 'Türkçe'),
]

#更新检查频率的可选天数
UPDATE_CHECK_DAYS = (_('Never'), '7', '30', '90')

class SettingsDialog_ui(Frame):
    def __init__(self, master):
        super().__init__(master)
        x = int((self.master.winfo_screenwidth() - 450) / 2)
        y = int((self.master.winfo_screenheight() - 301) / 2)
        self.master.geometry('450x301+{}+{}'.format(x, y))
        self.master.title('Settings')
        self.master.resizable(0, 0)
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
        self.master.iconphoto(True, self.iconimg)
        self.createWidgets()

    def createWidgets(self):
        self.top = self.winfo_toplevel()

        self.style = Style()

        self.style.configure('TfrmMcpServer.TLabelframe', font=('TkDefaultFont',10))
        self.style.configure('TfrmMcpServer.TLabelframe.Label', font=('TkDefaultFont',10))
        self.frmMcpServer = LabelFrame(self.top, text='MCP Server (AI bridge)', style='TfrmMcpServer.TLabelframe')
        self.frmMcpServer.place(relx=0.018, rely=0.558, relwidth=0.962, relheight=0.243)

        self.cmbUpdateCheckList = ['',]
        self.cmbUpdateCheckVar = StringVar(value='')
        self.cmbUpdateCheck = Combobox(self.top, exportselection=0, state='readonly', textvariable=self.cmbUpdateCheckVar, values=self.cmbUpdateCheckList, font=('TkDefaultFont',10))
        self.cmbUpdateCheck.setText = lambda x: self.cmbUpdateCheckVar.set(x)
        self.cmbUpdateCheck.text = lambda : self.cmbUpdateCheckVar.get()
        self.cmbUpdateCheck.place(relx=0.622, rely=0.425, relwidth=0.358)

        self.cmbEasyEdaSiteList = ['',]
        self.cmbEasyEdaSiteVar = StringVar(value='')
        self.cmbEasyEdaSite = Combobox(self.top, exportselection=0, state='readonly', textvariable=self.cmbEasyEdaSiteVar, values=self.cmbEasyEdaSiteList, font=('TkDefaultFont',10))
        self.cmbEasyEdaSite.setText = lambda x: self.cmbEasyEdaSiteVar.set(x)
        self.cmbEasyEdaSite.text = lambda : self.cmbEasyEdaSiteVar.get()
        self.cmbEasyEdaSite.place(relx=0.622, rely=0.292, relwidth=0.358)

        self.cmbLanguageList = ['',]
        self.cmbLanguageVar = StringVar(value='')
        self.cmbLanguage = Combobox(self.top, exportselection=0, state='readonly', textvariable=self.cmbLanguageVar, values=self.cmbLanguageList, font=('TkDefaultFont',10))
        self.cmbLanguage.setText = lambda x: self.cmbLanguageVar.set(x)
        self.cmbLanguage.text = lambda : self.cmbLanguageVar.get()
        self.cmbLanguage.place(relx=0.622, rely=0.159, relwidth=0.358)

        self.cmdSettingsCancelVar = StringVar(value='Cancel')
        self.style.configure('TcmdSettingsCancel.TButton', font=('TkDefaultFont',10))
        self.cmdSettingsCancel = Button(self.top, text='Cancel', textvariable=self.cmdSettingsCancelVar, command=self.top.destroy, style='TcmdSettingsCancel.TButton')
        self.cmdSettingsCancel.setText = lambda x: self.cmdSettingsCancelVar.set(x)
        self.cmdSettingsCancel.text = lambda : self.cmdSettingsCancelVar.get()
        self.cmdSettingsCancel.place(relx=0.533, rely=0.85, relwidth=0.34, relheight=0.11)

        self.cmdSettingsOkVar = StringVar(value='Ok')
        self.style.configure('TcmdSettingsOk.TButton', font=('TkDefaultFont',10))
        self.cmdSettingsOk = Button(self.top, text='Ok', textvariable=self.cmdSettingsOkVar, command=self.cmdSettingsOk_Cmd, style='TcmdSettingsOk.TButton')
        self.cmdSettingsOk.setText = lambda x: self.cmdSettingsOkVar.set(x)
        self.cmdSettingsOk.text = lambda : self.cmdSettingsOkVar.get()
        self.cmdSettingsOk.place(relx=0.071, rely=0.85, relwidth=0.34, relheight=0.11)

        self.lblUpdateCheckVar = StringVar(value='Update check (days)')
        self.style.configure('TlblUpdateCheck.TLabel', anchor='e', font=('TkDefaultFont',10))
        self.lblUpdateCheck = Label(self.top, text='Update check (days)', textvariable=self.lblUpdateCheckVar, style='TlblUpdateCheck.TLabel')
        self.lblUpdateCheck.setText = lambda x: self.lblUpdateCheckVar.set(x)
        self.lblUpdateCheck.text = lambda : self.lblUpdateCheckVar.get()
        self.lblUpdateCheck.place(relx=0.036, rely=0.425, relwidth=0.536, relheight=0.083)

        self.lblEasyEdaSiteVar = StringVar(value='EasyEDA server')
        self.style.configure('TlblEasyEdaSite.TLabel', anchor='e', font=('TkDefaultFont',10))
        self.lblEasyEdaSite = Label(self.top, text='EasyEDA server', textvariable=self.lblEasyEdaSiteVar, style='TlblEasyEdaSite.TLabel')
        self.lblEasyEdaSite.setText = lambda x: self.lblEasyEdaSiteVar.set(x)
        self.lblEasyEdaSite.text = lambda : self.lblEasyEdaSiteVar.get()
        self.lblEasyEdaSite.place(relx=0.036, rely=0.292, relwidth=0.536, relheight=0.083)

        self.lblLanguageTipsVar = StringVar(value='These settings will take effect after restarting')
        self.style.configure('TlblLanguageTips.TLabel', anchor='w', foreground='#7C7C7C', font=('TkDefaultFont',10))
        self.lblLanguageTips = Label(self.top, text='These settings will take effect after restarting', textvariable=self.lblLanguageTipsVar, style='TlblLanguageTips.TLabel')
        self.lblLanguageTips.setText = lambda x: self.lblLanguageTipsVar.set(x)
        self.lblLanguageTips.text = lambda : self.lblLanguageTipsVar.get()
        self.lblLanguageTips.place(relx=0.036, rely=0.027, relwidth=0.927, relheight=0.083)

        self.lblLanguageVar = StringVar(value='Language')
        self.style.configure('TlblLanguage.TLabel', anchor='e', font=('TkDefaultFont',10))
        self.lblLanguage = Label(self.top, text='Language', textvariable=self.lblLanguageVar, style='TlblLanguage.TLabel')
        self.lblLanguage.setText = lambda x: self.lblLanguageVar.set(x)
        self.lblLanguage.text = lambda : self.lblLanguageVar.get()
        self.lblLanguage.place(relx=0.036, rely=0.159, relwidth=0.536, relheight=0.083)

        self.lblMcpPortVar = StringVar(value='Port')
        self.style.configure('TlblMcpPort.TLabel', anchor='e', font=('TkDefaultFont',10))
        self.lblMcpPort = Label(self.frmMcpServer, text='Port', textvariable=self.lblMcpPortVar, style='TlblMcpPort.TLabel')
        self.lblMcpPort.setText = lambda x: self.lblMcpPortVar.set(x)
        self.lblMcpPort.text = lambda : self.lblMcpPortVar.get()
        self.lblMcpPort.place(relx=0.018, rely=0.329, relwidth=0.187, relheight=0.342)

        self.txtMcpPortVar = StringVar(value='5390')
        self.txtMcpPort = Entry(self.frmMcpServer, textvariable=self.txtMcpPortVar, font=('TkDefaultFont',10))
        self.txtMcpPort.setText = lambda x: self.txtMcpPortVar.set(x)
        self.txtMcpPort.text = lambda : self.txtMcpPortVar.get()
        self.txtMcpPort.place(relx=0.222, rely=0.329, relwidth=0.187, relheight=0.384)

        self.cmdMcpStartVar = StringVar(value='Start MCP Server')
        self.style.configure('TcmdMcpStart.TButton', font=('TkDefaultFont',10))
        self.cmdMcpStart = Button(self.frmMcpServer, text='Start MCP Server', textvariable=self.cmdMcpStartVar, command=self.cmdMcpStart_Cmd, style='TcmdMcpStart.TButton')
        self.cmdMcpStart.setText = lambda x: self.cmdMcpStartVar.set(x)
        self.cmdMcpStart.text = lambda : self.cmdMcpStartVar.get()
        self.cmdMcpStart.place(relx=0.48, rely=0.219, relwidth=0.483, relheight=0.562)

    def retranslateUi(self):
        self.master.title(_('Settings'))
        self.frmMcpServer.configure(text=_('MCP Server (AI bridge)'))
        self.cmdSettingsCancel.setText(_('Cancel'))
        self.cmdSettingsOk.setText(_('Ok'))
        self.lblUpdateCheck.setText(_('Update check (days)'))
        self.lblEasyEdaSite.setText(_('EasyEDA server'))
        self.lblLanguageTips.setText(_('These settings will take effect after restarting'))
        self.lblLanguage.setText(_('Language'))
        self.lblMcpPort.setText(_('Port'))
        self.cmdMcpStart.setText(_('Start MCP Server'))

class SettingsDialog(SettingsDialog_ui):
    #app: sprintFont的Application实例(独立预览界面时可以为None)
    #master: 对话框窗口，为None时自动创建Toplevel
    def __init__(self, app, master=None):
        if master is None:
            master = Toplevel(app.master)
        super().__init__(master)
        self.app = app
        self.retranslateUi()
        self.restoreValues()
        self.setModalSoon()

    #用应用当前的配置值填充各控件(值语义：打开时读入，点击Ok才统一写回)
    def restoreValues(self):
        app = self.app
        if app is None: #独立预览模式，保持生成代码中的默认值
            return

        self.cmbLanguage.configure(values=[name for _, name in LANGUAGE_DISPLAY_NAMES])
        self.cmbLanguage.current(self.currentLanguageIndex())
        self.cmbEasyEdaSite.configure(values=('Auto', 'CN', 'Global'))
        self.cmbEasyEdaSite.current({'cn':1, 'global':2}.get(app.easyEdaSite.lower(), 0))
        
        self.cmbUpdateCheck.configure(values=UPDATE_CHECK_DAYS)
        freq = str(app.checkUpdateFrequency)
        if freq in UPDATE_CHECK_DAYS:
            self.cmbUpdateCheck.current(UPDATE_CHECK_DAYS.index(freq))
        else:
            self.cmbUpdateCheck.current(0)

        self.txtMcpPort.setText(app.mcpPortVar.get())

    #计算当前语种在下拉框中的索引(空字符串=Auto跟随系统)
    def currentLanguageIndex(self):
        app = self.app
        langCode = app.configManager.language or ''
        codes = [code for code, _ in LANGUAGE_DISPLAY_NAMES]
        if langCode in codes:
            return codes.index(langCode)

        #配置中的语种无效时，按解析后的有效语种回退显示
        langCode = app.configManager.getSupportedLanguage(app.configManager.sysLanguge or 'en')
        return codes.index(langCode) if langCode in codes else 0
        
    #点击“启动MCP服务器”：写回端口、加载板图并启动服务器，成功后关闭本对话框(打开模态状态窗口)
    def cmdMcpStart_Cmd(self, event=None):
        app = self.app
        if app is None: #独立预览模式，直接关闭
            self.closeDialog()
            return
        app.mcpPortVar.set(self.txtMcpPort.text())
        if app.startMcpServer():
            self.closeDialog()

    #设置模态并置前(等窗口完成映射后再抓取焦点)
    def setModalSoon(self):
        try:
            if self.app:
                self.top.transient(self.app.master)
            self.top.lift()
            self.top.focus_force()
        except Exception:
            pass
        self.top.after(10, self.grabModal)

    #抓取模态焦点
    def grabModal(self):
        try:
            self.top.grab_set()
        except Exception:
            pass

    #根据端口刷新MCP连接地址提示
    def updateMcpEndPoint(self, event=None):
        port = str_to_int(self.txtMcpPort.text(), 0)
        if port > 0:
            self.lblMcpEndPoint.setText('http://127.0.0.1:{}/mcp'.format(port))
        else:
            self.lblMcpEndPoint.setText('')

    #点击确定：把对话框中的值写回应用并保存
    def cmdSettingsOk_Cmd(self, event=None):
        app = self.app
        if app is None: #独立预览模式，直接关闭
            self.closeDialog()
            return

        #界面语种(仅保存配置，重启后生效；Auto保存为空字符串，运行时跟随系统语言)
        selIdx = self.cmbLanguage.current()
        if selIdx >= 0:
            app.configManager.language = LANGUAGE_DISPLAY_NAMES[selIdx][0]

        #立创EDA服务器节点(下拉框显示为Auto/CN/Global，配置中保存小写的cn/global)
        site = self.cmbEasyEdaSite.get().lower()
        app.easyEdaSite = site if site in ('cn', 'global') else ''

        #更新检查频率
        app.checkUpdateFrequency = str_to_int(self.cmbUpdateCheck.text(), 0)

        #MCP端口(仅保存配置；服务器由“Start MCP Server”按钮手动启动)
        app.mcpPortVar.set(self.txtMcpPort.text())
        app.saveConfig()
        self.closeDialog()

    #复制MCP连接地址到剪贴板
    def lblMcpEndPoint_Button_1(self, event=None):
        self.copyEndPointToClipboard()

    #复制MCP连接地址到剪贴板
    def lblMcpEndPoint_Double_Button_1(self, event=None):
        self.copyEndPointToClipboard()

    #复制MCP连接地址到剪贴板
    def copyEndPointToClipboard(self):
        url = self.lblMcpEndPoint.text()
        if url:
            self.top.clipboard_clear()
            self.top.clipboard_append(url)
            if self.app:
                self.app.staBar.text('  {}'.format(url))

    #关闭对话框
    def closeDialog(self):
        try:
            self.top.grab_release()
        except Exception:
            pass
        self.top.destroy()


