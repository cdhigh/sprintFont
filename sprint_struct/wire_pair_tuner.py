#!/usr/bin/env python3
# -*- coding:utf-8 -*-
"""匹配 导线对 的长度
"""
import math, itertools, copy
from tkinter import *
from tkinter.ttk import *
import tkinter as tk
from tkinter.messagebox import *
from utils.comm_utils import *
import sprint_struct.sprint_textio as sprint_textio

#点击按钮时的修饰键掩码
MODIFIER_SHIFT = 0x0001
MODIFIER_CTRL = 0x0004
MODIFIER_ALT = 0x0008

class WirePairTuner(Toplevel):
    #注意：调用前请保证参数合法
    #textIo: SprintTextIO 实例，至少要有两根同层的导线
    #params: 界面上的配置参数
    def __init__(self, parent, textIo, params):
        root = parent.master
        super().__init__(root)
        self.title(_("Differential Wire Pair Length Tuning"))
        ws = root.winfo_screenwidth()
        hs = root.winfo_screenheight()
        self.geometry("{}x{}+0+0".format(ws - 20, hs - 100))
        self.iconphoto(False, parent.iconimg)
        self.transient(root)
        self.grab_set()
        self.createWidgets()
        
        self.wpType = params.get('type')
        self.aMin = params.get('aMin') or 0.1
        self.aMax = params.get('aMax') or 1
        self.spacing = params.get('spacing') or 0.6
        self.skew = params.get('skew') or 0
        
        self.textIo = textIo
        tracks = textIo.getTracks()
        assert(len(tracks) > 1)
        tracks.sort(key=lambda x: x.length, reverse=True) #最长的一根导线排在开头
        self.orgTracks = tracks
        self.tracks = [] #之后的导线长度调整在这个列表上修改
        self.margin = 30 #绘图边缘
        self.cavOrgPoints = None
        self.cavPoints = None
        self.trackIndex = 0
        self.segIndex = 0
        self.projPt = None
        self.mousePt = None
        self.deviation = 0.0 #最新创建的蛇形线和最长线的偏差
        self.spacingDelta = 0 #手动调整间隔，每次步进0.1mm，可正可负
        self.ridgeDelta = 0 #手动调整隆起个数，相当于调整振幅
        self.tagsMap = {}
        root.after(100, self.refreshDraw)

    #创建窗口控件
    def createWidgets(self):
        self.style = Style()
        buttonFrame = Frame(self)
        buttonFrame.pack(fill=tk.X, padx=5, pady=5)

        # 按钮列表
        buttons = [
            (_("Deviation-"), self.subDeviation),
            (_("Spacing+"), self.addSpacing),
            (_("Spacing-"), self.subSpacing),
            (_("Amplitude+"), self.addAmplitude),
            (_("Amplitude-"), self.subAmplitude),
            (_("Confirm"), self.confirm),
            (_("Cancel"), lambda event=None: self.destroy())
        ]
        for text, cmd in buttons:
            btn = Button(buttonFrame, text=text)
            btn.bind("<Button-1>", cmd)
            btn.pack(side=tk.LEFT, padx=5)
        self.style.configure('TlblTips.TLabel', anchor='w', foreground='#000000', background='#FFF5CC')
        self.lblTips = Label(self, text=_("Click the short track at the desired location to add a serpentine trace for length matching"), style='TlblTips.TLabel')
        self.lblTips.pack(fill=tk.X, padx=5, pady=2)
        self.canvas = Canvas(self, bg="black")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvasW = self.canvas.winfo_width()
        self.canvasH = self.canvas.winfo_height()
        self.canvas.bind("<Button-1>", self.canvasClick)
        self.canvas.bind("<Motion>", self.canvasMouseMove)
        self.bind("<Configure>", self.refreshDraw)

    #因为这个窗口是另一个事件循环，在按钮事件中处理showinfo会出现按钮无法弹出的情况，需要使用此函数弹出提示
    def showInfo(self, msg):
        self.after(10, lambda: showinfo(_("info"), msg))
        
    #减小长度偏差
    def subDeviation(self, event):
        if self.trackIndex == 0:
            self.showInfo(_("Please click on a track first to add a serpentine trace"))
            return
        if -0.01 <= self.deviation <= 0.01:
            self.showInfo(_("The deviation is already small enough"))
            return

        self.lblTips.configure(text='')
        if self.deviation < 0:
            values = [x / 10 for x in range(-1, int((self.deviation - 5.0) * 10) - 1, -1)]
        else:
            values = [x / 10 for x in range(1, int((self.deviation + 5.0) * 10) + 1)]

        #遍历这些数值，找到一个偏差最小的
        prevDeviation = self.deviation
        minDeviation = 99999999999
        minValue = 0
        for idx, value in enumerate(values):
            if self.wpType == 0:
                self.adjustSingleSidedLen(value, draw=False)
            else:
                self.adjustDoubleSidedLen(value, draw=False)
            if abs(self.deviation) <= 0.01: #偏差足够小了，提前退出
                minDeviation = self.deviation
                minValue = value
                break
            elif abs(self.deviation) < abs(minDeviation):
                minDeviation = self.deviation
                minValue = value
        
        if abs(minDeviation) < abs(prevDeviation):
            if self.wpType == 0:
                self.adjustSingleSidedLen(minValue)
            else:
                self.adjustDoubleSidedLen(minValue)
        else:
            if self.wpType == 0:
                self.adjustSingleSidedLen()
            else:
                self.adjustDoubleSidedLen()
        
    #增加宽度/间隔
    def addSpacing(self, event):
        if event.state & MODIFIER_SHIFT:
            self.changeSpacingDelta(0.1)
        elif event.state & MODIFIER_CTRL:
            self.changeSpacingDelta(1)
        else:
            self.changeSpacingDelta(0.2)
        
    #减小宽度/间隔
    def subSpacing(self, event):
        if event.state & MODIFIER_SHIFT:
            self.changeSpacingDelta(-0.1)
        elif event.state & MODIFIER_CTRL:
            self.changeSpacingDelta(-1)
        else:
            self.changeSpacingDelta(-0.2)
        
    #实际增加减小宽度/间隔
    def changeSpacingDelta(self, delta):
        self.lblTips.configure(text='')
        self.ridgeDelta = 0
        self.spacingDelta += delta
        if self.wpType == 0:
            self.adjustSingleSidedLen()
        else:
            self.adjustDoubleSidedLen()

    #增加幅度
    def addAmplitude(self, event):
        self.changeRidgeDelta(-1)
        
    #减小幅度
    def subAmplitude(self, event):
        self.changeRidgeDelta(1)
        
    #实际调整幅度
    def changeRidgeDelta(self, delta):
        self.lblTips.configure(text='')
        self.spacingDelta = 0
        self.ridgeDelta += delta
        if self.wpType == 0:
            self.adjustSingleSidedLen()
        else:
            self.adjustDoubleSidedLen()

    #确认返回
    def confirm(self, event=None):
        if not self.tracks:
            self.showInfo(_("The length of trace has not been adjusted yet"))
            return

        self.textIo.removeList(self.orgTracks)
        self.textIo.addAll(self.tracks)
        self.destroy()

    #将一个PCB导线点转换为cancas中的一个坐标
    def canvasCoordinate(self, pt):
        x, y = pt
        margin = self.margin
        scaleX = (self.canvasW - 2 * margin) / (self.xMax - self.xMin)
        scaleY = (self.canvasH - 2 * margin) / (self.yMax - self.yMin)
        scale = min(scaleX, scaleY)

        newX = round((x - self.xMin) * scale + margin, 4)
        newY = round((y - self.yMin) * scale + margin, 4)
        return newX, newY

    #将canvas中的一个坐标点转换回PCB导线坐标点
    def pcbCoordinate(self, pt):
        canvasX, canvasY = pt
        margin = self.margin
        scaleX = (self.canvasW - 2 * margin) / (self.xMax - self.xMin)
        scaleY = (self.canvasH - 2 * margin) / (self.yMax - self.yMin)
        scale = min(scaleX, scaleY)

        x = round((canvasX - margin) / scale + self.xMin, 4)
        y = round((canvasY - margin) / scale + self.yMin, 4)
        return x, y

    #刷新绘制的导线
    def refreshDraw(self, event=None):
        self.canvasW = self.canvas.winfo_width()
        self.canvasH = self.canvas.winfo_height()
        self.cavOrgPoints = []
        self.cavPoints = []

        #确定包含所有线段的最小矩形
        for track in self.orgTracks: #导线的坐标转换为canvas坐标
            track.updateSelfBbox()
        for track in self.tracks:
            track.updateSelfBbox()
        self.xMin = min([track.xMin for track in itertools.chain(self.orgTracks, self.tracks)])
        self.yMin = min([track.yMin for track in itertools.chain(self.orgTracks, self.tracks)])
        self.xMax = max([track.xMax for track in itertools.chain(self.orgTracks, self.tracks)])
        self.yMax = max([track.yMax for track in itertools.chain(self.orgTracks, self.tracks)])

        for track in self.orgTracks: #导线的坐标转换为canvas坐标
            self.cavOrgPoints.append([self.canvasCoordinate(pt) for pt in track.points])
        for track in self.tracks:
            self.cavPoints.append([self.canvasCoordinate(pt) for pt in track.points])

        if self.cavPoints:
            self.drawTrack(self.cavPoints, self.tracks)
        else:
            self.drawTrack(self.cavOrgPoints, self.orgTracks)

    #绘制导线，第一根导线为最长的一根
    #cavPoints: 经过转换为canvas坐标的导线坐标列表
    #tracks: 对应的SprintTrack列表
    def drawTrack(self, cavPoints, tracks):
        self.canvas.delete('all')
        #将所有线段绘制到canvas上，最长的一根（第一根）为红色
        color = 'red'
        maxLength = tracks[0].length
        self.tagsMap = {}
        for idx, points in enumerate(cavPoints):
            pts = list(itertools.chain(*points)) #展开为一维列表
            length = tracks[idx].length
            tag = 'trace_{}'.format(idx)
            if idx == 0:
                fullText = _('The longest trace. length: {} mm').format(length)
            else:
                fullText = _('The trace length: {} mm, deviation: {} mm').format(length, round(length - maxLength, 3))
            self.tagsMap[tag] = fullText
            self.canvas.create_line(*pts, fill=color, width=2, tags=tag)
            if color == 'red':
                color = '#00BA00' # '#1E6AF9'

    #给定一个点，寻找和这个点最接近的导线，
    #返回 (导线索引，导线内线段索引, 点到线段投影点PCB坐标)
    def trackUnderPoint(self, x, y):
        x = self.canvas.canvasx(x)
        y = self.canvas.canvasy(y)
        minDist = 999999999
        trackIndex = 0
        segIndex = 0
        proj = (0, 0)
        for idx, track in enumerate(self.cavOrgPoints):
            for i in range(len(track) - 1):
                x1, y1 = track[i]
                x2, y2 = track[i + 1]
                dist, _proj = pointToLineDistance(x, y, x1, y1, x2, y2)
                if dist < minDist:
                    minDist = dist
                    trackIndex = idx
                    segIndex = i
                    proj = _proj

        return trackIndex, segIndex, self.pcbCoordinate(proj)

    #canvas鼠标移动事件
    def canvasMouseMove(self, event):
        x, y = event.x, event.y
        items = self.canvas.find_overlapping(x - 3, y - 3, x + 3, y + 3)
        for item in items:
            if self.canvas.type(item) != "line":
                continue
            tags = self.canvas.gettags(item)
            for tag in tags:
                if tag in self.tagsMap:
                    self.lblTips.configure(text=self.tagsMap[tag])
                    return

    #canvas点击事件
    def canvasClick(self, event):
        self.lblTips.configure(text='')
        self.spacingDelta = 0
        self.ridgeDelta = 0
        
        #鼠标点击点对应到PCB坐标系，用于确定绘制的相对方位
        self.mousePt = self.pcbCoordinate((self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)))
        trackIndex, segIndex, projPt = self.trackUnderPoint(event.x, event.y)
        if trackIndex == 0: #第一根导线为最长的，点击无效
            self.trackIndex = 0
            self.segIndex = 0
            self.projPt = None
            return
        
        self.trackIndex = trackIndex
        self.segIndex = segIndex
        self.projPt = projPt
        if self.wpType == 0: #单侧隆起线
            self.adjustSingleSidedLen()
        else: #蛇形线
            self.adjustDoubleSidedLen()

    #使用单侧隆起方式调整导线对的长度
    def adjustSingleSidedLen(self, deviation=0, draw=True):
        tIndex = self.trackIndex #导线索引
        segIndex = self.segIndex #投影线段索引
        projPt = self.projPt #投影点坐标
        mousePt = self.mousePt #鼠标点击点，已经转化为PCB坐标
        if (tIndex == 0 or tIndex >= len(self.orgTracks) or segIndex >= len(self.cavOrgPoints[tIndex])
            or not projPt or not mousePt):
            return

        #计算需要添加的长度
        delta = self.orgTracks[0].length - self.orgTracks[tIndex].length + self.skew + deviation

        spacing = self.spacing + self.spacingDelta
        if spacing < 0.1:
            spacing = 0.1
        
        #根据界面参数，计算一个单独隆起的最大和最小长度
        #当前只支持100%圆弧，每个隆起包含4个90度圆弧（合并为一个整圆）
        #减去(spacing + diameter)是减去隆起在原导线上的投影长度，求出相对增加值
        diameter = min(self.aMin, spacing)
        minRidgeLen = math.pi * diameter + max(self.aMin, spacing) - diameter - (spacing + diameter)
        diameter = min(self.aMax, spacing)
        maxRidgeLen = math.pi * diameter + max(self.aMax, spacing) - diameter - (spacing + diameter)
        
        #计算需要多少个隆起
        if delta < minRidgeLen:
            if draw:
                self.showInfo(_("The difference is smaller than the minimum length of a ridge"))
            return
        
        maxRidgeNum = int(delta // minRidgeLen)
        ridgeNum = math.ceil(delta / maxRidgeLen) + self.ridgeDelta
        if ridgeNum < 1:
            ridgeNum = 1
        if ridgeNum > maxRidgeNum:
            ridgeNum = maxRidgeNum
        
        #将delta差值平均分配给ridgeNum个隆起，并且计算需要的振幅
        #实际上是通过下面两个等式求出a，要分两种情况:
        #a<=spacing: ridgeLen = pi * a + spacing - a - (spacing + a)
        #a>spacing: ridgeLen = pi * spacing + a - spacing - (spacing + spacing)
        #diameter = min(a, spacing)
        #ridgeLen = pi * diameter + max(a, spacing) - diameter
        ridgeLen = delta / ridgeNum #每一个隆起需要的长度
        a1 = ridgeLen / (math.pi - 2)
        a2 = ridgeLen - (math.pi - 3) * spacing
        a = a1 if a1 <= spacing else a2 #这个就是最终的振幅
        radius = min(a, spacing) / 2
        trackStep = spacing * 2 # + radius * 2 #每个隆起在导线上的步进距离

        #从投影点断开导线，切除 (spacing * 2) 的一段，接入一个隆起
        self.tracks = copy.deepcopy(self.orgTracks)
        track = self.tracks[tIndex]
        points = track.points
        ridgePts = [projPt]
        angle = angleWithXAxis(points[segIndex], projPt) #初始线段角度

        for idx in range(ridgeNum):
            #找出四个过渡圆弧的圆心
            #第一个圆弧
            pt = pointInLineWithDistance(projPt, points[segIndex + 1], trackStep * idx)
            endPoints = perpendicularLineEndPoints(points[segIndex], pt, radius)
            #垂直的两个点，哪个点离鼠标近就使用哪个
            endPoints.sort(key=lambda pt: math.dist(pt, mousePt))
            center1 = endPoints[0]
            #第二个圆弧
            pt = pointInLineWithDistance(projPt, points[segIndex + 1], radius * 2 + trackStep * idx)
            endPoints = perpendicularLineEndPoints(projPt, pt, a - radius)
            endPoints.sort(key=lambda pt: math.dist(pt, mousePt))
            center2 = endPoints[0]
            #第三个圆弧
            pt = pointInLineWithDistance(projPt, points[segIndex + 1], spacing + trackStep * idx)
            endPoints = perpendicularLineEndPoints(projPt, pt, a - radius)
            endPoints.sort(key=lambda pt: math.dist(pt, mousePt))
            center3 = endPoints[0]
            #第四个圆弧
            pt = pointInLineWithDistance(projPt, points[segIndex + 1], spacing + radius * 2 + trackStep * idx)
            endPoints = perpendicularLineEndPoints(projPt, pt, radius)
            endPoints.sort(key=lambda pt: math.dist(pt, mousePt))
            center4 = endPoints[0]

            if pointPosition(points[segIndex], projPt, center1) == 'L':
                start1 = -angle
                stop1 = start1 - 90
                clockWise1 = True
                start2 = 180 - angle
                stop2 = start2 + 90
                clockWise2 = False
                start3 = 90 - angle
                stop3 = start3 + 90
                clockWise3 = False
                start4 = -angle - 90
                stop4 = start4 + 90
                clockWise4 = True
            else:
                start1 = 90 - angle
                stop1 = start1 + 90
                clockWise1 = False
                start2 = -angle - 90
                stop2 = start2 + 90
                clockWise2 = True
                start3 = -angle
                stop3 = start3 + 90
                clockWise3 = True
                start4 = 180 - angle
                stop4 = start4 + 90
                clockWise4 = False

            ridgePts.extend(cutCircle(center1, radius, 10, start1, stop1, clockWise1))
            ridgePts.extend(cutCircle(center2, radius, 10, start2, stop2, clockWise2))
            ridgePts.extend(cutCircle(center3, radius, 10, start3, stop3, clockWise3))
            ridgePts.extend(cutCircle(center4, radius, 10, start4, stop4, clockWise4))
        
        #print(track.points)
        points[segIndex + 1:segIndex + 1] = ridgePts
        track.removeDuplicatePoints()
        self.deviation = self.tracks[0].length - self.tracks[tIndex].length + self.skew
        #print(track.points)
        if draw:
            self.refreshDraw()

    #调整双侧蛇形线，保持和第一根导线一样长
    def adjustDoubleSidedLen(self, deviation=0, draw=True):
        tIndex = self.trackIndex #导线索引
        segIndex = self.segIndex #投影线段索引
        projPt = self.projPt #投影点坐标
        mousePt = self.mousePt #鼠标点击点，已经转化为PCB坐标
        if (tIndex == 0 or tIndex >= len(self.orgTracks) or segIndex >= len(self.cavOrgPoints[tIndex])
            or not projPt or not mousePt):
            return

        #计算需要添加的长度
        delta = self.orgTracks[0].length - self.orgTracks[tIndex].length + self.skew + deviation

        spacing = self.spacing + self.spacingDelta
        if spacing < 0.1:
            spacing = 0.1
        
        #根据界面参数，计算一个单独隆起的最大和最小长度
        #当前只支持100%圆弧，开始和结束隆起包含3个90度圆弧，中间的隆起包含2个90度圆弧
        aMin = self.aMin
        aMax = self.aMax
        diameter = min(aMin, spacing)
        minEndLen = (math.pi * 3 - 10) * diameter / 4 + 2 * aMin + spacing - (spacing + diameter / 2)
        diameter = min(aMax, spacing)
        maxEndLen = (math.pi * 3 - 10) * diameter / 4 + 2 * aMax + spacing - (spacing + diameter / 2)
        #中间的隆起
        diameter = min(aMin, spacing)
        minMidBumpLen = math.pi * diameter / 2 + 2 * aMin + spacing - spacing
        diameter = min(aMax, spacing)
        maxMidBumpLen = math.pi * diameter / 2 + 2 * aMax + spacing - spacing

        #计算需要多少个隆起
        if delta < (minEndLen * 2):
            if draw:
                self.showInfo(_("The difference is smaller than the minimum length of a ridge"))
            return
        
        #每个蛇形线需要两个端点隆起和零或若干个中间隆起
        maxMidBumpNum = int((delta - (minEndLen * 2)) // minMidBumpLen)
        bumpNum = math.ceil((delta - (maxEndLen * 2)) / maxMidBumpLen) + self.ridgeDelta
        if bumpNum < 0:
            bumpNum = 0
        if bumpNum > maxMidBumpNum:
            bumpNum = maxMidBumpNum
        
        #将delta差值平均分配给bumpNum个中间隆起和两个起始隆起(一定存在)，并且计算需要的振幅
        #要分两种情况:a<=spacing, a>spacing
        a1 = (delta * 2 + spacing * 6 + bumpNum * spacing * 2) / (math.pi * (bumpNum + 3) - 4)
        a2 = (delta * 2 + spacing * (14 - math.pi * 3 - math.pi * bumpNum - bumpNum * 2)) / (bumpNum * 4 + 8)
        a = a1 if a1 <= spacing else a2 #这个就是最终的振幅
        radius = min(a, spacing) / 2
        #print(a1, a2, spacing, a)
        
        #从投影点断开导线，接入蛇形线
        self.tracks = copy.deepcopy(self.orgTracks)
        track = self.tracks[tIndex]
        points = track.points
        snakePts = [projPt]
        angle = angleWithXAxis(points[segIndex], projPt) #初始线段角度

        perpPtIdx = 0 # [0,1]，逐个取导线两侧的垂直线

        #第一个起始隆起
        #找出三个过渡圆弧的圆心
        #第一个圆弧
        endPoints = perpendicularLineEndPoints(points[segIndex], projPt, radius)
        center1 = endPoints[perpPtIdx]
        #第二个圆弧
        pt = pointInLineWithDistance(projPt, points[segIndex + 1], radius * 2)
        endPoints = perpendicularLineEndPoints(projPt, pt, a - radius)
        center2 = endPoints[perpPtIdx]
        #第三个圆弧
        pt = pointInLineWithDistance(projPt, points[segIndex + 1], spacing)
        endPoints = perpendicularLineEndPoints(projPt, pt, a - radius)
        center3 = endPoints[perpPtIdx]
        if pointPosition(points[segIndex], projPt, center1) == 'L':
            start1 = -angle
            stop1 = start1 - 90
            clockWise1 = True
            start2 = 180 - angle
            stop2 = start2 + 90
            clockWise2 = False
            start3 = 90 - angle
            stop3 = start3 + 90
            clockWise3 = False
        else:
            start1 = 90 - angle
            stop1 = start1 + 90
            clockWise1 = False
            start2 = -angle - 90
            stop2 = start2 + 90
            clockWise2 = True
            start3 = -angle
            stop3 = start3 + 90
            clockWise3 = True

        snakePts.extend(cutCircle(center1, radius, 10, start1, stop1, clockWise1))
        snakePts.extend(cutCircle(center2, radius, 10, start2, stop2, clockWise2))
        snakePts.extend(cutCircle(center3, radius, 10, start3, stop3, clockWise3))

        #开始为中间的隆起
        bumpStartPt = pointInLineWithDistance(projPt, points[segIndex + 1], radius + spacing)
        for idx in range(bumpNum):
            perpPtIdx = 1 - perpPtIdx
            #找出2个过渡圆弧的圆心
            #第一个圆弧
            pt = pointInLineWithDistance(bumpStartPt, points[segIndex + 1], radius + spacing * idx)
            endPoints = perpendicularLineEndPoints(bumpStartPt, pt, a - radius)
            center1 = endPoints[perpPtIdx]
            #第二个圆弧
            pt = pointInLineWithDistance(bumpStartPt, points[segIndex + 1], spacing - radius + spacing * idx)
            endPoints = perpendicularLineEndPoints(projPt, pt, a - radius)
            center2 = endPoints[perpPtIdx]

            if pointPosition(points[segIndex], projPt, center1) == 'L':
                start1 = 180 - angle
                stop1 = start1 + 90
                clockWise1 = False
                start2 = 90 - angle
                stop2 = start2 + 90
                clockWise2 = False
            else:
                start1 = -angle - 90
                stop1 = start1 + 90
                clockWise1 = True
                start2 = -angle
                stop2 = start2 + 90
                clockWise2 = True

            snakePts.extend(cutCircle(center1, radius, 10, start1, stop1, clockWise1))
            snakePts.extend(cutCircle(center2, radius, 10, start2, stop2, clockWise2))

        perpPtIdx = 1 - perpPtIdx

        #最后一个隆起（结束）
        #找出三个过渡圆弧的圆心
        #第一个圆弧
        lastStartPt = pointInLineWithDistance(projPt, points[segIndex + 1], spacing + radius + spacing * bumpNum)
        pt = pointInLineWithDistance(lastStartPt, points[segIndex + 1], radius)
        endPoints = perpendicularLineEndPoints(points[segIndex], pt, a - radius)
        center1 = endPoints[perpPtIdx]
        #第二个圆弧
        pt = pointInLineWithDistance(lastStartPt, points[segIndex + 1], spacing - radius)
        endPoints = perpendicularLineEndPoints(projPt, pt, a - radius)
        center2 = endPoints[perpPtIdx]
        #第三个圆弧
        pt = pointInLineWithDistance(lastStartPt, points[segIndex + 1], spacing + radius)
        endPoints = perpendicularLineEndPoints(projPt, pt, radius)
        center3 = endPoints[perpPtIdx]
        if pointPosition(points[segIndex], projPt, center1) == 'L':
            start1 = 180 - angle
            stop1 = start1 + 90
            clockWise1 = False
            start2 = 90 - angle
            stop2 = start2 + 90
            clockWise2 = False
            start3 = -angle - 90
            stop3 = start3 + 90
            clockWise3 = True
        else:
            start1 = -angle - 90
            stop1 = start1 + 90
            clockWise1 = True
            start2 = -angle
            stop2 = start2 + 90
            clockWise2 = True
            start3 = 180 - angle
            stop3 = start3 + 90
            clockWise3 = False

        snakePts.extend(cutCircle(center1, radius, 10, start1, stop1, clockWise1))
        snakePts.extend(cutCircle(center2, radius, 10, start2, stop2, clockWise2))
        snakePts.extend(cutCircle(center3, radius, 10, start3, stop3, clockWise3))
        
        #print(track.points)
        points[segIndex + 1:segIndex + 1] = snakePts
        track.removeDuplicatePoints()
        self.deviation = self.tracks[0].length - self.tracks[tIndex].length + self.skew
        #print(track.points)
        if draw:
            self.refreshDraw()
        
