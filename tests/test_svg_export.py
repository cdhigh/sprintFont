#!/usr/bin/env python3
# -*- coding:utf-8 -*-
"""
测试SVG导出功能
用法: python test_svg_export.py <输入的sprint文件> <输出的svg文件>
"""
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sprint_struct.sprint_textio import SprintTextIO
from conversion.sprint_to_svg import SVGGenerator

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
    if len(sys.argv) < 2:
        print("用法: python test_svg_export.py <输入文件> [输出文件]")
        print("\n示例:")
        print("  python test_svg_export.py test.txt")
        print("  python test_svg_export.py test.txt output.svg")
        sys.exit(1)
    
    input_file = sys.argv[1]
    if not os.path.exists(input_file):
        print(f"错误: 输入文件不存在: {input_file}")
        sys.exit(1)
    
    # 如果没有指定输出文件,使用默认名称
    if len(sys.argv) >= 3:
        output_file = sys.argv[2]
    else:
        base_name = os.path.splitext(input_file)[0]
        output_file = base_name + "_output.svg"
    
    success = test_svg_export(input_file, output_file)
    sys.exit(0 if success else 1)
