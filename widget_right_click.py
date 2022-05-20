#!/usr/bin/env python
#-*- coding:utf-8 -*-
"""
绑定tkinter的右键菜单
==========================
用法：
1. 绑定单个控件
self.entry.bind('<Button-3>', rightClicker, add='')

2. 绑定所有控件
bindAllWidgetRightClick(self.master)
"""

from tkinter import Menu, TclError

#控件右键事件的处理事件
def rightClicker(event):
    try:
        def rightClickCopy(event, apnd=0):
            event.widget.event_generate('<Control-c>')

        def rightClickCut(event):
            event.widget.event_generate('<Control-x>')

        def rightClickPaste(event):
            event.widget.event_generate('<Control-v>')

        event.widget.focus()

        nclst=[(_(' Cut'), lambda event=event: rightClickCut(event)),
               (_(' Copy'), lambda event=event: rightClickCopy(event)),
               (_(' Paste'), lambda event=event: rightClickPaste(event)),]

        rmenu = Menu(None, tearoff=0, takefocus=0)

        for (txt, cmd) in nclst:
            rmenu.add_command(label=txt, command=cmd)

        rmenu.tk_popup(event.x_root+40, event.y_root+10, entry="0")
    except TclError:
        pass

    return "break"

#遍历rootWidget的子控件，在有文本输入的控件上都绑定鼠标右键事件
def bindAllWidgetRightClick(rootWidget):
    try:
        for wType in ('Text', 'Entry'): #'Label', 'Listbox'
            rootWidget.bind_class(wType, sequence='<Button-3>', func=rightClicker, add='')
    except TclError:
        print('bindAllWidgetRightClick bind error')
        pass

