#!/usr/bin/env python3
# -*- coding:utf-8 -*-
"""
测试SVG导出功能
用法: python test_svg_export.py <输入的sprint文件> <输出的svg文件>
"""
import sys
import os
import unittest
import tempfile

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sprint_struct.sprint_element import LAYER_C1, LAYER_C2
from sprint_struct.sprint_pad import SprintPad
from sprint_struct.sprint_textio import SprintTextIO
from conversion.sprint_to_svg import SVGGenerator

class TestSvgExport(unittest.TestCase):
    #测试单铜层导出遇到存储在背面(C2)的过孔焊盘时不发生 KeyError，且能正确导出
    def test_opposite_layer_via(self):
        textIo = SprintTextIO(pcbWidth=50.0, pcbHeight=50.0)
        viaPad = SprintPad('PAD', LAYER_C2)
        viaPad.pos = (25.0, 25.0)
        viaPad.size = 1.6
        viaPad.drill = 0.8
        viaPad.via = True
        textIo.add(viaPad)

        tmpFile = tempfile.mktemp(suffix='.svg')
        try:
            gen = SVGGenerator(textIo, layers=[LAYER_C1])
            err = gen.generate(tmpFile)
            self.assertEqual(err, '')

            with open(tmpFile, 'r', encoding='utf-8') as f:
                content = f.read()

            self.assertIn('circle', content)
        finally:
            if os.path.exists(tmpFile):
                os.remove(tmpFile)

    #测试圆弧在默认 mirrorY=False (Y向下坐标系)下的方向与起止点正确性
    def test_arc_orientation(self):
        from sprint_struct.sprint_circle import SprintCircle
        textIo = SprintTextIO(pcbWidth=100.0, pcbHeight=100.0)
        arc = SprintCircle(LAYER_C1)
        arc.center = (50.0, 50.0)
        arc.radius = 10.0
        arc.width = 1.0
        arc.start = 0.0
        arc.stop = 90.0
        textIo.add(arc)

        tmpFile = tempfile.mktemp(suffix='.svg')
        try:
            gen = SVGGenerator(textIo, layers=[LAYER_C1], mirrorY=False)
            err = gen.generate(tmpFile)
            self.assertEqual(err, '')

            with open(tmpFile, 'r', encoding='utf-8') as f:
                content = f.read()

            # 0°为3点钟(60.5, 50.0)，90°逆时针到12点钟(50.0, 39.5)，外弧逆时针对应 sweep=0
            self.assertIn('M 60.5 50.0 A 10.5 10.5 0 0 0 50.0 39.5', content)
            self.assertIn('A 9.5 9.5 0 0 1 59.5 50.0 Z', content)
        finally:
            if os.path.exists(tmpFile):
                os.remove(tmpFile)

def test_svg_export(input_file, output_file):
    """测试SVG导出"""
    print(f"读取输入文件: {input_file}")
    
    # 读取Sprint-Layout文件
    textIo = SprintTextIO()
    textIo.parse(input_file)
    
    print(f"PCB尺寸: {textIo.pcbWidth} x {textIo.pcbHeight} mm")
    print(f"Y轴范围: {textIo.yMin} - {textIo.yMax}")
    
    # 统计各层元素数量
    for layer in range(1, 8):
        pads = list(textIo.getPads(layerIdx=[layer]))
        tracks = list(textIo.getTracks([layer]))
        circles = list(textIo.getCircles([layer]))
        polygons = list(textIo.getPolygons([layer]))
        
        total = len(pads) + len(tracks) + len(circles) + len(polygons)
        if total > 0:
            print(f"Layer {layer}: {len(pads)} pads, {len(tracks)} tracks, {len(circles)} circles, {len(polygons)} polygons")
    
    # 创建SVG生成器
    # layers=None 表示导出所有层
    generator = SVGGenerator(textIo, layers=None, mirrorY=False)
    
    print(f"\n开始生成SVG文件: {output_file}")
    error = generator.generate(output_file)
    
    if error:
        print(f"错误: {error}")
        return False
    else:
        print(f"成功! SVG文件已保存到: {output_file}")
        
        # 显示文件大小
        file_size = os.path.getsize(output_file)
        print(f"文件大小: {file_size} bytes ({file_size/1024:.2f} KB)")
        return True

if __name__ == '__main__':
    if len(sys.argv) > 1 and not sys.argv[1].startswith('-'):
        input_file = sys.argv[1]
        if not os.path.exists(input_file):
            print(f"错误: 输入文件不存在: {input_file}")
            sys.exit(1)
        output_file = sys.argv[2] if len(sys.argv) >= 3 else os.path.splitext(input_file)[0] + "_output.svg"
        success = test_svg_export(input_file, output_file)
        sys.exit(0 if success else 1)
    else:
        unittest.main()
