#!/usr/bin/env python
#-*- coding:utf-8 -*-
"""
表示Sprint-Layout的TextIO对象
保存到里面的参数使用mm为单位，角度单位为度，仅仅在输出文本时再转换为0.1微米和0.001度
Author: cdhigh <https://github.com/cdhigh>
"""

from .sprint_element import *
from .sprint_track import SprintTrack
from .sprint_polygon import SprintPolygon
from .sprint_pad import *
from .sprint_text import SprintText
from .sprint_circle import SprintCircle
from .sprint_group import SprintGroup
from .sprint_component import SprintComponent

class SprintTextIO(SprintElement):
    def __init__(self):
        super().__init__(self)
        self.elements = [] #各种绘图元素，都是SprintElement的子类
        
    def isValid(self):
        return (len(self.elements) > 0)

    #转换为字符串TextIO
    def __str__(self):
        return '\n'.join([str(obj) for obj in self.elements])
    
    #统一的添加绘图元素接口
    def add(self, elem: SprintComponent):
        if elem:
            elem.updateSelfBbox()
            self.updateBbox(elem)
            self.elements.append(elem)

    #添加列表中所有元素
    def addAll(self, elemList: list):
        for elem in elemList:
            self.add(elem)
    
    #更新元件所占的外框
    def updateSelfBbox(self):
        for elem in self.elements:
            elem.updateSelfBbox()
            self.updateBbox(elem)

    #根据绘图元素，更新元件自己的外框
    def updateBbox(self, elem):
        if elem.xMin < self.xMin:
            self.xMin = elem.xMin
        if elem.xMax > self.xMax:
            self.xMax = elem.xMax
        if elem.yMin < self.yMin:
            self.yMin = elem.yMin
        if elem.yMax > self.yMax:
            self.yMax = elem.yMax

    #获取特定板层的所有元素，返回一个列表
    def getAllElementsInLayer(self, layerIdx: int):
        elems = []
        for elem in self.elements:
            if isinstance(elem, (SprintComponent, SprintGroup)):
                elems.extend(elem.getAllElementsInLayer(layerIdx))
            elif elem.layerIdx == layerIdx:
                elems.append(elem)

        return elems

    #获取所有的下层绘图元素，如果碰到分组则先展开，返回一个列表，元件当作一个独立完整的绘图元素
    def children(self):
        elems = []
        for elem in self.elements:
            if isinstance(elem, SprintGroup):
                elems.extend(elem.children())
            else:
                elems.append(elem)
        return elems

    #获取可以当作元件的Group，标准是
    #1. 内部不包含元件
    #2. 内部包含至少一个焊盘
    #3. Group嵌套层次中合适条件的最上层
    def compLikeGroups(self, elems=None):
        if elems is None:
            elems = []
        for elem in self.elements:
            if isinstance(elem, SprintComponent):
                return [] #本Group里面有元件，则此Group不能当作元件
            #elif isinstance(elem, SprintGroup): #看下层是否合适

        return elems

    #获取所有的下层基本绘图元素，如果碰到分组/元件则先展开，返回一个列表
    def baseDrawElements(self):
        elems = []
        for elem in self.elements:
            if isinstance(elem, (SprintComponent, SprintGroup)):
                elems.extend(elem.baseDrawElements())
            else:
                elems.append(elem)
        return elems

    #将所有焊盘分类，同样形状的存入一个列表，字典的键为焊盘形状的名字
    def categorizePads(self):
        pads = [elem for elem in self.baseDrawElements() if isinstance(elem, SprintPad)]
        padDict = {}
        for pad in pads:
            name = pad.generateDsnName()
            if name in padDict:
                padDict[name].append(pad)
            else:
                padDict[name] = [pad]

        return padDict

    #每个焊盘都分配一个ID，这个函数要尽早调用
    def ensurePadHasId(self):
        pads = [e for e in self.baseDrawElements() if isinstance(e, SprintPad)]
        #第一步，获取已经分配的最大ID
        padIds = [pad.padId for pad in pads if pad.padId is not None]
        maxId = max(padIds) if padIds else 1

        #开始给还没有ID的焊盘分配一个ID
        for pad in pads:
            if pad.padId is None:
                pad.padId = maxId
                maxId += 1

    #保证所有的元件都有名字，如果有名字，名字里面不能有非法字符，这个函数要尽早调用
    def ensureComponentHasName(self):
        idx = 0
        for elem in self.children():
            if isinstance(elem, SprintComponent):
                if elem.name:
                    elem.name = elem.name.replace('"', '_').replace("'", '_') #避免freerouting解析出错
                    elem.value = elem.value.replace('"', '_').replace("'", '_') #避免freerouting解析出错
                else:
                    elem.name = f'unnamed_{idx}'
                idx += 1
    
    #将所有的元件分类，同样的元件存为一个列表，坐标为左下角，名字格式为 Component_0
    #includeFreePads: 是否包含游离的焊盘，如果包含，则将游离的焊盘生成一个临时元件包装起来，元件名已PadComp开头
    #返回格式{'Component_0': {'image': comp, 'instance': ins}, }
    def categorizeComponents(self, includeFreePads: bool=True, includeGroups: bool=True):
        children = self.children()
        comps = [elem for elem in children if isinstance(elem, SprintComponent)]
        #if includeGroups: #将内部不包含元件的Group当作元件
        #    for elem in children:

        if includeFreePads: #包含游离焊盘
            pads = [elem for elem in children if isinstance(elem, SprintPad)]
            idx = 0
            for pad in pads:
                padComp = SprintComponent()
                padComp.name = f'PaDcOmP{idx}'
                idx += 1
                padComp.add(pad)
                comps.append(padComp)
                #print(padComp.xMin, padComp.xMax)

        #将每个元件都克隆一份，以自身左下角为原点，方便下面判断元件是否相等
        compsOrigin = [elem.cloneToOrigin() for elem in comps]

        #判断两个元件是否是一样的元件的方法是将其转换为字符串，然后再通过最快的内置hash()函数计算出来一个整数
        #hash相等则认为相等，注意每次执行一个新的python实例，hash()返回的数值是不同的
        #但是每个python实例执行期间，字符串相等则hash值相等
        compsOriginHash = [hash(elem.toStr(forCompare=True)) for elem in compsOrigin]
        compsOriginHashUnique = list(set(compsOriginHash))
        compDict = {}
        for idx, comp in enumerate(comps):
            comp.updateSelfBbox()
            name = 'Component_{}'.format(compsOriginHashUnique.index(compsOriginHash[idx]))
            if name in compDict:
                compDict[name]['instance'].append(comp)
            else:
                compDict[name] = {'image': compsOrigin[idx], 'instance': [comp]}
        return compDict


