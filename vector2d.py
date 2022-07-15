#!/usr/bin/env python
#-*- coding:utf-8 -*-
"""
表示一个二维向量
Author: cdhigh <https://github.com/cdhigh>
"""
import math

#表示一个二维向量
class Vector2d:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y

    #向量相加
    def __add__(self, other):
        return Vector2d(self.x + other.x, self.y + other.y)

    #向量相减
    def __sub__(self, other):
        return Vector2d(self.x - other.x, self.y - other.y)

    #向量数乘
    def Scalar(self, c: float):
        return Vector2d(c * self.x, c * self.y)

    #向量点积
    def Dot(self, other):
        return self.x * other.x + self.y * other.y

    #向量的模，实际上是线段的长度
    def Mod(self):
        return math.sqrt(self.x * self.x + self.y * self.y)
