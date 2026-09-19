#!/usr/bin/env python
#-*- coding:utf-8 -*-
"""
MCP (Model Context Protocol) 服务器
在sprintFont插件运行期间内嵌一个HTTP服务器，向外部LLM客户端(如OpenAI/Antigravity/Claude/Cursor/ZCode等)
暴露Sprint-Layout的完整Text-IO接口，使AI可以通过MCP协议直接读取/绘制/修改PCB板图。
传输方式：Streamable HTTP (协议版本2025-06-18/2025-03-26)，端点 http://127.0.0.1:<port>/mcp
仅使用Python标准库实现，无第三方依赖。
坐标约定(与Text-IO文件格式一致)：单位mm，原点在板左上角，X向右，Y向下。
角度约定：焊盘/文本旋转顺时针为正(度)；圆弧起止角0度在3点钟方向，逆时针为正(度)。
Author: cdhigh <https://github.com/cdhigh>
"""
import os, json, math, copy, pickle, uuid, threading, traceback, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import socketserver

from app.config_manager import DEFAULT_MCP_PORT

from sprint_struct.sprint_element import *
from sprint_struct.sprint_track import SprintTrack
from sprint_struct.sprint_pad import SprintPad, sprintPadFormMap, PAD_FORM_ROUND
from sprint_struct.sprint_polygon import SprintPolygon
from sprint_struct.sprint_text import SprintText
from sprint_struct.sprint_circle import SprintCircle
from sprint_struct.sprint_group import SprintGroup
from sprint_struct.sprint_component import SprintComponent
from sprint_struct.sprint_textio import SprintTextIO
from sprint_struct.sprint_textio_parser import SprintTextIoParser
from sprint_struct.sprint_export_dsn import PcbRule, SprintExportDsn

#MCP协议版本协商
#只声明实现了Streamable HTTP传输的版本；2024-11-05的传输是HTTP+SSE双端点(GET建立SSE流+endpoint事件)，
#本服务器未实现(GET一律405)，声明它会导致旧客户端在握手期失败而非干净地版本协商回退
MCP_PROTOCOL_VERSIONS = ('2025-06-18', '2025-03-26')
MCP_LATEST_PROTOCOL_VERSION = '2025-06-18'
MCP_ENDPOINT_PATH = '/mcp'
MAX_UNDO_STEPS = 30 #撤销栈深度
DEFAULT_PAGE_LIMIT = 200 #getElements默认返回条数
MAX_PAGE_LIMIT = 2000 #getElements最大返回条数
MAX_LOG_ENTRIES = 500 #交互日志的最大保留条数
MAX_LOG_ARG_CHARS = 120 #交互日志中参数摘要的最大字符数

#板层短名字到板层索引的映射(1-7)
LAYER_NAME_MAP = {'C1': LAYER_C1, 'S1': LAYER_S1, 'C2': LAYER_C2, 'S2': LAYER_S2,
    'I1': LAYER_I1, 'I2': LAYER_I2, 'U': LAYER_U}
for _idx, _name in sprintLayerMap.items(): #F.Cu/B.Cu等KiCad风格名字
    LAYER_NAME_MAP[_name.upper()] = _idx

#焊盘形状名字到形状代码的映射
PAD_FORM_NAME_MAP = {value.upper(): key for key, value in sprintPadFormMap.items()}

#updateElements工具支持的属性清单: 属性名 -> (JSON类型, 描述)
#与toolUpdateElements/applyUpdateToElement的解析逻辑保持一致，新增属性时两处都要改
UPDATE_ELEMENT_PROPS = {
    'layer': ('string', 'Optional: move element(s) to this layer. Integer 1-7 (1=C1 front copper, '
        '2=S1 front silkscreen, 3=C2 back copper, 4=S2 back silkscreen, 5=I1, 6=I2, 7=U outline) '
        'or name like "C1"/"F.Cu". Ignored for COMPONENT/GROUP (their layer is derived from their '
        'contents); a layer-only change on them reports updated=0'),
    'name': ('string', 'Optional: set element name as a free-form label (empty string to clear; '
        'Sprint-Layout has no net names, this is display only)'),
    'width': ('number', 'TRACK/ZONE/CIRCLE: line width in mm'),
    'clearance': ('number', 'Optional: distance to automatic ground-plane in mm. '
        'For PAD note that 0 means direct connection (cross pad)'),
    'cutout': ('boolean', 'TRACK/ZONE/TEXT/CIRCLE: cutout/keepout flag'),
    'soldermask': ('boolean', 'Optional: expose soldermask opening over the element'),
    'flatStart': ('boolean', 'TRACK: start point is flat (not rounded)'),
    'flatEnd': ('boolean', 'TRACK: end point is flat (not rounded)'),
    'hatch': ('boolean', 'ZONE: hatched filling instead of solid'),
    'hatchAuto': ('boolean', 'ZONE: hatch thickness equals outline width'),
    'hatchWidth': ('number', 'ZONE: custom hatch line thickness in mm'),
    'pos': ('array', 'PAD/SMDPAD/TEXT: new position [x, y] in mm'),
    'size': ('number', 'PAD: outer diameter in mm (sets sizeX=sizeY)'),
    'sizeX': ('number', 'PAD/SMDPAD: width in mm'),
    'sizeY': ('number', 'PAD/SMDPAD: height in mm'),
    'drill': ('number', 'PAD: drill diameter in mm, 0 for no drill (must be >= 0)'),
    'form': ('integer', 'PAD: shape 1-9 or a shape name like Round/Octagon/Square/RectH'),
    'rotation': ('number', 'PAD/SMDPAD/TEXT: rotation in degrees, clockwise-positive'),
    'via': ('boolean', 'PAD: double-sided pad'),
    'thermal': ('boolean', 'PAD: thermal pad on automatic ground-plane'),
    'thermalTracksWidth': ('number', 'PAD: thermal spoke width in mm'),
    'thermalTracks': ('integer', 'PAD: thermal spoke count'),
    'thermalTracksIndividual': ('boolean', 'PAD: use individual thermal spoke settings'),
    'text': ('string', 'TEXT: new text content (non-empty)'),
    'height': ('number', 'TEXT: text height in mm'),
    'style': ('integer', 'TEXT: 0=Narrow, 1=Normal, 2=Wide'),
    'thickness': ('integer', 'TEXT: 0=Thin, 1=Normal, 2=Bold'),
    'mirrorHorz': ('boolean', 'TEXT: mirrored horizontally'),
    'mirrorVert': ('boolean', 'TEXT: mirrored vertically'),
    'visible': ('boolean', 'TEXT (component id/value label): visible'),
    'center': ('array', 'CIRCLE: new center [x, y] in mm'),
    'radius': ('number', 'CIRCLE: new radius in mm'),
    'startAngle': ('number', 'CIRCLE: arc start angle in degrees, 0 at 3 o\'clock, counterclockwise'),
    'stopAngle': ('number', 'CIRCLE: arc stop angle in degrees, counterclockwise'),
    'fill': ('boolean', 'CIRCLE: filled circle'),
    'idText': ('string', 'COMPONENT: new reference designator (id label text)'),
    'valueText': ('string', 'COMPONENT: new value label text'),
    'package': ('string', 'COMPONENT: package name'),
    'comment': ('string', 'COMPONENT: comment'),
}

#标准封装生成器(addStandardFootprint)的几何定义，单位mm，内部坐标Y向下，封装以原点(0,0)为几何中心构建
#被动元件：padSizeX/padSizeY焊盘尺寸、pitch两焊盘中心距、bodyX/bodyY丝印体尺寸
CHIP_PASSIVE_FOOTPRINTS = {
    '0402': (0.55, 0.55, 1.10, 1.0, 0.5),
    '0603': (0.90, 0.95, 1.80, 1.6, 0.85),
    '0805': (1.00, 1.50, 2.10, 2.1, 1.25),
    '1206': (1.20, 1.80, 3.10, 3.2, 1.65),
}
SOIC_PITCH = 1.27          #同排引脚间距
SOIC_ROW_DISTANCE = 5.4    #两排焊盘中心距
SOIC_PAD = (1.5, 0.6)      #(sizeX跨机体方向, sizeY沿排方向)
SOIC_BODY_WIDTH = 3.9
SOIC_BODY_LENGTH = {8: 4.9, 14: 8.65, 16: 9.9}
DIP_PITCH = 2.54
DIP_ROW_DISTANCE = 7.62    #300mil标准排距
TH_PAD_SIZE = 1.7          #通孔焊盘外径(DIP与排针共用)
TH_DRILL = 1.0             #通孔钻孔直径(DIP与排针共用)
SOT23_ROW_DISTANCE = 2.3   #左右焊盘中心距
SOT23_PIN_SPAN = 1.9       #同侧两焊盘中心距
SOT23_PAD = (1.0, 0.65)
SOT23_BODY = (1.5, 2.5)
HEADER_PITCH = 2.54
SILK_WIDTH = 0.15          #标准封装丝印线宽

#MCP服务器初始化时返回给客户端的说明文本
MCP_INSTRUCTIONS = (
    'This is a PCB editor bridge for Sprint-Layout v6. The AI can inspect, draw and modify a PCB board '
    'through Text-IO elements (TRACK/PAD/SMDPAD/ZONE/TEXT/CIRCLE, optionally grouped into COMPONENT/GROUP).\n'
    'Units: all coordinates and lengths in millimeters (float), all angles in degrees.\n'
    'Coordinates: origin at the TOP-LEFT of the board, X increases to the right, Y increases DOWNWARD '
    '(same as the Sprint-Layout Text-IO file format and the on-screen view).\n'
    'Layers (LAYER=): 1=C1 front copper, 2=S1 front silkscreen, 3=C2 back copper, 4=S2 back silkscreen, '
    '5=I1 inner1, 6=I2 inner2, 7=U outline. Accepts int 1-7 or name like "C1"/"F.Cu".\n'
    'Rotation: pad/text rotation is clockwise-positive; circle arc angles are counterclockwise from 3 o\'clock.\n'
    'Typical workflow: getBoardInfo -> place standard footprints (0402-1206 passives, SOIC/DIP-8/14/16, '
    'SOT-23, pin headers) with addStandardFootprint, draw everything else with batchAdd (many elements in '
    'one call) or the individual addTrack/addPad/addSmdPad/addZone/addText/addCircle/addComponent tools '
    '-> adjust placement with moveElements/rotateElements/mirrorElements, refine in place with updateElements '
    '-> route tracks, then checkDrc to catch clearance/width violations '
    '-> getElements/getNetlist to verify, exportSvg for a visual check '
    '-> applyToSprintLayout (or exportTextIo/saveTextIoFile).\n'
    'When routing manually, follow the design rules returned by getBoardInfo (rules: trackWidth, '
    'viaDiameter/viaDrill, clearance, smdSmdClearance, all in mm) and verify connectivity with getNetlist '
    '(it reports physical-touch nets only, not design intent).\n'
    'On large boards, keep getElements responses small: use the type/layer/bbox filters (bbox=[xMin, yMin, '
    'xMax, yMax] in mm finds the obstacles in a region), depth=0 for component/group summaries without '
    'their sub-elements, or indices=[...] to fetch specific elements only.\n'
)

#MCP工具调用错误，会被转换为isError=True的工具结果
class McpToolError(Exception):
    pass

#HTTP服务器：跳过socket.getfqdn反向DNS解析(Windows下可能阻塞1秒以上)，直接使用IP
class McpHttpServer(ThreadingHTTPServer):
    def server_bind(self):
        socketserver.TCPServer.server_bind(self)
        host, port = self.server_address[:2]
        self.server_name = '127.0.0.1'
        self.server_port = port

#JSON-RPC协议级错误
class McpRpcError(Exception):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code
        self.message = message

#判断一个mm浮点数是否为有效数值
def isFiniteNumber(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)

#四舍五入mm浮点数便于JSON输出
def roundMm(value):
    return round(value, 4)

#把工具调用的参数压缩成一行摘要文本(用于交互日志)
def summarizeArguments(arguments):
    try:
        text = json.dumps(arguments, ensure_ascii=False, default=str)
    except Exception:
        text = str(arguments)
    text = text.replace('\n', ' ')
    return text if len(text) <= MAX_LOG_ARG_CHARS else text[:MAX_LOG_ARG_CHARS - 3] + '...'

#获取元素的类型名字
def getElementType(elem):
    if isinstance(elem, SprintTrack):
        return 'TRACK'
    elif isinstance(elem, SprintPad):
        return elem.padType if elem.padType in ('PAD', 'SMDPAD') else 'PAD'
    elif isinstance(elem, SprintPolygon):
        return 'ZONE'
    elif isinstance(elem, SprintText):
        return 'TEXT'
    elif isinstance(elem, SprintCircle):
        return 'CIRCLE'
    elif isinstance(elem, SprintComponent):
        return 'COMPONENT'
    elif isinstance(elem, SprintGroup):
        return 'GROUP'
    return 'UNKNOWN'

