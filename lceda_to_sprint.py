#!/usr/bin/env python
#-*- coding:utf-8 -*-
"""
将力创的封装库转换为Sprint-Layout的Text-IO格式
文件格式：https://docs.lceda.cn/cn/DocumentFormat/EasyEDA-Format-Standard/index.html
Author: cdhigh <https://github.com/cdhigh>
"""
import json
from urllib import request
from comm_utils import *
from sprint_struct.sprint_textio import *

#全球节点
LC_PRODUCT_URI = "https://easyeda.com/api/products/{}/svgs"
LC_FOOTPRINT_INFO_URI = "https://easyeda.com/api/components/{}"

#中国节点
LC_PRODUCT_URI_CN = "https://lceda.cn/api/products/{}/svgs"
LC_FOOTPRINT_INFO_URI_CN = "https://lceda.cn/api/components/{}"

DEFAULT_WEB_TIMEOUT = 5
webHeaders = {
   'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36',
   'Referer': 'https://lceda.cn/editor',
   'Accept': 'application/json, text/javascript, */*; q=0.01',
   #'Accept-Encoding': 'gzip, deflate', #不传这个请求头，因数据量不大，不需要压缩
}

#力创板层和Sprint-Layout板层的对应关系
lcLayerMap = {
    '1':  LAYER_C1,
    '2':  LAYER_C2,
    '3':  LAYER_S1,
    '4':  LAYER_S2,
    '5':  LAYER_S1, #F.Paste
    '6':  LAYER_S2, #B.Paste
    '7':  LAYER_S1, #F.Mask
    '8':  LAYER_S2, #B.Mask
    '10': LAYER_U,  #Edge.Cuts
    '11': LAYER_U,  #Edge.Cuts
    '12': LAYER_U,  #Cmts.User 文档层 F.Fab
    '13': LAYER_U,  #F.Fab
    '14': LAYER_U,  #B.Fab
    '15': LAYER_U,  #Dwgs.User
    '21': LAYER_I1,
    '22': LAYER_I2,
    '100': LAYER_S1,
    '101': LAYER_U, #元件标识层
}

#力创焊盘形状和Sprint-Layout的对应关系
lcPadShapeMap = {
    'ELLIPSE': PAD_FORM_ROUND,
    'RECT': PAD_FORM_SQUARE,
    'OVAL': PAD_FORM_ROUND,
    'POLYGON': PAD_FORM_OCTAGON,
}

#力创的单位系统
#1 pixel = 10 mil
#1 pixel = 0.254mm
#1 pixel = 0.01inch
def mil2mm(data: str):
    return str_to_float(data) / 3.937
    
