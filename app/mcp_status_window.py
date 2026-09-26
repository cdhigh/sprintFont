#!/usr/bin/env python
#-*- coding:utf-8 -*-
"""
MCP运行状态窗口(模态)：显示MCP服务器状态与LLM交互概要日志
按钮"接受"：将内存中的SprintTextIO写入Sprint-Layout临时输出文件，以RETURN_CODE_REPLACE_ALL退出插件
按钮"取消"：确认后放弃全部修改退出插件
Author: cdhigh <https://github.com/cdhigh>
"""
import time
from tkinter import Toplevel, Text, Scrollbar, END
from tkinter.ttk import Frame, Label, Button
from tkinter.messagebox import askokcancel
from ui.tooltip import Tooltip

#MCP运行状态窗口(模态)
class McpStatusWindow(Toplevel):
    #app: sprintFont的Application实例
    def __init__(self, app):
        super().__init__(app.master)
        self.app = app
        self.title(_('MCP Server'))
        self.transient(app.master)
        self.protocol('WM_DELETE_WINDOW', self.cmdCancel)
        self.bind('<Escape>', self.cmdCancel)
        self.lastLogIdx = 0 #已显示的日志条数

        self.createWidgets()
        #居中于主窗口
        self.update_idletasks()
        reqW = self.winfo_reqwidth()
        reqH = self.winfo_reqheight()
        px, py = app.master.winfo_rootx(), app.master.winfo_rooty()
        pw, ph = app.master.winfo_width(), app.master.winfo_height()

        # 计算居中坐标 (用父窗口尺寸减去当前窗口尺寸)
        x = px + max(0, (pw - reqW) // 2)
        y = py + max(0, (ph - reqH) // 2)

        # 必须使用完整的 '宽x高+X+Y' 格式！
        self.geometry(f'{reqW}x{reqH}+{x}+{y}')
        self.resizable(0, 0)
        self.after(10, self.grabModal)
        #定时刷新状态与日志
        self.after(300, self.refreshStatus)

    #创建窗口内的控件
    def createWidgets(self):
        app = self.app
        main = Frame(self, padding=(10, 8))
        main.pack(fill='both', expand=1)

        #服务器状态与连接地址
        self.lblStatus = Label(main, text=_('Waiting for MCP server to start...'), font=('TkDefaultFont', 10))
        self.lblStatus.pack(fill='x', pady=(0, 8))
        
        #交互日志
        logFrame = Frame(main)
        logFrame.pack(fill='both', expand=1)
        self.logText = Text(logFrame, width=70, height=15, state='disabled', wrap='none',
            font=('Consolas', 9), background='#FAFAFA')
        scroll = Scrollbar(logFrame, command=self.logText.yview)
        self.logText.configure(yscrollcommand=scroll.set)
        self.logText.pack(side='left', fill='both', expand=1)
        scroll.pack(side='right', fill='y')

        #底部按钮
        btnFrame = Frame(main, padding=(0, 8, 0, 0))
        btnFrame.pack(fill='x')
        self.lblEndPoint = Label(btnFrame, text='', foreground='#666666', font=('TkDefaultFont', 9), cursor='hand2')
        self.lblEndPoint.pack(side='left')
        self.lblEndPoint.bind('<Button-1>', self.copyEndPoint)
        self.cmdSymbolTooltip = Tooltip(self.lblEndPoint, _('Click to copy to clipboard'))

        self.cmdCancelBtn = Button(btnFrame, text=_('Cancel'), width=14, command=self.cmdCancel)
        self.cmdCancelBtn.pack(side='right', padx=(20, 0))
        self.cmdAccept = Button(btnFrame, text=_('Accept'), width=14, command=self.cmdAccept_Cmd)
        self.cmdAccept.pack(side='right')
        #初始或无修改时接受按钮禁用，发生实质修改后才点亮
        self.cmdAccept.configure(state='disabled')
        
        #Standalone模式没有输出文件，接受按钮不可用
        if not app.inFileName:
            self.lblStatus.configure(text=_('Standalone mode: use the saveTextIoFile tool to save the board'))

    #定时刷新MCP状态与交互日志
    def refreshStatus(self):
        try:
            server = self.app.mcpServer
            if server is not None:
                self.lblStatus.configure(text=server.statusText or _('MCP server disabled'))
                port = server.listenPort
                if port:
                    self.lblEndPoint.configure(text='http://127.0.0.1:{}/mcp'.format(port))
                entries, self.lastLogIdx = server.drainLogEntries(self.lastLogIdx)
                if entries:
                    self.logText.configure(state='normal')
                    for ts, text in entries:
                        self.logText.insert(END, '[{}] {}\n'.format(
                            time.strftime('%H:%M:%S', time.localtime(ts)), text))
                    self.logText.see(END)
                    self.logText.configure(state='disabled')

            #仅在有输入文件且板图发生过实质修改时才启用接受按钮
            if not self.app.inFileName:
                self.cmdAccept.configure(state='disabled')
            else:
                isModified = self.app.isBoardModified()
                self.cmdAccept.configure(state=('normal' if isModified else 'disabled'))
        except Exception as e:
            print('McpStatusWindow.refreshStatus: {}'.format(str(e)))
        self.after(300, self.refreshStatus)

    #延迟抓取模态焦点(等窗口完成映射)
    def grabModal(self):
        try:
            self.grab_set()
        except Exception:
            pass
        self.lift()
        self.focus_force()

    #点击连接地址复制到剪贴板
    def copyEndPoint(self, event=None):
        url = self.lblEndPoint.cget('text')
        if url:
            self.clipboard_clear()
            self.clipboard_append(url)

    #点击接受：将板图写回Sprint-Layout并退出插件
    #自动根据修改情况判定模式：纯新增图元走insert_new(仅输出新图元)；改动旧图元走replace(整板替换)
    def cmdAccept_Cmd(self, event=None):
        if not self.app.isBoardModified():
            return
        self.app.applyMcpBoard('auto')

    #点击取消/关闭窗口：若未修改直接退出；发生修改后弹窗确认放弃全部修改退出插件
    def cmdCancel(self, event=None):
        if not self.app.isBoardModified():
            self.app.safeExit(0) #0=RETURN_CODE_NONE，无修改直接退出
            return
        if askokcancel(_('Cancel'), _('Discard all MCP changes and exit?')):
            self.app.safeExit(0) #0=RETURN_CODE_NONE，Sprint-Layout不做任何处理