#将一个绘图元素转换为JSON兼容的字典
#idx: 元素在父容器中的索引, depth: 展开子元素的层数(0=不展开)
def elementToDict(elem, idx, depth=1):
    #SprintGroup/SprintTextIO的__init__有super().__init__(self)的笔误，layerIdx可能不是int，需要防御
    layerIdx = getattr(elem, 'layerIdx', None)
    if not isinstance(layerIdx, int):
        layerIdx = None
    ret = {'index': idx, 'type': getElementType(elem)}
    if layerIdx is not None:
        ret['layer'] = layerIdx
        layerName = sprintLayerMap.get(layerIdx, '')
        if layerName:
            ret['layerName'] = layerName
    if elem.name:
        ret['name'] = elem.name

    #外框(元素无效时跳过，四个坐标必须全部有限，避免NaN/Infinity进入JSON)
    try:
        if (math.isfinite(elem.xMin) and math.isfinite(elem.yMin)
                and math.isfinite(elem.xMax) and math.isfinite(elem.yMax)):
            ret['bbox'] = [roundMm(elem.xMin), roundMm(elem.yMin), roundMm(elem.xMax), roundMm(elem.yMax)]
    except Exception:
        pass

    if isinstance(elem, SprintTrack):
        ret['width'] = roundMm(elem.width)
        ret['points'] = [[roundMm(x), roundMm(y)] for (x, y) in elem.points]
        ret['length'] = elem.length
        if elem.clearance:
            ret['clearance'] = roundMm(elem.clearance)
        for key, value in (('flatStart', elem.flatstart), ('flatEnd', elem.flatend),
                ('cutout', elem.cutout), ('soldermask', elem.soldermask)):
            if value is not None:
                ret[key] = value
    elif isinstance(elem, SprintPad):
        ret['pos'] = [roundMm(elem.pos[0]), roundMm(elem.pos[1])]
        ret['size'] = roundMm(elem.size)
        ret['sizeX'] = roundMm(elem.sizeX)
        ret['sizeY'] = roundMm(elem.sizeY)
        ret['drill'] = roundMm(elem.drill)
        ret['form'] = elem.form
        ret['formName'] = sprintPadFormMap.get(elem.form, '')
        if elem.rotation:
            ret['rotation'] = elem.rotation
        if elem.via is not None:
            ret['via'] = elem.via
        if elem.thermal is not None:
            ret['thermal'] = elem.thermal
        if elem.clearance is not None:
            ret['clearance'] = roundMm(elem.clearance)
        if elem.soldermask is not None:
            ret['soldermask'] = elem.soldermask
        if elem.thermalTracksWidth:
            ret['thermalTracksWidth'] = roundMm(elem.thermalTracksWidth)
        if elem.thermalTracksIndividual is not None:
            ret['thermalTracksIndividual'] = elem.thermalTracksIndividual
        if elem.thermalTracks:
            ret['thermalTracks'] = elem.thermalTracks
        if elem.padId is not None:
            ret['padId'] = elem.padId
        if elem.connectToOtherPads:
            ret['connectsTo'] = list(elem.connectToOtherPads)
    elif isinstance(elem, SprintPolygon):
        ret['width'] = roundMm(elem.width)
        ret['points'] = [[roundMm(x), roundMm(y)] for (x, y) in elem.points]
        ret['area'] = roundMm(elem.area())
        for key, value in (('hatch', elem.hatch), ('cutout', elem.cutout),
                ('soldermask', elem.soldermask), ('soldermaskCutout', elem.soldermaskCutout),
                ('hatchAuto', elem.hatchAuto)):
            if value is not None:
                ret[key] = value
        if elem.hatchWidth:
            ret['hatchWidth'] = roundMm(elem.hatchWidth)
        if elem.clearance:
            ret['clearance'] = roundMm(elem.clearance)
    elif isinstance(elem, SprintText):
        ret['pos'] = [roundMm(elem.pos[0]), roundMm(elem.pos[1])]
        ret['text'] = elem.text
        ret['height'] = roundMm(elem.height)
        if elem.style is not None:
            ret['style'] = elem.style
        if elem.thickness is not None:
            ret['thickness'] = elem.thickness
        if elem.rotation:
            ret['rotation'] = elem.rotation
        for key, value in (('mirrorHorz', elem.mirrorH), ('mirrorVert', elem.mirrorV),
                ('cutout', elem.cutout), ('soldermask', elem.soldermask)):
            if value is not None:
                ret[key] = value
        if elem.clearance:
            ret['clearance'] = roundMm(elem.clearance)
        ret['visible'] = elem.visible
    elif isinstance(elem, SprintCircle):
        ret['center'] = [roundMm(elem.center[0]), roundMm(elem.center[1])]
        ret['radius'] = roundMm(elem.radius)
        ret['width'] = roundMm(elem.width)
        ret['startAngle'] = roundMm(elem.start)
        ret['stopAngle'] = roundMm(elem.stop)
        if elem.fill is not None:
            ret['fill'] = elem.fill
        if elem.clearance:
            ret['clearance'] = roundMm(elem.clearance)
        if elem.cutout is not None:
            ret['cutout'] = elem.cutout
        if elem.soldermask is not None:
            ret['soldermask'] = elem.soldermask
    elif isinstance(elem, SprintComponent):
        ret['id'] = elem.idText.text
        ret['value'] = elem.valueText.text
        if elem.package:
            ret['package'] = elem.package
        if elem.comment:
            ret['comment'] = elem.comment
        ret['mounting'] = elem.getMountingType()
        ret['elementCount'] = len(elem.elements)
        if depth > 0:
            ret['subElements'] = [elementToDict(sub, subIdx, depth - 1)
                for subIdx, sub in enumerate(elem.elements)]
    elif isinstance(elem, SprintGroup):
        ret['elementCount'] = len(elem.elements)
        if depth > 0:
            ret['subElements'] = [elementToDict(sub, subIdx, depth - 1)
                for subIdx, sub in enumerate(elem.elements)]

    return ret


#判断元素的包围盒是否与查询范围相交(用于getElements的bbox空间过滤)
#包围盒无效(尚未计算，正负无穷)的元素一律排除
def elementIntersectsBbox(elem, bbox):
    try:
        if not (math.isfinite(elem.xMin) and math.isfinite(elem.yMin)
                and math.isfinite(elem.xMax) and math.isfinite(elem.yMax)):
            return False
    except Exception:
        return False
    qxMin, qyMin, qxMax, qyMax = bbox
    return not ((elem.xMax < qxMin) or (elem.xMin > qxMax)
        or (elem.yMax < qyMin) or (elem.yMin > qyMax))


#计算若干元素包围盒的并集，返回(xMin, yMin, xMax, yMax)，元素列表为空时返回None
def unionElementBbox(objs):
    coords = []
    for obj in objs:
        try:
            if math.isfinite(obj.xMin) and math.isfinite(obj.yMin) \
                    and math.isfinite(obj.xMax) and math.isfinite(obj.yMax):
                coords.append((obj.xMin, obj.yMin, obj.xMax, obj.yMax))
        except Exception:
            pass
    if not coords:
        return None
    return (min(c[0] for c in coords), min(c[1] for c in coords),
        max(c[2] for c in coords), max(c[3] for c in coords))