class LcComponent:
    #lcId: 力创的封装ID(以C开头，后接几位数字)
    def __init__(self):
        self.lcId = ''
        self.fpUuid = self.fpName = self.fpShape = self.fpPackage = self.prefix = ''
        self.importText = False
        self.handlers = {
            "TRACK": self.handleTrack,
            "PAD": self.handlePad,
            "ARC": self.handleArc,
            "CIRCLE": self.handleCircle,
            #"SOLIDREGION": self.handleSolidRegion,
            #"SVGNODE": self.handleSvgNode,
            "VIA": self.handleVia,
            "RECT": self.handleRect,
            "HOLE": self.handleHole,
            "TEXT": self.handleText,
        }

    #从立创ID创建
    #easyEdaSite: 'cn'-使用中国节点，其他-使用国际节点
    @classmethod
    def fromLcId(cls, lcId: str, easyEdaSite: str):
        if not lcId:
            return None

        lcId = lcId.upper()
        if not lcId.startswith('C'):
            lcId = 'C' + lcId

        errMsg = None
        errMsg, fpUuid = cls.getFootprintUuid(lcId, easyEdaSite)

        if not fpUuid:
            return errMsg

        #创建实例返回
        ins = LcComponent()
        ins.lcId = lcId
        ins.fpName, ins.packageName, ins.prefix, ins.fpShape = ins.fetchFpInfoFromUuid(fpUuid, easyEdaSite)
        #print(ins.fpShape) #TODO
        return ins

    #从JSON文件创建
    @classmethod
    def fromFile(cls, fileName: str):
        data = None
        try:
            with open(fileName, 'r', encoding='utf-8') as f:
                data = json.loads(f.read())
        except Exception as e:
            #print('open failed: {}, {}'.format(fileName, str(e)))
            return None

        if not isinstance(data, dict):
            return None

        ins = LcComponent()
        ins.fpName, ins.packageName, ins.prefix, ins.fpShape = ins.fetchFpInfoFromLocalJson(data)
        return ins
    
    #判断是否是力创EDA的组件ID，为字母C+数字
    @classmethod
    def isLcedaComponent(cls, txt: str):
        if (len(txt) < 3):
            return False

        #可以允许全部为数字，如果第一个字母的话，为C
        firstChar = txt[0].upper()
        if (firstChar != 'C') and (not firstChar.isdigit()):
            return False

        for ch in txt[1:]:
            if not ch.isdigit():
                return False

        return True
        
    #根据封装信息从网络创建一个SprintTextIo对象
    def createSprintTextIo(self, importText: bool):
        if not self.fpShape:
            return None
        
        self.importText = importText

        #逐行扫描，调用对应的解析函数
        textIo = SprintTextIO()
        component = SprintComponent()
        for line in self.fpShape:
            args = line.split("~")
            if len(args) <= 1:
                continue

            model = args[0] #第一个元素为绘图种类
            if model in self.handlers:
                self.handlers.get(model)(args[1:], component)

        #添加一些辅助信息
        if component.isValid():
            component.name = self.prefix
            component.nameVisible = True if self.prefix else False
            component.comment = '{} ({})'.format(self.fpName, self.lcId)
            component.package = self.packageName
            textIo.add(component)
            return textIo
        else:
            return None

    #联网获取一个json信息，返回 (errMsg, jsonObj)
    @classmethod
    def fetchJsonFromLc(cls, url: str):
        lcJsonData = ''
        try:
            reqInst = request.Request(url, headers=webHeaders)
            data = request.urlopen(reqInst, timeout=DEFAULT_WEB_TIMEOUT).read().decode('utf-8')
            lcJsonData = json.loads(data)
        except Exception as e:
            print(str(e))
            return (str(e), '')

        if not isinstance(lcJsonData, dict):
            return (_('The content is not json format'), '')
        else:
            return ('', lcJsonData)
        
    #根据力创商城ID获取封装的UUID，返回 (errMsg, uuid)
    @classmethod
    def getFootprintUuid(cls, lcId: str, easyEdaSite: str):
        url = LC_PRODUCT_URI.format(lcId) if (easyEdaSite != 'cn') else LC_PRODUCT_URI_CN.format(lcId)
        #print(url)
        errMsg, lcJsonData = cls.fetchJsonFromLc(url)
        if errMsg:
            return (errMsg, '')

        success = lcJsonData.get('success', '')
        result = lcJsonData.get('result')
        if not all((success, result, isinstance(result, list))):
            errMsg = lcJsonData.get('message', '')
            return (_('Error from easyEDA:\n{}').format(errMsg) if errMsg else _('The content is not a valid json format'), '')
        
        #获取到封装ID
        return ('', result[-1].get('component_uuid', ''))
    
    #联网获取封装绘制信息，返回(fpName, packageName, prefix, fpShape)
    @classmethod
    def fetchFpInfoFromUuid(cls, fpUuid: str, easyEdaSite: str):
        url = LC_FOOTPRINT_INFO_URI.format(fpUuid) if (easyEdaSite != 'cn') else LC_FOOTPRINT_INFO_URI_CN.format(fpUuid)
        errMsg, lcJsonData = cls.fetchJsonFromLc(url)
        if errMsg:
            print(errMsg)
            return ('', '', '', '')
        else:
            return cls.fetchFpInfoFromWebJson(lcJsonData)

    #从网络获取到的json包里面提取封装绘制信息，返回(fpName, packageName, prefix, fpShape)
    @classmethod
    def fetchFpInfoFromWebJson(cls, data: dict):
        result = data.get('result', '')
        if not result or not isinstance(result, dict):
            return ('', '', '', '')

        name = result.get('title', '')
        dataStr = result.get('dataStr', {})

        shape = dataStr.get('shape', '') if isinstance(dataStr, dict) else ''
        
        try:
            packageName = dataStr['head']['c_para']['package']
        except:
            packageName = ''

        try:
            prefix = dataStr['head']['c_para']['pre']
        except:
            prefix = ''

        if not name:
            name = "NoName"
            
        return (name, packageName, prefix, shape)

    #从本地的json包里面提取封装绘制信息，返回(fpName, packageName, prefix, fpShape)
    def fetchFpInfoFromLocalJson(self, data: dict):
        shape = data.get('shape', '')
        head = data.get('head', '')
        title = 'Untitled'

        #如果错误，尝试另一种文件格式，是通过以下URL格式返回的，同一个JSON里面包含原理图符号和封装符号
        #https://easyeda.com/api/products/C80909/components?version=6.4.19.5
        if not shape and not head:
            try:
                dataStr = data['result']['packageDetail']['dataStr']
                shape = dataStr['shape']
                head = dataStr['head']
                title = data['result']['packageDetail']['title']
            except:
                return ('', '', '', '')
        
        try:
            packageName = head['c_para']['package']
        except:
            packageName = ''

        try:
            prefix = head['c_para']['pre']
        except:
            prefix = ''

        return (title, packageName, prefix, shape)

    #分析Track对象
    #TRACK~0.591~3~~420.6665 298.189 421.2009 298.189~gge138~0
    #TRACK~0.591~3~S$134~421.2009 298.189 421.2009 308.0315~gge132~0
    #TRACK~1~3~~4014.9999 3012.0358 3986.7795 3012.0358 3986.7795 3000.0358~gge95~0
    #stroke_width,layer_id,net,points,id,is_locked
    #-1.[cmdKey]：图元标识符，TRACK
    #0.[strokeWidth]:线宽
    #1.[layerid]：所属层
    #2.[net]：网络
    #3.[pointArr]：坐标点数据
    #4.[gId]：元素id
    #5.[locked]：是否锁定
    def handleTrack(self, data: list, component: SprintComponent):
        if not data or not component or (len(data) < 4):
            return
            
        width = mil2mm(data[0])
        layer = lcLayerMap.get(data[1], LAYER_S1)
        points = [mil2mm(p) for p in data[3].split(" ") if p]
        for i in range(int(len(points) / 2) - 1):
            lcTra = SprintTrack(layer, width)
            lcTra.addPoint(points[2 * i], points[2 * i + 1])
            lcTra.addPoint(points[2 * i + 2], points[2 * i + 3])
            component.add(lcTra)

    #分析PAD对象
    #PAD~RECT~3970.275~3002.756~4.3307~0.7874~1~~1~0~3968.1099 3002.3623 3972.4406 3002.3623 3972.4406 3003.1497 3968.1099 3003.1497~0~gge8~0~~Y~0~0~0.1969~3970.2754,3002.7561
    #PAD~ELLIPSE~619~-370.748~5.9055~5.9055~11~~17~1.7717~~90~rep7~0~~Y~0~0~0.2~619,-370.748
    #-1.[cmdKey]：图元标识符，PAD
    #0.[shape]：焊盘形状
    #1.[x]：横坐标
    #2.[y]：纵坐标
    #3.[width]：宽度
    #4.[height]：高度
    #5.[layerid]：所属层
    #6.[net]：网络
    #7.[number]：编号
    #8.[holeR]：孔直径
    #9.[pointArr]：坐标点数据
    #10.[rotation]：旋转角度
    #11.[gId]：元素id
    #12.[holeLength]：孔长度
    #13.[slotPointArr]：孔的坐标点数据
    #14.[plated]：是否金属化
    #15.[locked]：是否锁定
    #16.[pasteexpansion]：助焊扩展
    #17.[solderexpansion]：阻焊扩展
    #18.[holeCenter]：孔中心坐标
    def handlePad(self, data: list, component: SprintComponent):
        if not data or not component:
            return
            
        shape = lcPadShapeMap.get(data[0], PAD_FORM_ROUND)
        x = mil2mm(data[1])
        y = mil2mm(data[2])
        width = mil2mm(data[3])
        height = mil2mm(data[4])
        padNumber = data[7]
        drill = mil2mm(data[8]) * 2 #转为直径
        rotation = str_to_float(data[10])
        via = True
        if data[5] == "1":
            #drill = 1
            padType = 'SMDPAD' if (drill == 0) else 'PAD'
            layer = LAYER_C1
        elif data[5] == "2":
            padType = 'SMDPAD' if (drill == 0) else 'PAD'
            layer = LAYER_C2
        elif (data[5] == "11"):
            padType = 'PAD'
            layer = LAYER_C1
        else:
            print("Skiping pad : {}".format(padNumber))
            return

        if drill > 0:
            via = True if (data[14] == 'Y') else False
        
        spPad = SprintPad(layerIdx=layer)
        spPad.pos = (x, y)
        spPad.rotation = (360 - rotation) if rotation else 0  #Sprint-Layout和立创的焊盘旋转方向是相反的
        spPad.padType = padType
        spPad.via = via  #via=True 双面焊盘
        
        if (padType == 'SMDPAD'):
            spPad.sizeX = width
            spPad.sizeY = height
        else:
            spPad.size = min(width, height)
            if (spPad.size <= 0):
                spPad.size = max(width, height)

            #处理椭圆焊盘，确定是水平还是垂直
            if (data[0] == 'OVAL'):
                #究竟使用圆形焊盘还是长条椭圆焊盘，取决于长轴是否大于短轴的4/3
                if ((width > height) and ((width * 2 / 3) > height)): #水平椭圆焊盘
                    spPad.form = PAD_FORM_RECT_ROUND_H
                elif ((width < height) and ((height * 2 / 3) > width)): #垂直椭圆焊盘
                    spPad.form = PAD_FORM_RECT_ROUND_V
                else: #圆形
                    spPad.form = PAD_FORM_ROUND
            elif (data[0] == 'RECT'):
                if ((width > height) and ((width * 2 / 3) > height)): #水平矩形焊盘
                    spPad.form = PAD_FORM_RECT_H
                elif ((width < height) and ((height * 2 / 3) > width)): #垂直矩形焊盘
                    spPad.form = PAD_FORM_RECT_V
                else: #正方形
                    spPad.form = PAD_FORM_SQUARE
            else:
                spPad.form = shape

        spPad.drill = drill

        #if 0.0 < spPad.drill <= 0.51: #小于0.51mm的过孔默认盖绿油
        #    spPad.soldermask = False

        component.add(spPad)
    
    #处理弧形，立创的弧形直接使用SVG的画圆弧命令
    #stroke_width,layer_id,net,path,helper_dots,id,is_locked
    #"ARC~1~3~~M4005.0049,3038.4907 A9.8425,9.8425 0 1 0 4005.0021,3038.4921~~gge43~0",
    #A radiusx radiusy x-axis-rotation large-arc-flag sweep-flag(1-顺时针) endx endy
    #-1.[cmdKey]：图元标识符，ARC
    #0.[strokeWidth]:线宽
    #1.[layerid]：所属层
    #2.[net]：网络
    #3.[d]：路径数据
    #4.[c_helper_dots]：辅助线路径数据
    #5.[gId]：元素id
    #6.[locked]：是否锁定
    def handleArc(self, data: list, component: SprintComponent):
        if not data or not component or (len(data) < 4):
            return
        
        width = mil2mm(data[0])
        layer = lcLayerMap.get(data[1], LAYER_S1)
        if layer == LAYER_U: #不引入外形层的弧形
            return
        
        arcCmd = [val for val in data[3].replace("M", " ").replace("A", " ").replace(",", " ").split(" ") if val]
        
        if (len(arcCmd) < 9):
            print("handleArc : token unknown")
            return
            
        startX = mil2mm(arcCmd[0])
        startY = mil2mm(arcCmd[1])
        radiusX = mil2mm(arcCmd[2])
        radiusY = mil2mm(arcCmd[3])
        axisAngle = str_to_int(arcCmd[4])
        bigArc = str_to_int(arcCmd[5])
        clockwise = str_to_int(arcCmd[6])
        endX = mil2mm(arcCmd[7])
        endY = mil2mm(arcCmd[8])
        
        spCir = SprintCircle(layerIdx=layer)
        spCir.width = width
        spCir.setByStartEndRadius(startX, startY, radiusX, radiusY, 
            axisAngle, bigArc, clockwise, endX, endY)
        
        component.add(spCir)
            
    #处理圆形
    #cx,cy,radius,stroke_width,layer_id,id,is_locked
    #"CIRCLE~3970.472~2999.213~0.118~0.2362~101~gge555~0~~circle_gge556,circle_gge557",
    #-1.[cmdKey]：图元标识符，CIRCLE
    #0.[cx]：圆心x坐标
    #1.[cy]：圆心y坐标
    #2.[r]：半径
    #3.[strokeWidth]：线宽
    #4.[layerid]：所属层
    #5.[gId]：元素id
    #6.[locked]：是否锁定
    #7.[net]：网络
    #8.[transformarc]:由圆转换的两个半圆的id信息
    def handleCircle(self, data: list, component: SprintComponent):
        if not data or not component or (len(data) < 5):
            return
        
        layer = lcLayerMap.get(data[4], LAYER_S1)
        if layer == LAYER_U: #不引入外形层的圆形
            return

        if (data[4] == "100"):  #焊盘上画一个圆圈，先忽略
            return
            
        centerX = mil2mm(data[0])
        centerY = mil2mm(data[1])
        radius = mil2mm(data[2])
        width = mil2mm(data[3])
        
        spCir = SprintCircle(layerIdx=layer)
        spCir.center = (centerX, centerY)
        spCir.width = width
        spCir.radius = radius
        component.add(spCir)
    
    #处理矩形
    #x,y,width,height,layer_id,name,xx,stroke_width
    #不填充：RECT~3998.425~3004.477~5.906~1.181~12~gge158~0~1~none~~~
    #填充：  RECT~3998.425~3004.477~5.906~1.181~12~gge158~0~0~~~~
    #-1.[cmdKey]：图元标识符，RECT
    #0.[x]:横坐标
    #1.[y]：纵坐标
    #2.[width]：宽度
    #3.[height]：高度
    #4.[layerid]：所属层
    #5.[gId]：元素id
    #6.[locked]：是否锁定
    #7.[strokeWidth]:线宽
    #8.[fill]:填充颜色
    #9.[transform]:偏移数据
    #10.[net]：网络
    #11.[c_etype]:c_etype属性值（自定义的用于细分图元类型的属性）
    def handleRect(self, data: list, component: SprintComponent):
        if not data or not component or (len(data) < 8):
            return

        layer = lcLayerMap.get(data[4], LAYER_S1)
        if layer == LAYER_U: #不引入外形层的矩形
            return

        x1 = mil2mm(data[0])
        y1 = mil2mm(data[1])
        width = mil2mm(data[2])
        height = mil2mm(data[3])
        strokeWidth = mil2mm(data[7])
        
        if strokeWidth: #仅是线条，不填充，使用四段线组成
            lcTra = SprintTrack(layer, strokeWidth)
            lcTra.addPoint(x1, y1)
            lcTra.addPoint(x1 + width, y1)
            lcTra.addPoint(x1 + width, y1 + height)
            lcTra.addPoint(x1, y1 + height)
            lcTra.addPoint(x1, y1)
            component.add(lcTra)
        else: #填充的话，使用多边形组成
            polygon = SprintPolygon(layer, strokeWidth)
            polygon.addPoint(x1, y1)
            polygon.addPoint(x1 + width, y1)
            polygon.addPoint(x1 + width, y1 + height)
            polygon.addPoint(x1, y1 + height)
            component.add(polygon)
    
    #开孔实现为内外径相等的过孔
    #center_x,center_y,radius,id,is_locked
    def handleHole(self, data: list, component: SprintComponent):
        if not data or not component:
            return
            
        x = mil2mm(data[0])
        y = mil2mm(data[1])
        size = mil2mm(data[2]) * 2 #转换为直径
        spPad = SprintPad(layerIdx=LAYER_C1)
        spPad.pos = (x, y)
        spPad.padType = 'PAD'
        spPad.size = size
        spPad.drill = spPad.size
        spPad.form = PAD_FORM_ROUND
        component.add(spPad)
    
    #处理文本信息
    #TEXT~L~4018.5~3025.62~0.8~0~0~3~~5.9055~+~M 4020.92 3019.4999 L 4020.92 
    #-1.[cmdKey]：图元标识符，TEXT
    #0.[type]：文本标记，可选值：L(普通文本) | N(器件名称) | P(器件编号) | PK(封装名)
    #1.[x]：横坐标   //弃用，参考pathStr
    #2.[y]：纵坐标   //弃用，参考pathStr
    #3.[strokeWidth]:线宽
    #4.[rotation]：旋转角度    //弃用，参考pathStr
    #5.[mirror]:是否镜像      //弃用，参考pathStr
    #6.[layerid]：所属层
    #7.[net]：网络
    #8.[fontSize]：文字大小
    #9.[text]：文本值        //弃用，参考pathStr
    #10.[pathStr]：路径数据
    #11.[display]：是否显示
    #12.[gId]：元素id
    #13.[fontFamily]：字体
    #14.[locked]：是否锁定
    #15.[c_etype]：c_etype属性值（c_etype是自定义的用于细分图元类型的属性）
    def handleText(self, data: list, component: SprintComponent):
        if not data or not component or not self.importText:
            return
        
        layer = lcLayerMap.get(data[6], LAYER_S1)
        spText = SprintText(layerIdx=layer)
        spText.text = data[9]
        spText.height = mil2mm(data[8])
        if (spText.height <= 0.1):
            spText.height = 1
        
        x, y = mil2mm(data[1]), mil2mm(data[2])
        spText.pos = (x, y)
        spText.rotation = str_to_int(data[4])
        if spText.rotation:
            spText.rotation = 360 - spText.rotation #Sprint-Layout的旋转方向和立创是相反的

        #width = mil2mm(data[3])
        #mirror = str_to_int(data[5])
        #net = data[7]
        
        component.add(spText)
        
    #处理过孔，过孔被处理为双面焊盘
    #x,y,diameter,hole_radius
    #VIA~4001.969~2998.032~2.4~~0.6~gge1050~0
    #-1.[cmdKey]：图元标识符，VIA
    #0.[x]：横坐标
    #1.[y]：纵坐标
    #2.[diameter]：过孔直径
    #3.[net]：网络
    #4.[holeR]：过孔内径
    #5.[gId]：元素id
    #6.[locked]：是否锁定
    def handleVia(self, data: list, component: SprintComponent):
        if not data or not component or not self.importText:
            return

        x = mil2mm(data[0])
        y = mil2mm(data[1])
        size = mil2mm(data[2])
        drill = mil2mm(data[4]) * 2
        spPad = SprintPad(layerIdx=LAYER_C1)
        spPad.pos = (x, y)
        spPad.padType = 'PAD'
        spPad.form = PAD_FORM_ROUND
        spPad.size = size
        spPad.drill = drill
        spPad.via = True
        spPad.soldermask = False  #盖绿油
        component.add(spPad)
