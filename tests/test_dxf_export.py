#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# DXF 导出功能单元测试

import os
import sys
import tempfile
import unittest

# 添加根目录到模块搜索路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 桩化 gettext _ 函数，避免未初始化报错
import builtins
if not hasattr(builtins, '_'):
    builtins._ = lambda x: x

from sprint_struct.sprint_element import LAYER_C1, LAYER_S1, LAYER_C2, LAYER_U
from sprint_struct.sprint_pad import (
    SprintPad, PAD_FORM_ROUND, PAD_FORM_OCTAGON, PAD_FORM_SQUARE,
    PAD_FORM_RECT_H, PAD_FORM_RECT_V, PAD_FORM_RECT_ROUND_H,
    PAD_FORM_RECT_ROUND_V, PAD_FORM_RECT_OCTAGON_H
)
from sprint_struct.sprint_track import SprintTrack
from sprint_struct.sprint_circle import SprintCircle
from sprint_struct.sprint_polygon import SprintPolygon
from sprint_struct.sprint_text import SprintText
from sprint_struct.sprint_textio import SprintTextIO
from conversion.sprint_to_dxf import DXFGenerator

class TestDxfExport(unittest.TestCase):
    def setUp(self):
        self.textIo = SprintTextIO(pcbWidth=100.0, pcbHeight=80.0)

        # 1. 各种焊盘
        # 圆形通孔焊盘（带钻孔）
        padRound = SprintPad('PAD', LAYER_C1)
        padRound.pos = (10.0, 10.0)
        padRound.size = 2.0
        padRound.drill = 1.0
        padRound.form = PAD_FORM_ROUND
        self.textIo.add(padRound)

        # 八角形焊盘
        padOctagon = SprintPad('PAD', LAYER_C1)
        padOctagon.pos = (20.0, 10.0)
        padOctagon.size = 2.0
        padOctagon.drill = 0.8
        padOctagon.form = PAD_FORM_OCTAGON
        self.textIo.add(padOctagon)

        # 方形焊盘
        padSquare = SprintPad('PAD', LAYER_C1)
        padSquare.pos = (30.0, 10.0)
        padSquare.size = 2.0
        padSquare.form = PAD_FORM_SQUARE
        self.textIo.add(padSquare)

        # SMD 矩形焊盘（带旋转角）
        padSmd = SprintPad('SMDPAD', LAYER_C1)
        padSmd.pos = (40.0, 10.0)
        padSmd.sizeX = 1.5
        padSmd.sizeY = 3.0
        padSmd.rotation = 45.0
        self.textIo.add(padSmd)

        # 水平圆角矩形(跑道型)焊盘
        padRoundH = SprintPad('PAD', LAYER_C1)
        padRoundH.pos = (50.0, 10.0)
        padRoundH.size = 2.0
        padRoundH.form = PAD_FORM_RECT_ROUND_H
        self.textIo.add(padRoundH)

        # 垂直圆角矩形焊盘
        padRoundV = SprintPad('PAD', LAYER_C1)
        padRoundV.pos = (60.0, 10.0)
        padRoundV.size = 2.0
        padRoundV.form = PAD_FORM_RECT_ROUND_V
        self.textIo.add(padRoundV)

        # 倒角矩形焊盘
        padOctH = SprintPad('PAD', LAYER_C1)
        padOctH.pos = (70.0, 10.0)
        padOctH.size = 2.0
        padOctH.form = PAD_FORM_RECT_OCTAGON_H
        self.textIo.add(padOctH)

        # 2. 导线
        track = SprintTrack(layerIdx=LAYER_C1, width=0.5)
        track.points = [(10.0, 10.0), (20.0, 20.0), (30.0, 20.0)]
        self.textIo.add(track)

        # 3. 圆形与圆弧
        circle = SprintCircle(layerIdx=LAYER_S1)
        circle.center = (50.0, 50.0)
        circle.radius = 5.0
        circle.start = 0
        circle.stop = 0
        self.textIo.add(circle)

        # 开孔圆（应出现在 DRILL 层）
        cutoutCircle = SprintCircle(layerIdx=LAYER_U)
        cutoutCircle.center = (80.0, 70.0)
        cutoutCircle.radius = 2.5
        cutoutCircle.cutout = True
        cutoutCircle.start = 0
        cutoutCircle.stop = 0
        self.textIo.add(cutoutCircle)

        # 圆弧
        arc = SprintCircle(layerIdx=LAYER_S1)
        arc.center = (30.0, 50.0)
        arc.radius = 4.0
        arc.start = 45.0
        arc.stop = 180.0
        self.textIo.add(arc)

        # 4. 多边形
        zone = SprintPolygon(layerIdx=LAYER_C1, width=0.2)
        zone.points = [(0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0)]
        self.textIo.add(zone)

        # 5. 文本
        text = SprintText(layerIdx=LAYER_S1)
        text.pos = (5.0, 5.0)
        text.text = 'TEST_PCB'
        text.height = 2.0
        text.rotation = 90.0
        self.textIo.add(text)

    def test_export_all_layers(self):
        with tempfile.NamedTemporaryFile(suffix='.dxf', delete=False) as tf:
            tempPath = tf.name

        try:
            generator = DXFGenerator(self.textIo, layers=None)
            err = generator.generate(tempPath)
            self.assertEqual(err, '')

            with open(tempPath, 'r', encoding='utf-8') as f:
                content = f.read()

            # 验证 DXF 关键结构
            self.assertIn('$ACADVER\n1\nAC1015', content)
            self.assertIn('$INSUNITS\n70\n4', content)      # 毫米单位
            self.assertIn('$MEASUREMENT\n70\n1', content)  # 公制
            self.assertIn('SECTION\n2\nTABLES', content)
            self.assertIn('TABLE\n2\nLAYER', content)
            self.assertIn('LAYER\n5\n', content)
            self.assertIn('2\nC1', content)
            self.assertIn('2\nS1', content)
            self.assertIn('2\nDRILL', content)
            self.assertIn('SECTION\n2\nENTITIES', content)
            self.assertIn('0\nCIRCLE', content)
            self.assertIn('0\nARC', content)
            self.assertIn('0\nLWPOLYLINE', content)
            self.assertIn('0\nTEXT', content)
            self.assertIn('1\nTEST_PCB', content)
            self.assertIn('0\nEOF', content)

            # 验证凸度 (bulge) 存在于圆角焊盘
            self.assertIn('42\n1', content)

            # 验证钻孔层包含焊盘孔与开孔
            self.assertIn('8\nDRILL', content)

            # 验证 Y 轴正确镜像翻转（原 (10, 10) 焊盘翻转为 (10, 80-10=70)）
            self.assertIn('10\n10\n20\n70', content)
            # 验证文字 Y 坐标（原 (5, 5) 文字翻转为 (5, 80-5=75)）
            self.assertIn('10\n5\n20\n75', content)
        finally:
            if os.path.exists(tempPath):
                os.remove(tempPath)

    def test_export_single_layer(self):
        with tempfile.NamedTemporaryFile(suffix='.dxf', delete=False) as tf:
            tempPath = tf.name

        try:
            # 仅导出板框层 (LAYER_U)
            generator = DXFGenerator(self.textIo, layers=LAYER_U)
            err = generator.generate(tempPath)
            self.assertEqual(err, '')

            with open(tempPath, 'r', encoding='utf-8') as f:
                content = f.read()

            self.assertIn('2\nU', content)
            self.assertNotIn('1\nTEST_PCB', content) # S1 层的文字不应出现在 U 层导出中
        finally:
            if os.path.exists(tempPath):
                os.remove(tempPath)

    def test_auto_board_outline(self):
        # 无任何元素的空板
        emptyIo = SprintTextIO(pcbWidth=50.0, pcbHeight=30.0)
        with tempfile.NamedTemporaryFile(suffix='.dxf', delete=False) as tf:
            tempPath = tf.name

        try:
            generator = DXFGenerator(emptyIo, layers=LAYER_U)
            err = generator.generate(tempPath)
            self.assertEqual(err, '')

            with open(tempPath, 'r', encoding='utf-8') as f:
                content = f.read()

            # 应自动生成 U 层板框折线
            self.assertIn('8\nU', content)
            self.assertIn('0\nLWPOLYLINE', content)
        finally:
            if os.path.exists(tempPath):
                os.remove(tempPath)

if __name__ == '__main__':
    unittest.main()
