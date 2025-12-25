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
    def __init__(self, pcbWidth=0, pcbHeight=0):
        super().__init__(self)
        self.pcbWidth = pcbWidth
        self.pcbHeight = pcbHeight
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

    #删除某一个对象，成功返回True
    def remove(self, obj):
        for elem in self.elements:
            if elem is obj:
                self.elements.remove(obj)
                self.updateSelfBbox()
                return True

        for elem in self.elements: #子容器递归搜索删除
            if isinstance(elem, (SprintComponent, SprintGroup)):
                if elem.remove(obj):
                    self.updateSelfBbox()
                    return True
        return False

    #删除列表中所有元素
    def removeList(self, objList: list):
        for obj in objList:
            self.remove(obj)
            
    #更新元件所占的外框
    def updateSelfBbox(self):
        self.xMin = self.yMin = float('inf')
        self.xMax = self.yMax = float('-inf')
        for elem in self.elements:
            elem.updateSelfBbox()
            self.updateBbox(elem)

    #根据绘图元素，更新元件自己的外框
    def updateBbox(self, elem):
        self.xMin = min(elem.xMin, self.xMin)
        self.xMax = max(elem.xMax, self.xMax)
        self.yMin = min(elem.yMin, self.yMin)
        self.yMax = max(elem.yMax, self.yMax)
        
    #获取所有焊盘
    #padType: 'PAD'/'SMDPAD'/none
    #layerIdx: 为空则仅返回导电焊盘, 输入参数可以是整数或一个列表
    def getPads(self, padType: str=None, layerIdx=None):
        if not layerIdx:
            layers = (LAYER_C1, LAYER_C2, LAYER_I1, LAYER_I2)
        elif isinstance(layerIdx, (list, tuple)):
            layers = layerIdx
        else:
            layers = (layerIdx,)

        padTypes = (padType,) if padType else ('PAD', 'SMDPAD')

        ret = []
        #双面焊盘相当于两个铜层都有
        viaNeed = (LAYER_C1 in layers) or (LAYER_C2 in layers)
        for elem in self.baseDrawElements():
            if not isinstance(elem, SprintPad) or (elem.padType not in padTypes):
                continue
            if (elem.layerIdx in layers) or (elem.via and viaNeed):
                ret.append(elem)
        
        return ret

    #获取所有导线，参数为空则仅返回导电导线, 输入参数可以是整数或一个列表
    def getTracks(self, layerIdx=None):
        if not layerIdx:
            layers = (LAYER_C1, LAYER_C2, LAYER_I1, LAYER_I2)
        elif isinstance(layerIdx, (list, tuple)):
            layers = layerIdx
        else:
            layers = (layerIdx,)
        return [elem for elem in self.baseDrawElements() 
            if (isinstance(elem, SprintTrack) and (elem.layerIdx in layers))]

    #获取所有多边形, 参数为空则仅返回导电多边形, 输入参数可以是整数或一个列表
    def getPolygons(self, layerIdx=None):
        if not layerIdx:
            layers = (LAYER_C1, LAYER_C2, LAYER_I1, LAYER_I2)
        elif isinstance(layerIdx, (list, tuple)):
            layers = layerIdx
        else:
            layers = (layerIdx,)
        return [elem for elem in self.baseDrawElements() 
            if (isinstance(elem, SprintPolygon) and (elem.layerIdx in layers))]

    #获取所有圆形或圆环, 参数为空则仅返回所有板层, 输入参数可以是整数或一个列表
    def getCircles(self, layerIdx=None):
        if not layerIdx:
            layers = list(range(1, 8))
        elif isinstance(layerIdx, (list, tuple)):
            layers = layerIdx
        else:
            layers = (layerIdx,)
        return [elem for elem in self.baseDrawElements() 
            if (isinstance(elem, SprintCircle) and (elem.layerIdx in layers))]
            
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
        pads = self.getPads()
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
    
    #将所有的元件分类，同样的元件存为一个列表，坐标为左下角，名字格式为 Footprint0
    #includeFreePads: 是否包含游离的焊盘，如果包含，则将游离的焊盘生成一个临时元件包装起来，元件名已PadComp开头
    #返回格式{'Footprint0': {'image': comp, 'instance': ins}, }
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
                padComp.name = f'PadComp{idx}'
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
            name = 'Footprint_{}'.format(compsOriginHashUnique.index(compsOriginHash[idx]))
            if name in compDict:
                compDict[name]['instance'].append(comp)
            else:
                compDict[name] = {'image': compsOrigin[idx], 'instance': [comp]}
        return compDict

    #整体移动自身的位置
    def moveByOffset(self, offsetX: float, offsetY: float):
        for elem in self.elements:
            elem.moveByOffset(offsetX, offsetY)
            
        self.updateSelfBbox()
    
    #合并首尾相连的track, 让圆弧导线体验更好
    #可能有多个track首尾相连, 可以统一合并为一个
    def mergeConnectedTracks(self):
        tracks = self.getTracks() #只选择导线
        if len(tracks) < 2:
            return 0
        
        pads = self.getPads()
        polys = self.getPolygons() #仅返回导电多边形
        
        #内嵌函数，判断一个点是否在导电区域（焊盘或多边形）内
        def isPointInsideConductiveArea(pt, layerIdx):
            for pad in pads:
                if ((pad.layerIdx == layerIdx) and pad.enclose(pt)):
                    return True
            for poly in polys:
                if ((poly.layerIdx == layerIdx) and poly.encircle(pt)):
                    return True
            return False
        
        # 辅助函数: 判断两个track是否可以合并 (属性相同)
        def canMerge(t1, t2):
            if t1.name or t2.name:  # 有名字的track不能合并
                return False
            return (t1.layerIdx == t2.layerIdx and
                    t1.width == t2.width and
                    t1.clearance == t2.clearance and
                    t1.cutout == t2.cutout and
                    t1.soldermask == t2.soldermask and
                    t1.flatstart == t2.flatstart and
                    t1.flatend == t2.flatend)
        
        # 辅助函数: 判断两个点是否相同 (考虑浮点数精度)
        def pointsEqual(p1, p2, tolerance=1e-6):
            return abs(p1[0] - p2[0]) < tolerance and abs(p1[1] - p2[1]) < tolerance
        
        # 辅助函数: 判断两个track是否首尾相连
        # 返回: None(不相连), 'normal'(t1尾连t2头), 'reverse'(t1尾连t2尾), 
        #      'reverse_first'(t1头连t2头), 'reverse_both'(t1头连t2尾)
        def getConnectionType(t1, t2):
            if not t1.isValid() or not t2.isValid():
                return None
            
            t1Start = t1.points[0]
            t1End = t1.points[-1]
            t2Start = t2.points[0]
            t2End = t2.points[-1]
            
            #如果首尾节点在焊盘或覆铜区域内, 这个点不应该视为和其他导线有可能连接
            if pointsEqual(t1End, t2Start) and not isPointInsideConductiveArea(t1End, t1.layerIdx):
                return 'normal'  # t1 -> t2
            elif pointsEqual(t1End, t2End) and not isPointInsideConductiveArea(t1End, t1.layerIdx):
                return 'reverse'  # t1 -> t2逆序
            elif pointsEqual(t1Start, t2Start) and not isPointInsideConductiveArea(t1Start, t1.layerIdx):
                return 'reverse_first'  # t1逆序 -> t2
            elif pointsEqual(t1Start, t2End) and not isPointInsideConductiveArea(t1Start, t1.layerIdx):
                return 'reverse_both'  # t1逆序 -> t2逆序
            return None
        
        # 辅助函数: 合并两个track的点列表
        def mergePoints(points1, points2, connectionType):
            if connectionType == 'normal':
                # t1尾 连接 t2头: 保持t1, 去掉t2的第一个点(重复点)后追加
                return points1 + points2[1:]
            elif connectionType == 'reverse':
                # t1尾 连接 t2尾: 保持t1, 将t2逆序后去掉最后一个点(重复点)
                return points1 + list(reversed(points2))[1:]
            elif connectionType == 'reverse_first':
                # t1头 连接 t2头: 将t1逆序后, 去掉t2的第一个点(重复点)后追加
                return list(reversed(points1)) + points2[1:]
            elif connectionType == 'reverse_both':
                # t1头 连接 t2尾: 将t1逆序, 将t2也逆序后去掉最后一个点(重复点)
                return list(reversed(points1)) + list(reversed(points2))[1:]
            return points1
        
        # 构建track链: 找出所有相连的track组
        mergedCount = 0
        processed = set()  # 已处理的track
        chains = []  # 存储所有的track链
        
        for i, track in enumerate(tracks):
            if i in processed:
                continue
            
            # 开始构建一个新的链
            chain = [track]
            chainIndices = [i]
            changed = True
            
            # 持续扩展链，直到没有新的track可以加入
            while changed:
                changed = False
                
                # 尝试在链的两端添加新的track
                for j, otherTrack in enumerate(tracks):
                    if j in chainIndices or j in processed:
                        continue
                    
                    if not canMerge(chain[0], otherTrack):
                        continue
                    
                    # 检查是否可以连接到链的开头
                    connType = getConnectionType(otherTrack, chain[0])
                    if connType:
                        chain.insert(0, otherTrack)
                        chainIndices.insert(0, j)
                        changed = True
                        continue
                    
                    # 检查是否可以连接到链的结尾
                    connType = getConnectionType(chain[-1], otherTrack)
                    if connType:
                        chain.append(otherTrack)
                        chainIndices.append(j)
                        changed = True
                        continue
            
            # 如果链长度大于1，说明有可以合并的track
            if len(chain) > 1:
                chains.append((chain, chainIndices))
                processed.update(chainIndices)
        
        # 执行合并操作
        for chain, chainIndices in chains:
            # 创建合并后的新track
            mergedTrack = SprintTrack(chain[0].layerIdx, chain[0].width)
            mergedTrack.clearance = chain[0].clearance
            mergedTrack.cutout = chain[0].cutout
            mergedTrack.soldermask = chain[0].soldermask
            mergedTrack.flatstart = chain[0].flatstart
            mergedTrack.flatend = chain[0].flatend
            
            # 合并所有点
            # 使用临时track来跟踪已合并的点，以正确判断连接类型
            mergedPoints = chain[0].points[:]
            for k in range(1, len(chain)):
                # 创建一个临时track来表示当前已合并的点
                tempTrack = SprintTrack()
                tempTrack.points = mergedPoints
                
                # 检查已合并的点与下一个track的连接方式
                connType = getConnectionType(tempTrack, chain[k])
                if connType == 'normal':
                    # tempTrack尾 连接 chain[k]头
                    mergedPoints.extend(chain[k].points[1:])
                elif connType == 'reverse':
                    # tempTrack尾 连接 chain[k]尾
                    mergedPoints.extend(list(reversed(chain[k].points))[1:])
                elif connType == 'reverse_first':
                    # tempTrack头 连接 chain[k]头
                    mergedPoints = list(reversed(mergedPoints)) + chain[k].points[1:]
                elif connType == 'reverse_both':
                    # tempTrack头 连接 chain[k]尾
                    mergedPoints = list(reversed(mergedPoints)) + list(reversed(chain[k].points))[1:]
            
            mergedTrack.points = mergedPoints
            mergedTrack.removeDuplicatePoints()  # 删除可能的重复点
            mergedTrack.updateSelfBbox()
            
            # 删除原来的track，添加合并后的track
            for track in chain:
                self.remove(track)
            
            self.add(mergedTrack)
            mergedCount += len(chain) - 1  # 合并数量 = 原track数 - 1
        
        return mergedCount