#MCP服务器主类，持有板图数据并提供HTTP+JSON-RPC服务
class SprintMcpServer:
    #textIo: 共享的SprintTextIO板图实例
    #serverVersion: 服务器版本号(取自sprintFont.__Version__)
    #pcbRule: 默认布线规则(PcbRule实例，可为None)
    #onApplyRequest: 回写Sprint-Layout的回调，原型 onApplyRequest(mode)，在MCP线程中被调用
    #pcbAll: 插件是否以整板模式启动
    #hasInputFile: 插件是否有输入文件(非Standalone模式)
    def __init__(self, textIo, serverVersion='', pcbRule=None, onApplyRequest=None,
            pcbAll=False, hasInputFile=False):
        self.textIo = textIo
        self.serverVersion = serverVersion or '1.0'
        self.pcbRule = pcbRule or PcbRule()
        self.onApplyRequest = onApplyRequest
        self.pcbAll = pcbAll
        self.hasInputFile = hasInputFile
        self.replaceDisabled = False #输入板图解析失败时由sprintFont置True，禁止replace整板回写

        self.boardLock = threading.RLock() #保护textIo的读写锁
        self.undoStack = [] #撤销快照栈(deepcopy的SprintTextIO)
        self.sessions = set() #已建立的MCP会话
        self.clientName = '' #最近一次initialize的客户端名字

        #供主线程状态栏轮播显示的状态文本(跨线程只做整体赋值)
        self.statusText = ''

        #交互日志(线程安全，供MCP状态窗口轮询显示LLM的调用概要)
        self.logEntries = [] #元素为(time戳, 文本)
        self.logLock = threading.Lock()

        self.httpd = None #ThreadingHTTPServer实例
        self.serverThread = None #服务线程
        self.listenPort = 0 #当前监听端口

        self.toolDefinitions = None #工具定义缓存
        self.toolHandlers = {
            'getBoardInfo': self.toolGetBoardInfo,
            'getElements': self.toolGetElements,
            'clearBoard': self.toolClearBoard,
            'setBoardSize': self.toolSetBoardSize,
            'addTrack': self.toolAddTrack,
            'addPad': self.toolAddPad,
            'addSmdPad': self.toolAddSmdPad,
            'addZone': self.toolAddZone,
            'addText': self.toolAddText,
            'addCircle': self.toolAddCircle,
            'addComponent': self.toolAddComponent,
            'batchAdd': self.toolBatchAdd,
            'addStandardFootprint': self.toolAddStandardFootprint,
            'deleteElements': self.toolDeleteElements,
            'moveElements': self.toolMoveElements,
            'rotateElements': self.toolRotateElements,
            'mirrorElements': self.toolMirrorElements,
            'groupElements': self.toolGroupElements,
            'updateElements': self.toolUpdateElements,
            'undo': self.toolUndo,
            'importTextIo': self.toolImportTextIo,
            'exportTextIo': self.toolExportTextIo,
            'exportSvg': self.toolExportSvg,
            'loadTextIoFile': self.toolLoadTextIoFile,
            'saveTextIoFile': self.toolSaveTextIoFile,
            'getNetlist': self.toolGetNetlist,
            'checkDrc': self.toolCheckDrc,
            'exportDsn': self.toolExportDsn,
            'importSes': self.toolImportSes,
            'applyToSprintLayout': self.toolApplyToSprintLayout,
        }

    #启动HTTP服务器，成功返回(True, 状态文本)，失败返回(False, 错误文本)
    def start(self, port=DEFAULT_MCP_PORT):
        if self.httpd is not None:
            self.stop()
        port = int(port)
        if not (1024 <= port <= 65535):
            port = DEFAULT_MCP_PORT
        try:
            #只绑定本机回环地址，避免暴露到局域网
            self.httpd = McpHttpServer(('127.0.0.1', port), McpHttpRequestHandler)
        except OSError as e:
            self.httpd = None
            return (False, 'MCP failed to bind port {}: {}'.format(port, str(e)))
        self.httpd.daemon_threads = True
        self.httpd.mcpServer = self
        self.listenPort = port
        self.serverThread = threading.Thread(target=self.httpd.serve_forever,
            kwargs={'poll_interval': 0.2}, daemon=True)
        self.serverThread.start()
        self.setStatusText('MCP: http://127.0.0.1:{}/mcp (running)'.format(port))
        self.addLogEntry('server started on port {}'.format(port))
        return (True, self.statusText)

    #停止HTTP服务器
    def stop(self):
        httpd = self.httpd
        self.httpd = None
        self.listenPort = 0
        if httpd is not None:
            try:
                httpd.shutdown()
                httpd.server_close()
            except Exception:
                pass
        self.sessions = set()
        self.addLogEntry('server stopped')
        self.setStatusText('')

    #服务器是否正在运行
    def isRunning(self):
        return self.httpd is not None

    #设置状态文本
    def setStatusText(self, text):
        self.statusText = text

    #创建一个新会话，返回会话ID
    def createSession(self):
        sessionId = uuid.uuid4().hex
        self.sessions.add(sessionId)
        return sessionId

    #检查会话ID是否有效
    def checkSession(self, sessionId):
        return sessionId in self.sessions

    #JSON-RPC消息分发，返回result或None(通知类消息)
    def dispatchMessage(self, method, params, requestHandler):
        if method == 'initialize':
            return self.handleInitialize(params, requestHandler)
        elif method.startswith('notifications/'):
            return None #所有通知类消息一律忽略
        elif method == 'ping':
            return {}
        elif method == 'tools/list':
            return {'tools': self.getToolDefinitions()}
        elif method == 'tools/call':
            return self.handleToolCall(params)
        elif method == 'resources/list':
            return {'resources': []}
        elif method == 'resources/templates/list':
            return {'resourceTemplates': []}
        elif method == 'prompts/list':
            return {'prompts': []}
        elif method == 'completion/complete':
            return {'completion': {'values': [], 'total': 0, 'hasMore': False}}
        elif method == 'logging/setLevel':
            return {}
        else:
            raise McpRpcError(-32601, 'Method not found: {}'.format(method))

    #处理initialize请求，协商协议版本并建立会话
    def handleInitialize(self, params, requestHandler):
        requested = str(params.get('protocolVersion') or '')
        version = requested if requested in MCP_PROTOCOL_VERSIONS else MCP_LATEST_PROTOCOL_VERSION
        clientInfo = params.get('clientInfo') or {}
        self.clientName = str(clientInfo.get('name', ''))
        if requestHandler is not None:
            requestHandler.responseSessionId = self.createSession()
        self.addLogEntry('LLM connected: {} (protocol {})'.format(self.clientName or 'unknown', version))
        return {
            'protocolVersion': version,
            'capabilities': {'tools': {}},
            'serverInfo': {'name': 'sprintFont', 'version': self.serverVersion},
            'instructions': MCP_INSTRUCTIONS,
        }

    #处理tools/call请求
    def handleToolCall(self, params):
        name = str(params.get('name') or '')
        arguments = params.get('arguments') or {}
        if not isinstance(arguments, dict):
            raise McpRpcError(-32602, 'Tool arguments must be an object')
        handlerFn = self.toolHandlers.get(name)
        if handlerFn is None:
            self.addLogEntry('{} error: unknown tool'.format(name))
            return self.buildToolErrorResult('Unknown tool: {}'.format(name))

        startClock = time.time()
        with self.boardLock:
            try:
                payload = handlerFn(arguments)
                text = json.dumps(payload, ensure_ascii=False, default=str)
                result = {'content': [{'type': 'text', 'text': text}], 'isError': False}
            except McpToolError as e:
                result = self.buildToolErrorResult(str(e))
            except Exception as e:
                traceback.print_exc()
                result = self.buildToolErrorResult('{}: {}'.format(type(e).__name__, e))

        elapsed = int((time.time() - startClock) * 1000)
        statusText = 'error' if result.get('isError') else 'ok'
        self.addLogEntry('{} {} ({} ms): {}'.format(name, statusText, elapsed, summarizeArguments(arguments)))
        return result

    #记录一条MCP交互日志(线程安全，超出上限时丢弃最早的)
    def addLogEntry(self, text):
        with self.logLock:
            self.logEntries.append((time.time(), text))
            if len(self.logEntries) > MAX_LOG_ENTRIES:
                del self.logEntries[:len(self.logEntries) - MAX_LOG_ENTRIES]

    #取出自lastIndex之后的新日志，返回(新日志列表, 最新索引)
    def drainLogEntries(self, lastIndex):
        with self.logLock:
            return self.logEntries[lastIndex:], len(self.logEntries)

    #构造isError=True的工具结果
    def buildToolErrorResult(self, message):
        payload = {'error': message}
        text = json.dumps(payload, ensure_ascii=False)
        return {'content': [{'type': 'text', 'text': text}], 'isError': True}

    #获取全部工具定义(带缓存)
    def getToolDefinitions(self):
        if self.toolDefinitions is None:
            self.toolDefinitions = buildToolDefinitions()
        return self.toolDefinitions

    #在锁内对板图做一次撤销快照并入栈，在每次修改性操作前调用
    def pushUndoSnapshot(self):
        self.commitUndoSnapshot(self.takeUndoSnapshot())

    #取一个撤销快照(暂不入栈)，调用方确认操作确实产生修改后再commitUndoSnapshot入栈，
    #避免无实际修改的操作(如dx=dy=0、属性全部不生效)也消耗撤销步数
    def takeUndoSnapshot(self):
        return copy.deepcopy(self.textIo)

    #把已取的快照压入撤销栈(满MAX_UNDO_STEPS时淘汰最旧一步)
    def commitUndoSnapshot(self, snapshot):
        if len(self.undoStack) >= MAX_UNDO_STEPS:
            self.undoStack.pop(0)
        self.undoStack.append(snapshot)

    #添加一个元素到板图，返回其索引
    def addElement(self, elem):
        if elem is None:
            raise McpToolError('Failed to create element')
        if not elem.isValid():
            raise McpToolError('Element is invalid (check required geometry parameters)')
        self.pushUndoSnapshot()
        self.textIo.add(elem)
        return len(self.textIo.elements) - 1

    #根据索引列表取顶层元素对象(保持原序去重)，索引非法时抛出McpToolError
    def getElementsByIndices(self, indices):
        return [obj for _, obj in self.resolveElementIndices(indices)]

    #根据索引列表解析出(索引, 元素)对，保持原序去重，索引非法时抛出McpToolError
    def resolveElementIndices(self, indices):
        if not isinstance(indices, (list, tuple)) or not indices:
            raise McpToolError('indices must be a non-empty array of element indexes')
        count = len(self.textIo.elements)
        ret = []
        seen = set()
        for idx in indices:
            if not isinstance(idx, int) or isinstance(idx, bool) or not (0 <= idx < count):
                raise McpToolError('Invalid element index: {} (valid range: 0-{})'.format(idx, count - 1))
            if idx in seen:
                continue
            seen.add(idx)
            ret.append((idx, self.textIo.elements[idx]))
        return ret

    #解析板层参数，接受1-7整数或板层名字，失败抛出McpToolError
    def parseLayerValue(self, value, default=None, argName='layer'):
        if value is None:
            if default is None:
                raise McpToolError('Missing required parameter: {}'.format(argName))
            return default
        if isinstance(value, bool):
            raise McpToolError('{} must be an integer 1-7 or a layer name'.format(argName))
        if isinstance(value, (int, float)):
            layer = int(value)
            if LAYER_C1 <= layer <= LAYER_U:
                return layer
            raise McpToolError('{} must be 1-7, got {}'.format(argName, value))
        if isinstance(value, str):
            key = value.strip().upper()
            if key in LAYER_NAME_MAP:
                return LAYER_NAME_MAP[key]
            raise McpToolError('Unknown layer name: {} (use 1-7 or C1/S1/C2/S2/I1/I2/U)'.format(value))
        raise McpToolError('{} must be an integer 1-7 or a layer name'.format(argName))

    #解析一个可选的布尔参数
    def parseOptionalBool(self, args, key, default=None):
        value = args.get(key)
        if value is None:
            return default
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.strip().lower() in ('true', 'yes', '1', 'on', 'y')
        raise McpToolError('{} must be a boolean'.format(key))

    #解析一个可选的数值参数
    def parseOptionalFloat(self, args, key, default=None):
        value = args.get(key)
        if value is None or value == '':
            return default
        if isFiniteNumber(value):
            return float(value)
        raise McpToolError('{} must be a number'.format(key))

    #解析一个正数参数
    def parsePositiveFloat(self, args, key, minValue=0.0001):
        value = self.parseOptionalFloat(args, key)
        if value is None:
            raise McpToolError('Missing required parameter: {} (number, unit mm)'.format(key))
        if value < minValue:
            raise McpToolError('{} must be >= {}'.format(key, minValue))
        return value

    #解析一个可选的正数参数：未提供返回None，提供了但小于minValue则报错，绝不静默回退默认值
    def parseOptionalPositiveFloat(self, args, key, minValue=0.0001):
        value = self.parseOptionalFloat(args, key)
        if (value is not None) and (value < minValue):
            raise McpToolError('{} must be >= {} (unit mm)'.format(key, minValue))
        return value

    #解析一个(x, y)坐标点
    def parsePoint(self, value, argName='point'):
        if (not isinstance(value, (list, tuple))) or (len(value) != 2):
            raise McpToolError('{} must be an [x, y] array (unit mm)'.format(argName))
        x, y = value
        if (not isFiniteNumber(x)) or (not isFiniteNumber(y)):
            raise McpToolError('{} contains non-numeric values'.format(argName))
        return (float(x), float(y))

    #解析焊盘形状参数，接受1-9整数或形状名字
    def parsePadForm(self, value):
        if value is None:
            return PAD_FORM_ROUND
        if isinstance(value, bool):
            raise McpToolError('form must be 1-9 or a shape name')
        if isinstance(value, (int, float)):
            form = int(value)
            if 1 <= form <= 9:
                return form
            raise McpToolError('form must be 1-9, got {}'.format(value))
        if isinstance(value, str):
            key = value.strip().upper()
            if key in PAD_FORM_NAME_MAP:
                return PAD_FORM_NAME_MAP[key]
            raise McpToolError('Unknown pad form name: {} (use 1-9 or Round/Octagon/Square/RectH...)'.format(value))
        raise McpToolError('form must be 1-9 or a shape name')

    #从一个spec字典构建SprintTrack
    def buildTrackFromSpec(self, spec):
        layer = self.parseLayerValue(spec.get('layer'))
        width = spec.get('width')
        if (not isFiniteNumber(width)) or (width <= 0):
            raise McpToolError('track.width must be a positive number (unit mm)')
        pointsRaw = spec.get('points')
        if (not isinstance(pointsRaw, (list, tuple))) or (len(pointsRaw) < 2):
            raise McpToolError('track.points must be an array of at least 2 [x, y] points')
        track = SprintTrack(layer, float(width))
        for pt in pointsRaw:
            track.addPoint(self.parsePoint(pt, 'track.points'))
        track.clearance = max(0, self.parseOptionalFloat(spec, 'clearance', 0) or 0)
        track.flatstart = self.parseOptionalBool(spec, 'flatStart', None)
        track.flatend = self.parseOptionalBool(spec, 'flatEnd', None)
        track.cutout = self.parseOptionalBool(spec, 'cutout', None)
        track.soldermask = self.parseOptionalBool(spec, 'soldermask', None)
        if spec.get('name'):
            track.name = track.sanitizeText(str(spec['name']))
        return track

    #从一个spec字典构建通孔SprintPad
    def buildPadFromSpec(self, spec):
        layer = self.parseLayerValue(spec.get('layer'))
        pad = SprintPad(padType='PAD', layerIdx=layer)
        pad.pos = self.parsePoint(spec.get('pos'), 'pad.pos')
        size = spec.get('size')
        if (not isFiniteNumber(size)) or (size <= 0):
            raise McpToolError('pad.size must be a positive number (unit mm)')
        pad.size = float(size)
        drill = self.parseOptionalFloat(spec, 'drill', 0) or 0
        if drill < 0:
            raise McpToolError('pad.drill must be >= 0 (unit mm)')
        pad.drill = drill
        pad.form = self.parsePadForm(spec.get('form'))
        pad.rotation = self.parseOptionalFloat(spec, 'rotation', 0) or 0
        pad.via = self.parseOptionalBool(spec, 'via', None)
        pad.thermal = self.parseOptionalBool(spec, 'thermal', None)
        thermalTracksWidth = self.parseOptionalFloat(spec, 'thermalTracksWidth')
        if thermalTracksWidth:
            if thermalTracksWidth < 0:
                raise McpToolError('pad.thermalTracksWidth must be >= 0 (unit mm)')
            pad.thermalTracksWidth = thermalTracksWidth
        pad.thermalTracksIndividual = self.parseOptionalBool(spec, 'thermalTracksIndividual', None)
        thermalTracks = spec.get('thermalTracks')
        if isFiniteNumber(thermalTracks):
            if thermalTracks < 0:
                raise McpToolError('pad.thermalTracks must be a non-negative integer')
            pad.thermalTracks = int(thermalTracks)
        pad.clearance = self.parseOptionalFloat(spec, 'clearance', None)
        if (pad.clearance is not None) and (pad.clearance < 0):
            raise McpToolError('pad.clearance must be >= 0 (unit mm)')
        pad.soldermask = self.parseOptionalBool(spec, 'soldermask', None)
        if spec.get('name'):
            pad.name = pad.sanitizeText(str(spec['name']))
        return pad

    #从一个spec字典构建贴片SprintPad
    def buildSmdPadFromSpec(self, spec):
        layer = self.parseLayerValue(spec.get('layer'))
        pad = SprintPad(padType='SMDPAD', layerIdx=layer)
        pad.pos = self.parsePoint(spec.get('pos'), 'smdPad.pos')
        sizeX = spec.get('sizeX')
        sizeY = spec.get('sizeY')
        if (not isFiniteNumber(sizeX)) or (sizeX <= 0) or (not isFiniteNumber(sizeY)) or (sizeY <= 0):
            raise McpToolError('smdPad.sizeX/sizeY must be positive numbers (unit mm)')
        pad.sizeX = float(sizeX)
        pad.sizeY = float(sizeY)
        pad.rotation = self.parseOptionalFloat(spec, 'rotation', 0) or 0
        pad.clearance = self.parseOptionalFloat(spec, 'clearance', None)
        if (pad.clearance is not None) and (pad.clearance < 0):
            raise McpToolError('pad.clearance must be >= 0 (unit mm)')
        pad.soldermask = self.parseOptionalBool(spec, 'soldermask', None)
        if spec.get('name'):
            pad.name = pad.sanitizeText(str(spec['name']))
        return pad

    #从一个spec字典构建SprintPolygon覆铜
    def buildZoneFromSpec(self, spec):
        layer = self.parseLayerValue(spec.get('layer'))
        width = self.parseOptionalFloat(spec, 'width')
        if width is None:
            raise McpToolError('zone.width is required (outline width in mm)')
        if width < 0:
            raise McpToolError('zone.width must be >= 0')
        pointsRaw = spec.get('points')
        if (not isinstance(pointsRaw, (list, tuple))) or (len(pointsRaw) < 3):
            raise McpToolError('zone.points must be an array of at least 3 [x, y] points')
        poly = SprintPolygon(layer, float(width))
        for pt in pointsRaw:
            poly.addPoint(self.parsePoint(pt, 'zone.points'))
        poly.clearance = max(0, self.parseOptionalFloat(spec, 'clearance', 0) or 0)
        poly.hatch = self.parseOptionalBool(spec, 'hatch', None)
        poly.hatchAuto = self.parseOptionalBool(spec, 'hatchAuto', None)
        hatchWidth = self.parseOptionalFloat(spec, 'hatchWidth')
        if hatchWidth:
            poly.hatchWidth = hatchWidth
        poly.cutout = self.parseOptionalBool(spec, 'cutout', None)
        poly.soldermask = self.parseOptionalBool(spec, 'soldermask', None)
        poly.soldermaskCutout = self.parseOptionalBool(spec, 'soldermaskCutout', None)
        if spec.get('name'):
            poly.name = poly.sanitizeText(str(spec['name']))
        return poly

    #从一个spec字典构建SprintText文本
    def buildTextFromSpec(self, spec, defaultLayer=LAYER_S1, defaultHeight=1.3):
        layer = self.parseLayerValue(spec.get('layer'), default=defaultLayer)
        text = SprintText(layer)
        text.text = text.sanitizeText(str(spec.get('text') or ''))
        if not text.text:
            raise McpToolError('text.text must be a non-empty string')
        height = self.parseOptionalFloat(spec, 'height', defaultHeight) or defaultHeight
        if height <= 0:
            raise McpToolError('text.height must be > 0')
        text.height = height
        text.pos = self.parsePoint(spec.get('pos'), 'text.pos')
        style = self.parseOptionalFloat(spec, 'style')
        if style is not None:
            if not (0 <= int(style) <= 2):
                raise McpToolError('text.style must be 0(Narrow)/1(Normal)/2(Wide)')
            text.style = int(style)
        thickness = self.parseOptionalFloat(spec, 'thickness')
        if thickness is not None:
            if not (0 <= int(thickness) <= 2):
                raise McpToolError('text.thickness must be 0(Thin)/1(Normal)/2(Bold)')
            text.thickness = int(thickness)
        text.rotation = self.parseOptionalFloat(spec, 'rotation', 0) or 0
        text.mirrorH = self.parseOptionalBool(spec, 'mirrorHorz', None)
        text.mirrorV = self.parseOptionalBool(spec, 'mirrorVert', None)
        text.cutout = self.parseOptionalBool(spec, 'cutout', None)
        text.soldermask = self.parseOptionalBool(spec, 'soldermask', None)
        if spec.get('name'):
            text.name = text.sanitizeText(str(spec['name']))
        return text

    #从一个spec字典构建SprintCircle圆/圆弧
    def buildCircleFromSpec(self, spec):
        layer = self.parseLayerValue(spec.get('layer'))
        cir = SprintCircle(layer)
        cir.center = self.parsePoint(spec.get('center'), 'circle.center')
        radius = spec.get('radius')
        if (not isFiniteNumber(radius)) or (radius <= 0):
            raise McpToolError('circle.radius must be a positive number (unit mm)')
        cir.radius = float(radius)
        cir.width = self.parseOptionalFloat(spec, 'width', 0) or 0
        if cir.width < 0:
            raise McpToolError('circle.width must be >= 0')
        cir.start = self.parseOptionalFloat(spec, 'startAngle', 0) or 0
        cir.stop = self.parseOptionalFloat(spec, 'stopAngle', 0) or 0
        cir.clearance = max(0, self.parseOptionalFloat(spec, 'clearance', 0) or 0)
        cir.cutout = self.parseOptionalBool(spec, 'cutout', None)
        cir.soldermask = self.parseOptionalBool(spec, 'soldermask', None)
        cir.fill = self.parseOptionalBool(spec, 'fill', None)
        if spec.get('name'):
            cir.name = cir.sanitizeText(str(spec['name']))
        return cir

    #构建撤销前的元素序列化字符串集合，用于回写Sprint-Layout时计算增量
    def collectElementStrings(self):
        with self.boardLock:
            return [str(elem) for elem in self.textIo.elements]

    #计算当前板图相对初始快照的增量元素列表(仅顶层元素，按序列化字符串计数判同)
    #必须用计数(multiset)而不是集合：板上存在序列化完全相同的元素时(如原位复制)，
    #集合判同会把多出来的那份也当作原有元素漏掉，回写Sprint-Layout时静默丢失；
    #也不能改用元素id判同：undo/importSes/importTextIo(replace)会整体替换textIo引用，id全部改变
    def getNewElementsSince(self, originalStrings):
        origCount = {}
        for s in originalStrings:
            origCount[s] = origCount.get(s, 0) + 1
        ret = []
        for elem in self.textIo.elements:
            s = str(elem)
            if origCount.get(s, 0) > 0:
                origCount[s] -= 1
            else:
                ret.append(elem)
        return ret

    #按板层过滤顶层元素，组/元件内部包含该层元素时整体保留，避免按层导出时漏掉组内图元
    def filterElementsByLayer(self, layer):
        ret = []
        for elem in self.textIo.elements:
            if isinstance(elem, (SprintComponent, SprintGroup)):
                if any(sub.layerIdx == layer for sub in elem.baseDrawElements()):
                    ret.append(elem)
            elif elem.layerIdx == layer:
                ret.append(elem)
        return ret


