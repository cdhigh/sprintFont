#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# 立创EDA格式转换单元测试（重点测试圆与圆弧的导出与往返）

import os
import sys
import json
import tempfile
import unittest

# 添加根目录到模块搜索路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import builtins
if not hasattr(builtins, '_'):
    builtins._ = lambda x: x

from sprint_struct.sprint_element import LAYER_C1, LAYER_S1
from sprint_struct.sprint_circle import SprintCircle
from sprint_struct.sprint_component import SprintComponent
from sprint_struct.sprint_textio import SprintTextIO
from conversion.sprint_to_lceda import LcedaGenerator
from conversion.lceda_to_sprint import LcComponent

class TestLcedaConversion(unittest.TestCase):
    #测试整圆导出为 CIRCLE 图元
    def testCircleExport(self):
        tio = SprintTextIO()

        # 默认 start=0, stop=0 整圆
        c1 = SprintCircle(LAYER_C1)
        c1.center = (10.0, 15.0)
        c1.radius = 5.0
        c1.width = 0.2
        tio.add(c1)

        # start == stop 非零整圆
        c2 = SprintCircle(LAYER_C1)
        c2.center = (20.0, 15.0)
        c2.radius = 4.0
        c2.width = 0.2
        c2.start = 90.0
        c2.stop = 90.0
        tio.add(c2)

        # 跨度 360 度整圆
        c3 = SprintCircle(LAYER_C1)
        c3.center = (30.0, 15.0)
        c3.radius = 3.0
        c3.width = 0.2
        c3.start = 0.0
        c3.stop = 360.0
        tio.add(c3)

        # 实心填充圆
        c4 = SprintCircle(LAYER_C1)
        c4.center = (40.0, 15.0)
        c4.radius = 2.0
        c4.width = 0.2
        c4.fill = True
        c4.start = 0.0
        c4.stop = 180.0
        tio.add(c4)

        tmpFile = tempfile.mktemp(suffix='.json')
        try:
            gen = LcedaGenerator(tio)
            gen.generate(tmpFile)
            with open(tmpFile, 'r', encoding='utf-8') as f:
                data = json.load(f)
            shapes = data.get('shape', [])
            self.assertEqual(len(shapes), 4)
            for s in shapes:
                self.assertTrue(s.startswith('CIRCLE~'), f"Expected CIRCLE primitive, got: {s}")
        finally:
            if os.path.exists(tmpFile):
                os.remove(tmpFile)

    #测试圆弧导出为 ARC 图元及与 lceda_to_sprint 的往返对称性
    def testArcExportAndRoundtrip(self):
        tio = SprintTextIO()

        arcConfigs = [
            (0.0, 90.0),    # 第1象限小圆弧
            (90.0, 270.0),  # 180度半圆
            (45.0, 315.0),  # 270度大圆弧 (>180度)
            (300.0, 60.0),  # 跨越0度小圆弧 (120度)
            (60.0, 300.0),  # 跨越0度大圆弧 (240度)
        ]

        for startDeg, stopDeg in arcConfigs:
            arc = SprintCircle(LAYER_S1)
            arc.center = (25.0, 30.0)
            arc.radius = 8.0
            arc.width = 0.25
            arc.start = startDeg
            arc.stop = stopDeg
            tio.add(arc)

        tmpFile = tempfile.mktemp(suffix='.json')
        try:
            gen = LcedaGenerator(tio)
            gen.generate(tmpFile)
            with open(tmpFile, 'r', encoding='utf-8') as f:
                data = json.load(f)
            shapes = data.get('shape', [])
            self.assertEqual(len(shapes), len(arcConfigs))

            for idx, shapeStr in enumerate(shapes):
                self.assertTrue(shapeStr.startswith('ARC~'), f"Expected ARC primitive, got: {shapeStr}")

                # 使用导入侧 LcComponent 解析并验证几何恢复
                p = LcComponent()
                comp = SprintComponent()
                p.handleArc(shapeStr.split('~')[1:], comp)
                self.assertEqual(len(comp.elements), 1)
                rec = comp.elements[0]

                origStart, origStop = arcConfigs[idx]
                normOrigStart = origStart % 360
                normOrigStop = origStop % 360
                normRecStart = rec.start % 360
                normRecStop = rec.stop % 360

                self.assertAlmostEqual(normOrigStart, normRecStart, delta=0.5)
                self.assertAlmostEqual(normOrigStop, normRecStop, delta=0.5)
                self.assertAlmostEqual(rec.radius, 8.0, delta=0.05)
                self.assertAlmostEqual(rec.width, 0.25, delta=0.05)
        finally:
            if os.path.exists(tmpFile):
                os.remove(tmpFile)

    #测试组件内部圆弧导出
    def testComponentWithArc(self):
        tio = SprintTextIO()
        comp = SprintComponent()
        comp.idText.text = 'U1'
        comp.package = 'SOP-8'

        arc = SprintCircle(LAYER_S1)
        arc.center = (10.0, 10.0)
        arc.radius = 3.0
        arc.width = 0.15
        arc.start = 45.0
        arc.stop = 135.0
        comp.add(arc)
        tio.add(comp)

        tmpFile = tempfile.mktemp(suffix='.json')
        try:
            gen = LcedaGenerator(tio)
            gen.generate(tmpFile)
            with open(tmpFile, 'r', encoding='utf-8') as f:
                data = json.load(f)
            shapes = data.get('shape', [])
            self.assertEqual(len(shapes), 1)
            libStr = shapes[0]
            self.assertTrue(libStr.startswith('LIB~'))
            self.assertIn('ARC~', libStr)
        finally:
            if os.path.exists(tmpFile):
                os.remove(tmpFile)

    #测试负旋转角度归一化到 [0, 360) 范围
    def testNegativeRotationNormalization(self):
        p = LcComponent()
        p.importText = True
        comp = SprintComponent()

        # PAD: rotation = -90 (data[10]), 应归一化为 90度而非 450度
        padData = ['RECT', '100', '100', '50', '30', '1', '', '1', '0', '', '-90']
        p.handlePad(padData, comp)
        self.assertEqual(len(comp.elements), 1)
        pad = comp.elements[0]
        self.assertEqual(pad.rotation, 90)

        # TEXT: rotation = -90 (data[4]), 应归一化为 90度而非 450度
        textData = ['TEXT', '100', '100', '50', '-90', '0', '3', '', '40', 'TEST']
        p.handleText(textData, comp)
        self.assertEqual(len(comp.elements), 2)
        text = comp.elements[1]
        self.assertEqual(text.rotation, 90)

if __name__ == '__main__':
    unittest.main()
