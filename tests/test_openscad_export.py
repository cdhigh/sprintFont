#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# OpenSCAD 导出功能单元测试

import os
import sys
import tempfile
import unittest

# 添加根目录到模块搜索路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import builtins
if not hasattr(builtins, '_'):
    builtins._ = lambda x: x

from sprint_struct.sprint_element import LAYER_C1, LAYER_S1, LAYER_C2
from sprint_struct.sprint_pad import SprintPad, PAD_FORM_OCTAGON, PAD_FORM_RECT_H
from sprint_struct.sprint_circle import SprintCircle
from sprint_struct.sprint_textio import SprintTextIO
from conversion.sprint_to_openscad import OpenSCADGenerator

class TestOpenScadExport(unittest.TestCase):
    def setUp(self):
        self.textIo = SprintTextIO(pcbWidth=100.0, pcbHeight=80.0)

        # 45度旋转 SMD 焊盘
        padSmd = SprintPad('SMDPAD', LAYER_C1)
        padSmd.pos = (30.0, 40.0)
        padSmd.sizeX = 4.0
        padSmd.sizeY = 2.0
        padSmd.rotation = 45.0
        self.textIo.add(padSmd)

        # 45度旋转八角形焊盘
        padOct = SprintPad('PAD', LAYER_C1)
        padOct.pos = (50.0, 40.0)
        padOct.size = 3.0
        padOct.form = PAD_FORM_OCTAGON
        padOct.rotation = 45.0
        self.textIo.add(padOct)

        # 0度八角形焊盘
        padOct0 = SprintPad('PAD', LAYER_C1)
        padOct0.pos = (60.0, 40.0)
        padOct0.size = 3.0
        padOct0.form = PAD_FORM_OCTAGON
        padOct0.rotation = 0.0
        self.textIo.add(padOct0)

        # 圆弧 (0度到90度)
        arc = SprintCircle(LAYER_S1)
        arc.center = (70.0, 40.0)
        arc.radius = 5.0
        arc.width = 0.5
        arc.start = 0.0
        arc.stop = 90.0
        self.textIo.add(arc)

    #测试默认 mirrorY=True 时的焊盘与圆弧角度镜像转换
    def testMirrorYAngles(self):
        tmpFile = tempfile.mktemp(suffix='.scad')
        try:
            gen = OpenSCADGenerator(self.textIo, mirrorY=True)
            err = gen.generate(tmpFile)
            self.assertEqual(err, '')

            with open(tmpFile, 'r', encoding='utf-8') as f:
                code = f.read()

            # 45度顺时针旋转在 OpenSCAD 镜像后应为 315度 (或 -45度)
            self.assertIn('rotate(315', code)
            self.assertIn('square([4', code)
            # 45度八角焊盘应为 (315 + 22.5) % 360 = 337.5度
            self.assertIn('rotate(337.5) circle(', code)
            # 0度八角焊盘保持默认 22.5度
            self.assertIn('rotate(22.5) circle(', code)
            # 0~90度圆弧在 Y 镜像后天然保持 0~90度(两者均为逆时针为正)
            self.assertIn('arcRing(70', code)
            self.assertIn('0.0, 90.0', code)
        finally:
            if os.path.exists(tmpFile):
                os.remove(tmpFile)

    #测试 mirrorY=False 时的角度
    def testNoMirrorAngles(self):
        tmpFile = tempfile.mktemp(suffix='.scad')
        try:
            gen = OpenSCADGenerator(self.textIo, mirrorY=False)
            err = gen.generate(tmpFile)
            self.assertEqual(err, '')

            with open(tmpFile, 'r', encoding='utf-8') as f:
                code = f.read()

            self.assertIn('rotate(45', code)
            self.assertIn('square([4', code)
            self.assertIn('rotate(67.5) circle(', code)
            # mirrorY=False 时坐标系未翻转，圆弧角度需反转为 270~0度
            self.assertIn('arcRing(70', code)
            self.assertIn('270.0, 0.0', code)
        finally:
            if os.path.exists(tmpFile):
                os.remove(tmpFile)

    #测试单铜层导出遇到存储在背面(C2)的过孔焊盘时不发生 KeyError，且能正确导出到 C1
    def testOppositeLayerVia(self):
        textIo = SprintTextIO(pcbWidth=50.0, pcbHeight=50.0)
        viaPad = SprintPad('PAD', LAYER_C2)
        viaPad.pos = (25.0, 25.0)
        viaPad.size = 1.6
        viaPad.drill = 0.8
        viaPad.via = True
        textIo.add(viaPad)

        tmpFile = tempfile.mktemp(suffix='.scad')
        try:
            gen = OpenSCADGenerator(textIo, layers=[LAYER_C1])
            err = gen.generate(tmpFile)
            self.assertEqual(err, '')

            with open(tmpFile, 'r', encoding='utf-8') as f:
                code = f.read()
            self.assertIn('circle(r=0.8', code)
            self.assertIn('circle(r=0.4', code)
        finally:
            if os.path.exists(tmpFile):
                os.remove(tmpFile)

if __name__ == '__main__':
    unittest.main()