#------------------------- 以下为各个MCP工具的实现 -------------------------

    #工具：获取板图概况
    def toolGetBoardInfo(self, args):
        board = self.textIo
        countByType = {}
        layerSet = set()
        for elem in board.baseDrawElements():
            typeName = getElementType(elem)
            countByType[typeName] = countByType.get(typeName, 0) + 1
            #layerIdx可能不是int(组/元件的layerIdx是推导值或无效值)，避免sorted()报TypeError
            if isinstance(elem.layerIdx, int):
                layerSet.add(elem.layerIdx)

        comps = []
        for idx, elem in enumerate(board.elements):
            if isinstance(elem, SprintComponent):
                comp = {'index': idx, 'id': elem.idText.text, 'value': elem.valueText.text,
                    'package': elem.package, 'padCount': len(elem.getPads())}
                #外框四个坐标必须全部有限才输出(空元件/坏坐标时省略)，避免NaN/Infinity进入JSON
                if (math.isfinite(elem.xMin) and math.isfinite(elem.yMin)
                        and math.isfinite(elem.xMax) and math.isfinite(elem.yMax)):
                    comp['bbox'] = [roundMm(elem.xMin), roundMm(elem.yMin), roundMm(elem.xMax), roundMm(elem.yMax)]
                comps.append(comp)

        ret = {
            'boardSize': {'width': roundMm(board.pcbWidth), 'height': roundMm(board.pcbHeight)},
            'topLevelElementCount': len(board.elements),
            'countByType': countByType,
            'layersInUse': sorted(layerSet),
            'components': comps,
            'coordinateSystem': 'origin top-left, X right, Y down, unit mm',
        }
        if (len(board.elements) > 0) and (math.isfinite(board.xMin) and math.isfinite(board.yMin)
                and math.isfinite(board.xMax) and math.isfinite(board.yMax)):
            ret['bbox'] = [roundMm(board.xMin), roundMm(board.yMin), roundMm(board.xMax), roundMm(board.yMax)]
        #布线设计规则(单位mm)，LLM手工布线必须遵循
        ret['rules'] = {
            'trackWidth': roundMm(self.pcbRule.trackWidth),
            'viaDiameter': roundMm(self.pcbRule.viaDiameter),
            'viaDrill': roundMm(self.pcbRule.viaDrill),
            'clearance': roundMm(self.pcbRule.clearance),
            'smdSmdClearance': roundMm(self.pcbRule.smdSmdClearance),
        }
        ret['canApplyToSprintLayout'] = bool(self.hasInputFile)
        if not self.hasInputFile:
            ret['applyMode'] = None
        else:
            #原板解析失败(replaceDisabled)时只能insert_new，让LLM不要白试replace
            ret['applyMode'] = 'insert_new' if (self.replaceDisabled or not self.pcbAll) else 'replace'
        return ret

    #工具：按条件列出元素
    def toolGetElements(self, args):
        #isinstance(True, int)为True，这里要把bool排除掉
        def cleanInt(value, default):
            if isinstance(value, bool) or not isinstance(value, int):
                return default
            return value
        offset = max(0, cleanInt(args.get('offset'), 0))
        limit = min(max(1, cleanInt(args.get('limit'), DEFAULT_PAGE_LIMIT)), MAX_PAGE_LIMIT)
        #展开深度：0=元件/组只返回概要信息不展开子元素，1=展开一层子元素(默认)
        depth = cleanInt(args.get('depth'), 1)
        if depth not in (0, 1):
            raise McpToolError('depth must be 0 (summary only, no sub-elements) or 1 (expand sub-elements)')

        if args.get('indices') is not None:
            #指定索引模式：直接查详情，忽略type/layer/bbox/offset/limit等过滤条件，
            #因此这些过滤参数也不校验(在下方过滤路径才解析)，避免带indices时被无关参数的非法值误报
            matched = self.resolveElementIndices(args.get('indices'))
            page = [elementToDict(elem, idx, depth=depth) for idx, elem in matched]
            return {'total': len(matched), 'count': len(page), 'elements': page}

        elemType = args.get('type')
        if elemType is not None:
            elemType = str(elemType).strip().upper()
            if elemType not in ('TRACK', 'PAD', 'SMDPAD', 'ZONE', 'TEXT', 'CIRCLE', 'COMPONENT', 'GROUP'):
                raise McpToolError('type must be one of TRACK/PAD/SMDPAD/ZONE/TEXT/CIRCLE/COMPONENT/GROUP')
        layer = None
        if args.get('layer') is not None:
            layer = self.parseLayerValue(args.get('layer'))
        bbox = self.parseBboxFilter(args.get('bbox'))

        matched = []
        for idx, elem in enumerate(self.textIo.elements):
            if elemType and (getElementType(elem) != elemType):
                continue
            if (layer is not None) and (elem.layerIdx != layer):
                continue
            if (bbox is not None) and (not elementIntersectsBbox(elem, bbox)):
                continue
            matched.append((idx, elem))

        page = [elementToDict(elem, idx, depth=depth) for idx, elem in matched[offset:offset + limit]]
        return {'total': len(matched), 'offset': offset, 'count': len(page), 'elements': page}

    #解析bbox空间过滤参数[xMin, yMin, xMax, yMax]，返回(float, float, float, float)或None
    def parseBboxFilter(self, value):
        if value is None:
            return None
        if (not isinstance(value, (list, tuple))) or (len(value) != 4) \
                or any(not isFiniteNumber(v) for v in value):
            raise McpToolError('bbox must be an [xMin, yMin, xMax, yMax] array of 4 numbers (unit mm)')
        xMin, yMin, xMax, yMax = (float(v) for v in value)
        if (xMin > xMax) or (yMin > yMax):
            raise McpToolError('bbox must satisfy xMin <= xMax and yMin <= yMax')
        return (xMin, yMin, xMax, yMax)

    #工具：清空板图
    def toolClearBoard(self, args):
        if not self.parseOptionalBool(args, 'confirm', False):
            raise McpToolError('Set confirm=true to delete ALL elements on the board')
        self.pushUndoSnapshot()
        count = len(self.textIo.elements)
        self.textIo.elements = []
        self.textIo.updateSelfBbox()
        return {'cleared': count}

    #工具：设置板图尺寸
    def toolSetBoardSize(self, args):
        width = self.parseOptionalFloat(args, 'width')
        height = self.parseOptionalFloat(args, 'height')
        if (width is None) or (height is None) or (width < 0) or (height < 0):
            raise McpToolError('width/height must be non-negative numbers (unit mm)')
        self.pushUndoSnapshot() #板图尺寸也是可撤销的修改
        self.textIo.pcbWidth = float(width)
        self.textIo.pcbHeight = float(height)
        return {'boardSize': {'width': roundMm(width), 'height': roundMm(height)}}

    #工具：添加导线
    def toolAddTrack(self, args):
        track = self.buildTrackFromSpec(args)
        idx = self.addElement(track)
        return self.buildAddResult(idx, track)

    #工具：添加通孔焊盘(含过孔)
    def toolAddPad(self, args):
        pad = self.buildPadFromSpec(args)
        idx = self.addElement(pad)
        return self.buildAddResult(idx, pad)

    #工具：添加贴片焊盘
    def toolAddSmdPad(self, args):
        pad = self.buildSmdPadFromSpec(args)
        idx = self.addElement(pad)
        return self.buildAddResult(idx, pad)

    #工具：添加覆铜多边形
    def toolAddZone(self, args):
        poly = self.buildZoneFromSpec(args)
        idx = self.addElement(poly)
        return self.buildAddResult(idx, poly)

    #工具：添加文本
    def toolAddText(self, args):
        text = self.buildTextFromSpec(args)
        idx = self.addElement(text)
        return self.buildAddResult(idx, text)

    #工具：添加圆/圆弧
    def toolAddCircle(self, args):
        cir = self.buildCircleFromSpec(args)
        idx = self.addElement(cir)
        return self.buildAddResult(idx, cir)

    #工具：添加一个完整元件(封装)
    def toolAddComponent(self, args):
        comp = SprintComponent()
        comp.comment = comp.sanitizeText(str(args.get('comment') or ''))
        comp.package = comp.sanitizeText(str(args.get('package') or ''))

        #ID_TEXT/VALUE_TEXT，可以是简单字符串或完整spec字典
        idSpec = args.get('idText')
        if idSpec is not None:
            comp.idText = self.buildLabelFromSpec(idSpec, 'idText')
        valueSpec = args.get('valueText')
        if valueSpec is not None:
            comp.valueText = self.buildLabelFromSpec(valueSpec, 'valueText')

        added = 0
        for spec in self.parseSpecList(args, 'pads'):
            comp.add(self.buildPadFromSpec(spec))
            added += 1
        for spec in self.parseSpecList(args, 'smdPads'):
            comp.add(self.buildSmdPadFromSpec(spec))
            added += 1
        for spec in self.parseSpecList(args, 'tracks'):
            comp.add(self.buildTrackFromSpec(spec))
            added += 1
        for spec in self.parseSpecList(args, 'zones'):
            comp.add(self.buildZoneFromSpec(spec))
            added += 1
        for spec in self.parseSpecList(args, 'texts'):
            comp.add(self.buildTextFromSpec(spec, defaultLayer=LAYER_S1, defaultHeight=1.0))
            added += 1
        for spec in self.parseSpecList(args, 'circles'):
            comp.add(self.buildCircleFromSpec(spec))
            added += 1

        if added == 0:
            raise McpToolError('The component must contain at least one element (pads/smdPads/tracks/zones/texts/circles)')

        comp.updateSelfBbox()
        #将元件ID标签自动放到元件外框上方(如果标签位置未指定)
        idx = self.addElement(comp)
        ret = self.buildAddResult(idx, comp, depth=1)
        ret['subElementCount'] = added
        return ret

    #工具：批量添加元素(一次HTTP往返添加多条导线/焊盘/文本等，适合总线布线/成排摆件)
    #原子化：先全部构建校验，任一spec非法则整体报错、不添加任何元素也不消耗撤销快照
    #整批只占一步撤销；各列表内保持传入顺序，添加顺序固定为tracks/pads/smdPads/zones/texts/circles
    def toolBatchAdd(self, args):
        builders = (('tracks', self.buildTrackFromSpec), ('pads', self.buildPadFromSpec),
            ('smdPads', self.buildSmdPadFromSpec), ('zones', self.buildZoneFromSpec),
            ('texts', self.buildTextFromSpec), ('circles', self.buildCircleFromSpec))
        built = []
        for key, builderFn in builders:
            for spec in self.parseSpecList(args, key):
                elem = builderFn(spec)
                if not elem.isValid():
                    raise McpToolError('Invalid {} spec (check required geometry parameters): {}'.format(
                        key, summarizeArguments(spec)))
                built.append(elem)
        if not built:
            raise McpToolError('Provide at least one of tracks/pads/smdPads/zones/texts/circles arrays')
        self.pushUndoSnapshot() #整批只占一步撤销
        firstIdx = len(self.textIo.elements)
        for elem in built:
            self.textIo.add(elem)
        return {'added': len(built), 'indexes': list(range(firstIdx, firstIdx + len(built))),
            'totalElements': len(self.textIo.elements)}

    #工具：放置参数化标准封装(0402~1206/SOIC/DIP/SOT-23/排针)，免手算引脚坐标
    def toolAddStandardFootprint(self, args):
        canonicalName = self.parseStandardFootprintName(args.get('package'))
        pos = self.parsePoint(args.get('pos'), 'pos')
        rotation = self.parseOptionalFloat(args, 'rotation', 0) or 0
        comp = self.buildStandardFootprint(canonicalName)
        if args.get('idText') is not None:
            comp.idText = self.buildLabelFromSpec(args.get('idText'), 'idText')
        if args.get('valueText') is not None:
            comp.valueText = self.buildLabelFromSpec(args.get('valueText'), 'valueText')
        comp.updateSelfBbox()
        if rotation:
            #封装几何以原点为中心构建，先绕自身中心旋转再平移，位号(0,0)的自动放置语义保持不变
            comp.rotateBy(rotation, 0, 0)
        comp.moveByOffset(pos[0], pos[1])
        idx = self.addElement(comp)
        ret = self.buildAddResult(idx, comp, depth=1)
        ret['pinCount'] = len(comp.getPads())
        return ret

    #解析标准封装名字，返回规范名(如SOIC-8/HEADER-1x4)，不认识则抛出McpToolError
    def parseStandardFootprintName(self, name):
        name = str(name or '').strip().upper().replace(' ', '')
        if name in CHIP_PASSIVE_FOOTPRINTS:
            return name

        #取前缀后面的纯数字后缀(容忍连字符，SOIC8/SOIC-8等价)
        def digitSuffix(prefix):
            rest = name[len(prefix):].lstrip('-')
            return rest if rest.isdigit() else None

        if name.startswith('SOIC'):
            num = digitSuffix('SOIC')
            if num in ('8', '14', '16'):
                return 'SOIC-' + num
        elif name.startswith('DIP'):
            num = digitSuffix('DIP')
            if num in ('8', '14', '16'):
                return 'DIP-' + num
        elif name.startswith('SOT'):
            if digitSuffix('SOT') == '23':
                return 'SOT-23'
        elif name.startswith('HEADER'):
            parts = name[len('HEADER'):].lstrip('-').split('X')
            if (len(parts) == 2) and (parts[0] in ('1', '2')) and parts[1].isdigit() \
                    and (1 <= int(parts[1]) <= 20):
                return 'HEADER-{}x{}'.format(parts[0], int(parts[1]))
        raise McpToolError('Unknown package: {} (supported: 0402/0603/0805/1206, SOIC-8/14/16, '
            'DIP-8/14/16, SOT-23, HEADER-1xN / HEADER-2xN with N=1-20)'.format(name))

    #构建两排引脚芯片的焊盘位置列表(以封装中心为原点)，引脚1在左上，逆时针编号
    def dualRowPadPositions(self, rows, pitch, rowDistance):
        ret = []
        yOffset = (rows - 1) * pitch / 2
        for i in range(rows): #左列从上到下：引脚1..rows
            ret.append((-rowDistance / 2, i * pitch - yOffset))
        for i in range(rows - 1, -1, -1): #右列从下到上：引脚rows+1..2*rows
            ret.append((rowDistance / 2, i * pitch - yOffset))
        return ret

    #构建带引脚号名字的贴片焊盘(名字便于AI引用引脚)
    def buildNamedSmdPad(self, pos, sizeX, sizeY, pinNo):
        pad = SprintPad(padType='SMDPAD', layerIdx=LAYER_C1)
        pad.pos = pos
        pad.sizeX = sizeX
        pad.sizeY = sizeY
        pad.name = str(pinNo)
        return pad

    #构建带引脚号名字的通孔焊盘(DIP与排针共用规格)
    def buildNamedThPad(self, pos, pinNo):
        pad = SprintPad(padType='PAD', layerIdx=LAYER_C1)
        pad.pos = pos
        pad.size = TH_PAD_SIZE
        pad.drill = TH_DRILL
        pad.name = str(pinNo)
        return pad

    #构建丝印外框(闭合矩形track，画在S1丝印层)
    def buildSilkRect(self, cx, cy, w, h):
        track = SprintTrack(LAYER_S1, SILK_WIDTH)
        x0, x1, y0, y1 = cx - w / 2, cx + w / 2, cy - h / 2, cy + h / 2
        for pt in ((x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)):
            track.addPoint(pt)
        return track

    #构建标准封装本体(以封装几何中心为原点)，引脚号写入焊盘name字段
    def buildStandardFootprint(self, canonicalName):
        comp = SprintComponent()
        comp.package = canonicalName
        pinNo = 0

        def addPads(positions, builderFn):
            nonlocal pinNo
            for pos in positions:
                pinNo += 1
                comp.add(builderFn(pos, pinNo))

        if canonicalName in CHIP_PASSIVE_FOOTPRINTS:
            padX, padY, pitch, bodyX, bodyY = CHIP_PASSIVE_FOOTPRINTS[canonicalName]
            addPads(((-pitch / 2, 0), (pitch / 2, 0)),
                lambda pos, no: self.buildNamedSmdPad(pos, padX, padY, no))
            comp.add(self.buildSilkRect(0, 0, bodyX, bodyY))

        elif canonicalName.startswith('SOIC'):
            pinCount = int(canonicalName.split('-')[1])
            addPads(self.dualRowPadPositions(pinCount // 2, SOIC_PITCH, SOIC_ROW_DISTANCE),
                lambda pos, no: self.buildNamedSmdPad(pos, SOIC_PAD[0], SOIC_PAD[1], no))
            comp.add(self.buildSilkRect(0, 0, SOIC_BODY_WIDTH, SOIC_BODY_LENGTH[pinCount]))

        elif canonicalName.startswith('DIP'):
            pinCount = int(canonicalName.split('-')[1])
            rows = pinCount // 2
            addPads(self.dualRowPadPositions(rows, DIP_PITCH, DIP_ROW_DISTANCE),
                lambda pos, no: self.buildNamedThPad(pos, no))
            #丝印画DIP本体：宽度略小于排距，长度覆盖引脚排布
            comp.add(self.buildSilkRect(0, 0, DIP_ROW_DISTANCE - 0.6, (rows - 1) * DIP_PITCH + 2.2))

        elif canonicalName == 'SOT-23':
            xHalf, yHalf = SOT23_ROW_DISTANCE / 2, SOT23_PIN_SPAN / 2
            addPads(((-xHalf, -yHalf), (-xHalf, yHalf), (xHalf, 0)),
                lambda pos, no: self.buildNamedSmdPad(pos, SOT23_PAD[0], SOT23_PAD[1], no))
            comp.add(self.buildSilkRect(0, 0, SOT23_BODY[0], SOT23_BODY[1]))

        else: #HEADER-1xN / HEADER-2xN，单列/双列沿Y向排布，引脚1在顶部
            rowsChar, nStr = canonicalName.split('-')[1].split('x')
            n = int(nStr)
            yOffset = (n - 1) * HEADER_PITCH / 2
            if rowsChar == '1':
                addPads([(0, i * HEADER_PITCH - yOffset) for i in range(n)],
                    lambda pos, no: self.buildNamedThPad(pos, no))
                comp.add(self.buildSilkRect(0, 0, HEADER_PITCH, n * HEADER_PITCH))
            else:
                positions = []
                for i in range(n):
                    y = i * HEADER_PITCH - yOffset
                    positions.extend(((-HEADER_PITCH / 2, y), (HEADER_PITCH / 2, y)))
                addPads(positions, lambda pos, no: self.buildNamedThPad(pos, no))
                comp.add(self.buildSilkRect(0, 0, HEADER_PITCH * 2, n * HEADER_PITCH))
        return comp

    #构建元件的ID/值标签，spec可以是字符串或字典
    #标签未指定位置时保持(0,0)，序列化时由SprintComponent自动放置到元件外框上方
    def buildLabelFromSpec(self, spec, labelName):
        if isinstance(spec, str):
            spec = {'text': spec}
        if not isinstance(spec, dict):
            raise McpToolError('{} must be a string or an object'.format(labelName))
        if not spec.get('text'):
            raise McpToolError('{}.text must be a non-empty string'.format(labelName))
        text = SprintText(self.parseLayerValue(spec.get('layer'), default=LAYER_S1, argName=labelName + '.layer'))
        text.text = text.sanitizeText(str(spec.get('text')))
        height = self.parseOptionalFloat(spec, 'height', 1.3) or 1.3
        if height <= 0:
            raise McpToolError('{}.height must be > 0'.format(labelName))
        text.height = height
        if spec.get('pos') is not None:
            text.pos = self.parsePoint(spec.get('pos'), labelName + '.pos')
        text.rotation = self.parseOptionalFloat(spec, 'rotation', 0) or 0
        text.visible = self.parseOptionalBool(spec, 'visible', True)
        return text

    #解析spec列表参数
    def parseSpecList(self, args, key):
        value = args.get(key)
        if value is None:
            return []
        if (not isinstance(value, (list, tuple))):
            raise McpToolError('{} must be an array of objects'.format(key))
        return list(value)

    #构造add类工具的统一返回
    def buildAddResult(self, idx, elem, depth=0):
        return {'added': True, 'index': idx,
            'totalElements': len(self.textIo.elements), 'element': elementToDict(elem, idx, depth=depth)}

    #工具：删除指定索引的元素
    def toolDeleteElements(self, args):
        resolved = self.resolveElementIndices(args.get('indices'))
        self.pushUndoSnapshot()
        #按索引逆序直接删除，避免list.remove按==匹配而误删同规格元素
        removed = 0
        for idx, _ in sorted(resolved, key=lambda item: item[0], reverse=True):
            del self.textIo.elements[idx]
            removed += 1
        self.textIo.updateSelfBbox()
        return {'removed': removed, 'remaining': len(self.textIo.elements)}

    #工具：平移指定索引的元素
    def toolMoveElements(self, args):
        objs = self.getElementsByIndices(args.get('indices'))
        dx = self.parseOptionalFloat(args, 'dx')
        dy = self.parseOptionalFloat(args, 'dy')
        if (dx is None) or (dy is None):
            raise McpToolError('dx/dy are required offsets (unit mm, can be negative)')
        if (dx != 0) or (dy != 0): #零偏移无实际移动，不消耗撤销快照
            self.pushUndoSnapshot()
        for obj in objs:
            obj.moveByOffset(float(dx), float(dy))
        self.textIo.updateSelfBbox()
        return {'moved': len(objs), 'dx': roundMm(dx), 'dy': roundMm(dy)}

    #工具：旋转指定索引的元素(绕指定中心，默认选区几何中心，顺时针为正，任意角度)
    def toolRotateElements(self, args):
        objs = self.getElementsByIndices(args.get('indices'))
        angle = self.parseOptionalFloat(args, 'angle')
        if angle is None:
            raise McpToolError('angle is required (degrees, clockwise-positive)')
        center = args.get('center')
        if center is not None:
            cx, cy = self.parsePoint(center, 'center')
        else:
            bbox = unionElementBbox(objs)
            if bbox is None:
                raise McpToolError('Cannot determine selection bounding box, pass an explicit center')
            cx, cy = (bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2
        if angle != 0: #零角度无实际旋转，不消耗撤销快照
            self.pushUndoSnapshot()
        for obj in objs:
            obj.rotateBy(float(angle), cx, cy)
        self.textIo.updateSelfBbox()
        return {'rotated': len(objs), 'angle': angle,
            'center': [roundMm(cx), roundMm(cy)],
            'totalElements': len(self.textIo.elements)}

    #工具：镜像指定索引的元素(绕选区包围盒中心线翻转)
    def toolMirrorElements(self, args):
        objs = self.getElementsByIndices(args.get('indices'))
        axis = str(args.get('axis') or '').strip().lower()
        if axis not in ('x', 'y'):
            raise McpToolError('axis must be "x" (mirror horizontally, left-right flip) '
                'or "y" (mirror vertically, up-down flip)')
        bbox = unionElementBbox(objs)
        if bbox is None:
            raise McpToolError('Cannot determine selection bounding box')
        cx, cy = (bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2
        self.pushUndoSnapshot()
        if axis == 'x':
            for obj in objs:
                obj.mirrorHorzBy(cx)
        else:
            for obj in objs:
                obj.mirrorVertBy(cy)
        self.textIo.updateSelfBbox()
        return {'mirrored': len(objs), 'axis': axis,
            'center': [roundMm(cx), roundMm(cy)],
            'totalElements': len(self.textIo.elements)}

    #工具：将指定索引的元素编为一个锁定组
    def toolGroupElements(self, args):
        objs = self.getElementsByIndices(args.get('indices'))
        if len(objs) < 1:
            raise McpToolError('At least one element index is required')
        self.pushUndoSnapshot()
        group = SprintGroup()
        for obj in objs:
            self.textIo.remove(obj)
            group.add(obj)
        self.textIo.add(group)
        idx = len(self.textIo.elements) - 1
        return {'grouped': len(objs), 'index': idx, 'element': elementToDict(group, idx, depth=0)}

    #工具：原地修改指定索引元素的属性(免删除重建)
    #每个属性只应用到支持它的元素类型上，不支持的元素忽略该属性
    def toolUpdateElements(self, args):
        resolved = self.resolveElementIndices(args.get('indices'))
        for key in args:
            if (key != 'indices') and (key not in UPDATE_ELEMENT_PROPS):
                raise McpToolError('Unknown property: {} (supported: {})'.format(key,
                    ', '.join(sorted(UPDATE_ELEMENT_PROPS))))
        #先取快照，确认有实际修改后再入栈，避免无效修改(如对GROUP只传layer)消耗撤销步数
        snapshot = self.takeUndoSnapshot()
        updated = 0
        for _, obj in resolved:
            backup = copy.deepcopy(obj)
            try:
                if self.applyUpdateToElement(obj, args):
                    obj.updateSelfBbox()
                    updated += 1
            except Exception:
                #单元素原子回滚：同一元素前面的属性可能已修改而后面属性才报错，
                #不能凭updated==0断定无修改，直接恢复该元素修改前状态即可保证板图与快照一致
                obj.__dict__.clear()
                obj.__dict__.update(backup.__dict__)
                raise
        if updated:
            self.commitUndoSnapshot(snapshot)
        self.textIo.updateSelfBbox()
        #响应用去重后的(索引, 元素)对，保证index与元素一一对应
        return {'updated': updated, 'requested': len(resolved),
            'elements': [elementToDict(obj, idx, depth=0) for idx, obj in resolved]}

    #把updateElements的参数应用到单个元素，返回是否有修改
    def applyUpdateToElement(self, obj, args):
        changed = False
        if 'layer' in args:
            #元件的layerIdx由焊盘层推导(只读property)，组的layerIdx不影响子元素，两者忽略layer修改
            if isinstance(obj, (SprintComponent, SprintGroup)):
                pass
            else:
                obj.layerIdx = self.parseLayerValue(args['layer'])
                changed = True
        if 'name' in args:
            obj.name = obj.sanitizeText(str(args['name'] or ''))
            changed = True

        if isinstance(obj, SprintTrack):
            if 'width' in args:
                obj.width = self.parsePositiveFloat(args, 'width')
                changed = True
            if 'clearance' in args:
                obj.clearance = max(0, self.parseOptionalFloat(args, 'clearance', 0) or 0)
                changed = True
            for key, attr in (('flatStart', 'flatstart'), ('flatEnd', 'flatend'),
                    ('cutout', 'cutout'), ('soldermask', 'soldermask')):
                if key in args:
                    setattr(obj, attr, self.parseOptionalBool(args, key))
                    changed = True

        elif isinstance(obj, SprintPad):
            if 'pos' in args:
                obj.pos = self.parsePoint(args.get('pos'))
                changed = True
            if 'size' in args:
                obj.size = self.parsePositiveFloat(args, 'size')
                changed = True
            for key in ('sizeX', 'sizeY'):
                if key in args:
                    setattr(obj, key, self.parsePositiveFloat(args, key))
                    changed = True
            if 'drill' in args:
                drill = self.parseOptionalFloat(args, 'drill', 0) or 0
                if drill < 0:
                    raise McpToolError('drill must be >= 0')
                obj.drill = drill
                changed = True
            if 'form' in args:
                obj.form = self.parsePadForm(args.get('form'))
                changed = True
            if 'rotation' in args:
                obj.rotation = self.parseOptionalFloat(args, 'rotation', 0) or 0
                changed = True
            for key, attr in (('via', 'via'), ('thermal', 'thermal'),
                    ('thermalTracksIndividual', 'thermalTracksIndividual'),
                    ('soldermask', 'soldermask')):
                if key in args:
                    setattr(obj, attr, self.parseOptionalBool(args, key))
                    changed = True
            if 'clearance' in args:
                value = self.parseOptionalFloat(args, 'clearance')
                if (value is not None) and (value < 0):
                    raise McpToolError('clearance must be >= 0')
                #注意None与0含义不同(0=十字焊盘与铺铜直连)
                obj.clearance = value
                changed = True
            if 'thermalTracksWidth' in args:
                value = self.parseOptionalFloat(args, 'thermalTracksWidth', 0) or 0
                if value < 0:
                    raise McpToolError('thermalTracksWidth must be >= 0')
                obj.thermalTracksWidth = value
                changed = True
            if 'thermalTracks' in args:
                value = args.get('thermalTracks')
                if (not isFiniteNumber(value)) or (value < 0):
                    raise McpToolError('thermalTracks must be a non-negative integer')
                obj.thermalTracks = int(value)
                changed = True

        elif isinstance(obj, SprintPolygon):
            if 'width' in args:
                obj.width = self.parsePositiveFloat(args, 'width')
                changed = True
            if 'clearance' in args:
                obj.clearance = max(0, self.parseOptionalFloat(args, 'clearance', 0) or 0)
                changed = True
            if 'hatchWidth' in args:
                value = self.parseOptionalFloat(args, 'hatchWidth', 0) or 0
                if value < 0:
                    raise McpToolError('hatchWidth must be >= 0')
                obj.hatchWidth = value
                changed = True
            for key, attr in (('cutout', 'cutout'), ('soldermask', 'soldermask'),
                    ('soldermaskCutout', 'soldermaskCutout'), ('hatch', 'hatch'),
                    ('hatchAuto', 'hatchAuto')):
                if key in args:
                    setattr(obj, attr, self.parseOptionalBool(args, key))
                    changed = True

        elif isinstance(obj, SprintText):
            if 'text' in args:
                value = obj.sanitizeText(str(args.get('text') or ''))
                if not value:
                    raise McpToolError('text must be a non-empty string')
                obj.text = value
                changed = True
            if 'height' in args:
                obj.height = self.parsePositiveFloat(args, 'height')
                changed = True
            if 'style' in args:
                style = args.get('style')
                if (not isFiniteNumber(style)) or (not (0 <= int(style) <= 2)):
                    raise McpToolError('style must be 0(Narrow)/1(Normal)/2(Wide)')
                obj.style = int(style)
                changed = True
            if 'thickness' in args:
                thickness = args.get('thickness')
                if (not isFiniteNumber(thickness)) or (not (0 <= int(thickness) <= 2)):
                    raise McpToolError('thickness must be 0(Thin)/1(Normal)/2(Bold)')
                obj.thickness = int(thickness)
                changed = True
            if 'rotation' in args:
                obj.rotation = self.parseOptionalFloat(args, 'rotation', 0) or 0
                changed = True
            for key, attr in (('mirrorHorz', 'mirrorH'), ('mirrorVert', 'mirrorV'),
                    ('cutout', 'cutout'), ('soldermask', 'soldermask'), ('visible', 'visible')):
                if key in args:
                    setattr(obj, attr, self.parseOptionalBool(args, key))
                    changed = True

        elif isinstance(obj, SprintCircle):
            if 'center' in args:
                obj.center = self.parsePoint(args.get('center'))
                changed = True
            if 'radius' in args:
                obj.radius = self.parsePositiveFloat(args, 'radius')
                changed = True
            if 'width' in args:
                value = self.parseOptionalFloat(args, 'width', 0) or 0
                if value < 0:
                    raise McpToolError('width must be >= 0')
                obj.width = value
                changed = True
            if 'startAngle' in args:
                obj.start = self.parseOptionalFloat(args, 'startAngle', 0) or 0
                changed = True
            if 'stopAngle' in args:
                obj.stop = self.parseOptionalFloat(args, 'stopAngle', 0) or 0
                changed = True
            for key, attr in (('fill', 'fill'), ('cutout', 'cutout'), ('soldermask', 'soldermask')):
                if key in args:
                    setattr(obj, attr, self.parseOptionalBool(args, key))
                    changed = True
            if 'clearance' in args:
                obj.clearance = max(0, self.parseOptionalFloat(args, 'clearance', 0) or 0)
                changed = True

        elif isinstance(obj, SprintComponent):
            if 'idText' in args:
                value = obj.idText.sanitizeText(str(args.get('idText') or ''))
                if not value:
                    raise McpToolError('idText must be a non-empty string')
                obj.idText.text = value
                changed = True
            if 'valueText' in args:
                value = obj.valueText.sanitizeText(str(args.get('valueText') or ''))
                if not value:
                    raise McpToolError('valueText must be a non-empty string')
                obj.valueText.text = value
                changed = True
            if 'package' in args:
                obj.package = obj.sanitizeText(str(args.get('package') or ''))
                changed = True
            if 'comment' in args:
                obj.comment = obj.sanitizeText(str(args.get('comment') or ''))
                changed = True

        return changed

    #工具：撤销上一次修改
    def toolUndo(self, args):
        if not self.undoStack:
            raise McpToolError('Nothing to undo')
        self.textIo = self.undoStack.pop()
        return {'undone': True, 'totalElements': len(self.textIo.elements)}

    #工具：导入Text-IO格式文本
    def toolImportTextIo(self, args):
        text = args.get('text')
        if (not isinstance(text, str)) or (not text.strip()):
            raise McpToolError('text is required (Text-IO format string)')
        mode = str(args.get('mode') or 'append').lower()
        if mode not in ('append', 'replace'):
            raise McpToolError('mode must be "append" or "replace"')
        parser = SprintTextIoParser(self.textIo.pcbWidth, self.textIo.pcbHeight)
        parsed = parser.parseText(text)
        if not parsed:
            raise McpToolError('No valid elements found in the Text-IO text')
        self.pushUndoSnapshot()
        if mode == 'replace':
            parsed.pcbWidth = self.textIo.pcbWidth
            parsed.pcbHeight = self.textIo.pcbHeight
            self.textIo = parsed
        else:
            self.textIo.addAll(parsed.elements)
        return {'imported': len(parsed.elements), 'mode': mode,
            'totalElements': len(self.textIo.elements)}

    #工具：导出板图为Text-IO格式文本
    def toolExportTextIo(self, args):
        layer = None
        if args.get('layer') is not None:
            layer = self.parseLayerValue(args.get('layer'))
        if layer is None:
            text = str(self.textIo)
            count = len(self.textIo.elements)
        else:
            elems = [str(elem) for elem in self.filterElementsByLayer(layer)]
            elems = [s for s in elems if s]
            text = '\n'.join(elems)
            count = len(elems)
        return {'text': text, 'elementCount': count}

    #工具：从文件加载Text-IO
    def toolLoadTextIoFile(self, args):
        fileName = str(args.get('path') or '').strip()
        if not fileName or not os.path.isfile(fileName):
            raise McpToolError('File does not exist: {}'.format(fileName))
        mode = str(args.get('mode') or 'append').lower()
        if mode not in ('append', 'replace'):
            raise McpToolError('mode must be "append" or "replace"')
        parser = SprintTextIoParser(self.textIo.pcbWidth, self.textIo.pcbHeight)
        parsed = parser.parse(fileName)
        if not parsed:
            raise McpToolError('Failed to parse Text-IO file: {}'.format(fileName))
        self.pushUndoSnapshot()
        if mode == 'replace':
            parsed.pcbWidth = self.textIo.pcbWidth
            parsed.pcbHeight = self.textIo.pcbHeight
            self.textIo = parsed
        else:
            self.textIo.addAll(parsed.elements)
        return {'imported': len(parsed.elements), 'mode': mode, 'path': fileName,
            'totalElements': len(self.textIo.elements)}

    #工具：保存板图为Text-IO文件(可再由Sprint-Layout手动导入)
    def toolSaveTextIoFile(self, args):
        fileName = str(args.get('path') or '').strip()
        if not fileName:
            raise McpToolError('path is required (absolute path recommended)')
        layer = None
        if args.get('layer') is not None:
            layer = self.parseLayerValue(args.get('layer'))
        if layer is None:
            text = str(self.textIo)
        else:
            text = '\n'.join([s for s in (str(elem) for elem in self.filterElementsByLayer(layer)) if s])
        if not text.strip():
            raise McpToolError('Board is empty, nothing to save')
        dirName = os.path.dirname(fileName)
        if dirName and not os.path.isdir(dirName):
            os.makedirs(dirName, exist_ok=True)
        with open(fileName, 'w', encoding='utf-8') as f:
            f.write(text)
        return {'saved': True, 'path': fileName, 'bytes': len(text.encode('utf-8'))}

    #工具：设计规则检查(间距/线宽/孤立焊盘)
    def toolCheckDrc(self, args):
        from conversion.drc_checker import DrcChecker
        #复制一份规则，允许调用方覆盖个别值(0/负值直接报错，绝不静默回退默认值)
        rule = copy.deepcopy(self.pcbRule)
        trackWidth = self.parseOptionalPositiveFloat(args, 'trackWidth')
        clearance = self.parseOptionalPositiveFloat(args, 'clearance')
        if trackWidth is not None:
            rule.trackWidth = trackWidth
        if clearance is not None:
            rule.clearance = clearance
        checker = DrcChecker(self.textIo, rule)
        return checker.check(labelMap=self.buildNetLabelMap(),
            includeIsolated=self.parseOptionalBool(args, 'includeIsolated', False))

    #工具：导出SVG矢量图(供LLM或用户视觉验证)
    def toolExportSvg(self, args):
        from conversion.sprint_to_svg import SVGGenerator
        fileName = str(args.get('path') or '').strip()
        if not fileName:
            raise McpToolError('path is required (absolute path of the .svg file to write)')
        if not fileName.lower().endswith('.svg'):
            fileName += '.svg'
        layers = None
        if args.get('layers') is not None:
            rawLayers = args.get('layers')
            if not isinstance(rawLayers, (list, tuple)):
                rawLayers = [rawLayers]
            layers = [self.parseLayerValue(v) for v in rawLayers]
        generator = SVGGenerator(self.textIo, layers=layers,
            mirrorY=self.parseOptionalBool(args, 'mirrorY', False))
        ret = generator.generate(fileName)
        if ret:
            raise McpToolError('SVG export failed: {}'.format(ret))
        result = {'saved': True, 'path': fileName, 'bytes': os.path.getsize(fileName)}
        if self.parseOptionalBool(args, 'returnText', False):
            with open(fileName, 'r', encoding='utf-8') as f:
                result['svg'] = f.read()
        return result

    #建立元素对象id到网表标签的映射，元件/组内部为"a.b"层级标签
    #子元素序号与getElements返回的subElements枚举一致(元件的ID_TEXT/VALUE_TEXT不导电也不占序号)
    def buildNetLabelMap(self):
        labelMap = {}
        def walk(elems, prefix):
            for subIdx, sub in enumerate(elems):
                label = '{}.{}'.format(prefix, subIdx) if prefix else str(subIdx)
                if isinstance(sub, (SprintComponent, SprintGroup)):
                    walk(sub.elements, label)
                else:
                    labelMap[id(sub)] = label
        walk(self.textIo.elements, '')
        return labelMap

    #工具：提取铜层网表(连通性)
    def toolGetNetlist(self, args):
        from conversion.netlist_builder import NetlistBuilder
        builder = NetlistBuilder(self.textIo)
        result = builder.build()

        labelMap = self.buildNetLabelMap()
        nets = []
        for net in result.get('nets', []):
            nets.append({'number': net['number'], 'name': net['name'],
                'elements': [labelMap.get(id(e), '?') for e in net['elements']]})
        return {'netCount': len(nets), 'nets': nets,
            'note': 'Physical-touch connectivity only, NOT design intent; nets are auto-numbered. '
                'Element labels: top-level index, "a.b" = sub-element b of component/group a '
                '(same order as the subElements array from getElements)'}

    #工具：导出Specctra DSN文件(供用户人工操作外部自动布线器)
    def toolExportDsn(self, args):
        fileName = str(args.get('path') or '').strip()
        if not fileName:
            raise McpToolError('path is required (absolute path of the .dsn file to write)')
        if not fileName.lower().endswith('.dsn'):
            fileName += '.dsn'

        #复制一份默认规则，再应用调用者传入的覆盖值(0/负值直接报错，绝不静默回退默认值)
        rule = PcbRule()
        rule.trackWidth = self.pcbRule.trackWidth
        rule.viaDiameter = self.pcbRule.viaDiameter
        rule.viaDrill = self.pcbRule.viaDrill
        rule.clearance = self.pcbRule.clearance
        rule.smdSmdClearance = self.pcbRule.smdSmdClearance
        trackWidth = self.parseOptionalPositiveFloat(args, 'trackWidth')
        viaDiameter = self.parseOptionalPositiveFloat(args, 'viaDiameter')
        viaDrill = self.parseOptionalPositiveFloat(args, 'viaDrill')
        clearance = self.parseOptionalPositiveFloat(args, 'clearance')
        if trackWidth is not None:
            rule.trackWidth = trackWidth
        if viaDiameter is not None:
            rule.viaDiameter = viaDiameter
        if viaDrill is not None:
            rule.viaDrill = viaDrill
        if clearance is not None:
            rule.clearance = clearance
        if rule.viaDiameter <= rule.viaDrill:
            raise McpToolError('viaDiameter must be greater than viaDrill')

        exporter = SprintExportDsn(self.textIo, rule, fileName)
        ret = exporter.export()
        if isinstance(ret, str):
            raise McpToolError(str(ret) if ret else 'Unknown DSN export error')
        dirName = os.path.dirname(fileName)
        if dirName and not os.path.isdir(dirName):
            os.makedirs(dirName, exist_ok=True)
        #DSN与pickle必须成对使用(importSes从pickle恢复板图状态)。先写临时文件再改名，
        #且DSN最后改名作为提交点：中途失败(磁盘满/权限/杀软锁定)不会留下孤儿DSN，
        #也不会因open('wb')的截断语义毁掉旧pickle形成"新DSN配旧pickle"的错位组合
        pickleFile = os.path.splitext(fileName)[0] + '.pickle'
        suffix = '.{}.tmp'.format(uuid.uuid4().hex)
        dsnTmpFile = fileName + suffix
        pickleTmpFile = pickleFile + suffix
        try:
            with open(dsnTmpFile, 'w', encoding='utf-8') as f:
                f.write(ret.output)
            with open(pickleTmpFile, 'wb') as f:
                pickle.dump(exporter, f)
            os.replace(pickleTmpFile, pickleFile)
            os.replace(dsnTmpFile, fileName)
        finally:
            #改名成功的临时文件已不存在；失败时清掉残留，不留垃圾
            for tmpFile in (dsnTmpFile, pickleTmpFile):
                if os.path.isfile(tmpFile):
                    os.remove(tmpFile)
        sesFile = os.path.splitext(fileName)[0] + '.ses'
        return {'dsnFile': fileName, 'pickleFile': pickleFile, 'sesFile': sesFile,
            'nextStep': 'Autorouting is performed externally and manually by the user; '
                'once the .ses file is produced, call importSes with it.'}

    #工具：导入外部自动布线器输出的SES文件，替换当前板图
    def toolImportSes(self, args):
        from sprint_struct.sprint_import_ses import SprintImportSes
        sesFile = str(args.get('path') or '').strip()
        if not sesFile or not os.path.isfile(sesFile):
            raise McpToolError('File does not exist: {}'.format(sesFile))
        if not sesFile.lower().endswith('.ses'):
            sesFile += '.ses'
            if not os.path.isfile(sesFile):
                raise McpToolError('File does not exist: {}'.format(sesFile))
        trimMode = str(args.get('trimMode') or 'trimRouted').lower()
        if trimMode not in ('trimRouted', 'trimAll', 'keepAll'):
            raise McpToolError('trimMode must be trimRouted/trimAll/keepAll')

        dsnPickleFile = os.path.splitext(sesFile)[0] + '.pickle'
        if not os.path.isfile(dsnPickleFile):
            raise McpToolError('DSN pickle file not found: {} (it is written by exportDsn)'.format(dsnPickleFile))
        try:
            with open(dsnPickleFile, 'rb') as f:
                dsnExporter = pickle.load(f)
        except Exception as e:
            raise McpToolError('Failed to load DSN pickle: {}'.format(str(e)))

        ses = SprintImportSes(sesFile, dsnExporter)
        newTextIo = ses.importSes(trimRatsnestMode=trimMode, trackOnly=False)
        if not newTextIo:
            raise McpToolError('Failed to import SES file')
        self.pushUndoSnapshot()
        self.textIo = newTextIo
        return {'imported': True, 'path': sesFile, 'trimMode': trimMode,
            'totalElements': len(self.textIo.elements),
            'trackCount': len(self.textIo.getTracks()), 'padCount': len(self.textIo.getPads())}

    #工具：将板图回写给Sprint-Layout并关闭插件
    def toolApplyToSprintLayout(self, args):
        if (self.onApplyRequest is None) or (not self.hasInputFile):
            raise McpToolError(
                'Standalone mode (no input file from Sprint-Layout), cannot apply. Use saveTextIoFile instead, '
                'then import the file in Sprint-Layout via Extras -> Text-IO: Import elements...')
        if not self.parseOptionalBool(args, 'confirm', False):
            raise McpToolError('Set confirm=true to hand the board back to Sprint-Layout. '
                'The sprintFont plugin window will close.')
        if len(self.textIo.elements) == 0:
            raise McpToolError('Board is empty, nothing to apply')
        mode = str(args.get('mode') or 'auto').lower()
        if mode not in ('auto', 'replace', 'insert_new'):
            raise McpToolError('mode must be auto/replace/insert_new')
        if (mode == 'replace') and self.replaceDisabled:
            raise McpToolError('The original board failed to parse in the plugin, '
                'replace mode is disabled. Use mode "auto" or "insert_new" instead.')
        self.onApplyRequest(mode)
        return {'status': 'closing',
            'message': 'The sprintFont plugin is closing and the board is being transferred to Sprint-Layout.'}


#------------------------- MCP工具的JSON Schema定义 -------------------------

#生成一个工具参数的属性描述
def prop(desc, type_='string', **kwargs):
    ret = {'type': type_, 'description': desc}
    ret.update(kwargs)
    return ret

#生成一个工具定义
def toolDef(name, description, properties, required=None):
    schema = {'type': 'object', 'properties': properties}
    if required:
        schema['required'] = required
    return {'name': name, 'description': description, 'inputSchema': schema}

#构建全部工具定义列表
def buildToolDefinitions():
    layerDesc = 'PCB layer: integer 1-7 (1=C1 front copper, 2=S1 front silkscreen, 3=C2 back copper, ' \
        '4=S2 back silkscreen, 5=I1, 6=I2, 7=U outline) or name like "C1"/"F.Cu"'
    pointDesc = 'Coordinate [x, y] in mm. Origin at TOP-LEFT of the board, X right, Y DOWN'

    trackProps = {
        'layer': prop(layerDesc),
        'width': prop('Track width in mm', 'number'),
        'points': prop('Polyline vertices, array of [x, y], at least 2 points', 'array',
            items={'type': 'array', 'items': {'type': 'number'}}),
        'clearance': prop('Optional: distance to automatic ground-plane in mm', 'number'),
        'cutout': prop('Optional: cutout element for automatic ground-plane', 'boolean'),
        'soldermask': prop('Optional: expose soldermask over this track', 'boolean'),
        'flatStart': prop('Optional: track start is flat (not rounded)', 'boolean'),
        'flatEnd': prop('Optional: track end is flat (not rounded)', 'boolean'),
        'name': prop('Optional: element name', 'string'),
    }

    padProps = {
        'layer': prop(layerDesc),
        'pos': prop('Pad center ' + pointDesc, 'array', items={'type': 'number'}),
        'size': prop('Pad outer diameter in mm', 'number'),
        'drill': prop('Drill diameter in mm, 0 for no drill (must be >= 0)', 'number'),
        'form': prop('Pad shape: 1=round, 2=octagon, 3=square, 4=round-horiz, 5=octagon-horiz, ' \
            '6=rect-horiz, 7=round-vert, 8=octagon-vert, 9=rect-vert (default 1)', 'integer'),
        'rotation': prop('Optional rotation in degrees, clockwise-positive (only for non-round forms)', 'number'),
        'via': prop('Optional: this pad is a via', 'boolean'),
        'thermal': prop('Optional: thermal pad on automatic ground-plane', 'boolean'),
        'clearance': prop('Optional: distance to automatic ground-plane in mm', 'number'),
        'soldermask': prop('Optional: soldermask opening', 'boolean'),
        'name': prop('Optional: free-form label for the pad (display hint only; Sprint-Layout has no net '
            'names, so this does not affect connectivity or DSN nets)'),
    }

    smdPadProps = {
        'layer': prop(layerDesc),
        'pos': prop('Pad center ' + pointDesc, 'array', items={'type': 'number'}),
        'sizeX': prop('Pad width (X) in mm', 'number'),
        'sizeY': prop('Pad height (Y) in mm', 'number'),
        'rotation': prop('Optional rotation in degrees, clockwise-positive', 'number'),
        'clearance': prop('Optional: distance to automatic ground-plane in mm', 'number'),
        'soldermask': prop('Optional: soldermask opening', 'boolean'),
        'name': prop('Optional: free-form label for the pad (display hint only, not a net name)', 'string'),
    }

    zoneProps = {
        'layer': prop(layerDesc),
        'width': prop('Outline width in mm', 'number'),
        'points': prop('Polygon vertices, array of [x, y], at least 3 points, auto-closed', 'array',
            items={'type': 'array', 'items': {'type': 'number'}}),
        'hatch': prop('Optional: hatched filling instead of solid', 'boolean'),
        'hatchAuto': prop('Optional: hatch thickness equals outline width (default true)', 'boolean'),
        'hatchWidth': prop('Optional: custom hatch line thickness in mm', 'number'),
        'cutout': prop('Optional: cutout (keepout) for automatic ground-plane', 'boolean'),
        'soldermask': prop('Optional: zone defines soldermask opening', 'boolean'),
        'soldermaskCutout': prop('Optional: zone defines a cutout in the solder mask', 'boolean'),
        'clearance': prop('Optional: clearance in mm', 'number'),
        'name': prop('Optional: element name', 'string'),
    }

    textProps = {
        'layer': prop(layerDesc),
        'pos': prop('Start position (bottom/left of text) ' + pointDesc, 'array', items={'type': 'number'}),
        'text': prop('The text content', 'string'),
        'height': prop('Text height in mm', 'number'),
        'style': prop('Optional: 0=Narrow, 1=Normal, 2=Wide (default 1)', 'integer'),
        'thickness': prop('Optional: 0=Thin, 1=Normal, 2=Bold (default 1)', 'integer'),
        'rotation': prop('Optional rotation in degrees, clockwise-positive', 'number'),
        'mirrorHorz': prop('Optional: mirrored horizontally', 'boolean'),
        'mirrorVert': prop('Optional: mirrored vertically', 'boolean'),
        'name': prop('Optional: element name', 'string'),
    }

    circleProps = {
        'layer': prop(layerDesc),
        'center': prop('Circle center ' + pointDesc, 'array', items={'type': 'number'}),
        'radius': prop('Radius in mm', 'number'),
        'width': prop('Line width in mm', 'number'),
        'startAngle': prop('Optional arc start angle in degrees, 0 at 3 o\'clock, counterclockwise (default 0 = full circle)', 'number'),
        'stopAngle': prop('Optional arc stop angle in degrees, counterclockwise (default 0 = full circle)', 'number'),
        'fill': prop('Optional: filled circle', 'boolean'),
        'clearance': prop('Optional: clearance in mm', 'number'),
        'cutout': prop('Optional: cutout element', 'boolean'),
        'soldermask': prop('Optional: soldermask opening', 'boolean'),
        'name': prop('Optional: element name', 'string'),
    }

    componentSubNote = 'Array of objects with the same fields as the corresponding add* tool'
    return [
        toolDef('getBoardInfo',
            'Get board overview: size, bounding box, element counts by type and layer, the list of '
            'components (footprints) with their bounding boxes, and the design rules (rules) that routing '
            'must respect: trackWidth, viaDiameter, viaDrill, clearance, smdSmdClearance (all mm). '
            'Call this first to understand the board.',
            {}),
        toolDef('getElements',
            'List board elements with optional filters. Element indexes returned here are used by '
            'deleteElements/moveElements/updateElements/groupElements. Large boards are paginated. '
            'Token-saving tips: pass depth=0 to get component/group summaries without expanding their '
            'sub-elements, pass indices=[...] to fetch details of specific elements only, and pass bbox '
            'to restrict the query to a rectangular region (find obstacles there before local routing '
            'or component placement).',
            {
                'type': prop('Optional filter: TRACK/PAD/SMDPAD/ZONE/TEXT/CIRCLE/COMPONENT/GROUP'),
                'layer': prop('Optional filter: ' + layerDesc),
                'offset': prop('Optional pagination offset (default 0)', 'integer'),
                'limit': prop('Optional page size, 1-2000 (default 200)', 'integer'),
                'depth': prop('Optional: 0 = COMPONENT/GROUP return summary only (id/value/package/'
                    'elementCount, no sub-elements), 1 = expand one level of sub-elements (default)', 'integer'),
                'indices': prop('Optional: array of element indexes (e.g. [0, 5]) to fetch directly; '
                    'returns exactly these elements and ignores type/layer/bbox/offset/limit', 'array',
                    items={'type': 'integer'}),
                'bbox': prop('Optional spatial filter [xMin, yMin, xMax, yMax] in mm: only elements whose '
                    'bounding box intersects this rectangle are returned', 'array',
                    items={'type': 'number'}),
            }),
        toolDef('addTrack',
            'Add a track (polyline) on a copper or silkscreen layer. ' + pointDesc,
            trackProps, ['layer', 'width', 'points']),
        toolDef('addPad',
            'Add a through-hole pad. Use via=true for a via. ' + pointDesc,
            padProps, ['layer', 'pos', 'size']),
        toolDef('addSmdPad',
            'Add an SMD pad (rectangular, optional rotation). ' + pointDesc,
            smdPadProps, ['layer', 'pos', 'sizeX', 'sizeY']),
        toolDef('addZone',
            'Add a zone (copper pour polygon / keepout / soldermask opening). ' + pointDesc,
            zoneProps, ['layer', 'width', 'points']),
        toolDef('addText',
            'Add a text element. ' + pointDesc,
            textProps, ['layer', 'pos', 'text', 'height']),
        toolDef('addCircle',
            'Add a circle or arc (set startAngle/stopAngle for an arc). ' + pointDesc,
            circleProps, ['layer', 'center', 'radius']),
        toolDef('addComponent',
            'Add a complete component (footprint) as one unit: pads, SMD pads, tracks (silkscreen outlines), '
            'zones, texts and circles grouped together, with an optional idText (reference designator like "R1") '
            'and valueText. Sub-element specs use the same fields as the corresponding add* tools, with absolute '
            'board coordinates. This is the preferred way to draw a footprint.',
            {
                'idText': prop('Optional reference designator: string or object {text, layer?, height?, pos?}'),
                'valueText': prop('Optional value label: string or object {text, layer?, height?, pos?}'),
                'comment': prop('Optional component comment', 'string'),
                'package': prop('Optional package name (enables pick+place data)', 'string'),
                'pads': prop('Optional. ' + componentSubNote, 'array'),
                'smdPads': prop('Optional. ' + componentSubNote, 'array'),
                'tracks': prop('Optional. ' + componentSubNote, 'array'),
                'zones': prop('Optional. ' + componentSubNote, 'array'),
                'texts': prop('Optional. ' + componentSubNote, 'array'),
                'circles': prop('Optional. ' + componentSubNote, 'array'),
            }),
        toolDef('batchAdd',
            'Add MANY elements in ONE call (fewer round-trips when routing a bus or placing a row of '
            'parts): pass arrays of specs with the same fields as the corresponding add* tools. The batch '
            'is atomic: if any spec is invalid nothing is added, and the whole batch counts as a single '
            'undo step. Returns the indexes of the added elements, ordered tracks, pads, smdPads, zones, '
            'texts, circles (input order preserved within each array). For a complete footprint use '
            'addComponent instead.',
            {
                'tracks': prop('Optional array of track specs (same fields as addTrack)', 'array'),
                'pads': prop('Optional array of through-hole pad specs (same fields as addPad; use via=true for vias)', 'array'),
                'smdPads': prop('Optional array of SMD pad specs (same fields as addSmdPad)', 'array'),
                'zones': prop('Optional array of zone specs (same fields as addZone)', 'array'),
                'texts': prop('Optional array of text specs (same fields as addText)', 'array'),
                'circles': prop('Optional array of circle/arc specs (same fields as addCircle)', 'array'),
            }),
        toolDef('addStandardFootprint',
            'Place a parametric standard footprint in one call (no manual pad math). Supported packages: '
            'chip passives 0402/0603/0805/1206 (2 SMD pads + silkscreen body outline), SOIC-8/14/16 '
            '(1.27mm pitch, pads 1.5x0.6, row distance 5.4mm), DIP-8/14/16 (2.54mm pitch, through-hole '
            'pads 1.7mm/drill 1.0mm, row distance 7.62mm), SOT-23, and pin headers HEADER-1xN / '
            'HEADER-2xN (2.54mm pitch, N=1-20, pins in a vertical row). pos is the CENTER of the '
            'footprint; rotation is clockwise-positive about that center. Pin 1 is at the top-left and '
            'numbered counterclockwise (SOIC/DIP/SOT-23) or top-to-bottom, row-major left-right '
            '(HEADER-1xN / HEADER-2xN). Each pad carries its pin number as name.',
            {
                'package': prop('Footprint name: 0402/0603/0805/1206, SOIC-8/14/16, DIP-8/14/16, '
                    'SOT-23, HEADER-1xN or HEADER-2xN (N=1-20)', 'string'),
                'pos': prop('Footprint center ' + pointDesc, 'array', items={'type': 'number'}),
                'rotation': prop('Optional rotation in degrees, clockwise-positive (default 0)', 'number'),
                'idText': prop('Optional reference designator: string or object {text, layer?, height?, pos?}; '
                    'pos (if given) is relative to the footprint center before rotation', 'string'),
                'valueText': prop('Optional value label: string or object {text, layer?, height?, pos?}; '
                    'pos (if given) is relative to the footprint center before rotation', 'string'),
            }, ['package', 'pos']),
        toolDef('deleteElements',
            'Delete top-level elements by their indexes (from getElements).',
            {'indices': prop('Array of element indexes to delete', 'array', items={'type': 'integer'})},
            ['indices']),
        toolDef('moveElements',
            'Move top-level elements by an offset.',
            {
                'indices': prop('Array of element indexes to move', 'array', items={'type': 'integer'}),
                'dx': prop('X offset in mm (can be negative)', 'number'),
                'dy': prop('Y offset in mm (can be negative)', 'number'),
            }, ['indices', 'dx', 'dy']),
        toolDef('rotateElements',
            'Rotate top-level elements around a center point (default: geometric center of the selection). '
            'Any angle works; 90/180/270 are exact. Rotation is clockwise-positive, same convention as '
            'pad/text rotation. Pads/texts get their own rotation property updated; component/group '
            'sub-elements are transformed as a unit.',
            {
                'indices': prop('Array of element indexes to rotate', 'array', items={'type': 'integer'}),
                'angle': prop('Rotation angle in degrees, clockwise-positive (e.g. 90, 180, 270, -90)', 'number'),
                'center': prop('Optional rotation center [x, y] in mm (default: center of the selection bounding box)', 'array',
                    items={'type': 'number'}),
            }, ['indices', 'angle']),
        toolDef('mirrorElements',
            'Mirror top-level elements in place, flipping around the center line of their bounding box. '
            'Texts get their glyph-mirror flag toggled and pad/text rotation angles reversed, so the '
            'result is a faithful mirrored copy.',
            {
                'indices': prop('Array of element indexes to mirror', 'array', items={'type': 'integer'}),
                'axis': prop('"x" = mirror horizontally (left-right flip, X mirrored across the vertical '
                    'center line); "y" = mirror vertically (up-down flip, Y mirrored across the horizontal center line)'),
            }, ['indices', 'axis']),
        toolDef('groupElements',
            'Wrap top-level elements into a locked group (they stay together when moved in Sprint-Layout).',
            {'indices': prop('Array of element indexes', 'array', items={'type': 'integer'})}, ['indices']),
        toolDef('updateElements',
            'Update properties of existing top-level elements in place, no delete + re-add needed. '
            'Each provided property is applied only to the selected elements whose type supports it '
            '(e.g. size only applies to PAD/SMDPAD, text only to TEXT); other elements skip it. '
            'Returns the updated elements.',
            dict([(key, prop(desc, type_)) for key, (type_, desc) in UPDATE_ELEMENT_PROPS.items()] +
                [('indices', prop('Array of element indexes to update', 'array', items={'type': 'integer'}))]),
            ['indices']),
        toolDef('undo', 'Undo the last board modification.', {}),
        toolDef('importTextIo',
            'Import elements from a Text-IO format string (the Sprint-Layout element exchange format). '
            'mode=append adds to the board, mode=replace clears the board first.',
            {
                'text': prop('Text-IO format content (one element per line, e.g. TRACK,LAYER=1,...;)'),
                'mode': prop('Optional: "append" (default) or "replace"'),
            }, ['text']),
        toolDef('exportTextIo',
            'Export the board (or one layer) as Text-IO format text.',
            {'layer': prop('Optional: only export this layer. ' + layerDesc)}),
        toolDef('loadTextIoFile',
            'Load elements from a Text-IO file on disk. mode=append (default) or replace.',
            {
                'path': prop('Absolute file path', 'string'),
                'mode': prop('Optional: "append" or "replace"'),
            }, ['path']),
        toolDef('saveTextIoFile',
            'Save the board as a Text-IO file. The file can be imported into Sprint-Layout via '
            'Extras -> Text-IO: Import elements...',
            {
                'path': prop('Absolute file path to write', 'string'),
                'layer': prop('Optional: only save this layer. ' + layerDesc),
            }, ['path']),
        toolDef('exportSvg',
            'Export the board as an SVG vector image (pads, SMD pads, tracks, circles/arcs, zones and '
            'approximate text rendering) for visual verification: open the file in a browser, '
            'or convert it to PNG.',
            {
                'path': prop('Absolute path of the .svg file to write', 'string'),
                'layers': prop('Optional: array of layers to export. ' + layerDesc),
                'mirrorY': prop('Optional: flip the board upside down', 'boolean'),
                'returnText': prop('Optional: also include the SVG text in the result', 'boolean'),
            }, ['path']),
        toolDef('getNetlist',
            'Extract copper connectivity (nets) by geometric intersection of touching elements. '
            'May be slow on very large boards. IMPORTANT: this is physical-touch connectivity only, NOT '
            'design intent - nets are auto-numbered (Net-1, Net-2, ...) and on an unrouted board every pad '
            'is its own isolated net. Element labels: top-level index, "a.b" = sub-element b of '
            'component/group a (same order as the subElements array returned by getElements). '
            'Use it to check which pads/tracks are already electrically connected.',
            {}),
        toolDef('checkDrc',
            'Run a design rule check (DRC) on the copper elements: reports clearance violations between '
            'elements of DIFFERENT nets on the same layer (pad-pad, pad-track, track-track and zone pairs; '
            'touching same-net elements are intended connections, not violations), tracks narrower than the '
            'minimum track width, and optionally isolated pads (a net consisting of a single unconnected '
            'pad). Nets are determined by physical-touch connectivity. Violations are sorted worst-first '
            'and each carries the element labels (same format as getNetlist), the actual gap, the required '
            'value and an approximate position. Run it after routing to verify the board. '
            'May be slow on very large boards.',
            {
                'trackWidth': prop('Optional: override minimum track width in mm, must be > 0 (default: rules from getBoardInfo)', 'number'),
                'clearance': prop('Optional: override minimum clearance in mm, must be > 0 (default: rules from getBoardInfo); SMD-SMD pairs always use the smdSmdClearance rule', 'number'),
                'includeIsolated': prop('Optional: also list isolated pads that are not connected to anything', 'boolean'),
            }),
        toolDef('exportDsn',
            'Export the board as a Specctra DSN file for external autorouting (the autorouter is operated '
            'manually by the user, not by the AI). Only 2 copper layers (F.Cu/B.Cu) are supported; components '
            'must be on the front side with unique names. A <name>.pickle file is written next to the DSN '
            'and is required by importSes.',
            {
                'path': prop('Absolute path of the .dsn file to write', 'string'),
                'trackWidth': prop('Optional routing track width in mm, must be > 0 (default from plugin settings)', 'number'),
                'viaDiameter': prop('Optional via outer diameter in mm, must be > 0', 'number'),
                'viaDrill': prop('Optional via drill diameter in mm, must be > 0', 'number'),
                'clearance': prop('Optional clearance in mm, must be > 0', 'number'),
            }, ['path']),
        toolDef('importSes',
            'Import an autorouter session (.ses) file produced externally from a DSN exported by exportDsn, '
            'and replace the board with the routed result.',
            {
                'path': prop('Absolute path of the .ses file', 'string'),
                'trimMode': prop('Optional: trimRouted (default, remove routed ratsnests) / trimAll / keepAll'),
            }, ['path']),
        toolDef('applyToSprintLayout',
            'Hand the board back to Sprint-Layout: the sprintFont plugin writes the result and closes, '
            'then Sprint-Layout updates the board (replace mode when launched with whole-board export, '
            'otherwise only newly added elements are inserted). Requires confirm=true.',
            {
                'confirm': prop('Must be true to actually close the plugin', 'boolean'),
                'mode': prop('Optional: auto (default) / replace / insert_new'),
            }),
    ]


#HTTP请求处理器，实现MCP Streamable HTTP传输
class McpHttpRequestHandler(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'
    server_version = 'sprintFontMCP'
    #initialize响应需要回传的会话ID
    responseSessionId = None

    #处理POST请求(JSON-RPC消息)
    def do_POST(self):
        mcpServer = getattr(self.server, 'mcpServer', None)
        self.responseSessionId = None
        path = self.path.split('?')[0]
        if path != MCP_ENDPOINT_PATH:
            return self.sendHttpResponse(404, {'error': 'Not found. MCP endpoint is {}'.format(MCP_ENDPOINT_PATH)})

        #防DNS重绑定攻击：校验Host头
        host = (self.headers.get('Host') or '').split(':')[0].strip().lower()
        if host and host not in ('127.0.0.1', 'localhost'):
            return self.sendHttpResponse(403, {'error': 'Invalid Host header'})

        try:
            length = int(self.headers.get('Content-Length') or 0)
            raw = self.rfile.read(length) if length > 0 else b''
            msg = json.loads(raw.decode('utf-8'))
        except Exception:
            return self.sendRpcError(None, -32700, 'Parse error')

        if isinstance(msg, list):
            return self.sendRpcError(None, -32600, 'Batch requests are not supported')
        if (not isinstance(msg, dict)) or (msg.get('jsonrpc') != '2.0') or (not msg.get('method')):
            return self.sendRpcError(msg.get('id') if isinstance(msg, dict) else None,
                -32600, 'Invalid Request')

        #会话校验(initialize除外)，客户端不带会话头时以无状态模式兼容处理
        #initialize必须先解析出方法名再跳过校验，避免代理转发残留会话头导致握手被404拒绝
        sessionId = self.headers.get('Mcp-Session-Id')
        if (sessionId is not None) and (msg.get('method') != 'initialize') \
                and mcpServer and (not mcpServer.checkSession(sessionId)):
            return self.sendHttpResponse(404, {'error': 'Session not found or expired'})

        msgId = msg.get('id')
        isNotification = 'id' not in msg
        method = msg.get('method')
        params = msg.get('params') or {}
        if not isinstance(params, dict):
            params = {}

        try:
            result = mcpServer.dispatchMessage(method, params, self) if mcpServer else None
        except McpRpcError as e:
            if isNotification:
                return self.sendHttpResponse(202, None)
            return self.sendRpcError(msgId, e.code, e.message)
        except Exception as e:
            traceback.print_exc()
            if isNotification:
                return self.sendHttpResponse(202, None)
            return self.sendRpcError(msgId, -32603, 'Internal error: {}'.format(str(e)))

        if isNotification:
            return self.sendHttpResponse(202, None)
        return self.sendHttpResponse(200, {'jsonrpc': '2.0', 'id': msgId, 'result': result})

    #处理GET请求：本服务器不支持SSE长连接流，按规范返回405
    def do_GET(self):
        return self.sendHttpResponse(405, {'error': 'GET (SSE stream) not supported, use POST'})

    #处理DELETE请求：按MCP规范终止会话并注销会话ID
    def do_DELETE(self):
        mcpServer = getattr(self.server, 'mcpServer', None)
        path = self.path.split('?')[0]
        if path != MCP_ENDPOINT_PATH:
            return self.sendHttpResponse(404, {'error': 'Not found. MCP endpoint is {}'.format(MCP_ENDPOINT_PATH)})
        sessionId = self.headers.get('Mcp-Session-Id')
        if (not sessionId) or (mcpServer is None) or (not mcpServer.checkSession(sessionId)):
            return self.sendHttpResponse(404, {'error': 'Session not found or expired'})
        mcpServer.sessions.discard(sessionId)
        self.responseSessionId = None
        return self.sendHttpResponse(204, None)

    #处理OPTIONS预检请求(浏览器客户端需要)
    def do_OPTIONS(self):
        self.send_response(204)
        self.sendHeaderCommon()
        self.send_header('Access-Control-Allow-Methods', 'POST, GET, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        self.send_header('Content-Length', '0')
        self.end_headers()

    #发送公共响应头
    def sendHeaderCommon(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Mcp-Session-Id, Authorization, Mcp-Protocol-Version')

    #发送一个JSON响应
    def sendHttpResponse(self, status, obj):
        body = b'' if (obj is None) else json.dumps(obj, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.sendHeaderCommon()
        if self.responseSessionId:
            self.send_header('Mcp-Session-Id', self.responseSessionId)
        if body:
            self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        if body:
            self.wfile.write(body)

    #发送一个JSON-RPC错误响应
    def sendRpcError(self, msgId, code, message):
        payload = {'jsonrpc': '2.0', 'id': msgId, 'error': {'code': code, 'message': message}}
        self.sendHttpResponse(200, payload)

    #关闭访问日志(打包后无控制台)
    def log_message(self, format, *args):
        return
