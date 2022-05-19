import json, requests
from math import pow
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
    '12': LAYER_U,  #Cmts.User
    '13': LAYER_U,  #F.Fab
    '14': LAYER_U,  #B.Fab
    '15': LAYER_U,  #Dwgs.User
    '21': LAYER_I1,
    '22': LAYER_I2,
    '100': LAYER_S1,
    '101': LAYER_S1,
}

#力创焊盘形状和Sprint-Layout的对应关系
lcPadShapeMap = {
    'ELLIPSE': PAD_FORM_ROUND,
    'RECT': PAD_FORM_SQUARE,
    'OVAL': PAD_FORM_ROUND,
    'POLYGON': PAD_FORM_OCTAGON,
}

def mil2mm(data: str):
    return round(str_to_float(data) / 3.937, 3)
    
class LcComponent:
    #lcId: 力创的封装ID(以C开头，后接几位数字)
    def __init__(self, lcId: str):
        self.lcId = lcId.upper()
        self.fpUuid = self.fpName = self.fpShape = ''
        self.importText = False
        self.handlers = {
            "TRACK": self.h_TRACK,
            "PAD": self.h_PAD,
            "ARC": self.h_ARC,
            "CIRCLE": self.h_CIRCLE,
            #"SOLIDREGION": self.h_SOLIDREGION,
            #"SVGNODE": self.h_SVGNODE,
            #"VIA": self.h_VIA,
            "RECT": self.h_RECT,
            "HOLE": self.h_HOLE,
            "TEXT": self.h_TEXT,
        }

    
    #判断是否是力创EDA的组件ID，为字母C+4个数字
    @classmethod
    def isLcedaComponent(cls, txt: str):
        if ((len(txt) < 5) or (not txt.startswith(('C', 'c')))):
            return False

        for ch in txt[1:]:
            if not ch.isdigit():
                return False

        return True
        
    #根据封装信息创建一个SprintTextIo对象
    def createSprintTextIo(self, importText: bool):
        self.importText = importText
        self.fpUuid = self.getFootprintUuid()
        if not self.fpUuid:
            return None
            
        fpName, fpShape = self.getFootprintInfo(self.fpUuid)
        if not fpShape:
            return None
        
        #逐行扫描，调用对应的解析函数
        textIo = SprintTextIO(isComponent=True)
        for line in fpShape:
            args = [elem for elem in line.split("~") if elem] #去掉空元素
            model = args[0] #第一个元素为绘图种类
            if model in self.handlers:
                self.handlers.get(model)(args[1:], textIo)
        
        return textIo
        
    #根据力创商城ID获取封装的UUID
    def getFootprintUuid(self):
        try:
            data = requests.get(LC_PRODUCT_URI.format(self.lcId)).content.decode()
            lcJsonData = json.loads(data)
            if not isinstance(lcJsonData, dict) or (not lcJsonData.get('success', '')):
                return ''
            
            #获取到封装ID
            return lcJsonData["result"][-1]["component_uuid"]
        except Exception as e:
            print(str(e))
            return ''

    #联网获取封装绘制信息，返回(fpName, fpShape)
    def getFootprintInfo(self, fpUuid: str):
        try:
            response = requests.get(LC_FOOTPRINT_INFO_URI.format(fpUuid))

            if response.status_code == requests.codes.ok:
                data = json.loads(response.content.decode())
            else:
                print("create_footprint error. error code {}".format(response.status_code))
                return ('', '')
        except Exception as e:
            print(str(e))
            return ('', '')

        shape = data["result"]["dataStr"]["shape"]
        name = data["result"]["title"].replace(" ", "_").replace("/", "_")
        if not name:
            name = "NoName"
            
        return (name, shape)

    #分析Track对象
    def h_TRACK(self, data: list, textIo: SprintTextIO):
        if not data or not textIo:
            return
            
        width = mil2mm(data[0])
        try:
            points = [mil2mm(p) for p in data[2].split(" ") if p]
        except:
            if len(data) > 5:
                points = [mil2mm(p) for p in data[3].split(" ") if p]
            else:
                print("h_TRACK skipping line")
                return
        
        layer = lcLayerMap.get(data[1], LAYER_S1)
        for i in range(int(len(points) / 2) - 1):
            kiTra = SprintTrack(layer, width * 10000)
            kiTra.addPoint(points[2 * i] * 10000, points[2 * i + 1] * 10000) #Sprint-Layout以0.1微米为单位
            kiTra.addPoint(points[2 * i + 2] * 10000, points[2 * i + 3] * 10000)
            textIo.addTrack(kiTra)
            
    #分析PAD对象
    #shape,atx,aty,width,height,xx,xx,drill
    #PAD~RECT~3970.275~3002.756~4.3307~0.7874~1~~1~0~3968.1099 3002.3623 3972.4406 3002.3623 3972.4406 3003.1497 3968.1099 3003.1497~0~gge8~0~~Y~0~0~0.1969~3970.2754,3002.7561
    def h_PAD(self, data: list, textIo: SprintTextIO):
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
        if data[5] == "1": #data[5] 组装工艺
            #drill = 1
            padType = 'SMDPAD'
            layer = LAYER_C1
        elif (data[5] == "11"):
            padType = 'PAD'
            layer = LAYER_C1
            if drill == 0:
                drill = mil2mm(data[11])
        else:
            print("Skiping pad : {}".format(padNumber))
            return
        
        spPad = SprintPad(layerIdx=layer)
        spPad.pos = (x * 10000, y * 10000)
        spPad.rotation = rotation * 100 #Sprint-Layout的角度单位为0.01度
        spPad.padType = padType
        spPad.via = True #统一为镀铜过孔
        
        if (padType == 'SMDPAD'):
            spPad.sizeX = width * 10000
            spPad.sizeY = height * 10000
        else:
            spPad.size = min(width, height) * 10000
            if (spPad.size <= 0):
                spPad.size = max(width, height) * 10000

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

        spPad.drill = drill * 10000
        textIo.addPad(spPad)
    
    #处理弧形
    def h_ARC(self, data: list, textIo: SprintTextIO):
        if not data or not textIo:
            return
        
        width = mil2mm(data[0])
        layer = lcLayerMap.get(data[1], LAYER_S1)
        
        try:
            if data[2][0] == "M":
                startX, startY, midX, midY, _, _, _, endX, endY = [
                    val
                    for val in data[2].replace("M", "").replace("A", "").replace(",", " ").split(" ")
                    if val
                ]
            elif data[3][0] == "M":
                startX, startY, midX, midY, _, _, _, endX, endY = [
                    val
                    for val in data[3].replace("M", "").replace("A", "").replace(",", " ").split(" ")
                    if val
                ]
            else:
                print("h_ARC : failed to parse ARC data, token unknown")
                
            startX = mil2mm(startX)
            startY = mil2mm(startY)
            midX = mil2mm(midX)
            midY = mil2mm(midY)
            endX = mil2mm(endX)
            endY = mil2mm(endY)

            start = [startX, startY]
            end = [endX, endY]
            midpoint = [end[0] + midX, end[1] + midY]

            sq1 = pow(midpoint[0], 2) + pow(midpoint[1], 2) - pow(start[0], 2) - pow(start[1], 2)
            sq2 = pow(end[0], 2) + pow(end[1], 2) - pow(start[0], 2) - pow(start[1], 2)

            centerX = ((start[1] - end[1]) / (start[1] - midpoint[1]) * sq1 - sq2) / (
                2 * (start[0] - end[0])
                - 2 * (start[0] - midpoint[0]) * (start[1] - end[1]) / (start[1] - midpoint[1])
            )
            centerY = -(2 * (start[0] - midpoint[0]) * centerX + sq1) / (
                2 * (start[1] - midpoint[1])
            )
            
            #起点和终点到圆心的角度
            angle = math.atan2(endY - centerY, endX - centerX) - math.atan2(startY - centerY, startX - centerX)
            if angle < 0.0:
                angle = 2 * math.pi + angle
            
            spCir = SprintCircle(layerIdx=layer)
            spCir.width = width * 10000
            spCir.setArcByCenterStartAngle(centerX * 10000, centerY * 10000, startX * 10000, 
                startY * 10000, angle * 1000) #Sprint-Layout的圆弧角度单位为0.001度
            
            textIo.addCircle(spCir)
        except:
            print("h_ARC : failed to parse ARC data")
            
    #处理圆形
    #"CIRCLE~3970.472~2999.213~0.118~0.2362~101~gge555~0~~circle_gge556,circle_gge557",
    def h_CIRCLE(self, data: list, textIo: SprintTextIO):
        if not data or not textIo:
            return
            
        if (data[4] == "100"):  #焊盘上画一个圆圈，先忽略
            return
            
        centerX = mil2mm(data[0])
        centerY = mil2mm(data[1])
        radius = mil2mm(data[2])
        width = mil2mm(data[3])
        layer = lcLayerMap.get(data[4], LAYER_S1)
        
        spCir = SprintCircle(layerIdx=layer)
        spCir.center = (centerX * 10000, centerY * 10000)
        spCir.width = width * 10000
        spCir.radius = radius * 10000
        textIo.addCircle(spCir)
    
    #处理矩形
    def h_RECT(self, data: list, textIo: SprintTextIO):
        if not data or not textIo:
            return
            
        x1 = mil2mm(data[0])
        y1 = mil2mm(data[1])
        width = mil2mm(data[2])
        height = mil2mm(data[3])
        layer = lcLayerMap.get(data[4], LAYER_S1)
        kiTra = SprintTrack(layer, 0.01 * 10000)
        kiTra.addPoint(x1 * 10000, y1 * 10000) #Sprint-Layout以0.1微米为单位
        kiTra.addPoint((x1 + width) * 10000, y1 * 10000)
        kiTra.addPoint((x1 + width) * 10000, (y1 + height) * 10000)
        kiTra.addPoint(x1 * 10000, (y1 + height) * 10000)
        textIo.addTrack(kiTra)
    
    #开孔实现为内外径相等的过孔
    def h_HOLE(self, data: list, textIo: SprintTextIO):
        if not data or not textIo:
            return
            
        x = mil2mm(data[0])
        y = mil2mm(data[1])
        size = mil2mm(data[2]) * 2 #转换为直径
        spPad = SprintPad(layerIdx=LAYER_C1)
        spPad.pos = (x * 10000, y * 10000)
        spPad.padType = 'PAD'
        spPad.size = size * 10000
        spPad.drill = spPad.size
        spPad.form = PAD_FORM_ROUND
        textIo.addPad(spPad)
        
    def h_TEXT(self, data: list, textIo: SprintTextIO):
        if not data or not textIo or not self.importText:
            return
        
        layer = lcLayerMap.get(data[7], LAYER_S1)
        spText = SprintText(layerIdx=layer)
        spText.text = data[8]
        spText.height = kiText.size[0] * 10000
        
        x, y = mil2mm(data[1]), mil2mm(data[2])
        spText.pos = (x * 10000, y * 10000)
        
        textIo.addText(spText)
        


