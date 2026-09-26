#!/usr/bin/env python3
# -*- coding:utf-8 -*-
"""tkinter控件的鼠标悬浮提示
Author: cdhigh <https://github.com/cdhigh>
"""
import tkinter as tk
from tkinter import ttk

class Tooltip:
    def __init__(self, widget, text, bg='#FFFFEA', pad=(5, 3, 5, 3), waittime=500, wraplength=300):
        self.waittime = waittime
        self.wraplength = wraplength
        self.widget = widget
        self.text = text
        self.widget.bind('<Enter>', self.onEnter)
        self.widget.bind('<Leave>', self.onLeave)
        self.widget.bind('<ButtonPress>', self.onLeave)
        self.bg = bg
        self.pad = pad
        self.id_ = None
        self.tw = None

    def onEnter(self, event=None):
        self.schedule()

    def onLeave(self, event=None):
        self.unschedule()
        self.Hide()

    def schedule(self):
        self.unschedule()
        self.id_ = self.widget.after(self.waittime, self.Show)

    def unschedule(self):
        id_ = self.id_
        self.id_ = None
        if id_:
            self.widget.after_cancel(id_)

    def Show(self):
        def tip_pos_calculator(widget, label, pad=(5, 3, 5, 3), tip_delta=(15, 10)):
            s_width, s_height = widget.winfo_screenwidth(), widget.winfo_screenheight()
            width, height = (pad[0] + label.winfo_reqwidth() + pad[2], pad[1] + label.winfo_reqheight() + pad[3])
            mouse_x, mouse_y = widget.winfo_pointerxy()
            x1, y1 = mouse_x + tip_delta[0], mouse_y + tip_delta[1]
            if x1 + width > s_width:
                x1 = mouse_x - tip_delta[0] - width
            if y1 + height > s_height - 30:
                y1 = mouse_y - tip_delta[1] - height
                if y1 < 0:
                    Y1 = 0
            return x1, y1

        self.Hide()
        self.tw = tk.Toplevel(self.widget)
        self.tw.wm_overrideredirect(True)
        label = ttk.Label(self.tw, text=self.text, justify=tk.LEFT, background=self.bg, relief=tk.RAISED, borderwidth=1, wraplength=self.wraplength)
        label.pack(ipadx=1)
        x, y = tip_pos_calculator(self.widget, label, self.pad)
        self.tw.wm_geometry('+%d+%d' % (x, y))

    def Hide(self):
        tw = self.tw
        if tw:
            tw.destroy()
        self.tw = None
