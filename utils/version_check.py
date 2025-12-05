#!/usr/bin/env python
#-*- coding:utf-8 -*-
"""
版本检查
Author: cdhigh <https://github.com/cdhigh>
使用方法：
1. 适当的时候调用 checkUpdate(currVersion, skipVersion) 获取新版本的Json字典
2. 如果 checkUpdate() 返回一个字典，可以调用 openNewVersionDialog(self.top, currVersion, self.versionJson) 打开版本提示对话框
3. 根据 openNewVersionDialog() 的返回值更新配置文件（如果是'skip'）
"""
import os, sys, json
from urllib import request
from tkinter import *
from tkinter.font import Font
from tkinter.ttk import *
#Usage:showinfo/warning/error,askquestion/okcancel/yesno/retrycancel
from tkinter.messagebox import *
#Usage:f=tkFileDialog.askopenfilename(initialdir='E:/Python')
#import tkinter.filedialog as tkFileDialog
#import tkinter.simpledialog as tkSimpleDialog  #askstring()
from .comm_utils import str_to_int
from .widget_right_click import rightClicker

VERSION_JSON_URI = 'https://raw.githubusercontent.com/cdhigh/sprintFontRelease/main/version.json'

#查询是否有新版本，如果有新版本，返回新版本信息
def checkUpdate(currVersion: str, skipVersion: str):
    versionJsonData = fetchVersionJson()
    if not versionJsonData:
        return None
    
    lastestVersion = versionJsonData.get('lastest', currVersion)
    if isVersionGreaterThan(lastestVersion, currVersion):
        if not skipVersion or isVersionGreaterThan(lastestVersion, skipVersion):
            return versionJsonData
        else:
            return None
    else:
        return None

#使用此函数打开新版本下载提示对话框，top为主程序的Tk实例
#返回用户选择的行为：'download'/'skip'/'later'
def openNewVersionDialog(master, currVersion, versionJson):
    dialogTop = Toplevel(master)
    dialog = VersionDialog(dialogTop, currVersion, versionJson)
    #dialogTop.mainloop() #使用下面一句代替此句，否则会出错
    master.wait_window(dialog)
    return versionJson.get('action', '')

class VersionDialog_ui(Frame):
    #这个类仅实现界面生成功能，具体事件处理代码在子类Application中。
    def __init__(self, master=None):
        Frame.__init__(self, master)
        # To center the window on the screen.
        ws = self.master.winfo_screenwidth()
        hs = self.master.winfo_screenheight()
        x = (ws / 2) - (584 / 2)
        y = (hs / 2) - (410 / 2)
        self.master.geometry('%dx%d+%d+%d' % (584,410,x,y))
        self.master.title('New version found')
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

        self.cmdLaterVar = StringVar(value='Later')
        self.style.configure('TcmdLater.TButton', font=('微软雅黑',10))
        self.cmdLater = Button(self.top, text='Later', textvariable=self.cmdLaterVar, command=self.cmdLater_Cmd, style='TcmdLater.TButton')
        self.cmdLater.setText = lambda x: self.cmdLaterVar.set(x)
        self.cmdLater.text = lambda : self.cmdLaterVar.get()
        self.cmdLater.place(relx=0.712, rely=0.898, relwidth=0.262, relheight=0.08)

        self.cmdSkipThisVersionVar = StringVar(value='Skip this version')
        self.style.configure('TcmdSkipThisVersion.TButton', font=('微软雅黑',10))
        self.cmdSkipThisVersion = Button(self.top, text='Skip this version', textvariable=self.cmdSkipThisVersionVar, command=self.cmdSkipThisVersion_Cmd, style='TcmdSkipThisVersion.TButton')
        self.cmdSkipThisVersion.setText = lambda x: self.cmdSkipThisVersionVar.set(x)
        self.cmdSkipThisVersion.text = lambda : self.cmdSkipThisVersionVar.get()
        self.cmdSkipThisVersion.place(relx=0.37, rely=0.898, relwidth=0.262, relheight=0.08)

        self.cmdDownloadVar = StringVar(value='Download')
        self.style.configure('TcmdDownload.TButton', font=('微软雅黑',10))
        self.cmdDownload = Button(self.top, text='Download', textvariable=self.cmdDownloadVar, command=self.cmdDownload_Cmd, style='TcmdDownload.TButton')
        self.cmdDownload.setText = lambda x: self.cmdDownloadVar.set(x)
        self.cmdDownload.text = lambda : self.cmdDownloadVar.get()
        self.cmdDownload.place(relx=0.027, rely=0.898, relwidth=0.262, relheight=0.08)

        self.vScrlTxt = Scrollbar(self.top, orient='vertical')
        self.vScrlTxt.place(relx=0.945, rely=0.195, relwidth=0.029, relheight=0.646)

        self.txtChangelogFont = Font(font=('微软雅黑',10))
        self.txtChangelog = Text(self.top, bg='#E0E0E0', yscrollcommand=self.vScrlTxt.set, font=self.txtChangelogFont)
        self.txtChangelog.place(relx=0.027, rely=0.195, relwidth=0.92, relheight=0.646)
        self.txtChangelog.insert('1.0','')
        self.vScrlTxt['command'] = self.txtChangelog.yview

        self.lblLastestVar = StringVar(value='Lastest')
        self.style.configure('TlblLastest.TLabel', anchor='w', font=('微软雅黑',10,'bold'))
        self.lblLastest = Label(self.top, text='Lastest', textvariable=self.lblLastestVar, style='TlblLastest.TLabel')
        self.lblLastest.setText = lambda x: self.lblLastestVar.set(x)
        self.lblLastest.text = lambda : self.lblLastestVar.get()
        self.lblLastest.place(relx=0.027, rely=0.09, relwidth=0.509, relheight=0.061)

        self.lblCurrentVersionVar = StringVar(value='Current')
        self.style.configure('TlblCurrentVersion.TLabel', anchor='w', font=('微软雅黑',10,'bold'))
        self.lblCurrentVersion = Label(self.top, text='Current', textvariable=self.lblCurrentVersionVar, style='TlblCurrentVersion.TLabel')
        self.lblCurrentVersion.setText = lambda x: self.lblCurrentVersionVar.set(x)
        self.lblCurrentVersion.text = lambda : self.lblCurrentVersionVar.get()
        self.lblCurrentVersion.place(relx=0.027, rely=0.02, relwidth=0.495, relheight=0.061)

