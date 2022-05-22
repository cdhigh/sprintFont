#!/usr/bin/env python
#-*- coding:utf-8 -*-
"""
将力创的封装库转换为Sprint-Layout的Text-IO格式
C80909 还有问题
"""

import json, requests
from comm_utils import *
from sprint_struct.sprint_textio import *

LC_PRODUCT_URI = "https://easyeda.com/api/products/{}/svgs"
LC_FOOTPRINT_INFO_URI = "https://easyeda.com/api/components/{}"

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
    @classmethod
    def fromLcId(cls, lcId: str):
        if not lcId:
            return None

        lcId = lcId.upper()
        if not lcId.startswith('C'):
            lcId = 'C' + lcId

        errMsg = None
        errMsg, fpUuid = cls.getFootprintUuid(lcId)

        if not fpUuid:
            return errMsg

        #创建实例返回
        ins = LcComponent()
        ins.lcId = lcId
        ins.fpName, ins.packageName, ins.prefix, ins.fpShape = ins.fetchFpInfoFromUuid(fpUuid)
        #print(ins.fpShape) #TODO
        return ins

    #从JSON文件创建
    @classmethod
    def fromFile(cls, fileName: str):
        try:
            with open(fileName, 'r', encoding='utf-8') as f:
                data = json.loads(f.read())
        except Exception as e:
            #print('open failed: {}, {}'.format(fileName, str(e)))
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
        textIo = SprintTextIO(isComponent=True)
        for line in self.fpShape:
            args = [elem for elem in line.split("~") if elem] #去掉空元素
            model = args[0] #第一个元素为绘图种类
            if model in self.handlers:
                self.handlers.get(model)(args[1:], textIo)

        #添加一些辅助信息
        if textIo.isValid():
            textIo.name = self.prefix
            textIo.comment = '{} ({})'.format(self.fpName, self.lcId)
            textIo.package = self.packageName

        return textIo
        
    #根据力创商城ID获取封装的UUID，返回 (errMsg, uuid)
    @classmethod
    def getFootprintUuid(cls, lcId: str):
        try:
            data = requests.get(LC_PRODUCT_URI.format(lcId)).content.decode()
            lcJsonData = json.loads(data)
            if not isinstance(lcJsonData, dict):
                return (_('The content is not json format'), '')

            success = lcJsonData.get('success', '')
            if not success:
                return (lcJsonData.get('message', ''), '')
            
            #获取到封装ID
            return ('', lcJsonData["result"][-1]["component_uuid"])
        except Exception as e:
            #print(str(e))
            return (str(e), '')

    #联网获取封装绘制信息，返回(fpName, packageName, prefix, fpShape)
    @classmethod
    def fetchFpInfoFromUuid(cls, fpUuid: str):
        try:
            response = requests.get(LC_FOOTPRINT_INFO_URI.format(fpUuid))
            if response.status_code == requests.codes.ok:
                data = json.loads(response.content.decode())
            else:
                #print("fetchFpInfoFromUuid error. error code {}".format(response.status_code))
                return ('', '', '', '')
        except Exception as e:
            print(str(e))
            return ('', '', '', '')

        return cls.fetchFpInfoFromWebJson(data)

    #从网络获取到的json包里面提取封装绘制信息，返回(fpName, packageName, prefix, fpShape)
    @classmethod
    def fetchFpInfoFromWebJson(cls, data: dict):
        try:
            shape = data["result"]["dataStr"]["shape"]
        except:
            shape = ''

        try:
            name = data["result"]["title"]
        except:
            name = ''

        try:
            packageName = data['result']["dataStr"]['head']['c_para']['package']
        except:
            packageName = ''

        try:
            prefix = data['result']["dataStr"]['head']['c_para']['pre']
        except:
            prefix = ''

        if not name:
            name = "NoName"
            
        return (name, packageName, prefix, shape)

    #从本地的json包里面提取封装绘制信息，返回(fpName, packageName, prefix, fpShape)
    def fetchFpInfoFromLocalJson(self, data: dict):
        try:
            shape = data["shape"]
        except:
            shape = ''

        name = ''

        try:
            packageName = data['head']['c_para']['package']
        except:
            packageName = ''

        try:
            prefix = data['head']['c_para']['pre']
        except:
            prefix = ''

        if not name:
            name = "NoName"
            
        return (name, packageName, prefix, shape)

    #分析Track对象
    #TRACK~0.591~3~~420.6665 298.189 421.2009 298.189~gge138~0
    #TRACK~0.591~3~S$134~421.2009 298.189 421.2009 308.0315~gge132~0
    #TRACK~1~3~~4014.9999 3012.0358 3986.7795 3012.0358 3986.7795 3000.0358~gge95~0
    #stroke_width,layer_id,net,points,id,is_locked
    def handleTrack(self, data: list, textIo: SprintTextIO):
        if not data or not textIo:
            return
            
        width = mil2mm(data[0])
        points = [mil2mm(p) for p in data[2].split(" ") if p]
        if (len(points) < 4):
            points = [mil2mm(p) for p in data[3].split(" ") if p]
            if (len(points) < 4):
                #print("handleTrack skipping line")
                return
                
        layer = lcLayerMap.get(data[1], LAYER_S1)
        for i in range(int(len(points) / 2) - 1):
            lcTra = SprintTrack(layer, width)
            lcTra.addPoint(points[2 * i], points[2 * i + 1])
            lcTra.addPoint(points[2 * i + 2], points[2 * i + 3])
            textIo.addTrack(lcTra)

    #分析PAD对象
    #shape,center_x,center_y,width,height,layer_id,net,number,hole_radius,points,rotation,id,hole_length,hole_point,is_plated,is_locked
    #PAD~RECT~3970.275~3002.756~4.3307~0.7874~1~~1~0~3968.1099 3002.3623 3972.4406 3002.3623 3972.4406 3003.1497 3968.1099 3003.1497~0~gge8~0~~Y~0~0~0.1969~3970.2754,3002.7561
    #PAD~ELLIPSE~619~-370.748~5.9055~5.9055~11~~17~1.7717~~90~rep7~0~~Y~0~0~0.2~619,-370.748
    def handlePad(self, data: list, textIo: SprintTextIO):
        if not data or not textIo:
            return
            
        shape = lcPadShapeMap.get(data[0], PAD_FORM_ROUND)
        x = mil2mm(data[1])
        y = mil2mm(data[2])
        width = mil2mm(data[3])
        height = mil2mm(data[4])
        padNumber = data[6]
        drill = mil2mm(data[7]) * 2 #转为直径
        rotation = str_to_float(data[9])
        via = True
        if data[5] == "1": #data[5] 组装工艺
            #drill = 1
            padType = 'SMDPAD'
            layer = LAYER_C1
        elif (data[5] == "11"):
            padType = 'PAD'
            layer = LAYER_C1
            #if drill > 0:
            #    via = True if (data[11] == 'Y') else False
        else:
            print("Skiping pad : {}".format(padNumber))
            return
        
        spPad = SprintPad(layerIdx=layer)
        spPad.pos = (x, y)
        spPad.rotation = (360 - rotation) if rotation else 0  #Sprint-Layout和立创的焊盘旋转方向是相反的
        spPad.padType = padType
        spPad.via = via
        
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

        if 0.0 < spPad.drill <= 0.51: #小于0.51mm的过孔默认盖绿油
            spPad.soldermask = False

        textIo.addPad(spPad)
    
    #处理弧形，立创的弧形直接使用SVG的画圆弧命令
    #stroke_width,layer_id,net,path,helper_dots,id,is_locked
    #"ARC~1~3~~M4005.0049,3038.4907 A9.8425,9.8425 0 1 0 4005.0021,3038.4921~~gge43~0",
    #A radiusx radiusy x-axis-rotation large-arc-flag sweep-flag(1-顺时针) endx endy
    def handleArc(self, data: list, textIo: SprintTextIO):
        if not data or not textIo:
            return
        
        width = mil2mm(data[0])
        layer = lcLayerMap.get(data[1], LAYER_S1)
        if layer == LAYER_U: #不引入外形层的弧形
            return
        
        if data[2][0] == "M":
            arcCmd = [val for val in data[2].replace("M", " ").replace("A", " ").replace(",", " ").split(" ") if val]
        elif data[3][0] == "M":
            arcCmd = [val for val in data[3].replace("M", " ").replace("A", " ").replace(",", " ").split(" ") if val]
        else:
            arcCmd = []

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
        
        textIo.addCircle(spCir)
            
    #处理圆形
    #cx,cy,radius,stroke_width,layer_id,id,is_locked
    #"CIRCLE~3970.472~2999.213~0.118~0.2362~101~gge555~0~~circle_gge556,circle_gge557",
    def handleCircle(self, data: list, textIo: SprintTextIO):
        if not data or not textIo:
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
        textIo.addCircle(spCir)
    
    #处理矩形
    #x,y,width,height,layer_id,name,xx,stroke_width
    #不填充：RECT~3998.425~3004.477~5.906~1.181~12~gge158~0~1~none~~~
    #填充：  RECT~3998.425~3004.477~5.906~1.181~12~gge158~0~0~~~~
    def handleRect(self, data: list, textIo: SprintTextIO):
        if not data or not textIo:
            return
        #print(data)
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
            textIo.addTrack(lcTra)
        else: #填充的话，使用多边形组成
            polygon = SprintPolygon(layer, strokeWidth)
            polygon.addPoint(x1, y1)
            polygon.addPoint(x1 + width, y1)
            polygon.addPoint(x1 + width, y1 + height)
            polygon.addPoint(x1, y1 + height)
            textIo.addPolygon(polygon)
    
    #开孔实现为内外径相等的过孔
    #center_x,center_y,radius,id,is_locked
    def handleHole(self, data: list, textIo: SprintTextIO):
        if not data or not textIo:
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
        textIo.addPad(spPad)
    
    #处理文本信息
    #TEXT~L~4018.5~3025.62~0.8~0~0~3~~5.9055~+~M 4020.92 3019.4999 L 4020.92 
    def handleText(self, data: list, textIo: SprintTextIO):
        if not data or not textIo or not self.importText:
            return
        
        layer = lcLayerMap.get(data[6], LAYER_S1)
        spText = SprintText(layerIdx=layer)
        spText.text = data[8]
        spText.height = mil2mm(data[7])
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
        
        textIo.addText(spText)
        
    #处理过孔，过孔被处理为双面焊盘
    #x,y,diameter,hole_radius
    #VIA~4001.969~2998.032~2.4~~0.6~gge1050~0
    def handleVia(self, data: list, textIo: SprintTextIO):
        if not data or not textIo or not self.importText:
            return

        x = mil2mm(data[0])
        y = mil2mm(data[1])
        size = mil2mm(data[2])
        drill = mil2mm(data[3]) * 2
        spPad = SprintPad(layerIdx=LAYER_C1)
        spPad.pos = (x, y)
        spPad.padType = 'PAD'
        spPad.form = PAD_FORM_ROUND
        spPad.size = size
        spPad.drill = drill
        spPad.via = True
        spPad.soldermask = False  #盖绿油
        textIo.addPad(spPad)



