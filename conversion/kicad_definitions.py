#!/usr/bin/env python3
# -*- coding:utf-8 -*-
"""Kicad一些对应常量定义:
* 坐标系
  Kicad坐标系原点在左上角(屏幕坐标系)
  Sprint-Layout坐标系原点在左下角(标准笛卡尔坐标系)
* 数值单位
  Kicad 数值使用浮点数,单位为mm
  Sprint-Layout 数值使用整数,单位为0.1微米(万分之一毫米), 除以10000就是mm值
* 角度和旋转
  Kicad 角度零度是X轴正方向,逆时针旋转为正,顺时针为负
  Sprint-Layout 角度零度是X轴正方向,顺时针旋转为正,逆时针为负
  大部分元件的旋转中心点是元件中心,但是Sprint-Layout的文本例外,绕文本左下角旋转

Author: cdhigh <https://github.com/cdhigh>
"""
from sprint_struct.sprint_element import *
from sprint_struct.sprint_pad import *

#kicad板层和Sprint-Layout板层的对应关系
kicadLayerMap = {
    "*.Cu":    LAYER_C1,
    "F.Cu":    LAYER_C1,
    "F.SilkS": LAYER_S1,
    "B.Cu":    LAYER_C2,
    "B.SilkS": LAYER_S2,
    "F.Fab":   LAYER_U,
    "B.Fab":   LAYER_U,
    "F.CrtYd": LAYER_S1,
    "B.CrtYd": LAYER_S2,
    "F.Paste": LAYER_S1,
    "B.Paste": LAYER_S2,
    "F.Mask":  LAYER_S1,
    "B.Mask":  LAYER_S2,
    "Edge.Cuts": LAYER_U,
    "Margin":  LAYER_U,
    "In1.Cu": LAYER_I1,
    "In2.Cu": LAYER_I2,
}

#kicad焊盘形状和Sprint-Layout的对应关系
kicadPadShapeMap = {
    'circle': PAD_FORM_ROUND,
    'rect': PAD_FORM_SQUARE,
    'oval': PAD_FORM_ROUND,
    'trapezoid': PAD_FORM_SQUARE,
    'roundrect': PAD_FORM_OCTAGON,
    'custom': PAD_FORM_OCTAGON,
}

#Sprint-Layout的角度转换为Kicad的角度
def sprintAngleToKicad(angle):
    return int((360 - angle) % 360)