class VersionDialog(VersionDialog_ui):
    #这个类实现具体的事件处理回调函数。界面生成代码在Application_ui中。
    def __init__(self, master, currVersion, versionJson):
        VersionDialog_ui.__init__(self, master)
        self.txtChangelog.bind('<Button-3>', rightClicker, add='')
        self.txtChangelog.configure(padx=10)
        self.txtChangelog.configure(pady=5)
        self.txtChangelog.configure(spacing1=3)
        self.txtChangelog.configure(state='disabled')
        self.txtChangelog.bind("<1>", lambda event: self.txtChangelog.focus_set()) #让Text可以被拷贝
        
        self.versionJson = versionJson
        lastest = versionJson.get('lastest', '')

        #翻译控件
        self.master.title(_('New version found'))
        self.lblCurrentVersion.setText(_('Current version: v{}').format(currVersion))
        self.lblLastest.setText(_('Lastest version: v{}').format(lastest))
        self.cmdDownload.setText(_('Download'))
        self.cmdSkipThisVersion.setText(_('Skip this version'))
        self.cmdLater.setText(_('Later'))

        #显示版本历史
        txtHistoryList = []
        history = versionJson.get('history')
        if (history and isinstance(history, list)):
            for item in history:
                ver = item.get('version', '')
                build = item.get('build', '')
                whatsnew = item.get('whatsnew', '')
                txtHistoryList.append('v{} (build {})\n{}\n'.format(ver, build, whatsnew))

        self.txtChangelog.configure(state='normal') #要设置为normal才能添加文本
        self.txtChangelog.insert('1.0', '\n'.join(txtHistoryList))
        self.txtChangelog.configure(state='disabled')

        self.focus_force()
        #self.grab_set()

    def cmdDownload_Cmd(self, event=None):
        import webbrowser
        self.versionJson['action'] = 'download'
        history = self.versionJson.get('history', '')
        if (history and isinstance(history, list)):
            url = history[0].get('url')
            if url:
                webbrowser.open_new_tab(url)
        self.top.destroy()
        
    def cmdSkipThisVersion_Cmd(self, event=None):
        self.versionJson['action'] = 'skip'
        self.top.destroy()

    def cmdLater_Cmd(self, event=None):
        self.versionJson['action'] = 'later'
        self.top.destroy()


#联网获取版本更新的json包
def fetchVersionJson():
    versionJsonData = None
    try:
        data = request.urlopen(VERSION_JSON_URI, timeout=5).read().decode('utf-8')
        versionJsonData = json.loads(data)
    except Exception as e:
        return None

    return versionJsonData if isinstance(versionJsonData, dict) else None


#比较两个版本号，确定新版本号是否比老版本号更新，
#版本号格式为：1.1或1.1.0
def isVersionGreaterThan(newVersion: str, currVersion: str):
    if not newVersion or not currVersion:
        return False
    else:
        from packaging import version
        try:
            return version.parse(newVersion) > version.parse(currVersion)
        except:
            return False

    #if not newVersion[0].isdigit(): #去掉可能的第一个字符'V'
    #    newVersion = newVersion[1:]
    #if not currVersion[0].isdigit(): #去掉可能的第一个字符'V'
    #    currVersion = currVersion[1:]
    #newV = newVersion.split('.')
    #currV = currVersion.split('.')
    #maxSegNum = min(len(newV), len(currV))
    #for idx in range(maxSegNum):
    #    vn = str_to_int(newV[idx])
    #    vc = str_to_int(currV[idx])
    #    if (vn != vc):
    #        return True if (vn > vc) else False
    
    #如果前面的比较都一致，但新版本字符串比当前版本字符串要多一个字段，则说明是小更新版本
    #return True if (len(newV) > len(currV)) else False

