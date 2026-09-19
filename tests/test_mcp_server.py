#!/usr/bin/env python3
# -*- coding:utf-8 -*-
"""
MCP服务器的单元测试：HTTP传输层、JSON-RPC分发、全部Text-IO工具
运行：python tests/test_mcp_server.py (无外部依赖，可独立执行)
"""
import os, sys, json, time, shutil, tempfile, threading, unittest
import urllib.request, urllib.error
import copy

try:
    import builtins
    if not hasattr(builtins, '_'):
        builtins.__dict__['_'] = lambda x: x
except Exception:
    pass

testDir = os.path.dirname(__file__)
appDir = os.path.abspath(os.path.join(testDir, '..'))
if appDir not in sys.path:
    sys.path.insert(0, appDir)

from sprint_struct.sprint_textio import SprintTextIO
from sprint_struct.sprint_track import SprintTrack
from sprint_struct.sprint_pad import SprintPad
from sprint_struct.sprint_polygon import SprintPolygon
from sprint_struct.sprint_text import SprintText
from sprint_struct.sprint_group import SprintGroup
from sprint_struct.sprint_component import SprintComponent
from app.mcp_server import SprintMcpServer, DEFAULT_MCP_PORT, elementToDict


#向MCP服务器发送一个JSON-RPC请求，返回(HTTP状态码, 响应头, 响应体字典或None)
def postRpc(port, payload, sessionId=None, path='/mcp', host='127.0.0.1', raw=None):
    url = 'http://127.0.0.1:{}{}'.format(port, path)
    data = raw if raw is not None else json.dumps(payload).encode('utf-8')
    headers = {'Content-Type': 'application/json', 'Accept': 'application/json, text/event-stream'}
    if sessionId:
        headers['Mcp-Session-Id'] = sessionId
    if host:
        headers['Host'] = host
    req = urllib.request.Request(url, data=data, headers=headers, method='POST')
    try:
        resp = urllib.request.urlopen(req, timeout=10)
        body = resp.read()
        return resp.status, dict(resp.headers), (json.loads(body) if body else None)
    except urllib.error.HTTPError as e:
        body = e.read()
        return e.code, dict(e.headers), (json.loads(body) if body else None)

#向MCP服务器发送GET/OPTIONS/DELETE请求，返回状态码
def sendMethod(port, method, path='/mcp', sessionId=None):
    url = 'http://127.0.0.1:{}{}'.format(port, path)
    req = urllib.request.Request(url, method=method)
    if sessionId:
        req.add_header('Mcp-Session-Id', sessionId)
    try:
        resp = urllib.request.urlopen(req, timeout=10)
        resp.read()
        return resp.status
    except urllib.error.HTTPError as e:
        e.read()
        return e.code

#提取工具调用结果中的JSON负载
def toolPayload(rpcResult):
    content = rpcResult.get('content') or []
    text = content[0].get('text', '') if content else ''
    return json.loads(text) if text else {}


class TestMcpServer(unittest.TestCase):
    #每个用例启动一个独立的服务器实例，端口自动选择
    def setUp(self):
        self.textIo = SprintTextIO(50.0, 40.0)
        track = SprintTrack(1, 0.3)
        track.addPoint(5, 5)
        track.addPoint(15, 5)
        self.textIo.add(track)
        pad = SprintPad(padType='PAD', layerIdx=1)
        pad.pos = (5, 5)
        pad.size = 1.0
        pad.drill = 0.5
        self.textIo.add(pad)

        self.server = SprintMcpServer(self.textIo, serverVersion='1.10-test')
        #从默认端口开始尝试，避开被占用的端口
        self.port = None
        for p in range(55380, 55400):
            ok, msg = self.server.start(p)
            if ok:
                self.port = p
                break
        self.assertTrue(self.port, 'MCP server failed to start: {}'.format(msg))
        self.sessionId = None

    def tearDown(self):
        self.server.stop()

    #发送initialize握手，返回result
    def doInitialize(self):
        status, headers, resp = postRpc(self.port, {
            'jsonrpc': '2.0', 'id': 1, 'method': 'initialize',
            'params': {'protocolVersion': '2025-03-26',
                'capabilities': {}, 'clientInfo': {'name': 'unittest', 'version': '0'}}})
        self.assertEqual(status, 200)
        self.assertEqual(resp['result']['protocolVersion'], '2025-03-26')
        self.assertEqual(resp['result']['serverInfo']['name'], 'sprintFont')
        self.sessionId = headers.get('Mcp-Session-Id')
        self.assertTrue(self.sessionId)
        return resp['result']

    #调用一个工具并返回解析后的负载，expectError=True时断言isError为真
    def callTool(self, name, arguments=None, expectError=False):
        status, headers, resp = postRpc(self.port, {
            'jsonrpc': '2.0', 'id': 99, 'method': 'tools/call',
            'params': {'name': name, 'arguments': arguments or {}}}, sessionId=self.sessionId)
        self.assertEqual(status, 200)
        result = resp.get('result') or {}
        self.assertIn('content', result)
        if expectError:
            self.assertTrue(result.get('isError'), 'expected tool error, got: {}'.format(result))
        else:
            self.assertFalse(result.get('isError'), 'unexpected tool error: {}'.format(result))
        return toolPayload(result)

    #测试：握手、tools/list、ping
    def testInitializeAndListTools(self):
        result = self.doInitialize()
        self.assertIn('instructions', result)
        self.assertIn('capabilities', result)

        status, headers, resp = postRpc(self.port, {'jsonrpc': '2.0', 'id': 2, 'method': 'tools/list'}, sessionId=self.sessionId)
        self.assertEqual(status, 200)
        names = [t['name'] for t in resp['result']['tools']]
        for expect in ('getBoardInfo', 'getElements', 'addTrack', 'addPad', 'addSmdPad', 'addZone',
                'addText', 'addCircle', 'addComponent', 'batchAdd', 'addStandardFootprint',
                'deleteElements', 'moveElements', 'rotateElements', 'mirrorElements', 'groupElements',
                'updateElements', 'undo', 'importTextIo', 'exportTextIo', 'exportSvg', 'loadTextIoFile',
                'saveTextIoFile', 'getNetlist', 'checkDrc', 'exportDsn', 'importSes', 'applyToSprintLayout'):
            self.assertIn(expect, names)
        #每个工具必须有合法的inputSchema
        for t in resp['result']['tools']:
            self.assertEqual(t['inputSchema']['type'], 'object')

        status, headers, resp = postRpc(self.port, {'jsonrpc': '2.0', 'id': 3, 'method': 'ping'}, sessionId=self.sessionId)
        self.assertEqual(resp['result'], {})

    #测试：通知消息返回202，GET返回405，OPTIONS返回204，错误路径
    def testHttpTransports(self):
        self.doInitialize()
        #通知类消息(无id)返回202
        status, headers, body = postRpc(self.port, {'jsonrpc': '2.0', 'method': 'notifications/initialized'}, sessionId=self.sessionId)
        self.assertEqual(status, 202)
        self.assertIsNone(body)
        #GET/SSE不支持
        self.assertEqual(sendMethod(self.port, 'GET', sessionId=self.sessionId), 405)
        #OPTIONS预检
        self.assertEqual(sendMethod(self.port, 'OPTIONS'), 204)
        #未知路径
        status, headers, resp = postRpc(self.port, {'jsonrpc': '2.0', 'id': 1, 'method': 'ping'}, path='/other')
        self.assertEqual(status, 404)
        #非法JSON
        status, headers, resp = postRpc(self.port, None, raw=b'{not json')
        self.assertEqual(resp['error']['code'], -32700)
        #非法请求结构
        status, headers, resp = postRpc(self.port, {'method': 'ping'})
        self.assertEqual(resp['error']['code'], -32600)
        #未知方法
        status, headers, resp = postRpc(self.port, {'jsonrpc': '2.0', 'id': 1, 'method': 'no/such'}, sessionId=self.sessionId)
        self.assertEqual(resp['error']['code'], -32601)
        #无效会话
        status, headers, resp = postRpc(self.port, {'jsonrpc': '2.0', 'id': 1, 'method': 'ping'}, sessionId='bogus')
        self.assertEqual(status, 404)
        #错误的Host头(防DNS重绑定)
        status, headers, resp = postRpc(self.port, {'jsonrpc': '2.0', 'id': 1, 'method': 'ping'}, sessionId=self.sessionId, host='evil.example.com')
        self.assertEqual(status, 403)

    #测试：getBoardInfo与getElements
    def testBoardInfoAndElements(self):
        self.doInitialize()
        info = self.callTool('getBoardInfo')
        self.assertEqual(info['boardSize'], {'width': 50.0, 'height': 40.0})
        self.assertEqual(info['topLevelElementCount'], 2)
        self.assertEqual(info['countByType'].get('TRACK'), 1)
        self.assertEqual(info['countByType'].get('PAD'), 1)
        self.assertFalse(info['canApplyToSprintLayout'])
        #必须返回布线设计规则(与PcbRule默认值一致)
        self.assertEqual(info['rules'], {'trackWidth': 0.3, 'viaDiameter': 0.7,
            'viaDrill': 0.3, 'clearance': 0.2, 'smdSmdClearance': 0.06})

        elems = self.callTool('getElements', {'type': 'TRACK'})
        self.assertEqual(elems['total'], 1)
        track = elems['elements'][0]
        self.assertEqual(track['layer'], 1)
        self.assertEqual(track['width'], 0.3)
        self.assertEqual(len(track['points']), 2)

        elems = self.callTool('getElements', {'layer': 2})
        self.assertEqual(elems['total'], 0)

    #测试：全部add类工具
    def testAddElements(self):
        self.doInitialize()
        ret = self.callTool('addTrack', {'layer': 'C1', 'width': 0.5,
            'points': [[10, 10], [20, 10], [20, 20]], 'name': 'sig1'})
        self.assertTrue(ret['added'])
        self.assertEqual(ret['element']['points'], [[10.0, 10.0], [20.0, 10.0], [20.0, 20.0]])

        ret = self.callTool('addPad', {'layer': 3, 'pos': [5, 30], 'size': 2.0, 'drill': 1.0,
            'form': 'Square', 'via': True})
        self.assertEqual(ret['element']['formName'], 'Square')
        self.assertTrue(ret['element']['via'])

        ret = self.callTool('addSmdPad', {'layer': 'F.Cu', 'pos': [40, 10], 'sizeX': 1.2, 'sizeY': 0.6})
        self.assertEqual(ret['element']['type'], 'SMDPAD')
        self.assertEqual(ret['element']['layerName'], 'F.Cu')

        ret = self.callTool('addZone', {'layer': 1, 'width': 0.4,
            'points': [[0, 35], [50, 35], [50, 40], [0, 40]], 'hatch': True, 'name': 'gnd'})
        self.assertEqual(ret['element']['type'], 'ZONE')
        self.assertTrue(ret['element']['hatch'])

        ret = self.callTool('addText', {'layer': 2, 'pos': [10, 2], 'text': 'Hello PCB', 'height': 1.5})
        self.assertEqual(ret['element']['text'], 'Hello PCB')

        ret = self.callTool('addCircle', {'layer': 7, 'center': [25, 20], 'radius': 5, 'width': 0.2,
            'startAngle': 0, 'stopAngle': 180})
        self.assertEqual(ret['element']['radius'], 5.0)

        #非法参数必须报错
        self.callTool('addTrack', {'layer': 9, 'width': 0.3, 'points': [[0, 0], [1, 1]]}, expectError=True)
        self.callTool('addPad', {'layer': 1, 'pos': [0, 0]}, expectError=True)
        self.callTool('addSmdPad', {'layer': 1, 'pos': [0, 0], 'sizeX': -1, 'sizeY': 1}, expectError=True)
        self.callTool('addZone', {'layer': 1, 'width': 0.4, 'points': [[0, 0], [1, 1]]}, expectError=True)
        self.callTool('noSuchTool', {}, expectError=True)

        info = self.callTool('getBoardInfo')
        self.assertEqual(info['topLevelElementCount'], 8)

    #测试：addComponent完整封装
    def testAddComponent(self):
        self.doInitialize()
        ret = self.callTool('addComponent', {
            'idText': 'R1', 'valueText': '10k', 'package': 'R_0805',
            'smdPads': [
                {'layer': 1, 'pos': [30, 10], 'sizeX': 1.0, 'sizeY': 0.6},
                {'layer': 1, 'pos': [33, 10], 'sizeX': 1.0, 'sizeY': 0.6},
            ],
            'tracks': [{'layer': 2, 'width': 0.15,
                'points': [[29.5, 10], [29.5, 11], [33.5, 11], [33.5, 10]]}],
        })
        self.assertTrue(ret['added'])
        comp = ret['element']
        self.assertEqual(comp['type'], 'COMPONENT')
        self.assertEqual(comp['id'], 'R1')
        self.assertEqual(comp['value'], '10k')
        self.assertEqual(comp['mounting'], 'smd')
        self.assertEqual(len(comp['subElements']), 3) #2个焊盘+1条丝印

        elems = self.callTool('getElements', {'type': 'COMPONENT'})
        self.assertEqual(elems['total'], 1)
        self.assertEqual(elems['elements'][0]['id'], 'R1')

    #测试：删除/移动/编组/撤销
    def testEditOperations(self):
        self.doInitialize()
        ret = self.callTool('addTrack', {'layer': 1, 'width': 0.3, 'points': [[1, 1], [2, 2]]})
        idx = ret['index']

        ret = self.callTool('moveElements', {'indices': [idx], 'dx': 5, 'dy': 5})
        self.assertEqual(ret['moved'], 1)
        elems = self.callTool('getElements', {'type': 'TRACK'})
        moved = [e for e in elems['elements'] if e['index'] == idx][0]
        self.assertEqual(moved['points'][0], [6.0, 6.0])

        ret = self.callTool('groupElements', {'indices': [idx]})
        self.assertEqual(ret['grouped'], 1)
        self.assertEqual(ret['element']['type'], 'GROUP')

        #撤销掉编组和移动，恢复为3个顶层元素(track+pad+track)
        self.callTool('undo')
        self.callTool('undo')
        elems = self.callTool('getElements', {'type': 'TRACK'})
        self.assertEqual(elems['total'], 2)

        ret = self.callTool('deleteElements', {'indices': [0]})
        self.assertEqual(ret['removed'], 1)
        self.assertEqual(ret['remaining'], 2)
        self.callTool('deleteElements', {'indices': [999]}, expectError=True)
        self.callTool('undo')
        info = self.callTool('getBoardInfo')
        self.assertEqual(info['topLevelElementCount'], 3)

        self.callTool('clearBoard', {}, expectError=True) #未confirm必须拒绝
        self.assertEqual(self.callTool('getBoardInfo')['topLevelElementCount'], 3)
        self.callTool('clearBoard', {'confirm': True})
        self.assertEqual(self.callTool('getBoardInfo')['topLevelElementCount'], 0)

    #测试：TextIO的导入/导出/文件存取
    def testTextIoImportExport(self):
        self.doInitialize()
        textIoStr = str(self.textIo)
        self.assertIn('TRACK,LAYER=1', textIoStr)
        self.assertIn('PAD,LAYER=1', textIoStr)

        #替换模式导入(等价内容)
        ret = self.callTool('importTextIo', {'text': textIoStr, 'mode': 'replace'})
        self.assertEqual(ret['imported'], 2)
        self.assertEqual(ret['totalElements'], 2)

        #追加模式导入
        ret = self.callTool('importTextIo', {'text': textIoStr, 'mode': 'append'})
        self.assertEqual(ret['totalElements'], 4)
        self.callTool('undo')

        #导出后能被解析回同样的元素个数
        exported = self.callTool('exportTextIo')
        parser = __import__('sprint_struct.sprint_textio_parser', fromlist=['SprintTextIoParser']).SprintTextIoParser()
        parsed = parser.parseText(exported['text'])
        self.assertEqual(len(parsed.elements), 2)

        #按层导出
        exported = self.callTool('exportTextIo', {'layer': 3})
        self.assertEqual(exported['elementCount'], 0)

        #文件保存与加载
        tmpDir = tempfile.mkdtemp(prefix='sprintfont_mcp_test_')
        try:
            savePath = os.path.join(tmpDir, 'board.txt')
            ret = self.callTool('saveTextIoFile', {'path': savePath})
            self.assertTrue(ret['saved'])
            self.assertTrue(os.path.isfile(savePath))
            self.callTool('clearBoard', {'confirm': True})
            ret = self.callTool('loadTextIoFile', {'path': savePath, 'mode': 'append'})
            self.assertEqual(ret['imported'], 2)
        finally:
            shutil.rmtree(tmpDir, ignore_errors=True)

    #测试：网表提取
    def testNetlist(self):
        self.doInitialize()
        #再画一条连接焊盘的导线，形成同一个网络
        self.callTool('addTrack', {'layer': 1, 'width': 0.3, 'points': [[5, 5], [20, 5]]})
        net = self.callTool('getNetlist')
        self.assertGreaterEqual(net['netCount'], 1)
        #焊盘+两条导线应该在同一个网络里
        allElements = []
        for netItem in net['nets']:
            allElements.extend(netItem['elements'])
        self.assertTrue(any('.' not in e for e in allElements))

    #测试：网表元件子元素标签必须与getElements的subElements序号一致(不含ID/VALUE标签偏移)
    def testNetlistComponentLabels(self):
        self.doInitialize()
        self.callTool('addComponent', {'idText': 'R1',
            'smdPads': [{'layer': 1, 'pos': [30, 10], 'sizeX': 1.0, 'sizeY': 0.6},
                        {'layer': 1, 'pos': [33, 10], 'sizeX': 1.0, 'sizeY': 0.6}]})
        self.callTool('addTrack', {'layer': 1, 'width': 0.2, 'points': [[30, 10], [33, 10]]})
        net = self.callTool('getNetlist')
        allLabels = []
        for netItem in net['nets']:
            allLabels.extend(netItem['elements'])
        #元件是顶层索引2，两个焊盘必须是"2.0"和"2.1"(旧实现因ID/VALUE标签错位成2.2/2.3)
        self.assertIn('2.0', allLabels)
        self.assertIn('2.1', allLabels)
        self.assertIn('3', allLabels)
        self.assertIn('Physical-touch', net['note'])

    #测试：checkDrc间距/线宽/孤立焊盘
    def testCheckDrc(self):
        self.doInitialize()
        #初始板：焊盘与导线相连(同网络)，无违规、无孤立焊盘
        ret = self.callTool('checkDrc', {'includeIsolated': True})
        self.assertTrue(ret['ok'])
        self.assertEqual(ret['violationCount'], 0)
        self.assertEqual(ret['isolatedPadCount'], 0)

        #两个不同网络的焊盘边缘间距0.1mm < 规则0.2mm → 间距违规
        self.callTool('addPad', {'layer': 1, 'pos': [40, 30], 'size': 1.0})
        self.callTool('addPad', {'layer': 1, 'pos': [41.1, 30], 'size': 1.0})
        ret = self.callTool('checkDrc', {'includeIsolated': True})
        self.assertFalse(ret['ok'])
        viol = ret['violations'][0]
        self.assertEqual(viol['type'], 'clearance')
        self.assertAlmostEqual(viol['gap'], 0.1, places=3)
        self.assertEqual(viol['required'], 0.2)
        self.assertEqual(set(viol['elements']), {'2', '3'})
        self.assertEqual(viol['elementTypes'], ['PAD', 'PAD'])
        #两个焊盘各自成网 → 两个孤立焊盘
        self.assertEqual(ret['isolatedPadCount'], 2)

        #线宽不足 → width违规
        self.callTool('addTrack', {'layer': 1, 'width': 0.1, 'points': [[20, 20], [25, 20]]})
        ret = self.callTool('checkDrc', {})
        types = [v['type'] for v in ret['violations']]
        self.assertIn('width', types)
        self.assertIn('clearance', types)

        #放宽间隙规则后间距违规消失(线宽违规仍在)
        ret = self.callTool('checkDrc', {'clearance': 0.05})
        types = [v['type'] for v in ret['violations']]
        self.assertNotIn('clearance', types)
        self.assertIn('width', types)

        #0/负值覆盖必须报错，而不是被静默忽略后回退默认值
        self.callTool('checkDrc', {'clearance': 0}, expectError=True)
        self.callTool('checkDrc', {'clearance': -0.1}, expectError=True)
        self.callTool('checkDrc', {'trackWidth': 0}, expectError=True)

    #测试：游离导电元素(单元素网络被netlist过滤)之间仍必须做间距检查
    def testCheckDrcIsolatedElements(self):
        self.doInitialize()
        #两条孤立导线边缘间距0.05mm < 规则0.2mm → 间距违规(不能因同为无网络而互相跳过)
        self.callTool('addTrack', {'layer': 1, 'width': 0.3, 'points': [[5, 20], [15, 20]]})
        self.callTool('addTrack', {'layer': 1, 'width': 0.3, 'points': [[5, 20.35], [15, 20.35]]})
        ret = self.callTool('checkDrc', {})
        self.assertFalse(ret['ok'])
        viol = [v for v in ret['violations'] if v['type'] == 'clearance']
        self.assertEqual(len(viol), 1)
        self.assertEqual(viol[0]['elementTypes'], ['TRACK', 'TRACK'])
        self.assertAlmostEqual(viol[0]['gap'], 0.05, places=3)

    #测试：add入口的负值参数必须报错或钳位，与update入口约束一致
    def testPadNegativeValueRejected(self):
        self.doInitialize()
        #pad家族与update路径同为raise语义
        self.callTool('addPad', {'layer': 1, 'pos': [10, 10], 'size': 1.0, 'drill': -1.0}, expectError=True)
        self.callTool('addPad', {'layer': 1, 'pos': [10, 10], 'size': 1.0, 'clearance': -0.1}, expectError=True)
        self.callTool('addPad', {'layer': 1, 'pos': [10, 10], 'size': 1.0, 'thermalTracksWidth': -0.5}, expectError=True)
        self.callTool('addPad', {'layer': 1, 'pos': [10, 10], 'size': 1.0, 'thermalTracks': -3}, expectError=True)
        self.callTool('addSmdPad', {'layer': 1, 'pos': [10, 10], 'sizeX': 1.0, 'sizeY': 0.5, 'clearance': -0.1}, expectError=True)
        ret = self.callTool('addPad', {'layer': 1, 'pos': [30, 10], 'size': 1.0})
        self.callTool('updateElements', {'indices': [ret['index']], 'drill': -1}, expectError=True)
        #track/zone/circle与update路径同为钳位语义：负clearance归0
        ret = self.callTool('addTrack', {'layer': 1, 'width': 0.3, 'points': [[20, 20], [25, 20]], 'clearance': -0.1})
        self.assertEqual(self.server.textIo.elements[ret['index']].clearance, 0)

    #测试：无实际修改的操作不得消耗撤销快照
    def testUndoNotConsumedByNoOp(self):
        self.doInitialize()
        #dx=dy=0移动不消耗撤销步：undo直接撤销addText，文本应消失
        self.callTool('addText', {'layer': 2, 'pos': [10, 2], 'text': 'T1', 'height': 1.5})
        self.callTool('moveElements', {'indices': [2], 'dx': 0, 'dy': 0})
        self.callTool('undo')
        self.assertEqual(len(self.server.textIo.elements), 2)

        #对不支持属性的类型修改(updated=0，如对TRACK传text)不消耗撤销步
        self.callTool('addText', {'layer': 2, 'pos': [10, 2], 'text': 'T2', 'height': 1.5})
        self.callTool('updateElements', {'indices': [0], 'text': 'X'})
        self.callTool('undo')
        self.assertEqual(len(self.server.textIo.elements), 2)

        #零角度旋转不消耗撤销步
        self.callTool('addText', {'layer': 2, 'pos': [10, 2], 'text': 'T3', 'height': 1.5})
        self.callTool('rotateElements', {'indices': [2], 'angle': 0})
        self.callTool('undo')
        self.assertEqual(len(self.server.textIo.elements), 2)

        #update中途报错：单元素原子回滚，板图立即恢复原状且不消耗撤销步
        self.callTool('updateElements', {'indices': [1], 'drill': 0.6, 'thermalTracks': 'x'}, expectError=True)
        pad = self.server.textIo.elements[1]
        self.assertEqual(pad.drill, 0.5) #部分修改的drill立即回滚
        self.assertEqual(len(self.server.undoStack), 0) #无实际修改，撤销栈未被占用

        #第一个元素解析参数即报错(无任何修改)：同样不得入栈快照
        self.callTool('updateElements', {'indices': [1], 'layer': 'BOGUS'}, expectError=True)
        self.assertEqual(len(self.server.undoStack), 0)

    #测试：getBoardInfo的元件bbox必须四值全查(空元件外框为无穷时省略，不得产生非法JSON)
    def testBoardInfoComponentBboxGuard(self):
        self.doInitialize()
        self.callTool('addStandardFootprint', {'package': '0603', 'pos': [10, 10]})
        #空元件经importTextIo进入板图，其外框为正负无穷
        self.callTool('importTextIo', {'text': 'BEGIN_COMPONENT,COMMENT=|EMPTY|,PACKAGE=|T|;\nEND_COMPONENT;'})
        info = self.callTool('getBoardInfo')
        s = json.dumps(info)
        self.assertNotIn('Infinity', s)
        self.assertNotIn('NaN', s)
        byPkg = {c['package']: c for c in info['components']}
        self.assertIn('bbox', byPkg['0603']) #正常元件的bbox仍输出
        self.assertNotIn('bbox', byPkg['T']) #空元件的bbox省略

    #测试：getElements指定indices时忽略过滤参数(非法bbox/type/layer不报错，indices照常生效)
    def testGetElementsIndicesIgnoreFilters(self):
        self.doInitialize()
        #indices + 非法bbox：indices优先，不得报bbox错
        ret = self.callTool('getElements', {'indices': [0, 1], 'bbox': [10, 10, 5, 5]})
        self.assertEqual(ret['count'], 2)
        #indices + 非法type/layer：同样忽略
        ret = self.callTool('getElements', {'indices': [0], 'type': 'BOGUS', 'layer': 'NOSUCH'})
        self.assertEqual(ret['count'], 1)
        #无indices时非法过滤参数仍必须报错
        self.callTool('getElements', {'bbox': [10, 10, 5, 5]}, expectError=True)
        self.callTool('getElements', {'type': 'BOGUS'}, expectError=True)
        self.callTool('getElements', {'layer': 'NOSUCH'}, expectError=True)

    #测试：exportDsn写盘失败时不得留下错位的DSN/pickle组合(临时文件+DSN最后改名提交)
    def testExportDsnAtomicWrite(self):
        self.doInitialize()
        #DSN导出要求U层有板框
        outline = SprintPolygon(7, 0.2)
        for pt in ((0, 0), (50, 0), (50, 40), (0, 40)):
            outline.addPoint(*pt)
        self.textIo.add(outline)
        tmpDir = tempfile.mkdtemp(prefix='sprintfont_mcp_test_')
        try:
            dsnPath = os.path.join(tmpDir, 'board.dsn')
            ret = self.callTool('exportDsn', {'path': dsnPath})
            with open(ret['dsnFile'], 'r', encoding='utf-8') as f:
                firstDsn = f.read()
            #把pickle路径换成同名目录，模拟第二次导出时pickle替换失败
            os.remove(ret['pickleFile'])
            os.mkdir(ret['pickleFile'])
            self.callTool('exportDsn', {'path': dsnPath}, expectError=True)
            #DSN必须保持第一次的内容(未被截断/覆盖)，不得出现新DSN配坏pickle的错位
            with open(dsnPath, 'r', encoding='utf-8') as f:
                self.assertEqual(f.read(), firstDsn)
            #不留临时文件垃圾
            self.assertEqual([n for n in os.listdir(tmpDir) if n.endswith('.tmp')], [])
        finally:
            shutil.rmtree(tmpDir, ignore_errors=True)

    #测试：DSN导出(不实际跑freerouting，只验证文件生成)
    def testExportDsn(self):
        self.doInitialize()
        #DSN导出要求U层有板框，画一个矩形板框
        outline = SprintPolygon(7, 0.2)
        outline.addPoint(0, 0)
        outline.addPoint(50, 0)
        outline.addPoint(50, 40)
        outline.addPoint(0, 40)
        self.textIo.add(outline)

        tmpDir = tempfile.mkdtemp(prefix='sprintfont_mcp_test_')
        try:
            dsnPath = os.path.join(tmpDir, 'board.dsn')
            ret = self.callTool('exportDsn', {'path': dsnPath, 'trackWidth': 0.25, 'viaDiameter': 0.7, 'viaDrill': 0.3})
            self.assertTrue(os.path.isfile(ret['dsnFile']))
            self.assertTrue(os.path.isfile(ret['pickleFile']))
            with open(ret['dsnFile'], 'r', encoding='utf-8') as f:
                content = f.read()
            self.assertIn('(PCB', content)
            self.assertIn('(boundary', content)
            #0/负值参数必须报错
            self.callTool('exportDsn', {'path': dsnPath, 'clearance': 0}, expectError=True)
            self.callTool('exportDsn', {'path': dsnPath, 'clearance': -1}, expectError=True)
            #合法小值必须生效写入DSN，而不是被旧阈值(>0.1)静默丢弃后用默认值
            ret = self.callTool('exportDsn', {'path': dsnPath, 'trackWidth': 0.15, 'viaDiameter': 0.7,
                'viaDrill': 0.1, 'clearance': 0.05})
            with open(ret['dsnFile'], 'r', encoding='utf-8') as f:
                content = f.read()
            self.assertIn('(clearance 50)', content) #mm2um: 0.05mm -> 50
            self.assertIn('Via_700x100', content) #viaDrill=0.1mm生效(细间距设计合法值)
            self.assertIn('(width 150)', content) #trackWidth=0.15mm生效
            #importSes缺少ses文件时必须报错而不是崩溃
            self.callTool('importSes', {'path': os.path.join(tmpDir, 'no.ses')}, expectError=True)
        finally:
            shutil.rmtree(tmpDir, ignore_errors=True)

    #测试：standalone模式下applyToSprintLayout必须报错
    def testApplyStandaloneError(self):
        self.doInitialize()
        self.callTool('applyToSprintLayout', {'confirm': True}, expectError=True)

    #测试：并发工具调用的线程安全(全部请求都应成功返回)
    def testConcurrentCalls(self):
        self.doInitialize()
        errors = []
        def worker(base):
            try:
                for i in range(5):
                    ret = self.callTool('addTrack', {'layer': 1, 'width': 0.2,
                        'points': [[base + i, 1], [base + i, 2]]})
                    self.assertTrue(ret['added'])
            except Exception as e:
                errors.append(e)
        threads = [threading.Thread(target=worker, args=(10 * n,)) for n in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=30)
        self.assertEqual(errors, [])
        info = self.callTool('getBoardInfo')
        self.assertEqual(info['topLevelElementCount'], 2 + 20)

    #测试：updateElements原地修改属性
    def testUpdateElements(self):
        self.doInitialize()
        ret = self.callTool('addText', {'layer': 2, 'pos': [10, 2], 'text': 'OLD', 'height': 1.5})
        textIdx = ret['index']
        ret = self.callTool('addSmdPad', {'layer': 1, 'pos': [40, 30], 'sizeX': 1.0, 'sizeY': 0.5})
        smdIdx = ret['index']

        #文本属性原地修改
        ret = self.callTool('updateElements', {'indices': [textIdx],
            'text': 'NEW', 'height': 2.0, 'rotation': 90})
        self.assertEqual(ret['updated'], 1)
        elem = ret['elements'][0]
        self.assertEqual(elem['text'], 'NEW')
        self.assertEqual(elem['height'], 2.0)
        self.assertEqual(elem['rotation'], 90)

        #类型专属属性只应用到匹配类型：索引0是TRACK(width生效)，SMDPAD(sizeX/sizeY生效)
        ret = self.callTool('updateElements', {'indices': [0, smdIdx], 'width': 0.5, 'sizeX': 2.0, 'sizeY': 1.0})
        byIndex = {e['index']: e for e in ret['elements']}
        self.assertEqual(ret['updated'], 2)
        self.assertEqual(byIndex[0]['width'], 0.5)
        self.assertEqual(byIndex[smdIdx]['sizeX'], 2.0)

        #移动板层
        ret = self.callTool('updateElements', {'indices': [smdIdx], 'layer': 'C2'})
        self.assertEqual(ret['elements'][0]['layer'], 3)

        #未知属性必须报错，非法索引必须报错
        self.callTool('updateElements', {'indices': [textIdx], 'bogus': 1}, expectError=True)
        self.callTool('updateElements', {'indices': [999]}, expectError=True)

        #修改后可撤销(前面共修改了3次：文本、宽高、移层)
        self.callTool('undo')
        self.callTool('undo')
        self.callTool('undo')
        elems = self.callTool('getElements', {'type': 'TEXT'})
        self.assertEqual(elems['elements'][0]['text'], 'OLD')

        #修改COMPONENT的标签
        ret = self.callTool('addComponent', {'idText': 'R1', 'valueText': '10k',
            'smdPads': [{'layer': 1, 'pos': [30, 10], 'sizeX': 1.0, 'sizeY': 0.6}]})
        compIdx = ret['index']
        ret = self.callTool('updateElements', {'indices': [compIdx], 'idText': 'C3', 'valueText': '100n'})
        elem = ret['elements'][0]
        self.assertEqual(elem['id'], 'C3')
        self.assertEqual(elem['value'], '100n')

    #测试：getElements/addPad回显全部属性(含clearance/soldermask/thermal)
    def testElementEchoFields(self):
        self.doInitialize()
        ret = self.callTool('addPad', {'layer': 1, 'pos': [10, 30], 'size': 1.5, 'drill': 0.6,
            'clearance': 0.3, 'soldermask': True, 'thermal': True,
            'thermalTracksWidth': 0.2, 'thermalTracks': 4, 'thermalTracksIndividual': True})
        pad = ret['element']
        self.assertEqual(pad['clearance'], 0.3)
        self.assertTrue(pad['soldermask'])
        self.assertEqual(pad['thermalTracksWidth'], 0.2)
        self.assertEqual(pad['thermalTracks'], 4)
        self.assertTrue(pad['thermalTracksIndividual'])

        #序列化到Text-IO时热焊盘辐条宽度必须转成0.1µm整数(0.2mm -> 2000)
        exported = self.callTool('exportTextIo')
        self.assertIn('CLEAR=3000', exported['text'])
        self.assertIn('THERMAL_TRACKS_WIDTH=2000', exported['text'])

        #ZONE的hatchAuto和TEXT/CIRCLE的cutout/soldermask也要回显
        ret = self.callTool('addZone', {'layer': 1, 'width': 0.3,
            'points': [[0, 35], [10, 35], [10, 40], [0, 40]], 'hatchAuto': False})
        self.assertFalse(ret['element']['hatchAuto'])
        ret = self.callTool('addCircle', {'layer': 7, 'center': [25, 20], 'radius': 5, 'cutout': True})
        self.assertTrue(ret['element']['cutout'])

    #测试：getElements的depth/indices/bbox增强参数(省Token与局部查询)
    def testGetElementsDepthIndicesBbox(self):
        self.doInitialize()
        #加一个元件和一个远处的导线
        ret = self.callTool('addComponent', {'idText': 'R1',
            'smdPads': [{'layer': 1, 'pos': [30, 10], 'sizeX': 1.0, 'sizeY': 0.6},
                {'layer': 1, 'pos': [33, 10], 'sizeX': 1.0, 'sizeY': 0.6}]})
        compIdx = ret['index']
        self.callTool('addTrack', {'layer': 1, 'width': 0.3, 'points': [[40, 30], [45, 30]]})

        #默认depth=1：元件展开子元素
        elems = self.callTool('getElements', {'type': 'COMPONENT'})
        self.assertEqual(elems['total'], 1)
        self.assertEqual(len(elems['elements'][0]['subElements']), 2)

        #depth=0：元件只返回概要信息，不展开内部子元素
        elems = self.callTool('getElements', {'type': 'COMPONENT', 'depth': 0})
        comp = elems['elements'][0]
        self.assertNotIn('subElements', comp)
        self.assertEqual(comp['elementCount'], 2)
        self.assertEqual(comp['id'], 'R1')

        #depth只允许0/1
        self.callTool('getElements', {'depth': 2}, expectError=True)

        #indices：直接查指定索引详情，忽略type过滤，顺序与回传一致
        elems = self.callTool('getElements', {'indices': [compIdx, 0]})
        self.assertEqual(elems['total'], 2)
        self.assertEqual([e['index'] for e in elems['elements']], [compIdx, 0])
        self.assertEqual(elems['elements'][1]['type'], 'TRACK')
        #indices模式下depth同样生效
        elems = self.callTool('getElements', {'indices': [compIdx], 'depth': 0})
        self.assertNotIn('subElements', elems['elements'][0])
        #非法索引必须报错
        self.callTool('getElements', {'indices': [999]}, expectError=True)

        #bbox：只返回包围盒与范围相交的元素
        elems = self.callTool('getElements', {'bbox': [28, 8, 34, 12]})
        self.assertEqual(elems['total'], 1)
        self.assertEqual(elems['elements'][0]['type'], 'COMPONENT')
        #起始导线(5,5)与焊盘(5,5)的范围
        elems = self.callTool('getElements', {'bbox': [0, 0, 10, 10]})
        self.assertEqual(sorted(e['type'] for e in elems['elements']), ['PAD', 'TRACK'])
        #空范围
        elems = self.callTool('getElements', {'bbox': [45, 35, 50, 40]})
        self.assertEqual(elems['total'], 0)
        #bbox与type过滤可组合
        elems = self.callTool('getElements', {'bbox': [0, 0, 10, 10], 'type': 'PAD'})
        self.assertEqual(elems['total'], 1)
        #非法bbox必须报错
        self.callTool('getElements', {'bbox': [10, 10, 5, 5]}, expectError=True)
        self.callTool('getElements', {'bbox': [1, 2, 3]}, expectError=True)

    #测试：batchAdd批量添加(一次往返、原子化、单步撤销)
    def testBatchAdd(self):
        self.doInitialize()
        #一次调用添加2条导线+1个焊盘+1个文本，返回连续索引
        ret = self.callTool('batchAdd', {
            'tracks': [
                {'layer': 1, 'width': 0.3, 'points': [[5, 20], [15, 20]]},
                {'layer': 1, 'width': 0.3, 'points': [[5, 22], [15, 22]]},
            ],
            'pads': [{'layer': 1, 'pos': [20, 20], 'size': 1.0, 'drill': 0.5, 'via': True}],
            'texts': [{'layer': 2, 'pos': [5, 25], 'text': 'BUS', 'height': 1.0}],
        })
        self.assertEqual(ret['added'], 4)
        self.assertEqual(ret['indexes'], [2, 3, 4, 5])
        self.assertEqual(ret['totalElements'], 6)
        #添加顺序固定：tracks在前，用indices直查验证类型与内容
        elems = self.callTool('getElements', {'indices': [2, 4]})
        self.assertEqual(elems['elements'][0]['type'], 'TRACK')
        self.assertEqual(elems['elements'][0]['points'], [[5.0, 20.0], [15.0, 20.0]])
        self.assertEqual(elems['elements'][1]['type'], 'PAD')
        self.assertTrue(elems['elements'][1]['via'])
        elems = self.callTool('getElements', {'indices': [5]})
        self.assertEqual(elems['elements'][0]['text'], 'BUS')

        #整批只占一步撤销
        self.callTool('undo')
        info = self.callTool('getBoardInfo')
        self.assertEqual(info['topLevelElementCount'], 2)

        #任一spec非法则整体不添加(原子化)，且不消耗撤销快照
        self.callTool('batchAdd', {
            'tracks': [{'layer': 1, 'width': 0.3, 'points': [[1, 30], [2, 30]]}],
            'pads': [{'layer': 1, 'pos': [30, 30], 'size': -1.0}],
        }, expectError=True)
        info = self.callTool('getBoardInfo')
        self.assertEqual(info['topLevelElementCount'], 2)
        self.callTool('undo', expectError=True) #Nothing to undo

        #空调用必须报错
        self.callTool('batchAdd', {}, expectError=True)

    #测试：rotateElements/mirrorElements几何变换(角度方向、弧角度重映射、标签跟随、单步撤销)
    def testRotateMirrorElements(self):
        self.doInitialize()
        ret = self.callTool('addTrack', {'layer': 1, 'width': 0.3, 'points': [[10, 20], [20, 20]]})
        trackIdx = ret['index']
        ret = self.callTool('addSmdPad', {'layer': 1, 'pos': [30, 30], 'sizeX': 2.0, 'sizeY': 1.0, 'rotation': 30})
        padIdx = ret['index']

        #绕选区几何中心(默认)旋转90度(顺时针为正)：水平线变竖直线
        ret = self.callTool('rotateElements', {'indices': [trackIdx], 'angle': 90})
        self.assertEqual(ret['rotated'], 1)
        self.assertEqual(ret['center'], [15.0, 20.0])
        elems = self.callTool('getElements', {'indices': [trackIdx]})
        self.assertEqual(elems['elements'][0]['points'], [[15.0, 15.0], [15.0, 25.0]])

        #再转90度(累计180)：回到水平但端点顺序反映旋转轨迹
        self.callTool('rotateElements', {'indices': [trackIdx], 'angle': 90})
        elems = self.callTool('getElements', {'indices': [trackIdx]})
        self.assertEqual(elems['elements'][0]['points'], [[20.0, 20.0], [10.0, 20.0]])

        #显式指定旋转中心的180度旋转
        self.callTool('rotateElements', {'indices': [trackIdx], 'angle': 180, 'center': [10, 20]})
        elems = self.callTool('getElements', {'indices': [trackIdx]})
        self.assertEqual(elems['elements'][0]['points'], [[0.0, 20.0], [10.0, 20.0]])

        #焊盘旋转：自身旋转角同步增加，绕自身中心旋转位置不变
        self.callTool('rotateElements', {'indices': [padIdx], 'angle': 90, 'center': [30, 30]})
        elems = self.callTool('getElements', {'indices': [padIdx]})
        self.assertEqual(elems['elements'][0]['rotation'], 120)
        self.assertEqual(elems['elements'][0]['pos'], [30.0, 30.0])

        #水平镜像(axis=x)：X坐标绕选区中心线(x=5)翻转
        ret = self.callTool('mirrorElements', {'indices': [trackIdx], 'axis': 'x'})
        self.assertEqual(ret['center'], [5.0, 20.0])
        elems = self.callTool('getElements', {'indices': [trackIdx]})
        self.assertEqual(elems['elements'][0]['points'], [[10.0, 20.0], [0.0, 20.0]])
        self.callTool('mirrorElements', {'indices': [padIdx], 'axis': 'x'})
        elems = self.callTool('getElements', {'indices': [padIdx]})
        self.assertEqual(elems['elements'][0]['rotation'], 240)
        self.assertEqual(elems['elements'][0]['pos'], [30.0, 30.0])

        #垂直镜像(axis=y)：文本旋转角取反、字形垂直镜像标志翻转
        ret = self.callTool('addText', {'layer': 2, 'pos': [10, 35], 'text': 'AB', 'height': 1.0, 'rotation': 30})
        textIdx = ret['index']
        self.callTool('mirrorElements', {'indices': [textIdx], 'axis': 'y'})
        elems = self.callTool('getElements', {'indices': [textIdx]})
        self.assertEqual(elems['elements'][0]['rotation'], 330)
        self.assertTrue(elems['elements'][0]['mirrorVert'])

        #圆弧旋转：存储约定逆时针为正，顺时针旋转90度后弧角度要减90
        ret = self.callTool('addCircle', {'layer': 7, 'center': [25, 10], 'radius': 5, 'startAngle': 0, 'stopAngle': 90})
        cirIdx = ret['index']
        self.callTool('rotateElements', {'indices': [cirIdx], 'angle': 90})
        elems = self.callTool('getElements', {'indices': [cirIdx]})
        self.assertEqual(elems['elements'][0]['startAngle'], 270)
        self.assertEqual(elems['elements'][0]['stopAngle'], 0)

        #元件整体旋转：子焊盘跟随，自动放置的位号保持(0,0)不动
        ret = self.callTool('addComponent', {'idText': 'R1',
            'smdPads': [{'layer': 1, 'pos': [40, 10], 'sizeX': 1.0, 'sizeY': 0.5}]})
        compIdx = ret['index']
        self.callTool('rotateElements', {'indices': [compIdx], 'angle': 90, 'center': [40, 10]})
        elems = self.callTool('getElements', {'indices': [compIdx]})
        self.assertEqual(elems['elements'][0]['subElements'][0]['pos'], [40.0, 10.0])
        self.assertEqual(elems['elements'][0]['subElements'][0]['rotation'], 90)

        #一次变换只占一步撤销(撤销后焊盘rotation回到0，回显中该键消失)
        self.callTool('undo')
        elems = self.callTool('getElements', {'indices': [compIdx]})
        self.assertEqual(elems['elements'][0]['subElements'][0].get('rotation', 0), 0)

        #非法参数必须报错
        self.callTool('rotateElements', {'indices': [trackIdx]}, expectError=True)
        self.callTool('mirrorElements', {'indices': [trackIdx], 'axis': 'z'}, expectError=True)
        self.callTool('rotateElements', {'indices': [999], 'angle': 90}, expectError=True)

    #测试：addStandardFootprint标准封装生成器(引脚坐标/编号/旋转/参数归一化)
    def testStandardFootprint(self):
        self.doInitialize()
        #0603：两贴片焊盘+丝印外框，引脚号写入name，位号回显
        ret = self.callTool('addStandardFootprint', {'package': '0603', 'pos': [30, 20], 'idText': 'C1'})
        self.assertEqual(ret['pinCount'], 2)
        self.assertEqual(ret['element']['package'], '0603')
        self.assertEqual(ret['element']['id'], 'C1')
        self.assertEqual(len(ret['element']['subElements']), 3)
        pads = sorted((e for e in ret['element']['subElements'] if e['type'] == 'SMDPAD'),
            key=lambda e: int(e['name']))
        self.assertEqual([p['name'] for p in pads], ['1', '2'])
        self.assertEqual([p['pos'] for p in pads], [[29.1, 20.0], [30.9, 20.0]])
        self.assertEqual(pads[0]['sizeX'], 0.9)
        self.assertEqual(pads[0]['sizeY'], 0.95)

        #SOIC-8(soic8归一化)：1.27mm间距，引脚1左上，逆时针编号
        ret = self.callTool('addStandardFootprint', {'package': 'soic8', 'pos': [20, 20]})
        self.assertEqual(ret['pinCount'], 8)
        pads = sorted((e for e in ret['element']['subElements'] if e['type'] == 'SMDPAD'),
            key=lambda e: int(e['name']))
        self.assertEqual(pads[0]['pos'], [17.3, 18.095])  #引脚1：左上
        self.assertEqual(pads[3]['pos'], [17.3, 21.905])  #引脚4：左下
        self.assertEqual(pads[4]['pos'], [22.7, 21.905])  #引脚5：右下
        self.assertEqual(pads[7]['pos'], [22.7, 18.095])  #引脚8：右上
        self.assertEqual(pads[0]['sizeX'], 1.5)
        self.assertEqual(pads[0]['sizeY'], 0.6)

        #DIP-8：通孔焊盘，2.54mm间距，排距7.62
        ret = self.callTool('addStandardFootprint', {'package': 'DIP-8', 'pos': [20, 20]})
        pads = sorted((e for e in ret['element']['subElements'] if e['type'] == 'PAD'),
            key=lambda e: int(e['name']))
        self.assertEqual(pads[0]['pos'], [16.19, 16.19])
        self.assertEqual(pads[0]['drill'], 1.0)
        self.assertEqual(pads[0]['size'], 1.7)

        #SOT-23：1/2脚在左侧，3脚在右侧中部
        ret = self.callTool('addStandardFootprint', {'package': 'SOT-23', 'pos': [20, 20]})
        pads = sorted((e for e in ret['element']['subElements'] if e['type'] == 'SMDPAD'),
            key=lambda e: int(e['name']))
        self.assertEqual(pads[0]['pos'], [18.85, 19.05])
        self.assertEqual(pads[1]['pos'], [18.85, 20.95])
        self.assertEqual(pads[2]['pos'], [21.15, 20.0])

        #HEADER-2x3(header-2x3归一化)：行优先编号，1/2脚在顶行左右
        ret = self.callTool('addStandardFootprint', {'package': 'header-2x3', 'pos': [20, 20]})
        self.assertEqual(ret['pinCount'], 6)
        pads = sorted((e for e in ret['element']['subElements'] if e['type'] == 'PAD'),
            key=lambda e: int(e['name']))
        self.assertEqual(pads[0]['pos'], [18.73, 17.46])
        self.assertEqual(pads[1]['pos'], [21.27, 17.46])
        self.assertEqual(pads[4]['pos'], [18.73, 22.54])
        self.assertEqual(pads[5]['pos'], [21.27, 22.54])

        #HEADER-1X04(前导0归一化)：单列垂直排布，引脚1在顶部
        ret = self.callTool('addStandardFootprint', {'package': 'HEADER-1X04', 'pos': [20, 20]})
        pads = sorted((e for e in ret['element']['subElements'] if e['type'] == 'PAD'),
            key=lambda e: int(e['name']))
        self.assertEqual([p['pos'] for p in pads],
            [[20.0, 16.19], [20.0, 18.73], [20.0, 21.27], [20.0, 23.81]])

        #带旋转：0402旋转90度后焊盘变纵向排布，自身rotation=90
        ret = self.callTool('addStandardFootprint', {'package': '0402', 'pos': [10, 10], 'rotation': 90})
        pads = sorted((e for e in ret['element']['subElements'] if e['type'] == 'SMDPAD'),
            key=lambda e: e['pos'][1])
        self.assertEqual(pads[0]['pos'], [10.0, 9.45])
        self.assertEqual(pads[1]['pos'], [10.0, 10.55])
        self.assertEqual(pads[0]['rotation'], 90)

        #非法封装名或缺pos必须报错
        self.callTool('addStandardFootprint', {'package': 'QFN-32', 'pos': [0, 0]}, expectError=True)
        self.callTool('addStandardFootprint', {'package': 'SOIC-20', 'pos': [0, 0]}, expectError=True)
        self.callTool('addStandardFootprint', {'package': 'HEADER-1x25', 'pos': [0, 0]}, expectError=True)
        self.callTool('addStandardFootprint', {'package': '0603'}, expectError=True)

    #测试：SVG导出(含文本渲染与XML转义)
    def testExportSvg(self):
        self.doInitialize()
        self.callTool('addText', {'layer': 2, 'pos': [10, 2], 'text': 'SVG&<T>', 'height': 1.5})
        tmpDir = tempfile.mkdtemp(prefix='sprintfont_mcp_test_')
        try:
            svgPath = os.path.join(tmpDir, 'board.svg')
            ret = self.callTool('exportSvg', {'path': svgPath})
            self.assertTrue(ret['saved'])
            self.assertTrue(os.path.isfile(svgPath))
            with open(svgPath, 'r', encoding='utf-8') as f:
                content = f.read()
            self.assertIn('<svg', content)
            self.assertIn('<text', content)
            self.assertIn('SVG&amp;&lt;T&gt;', content)

            #只导出F.Cu层时不应包含S1层的文本
            ret = self.callTool('exportSvg', {'path': os.path.join(tmpDir, 'l1.svg'),
                'layers': ['F.Cu'], 'returnText': True})
            self.assertNotIn('<text', ret['svg'])
            self.assertIn('viewBox', ret['svg'])

            #缺少path必须报错
            self.callTool('exportSvg', {}, expectError=True)
        finally:
            shutil.rmtree(tmpDir, ignore_errors=True)

    #测试：initialize携带过期/非法会话头时必须正常握手(客户端重连或代理转发残留头的场景)
    def testInitializeWithStaleSessionId(self):
        status, headers, resp = postRpc(self.port, {
            'jsonrpc': '2.0', 'id': 1, 'method': 'initialize',
            'params': {'protocolVersion': '2025-03-26', 'capabilities': {},
                'clientInfo': {'name': 'unittest', 'version': '0'}}}, sessionId='stale-or-expired-session')
        self.assertEqual(status, 200)
        self.assertEqual(resp['result']['protocolVersion'], '2025-03-26')
        self.assertTrue(headers.get('Mcp-Session-Id'))

    #测试：2024-11-05是HTTP+SSE双端点传输，服务器未实现，协商时必须回退到所支持的最高版本
    def testInitializeVersionFallback(self):
        status, headers, resp = postRpc(self.port, {
            'jsonrpc': '2.0', 'id': 1, 'method': 'initialize',
            'params': {'protocolVersion': '2024-11-05',
                'capabilities': {}, 'clientInfo': {'name': 'unittest', 'version': '0'}}})
        self.assertEqual(status, 200)
        self.assertEqual(resp['result']['protocolVersion'], '2025-06-18')

    #测试：setBoardSize必须可撤销，且非法参数不能消耗撤销快照
    def testSetBoardSizeUndoable(self):
        self.doInitialize()
        self.callTool('setBoardSize', {'width': -1.0, 'height': 80.0}, expectError=True)
        self.callTool('undo', expectError=True) #Nothing to undo
        self.callTool('setBoardSize', {'width': 100.0, 'height': 80.0})
        info = self.callTool('getBoardInfo')
        self.assertEqual(info['boardSize'], {'width': 100.0, 'height': 80.0})
        self.callTool('undo')
        info = self.callTool('getBoardInfo')
        self.assertEqual(info['boardSize'], {'width': 50.0, 'height': 40.0})

    #测试：DELETE按MCP规范终止会话
    def testDeleteSessionTermination(self):
        self.doInitialize()
        #非法会话DELETE返回404
        self.assertEqual(sendMethod(self.port, 'DELETE', sessionId='bogus'), 404)
        #有效会话DELETE返回204并注销会话
        self.assertEqual(sendMethod(self.port, 'DELETE', sessionId=self.sessionId), 204)
        status, _, _ = postRpc(self.port, {'jsonrpc': '2.0', 'id': 3, 'method': 'ping'}, sessionId=self.sessionId)
        self.assertEqual(status, 404)

    #测试：updateElements修改元件/组的layer必须被安全忽略而不是崩溃
    def testUpdateLayerOnComponentAndGroup(self):
        self.doInitialize()
        ret = self.callTool('addComponent', {'idText': 'R2',
            'smdPads': [{'layer': 1, 'pos': [30, 10], 'sizeX': 1.0, 'sizeY': 0.6}]})
        compIdx = ret['index']
        #元件的layer由焊盘推导(只读)，layer修改被忽略但同批其它属性照常生效
        ret = self.callTool('updateElements', {'indices': [compIdx], 'layer': 'C2', 'package': 'R0402'})
        self.assertEqual(ret['updated'], 1)
        self.assertEqual(ret['elements'][0].get('package'), 'R0402')

        #组的layer修改同样被忽略
        ret = self.callTool('addTrack', {'layer': 1, 'width': 0.3, 'points': [[1, 30], [2, 30]]})
        ret = self.callTool('groupElements', {'indices': [ret['index']]})
        ret = self.callTool('updateElements', {'indices': [ret['index']], 'layer': 'S2'})
        self.assertEqual(ret['updated'], 0)

    #测试：元件平移时显式指定坐标的位号/值标签必须跟随移动
    def testComponentLabelMoveWithOffset(self):
        comp = SprintComponent()
        comp.idText.text = 'R1'
        comp.idText.pos = (3.0, 4.0) #显式指定位号坐标
        comp.valueText.text = '10k'
        comp.valueText.pos = (3.0, 5.0)
        pad = SprintPad(padType='SMDPAD', layerIdx=1)
        pad.pos = (10.0, 10.0)
        pad.size = 1.0
        comp.add(pad)
        comp.moveByOffset(1.5, -2.0)
        self.assertEqual(pad.pos, (11.5, 8.0))
        self.assertEqual(comp.idText.pos, (4.5, 2.0))
        self.assertEqual(comp.valueText.pos, (4.5, 3.0))

        #未指定坐标(0,0)的标签保持(0,0)，由序列化时自动放置在元件上方
        comp2 = SprintComponent()
        comp2.idText.text = 'C1'
        pad2 = SprintPad(padType='SMDPAD', layerIdx=1)
        pad2.pos = (5.0, 5.0)
        pad2.size = 1.0
        comp2.add(pad2)
        comp2.moveByOffset(1.0, 1.0)
        self.assertEqual(comp2.idText.pos, (0, 0))

    #测试：CLEAR=0(十字焊盘与铺铜直连)序列化时不能被丢弃
    def testPadClearanceZeroRoundTrip(self):
        self.doInitialize()
        ret = self.callTool('addPad', {'layer': 1, 'pos': [20, 20], 'size': 1.2, 'drill': 0.6, 'clearance': 0})
        self.assertEqual(ret['element']['clearance'], 0)
        exported = self.callTool('exportTextIo')
        self.assertIn('CLEAR=0', exported['text'])

    #测试：删除同规格元素时不能误删其它相等元素(list.remove按==匹配的坑)
    def testDeleteAmongIdenticalElements(self):
        self.doInitialize()
        #板上已有同规格焊盘(index 1)，新加的焊盘仅名字不同(SprintPad.__eq__忽略名字)
        ret = self.callTool('addPad', {'layer': 1, 'pos': [5, 5], 'size': 1.0, 'drill': 0.5, 'name': 'CLONE'})
        cloneIdx = ret['index']
        self.callTool('deleteElements', {'indices': [cloneIdx]})
        elems = self.callTool('getElements', {'type': 'PAD'})
        self.assertEqual(elems['total'], 1)
        #留下的是原焊盘(无名字)，而不是CLONE
        self.assertEqual(elems['elements'][0].get('name', ''), '')

        #容器remove必须按身份删除：两个相等的track，删除第二个，留下第一个
        t1 = SprintTrack(1, 0.3)
        t1.addPoint(1, 1)
        t1.addPoint(2, 2)
        t2 = SprintTrack(1, 0.3)
        t2.addPoint(1, 1)
        t2.addPoint(2, 2)
        board = SprintTextIO(50, 40)
        board.add(t1)
        board.add(t2)
        self.assertTrue(board.remove(t2))
        self.assertIs(board.elements[0], t1)

    #测试：图元layerIdx非int时getBoardInfo不能崩溃
    def testBoardInfoWithInvalidLayerIdx(self):
        self.doInitialize()
        bad = SprintTrack(None, 0.3) #模拟layerIdx无效的图元
        bad.addPoint(1, 1)
        bad.addPoint(2, 2)
        self.textIo.add(bad)
        info = self.callTool('getBoardInfo')
        self.assertEqual(info['countByType'].get('TRACK'), 2)
        for layer in info['layersInUse']:
            self.assertIsInstance(layer, int)

    #测试：重复索引必须去重，避免移动翻倍/组内重复添加
    def testDuplicateIndicesDeduplicated(self):
        self.doInitialize()
        ret = self.callTool('addText', {'layer': 2, 'pos': [10, 10], 'text': 'DUP', 'height': 1.0})
        textIdx = ret['index']
        #重复索引只移动一次
        self.callTool('moveElements', {'indices': [textIdx, textIdx], 'dx': 1.0, 'dy': 0.0})
        elems = self.callTool('getElements', {'type': 'TEXT'})
        self.assertEqual(elems['elements'][0]['pos'], [11.0, 10.0])
        #编组时重复索引不会把同一对象加入组两次
        ret = self.callTool('groupElements', {'indices': [textIdx, textIdx]})
        self.assertEqual(ret['grouped'], 1)
        elems = self.callTool('getElements', {'type': 'GROUP'})
        self.assertEqual(elems['elements'][0]['elementCount'], 1)

    #测试：updateElements响应中的index必须与去重后的对象一一对应
    def testUpdateElementsResponseIndices(self):
        self.doInitialize()
        #板上index 0是TRACK(仅width生效)，index 1是PAD(仅size生效)
        ret = self.callTool('updateElements', {'indices': [0, 0, 1], 'width': 0.4, 'size': 1.2})
        self.assertEqual(ret['updated'], 2)
        self.assertEqual([e['index'] for e in ret['elements']], [0, 1])
        self.assertEqual(ret['elements'][0]['type'], 'TRACK')
        self.assertEqual(ret['elements'][1]['type'], 'PAD')

    #测试：ZONE/CIRCLE线宽不允许负数
    def testNegativeWidthRejected(self):
        self.doInitialize()
        self.callTool('addZone', {'layer': 1, 'width': -0.2,
            'points': [[0, 35], [10, 35], [10, 40], [0, 40]]}, expectError=True)
        self.callTool('addCircle', {'layer': 1, 'center': [25, 20], 'radius': 5, 'width': -0.2}, expectError=True)
        #0线宽是合法的
        ret = self.callTool('addCircle', {'layer': 1, 'center': [25, 20], 'radius': 5, 'width': 0})
        self.assertEqual(ret['element']['width'], 0)

    #测试：按层导出/保存时组与元件内的目标层元素不能漏掉
    def testExportLayerIncludesGroupsAndComponents(self):
        self.doInitialize()
        #加一条C2导线并编组
        ret = self.callTool('addTrack', {'layer': 3, 'width': 0.3, 'points': [[20, 20], [30, 20]]})
        ret = self.callTool('groupElements', {'indices': [ret['index']]})
        #加一个C1贴片元件
        ret = self.callTool('addComponent', {'idText': 'U1',
            'smdPads': [{'layer': 1, 'pos': [40, 10], 'sizeX': 1.0, 'sizeY': 0.5}]})

        #导出C2层：必须包含组及其内部导线
        exported = self.callTool('exportTextIo', {'layer': 'C2'})
        self.assertIn('GROUP;', exported['text'])
        self.assertIn('TRACK,LAYER=3', exported['text'])
        #导出C1层：必须包含元件
        exported = self.callTool('exportTextIo', {'layer': 'C1'})
        self.assertIn('BEGIN_COMPONENT', exported['text'])
        self.assertIn('SMDPAD,LAYER=1', exported['text'])

        #saveTextIoFile同样不能漏掉组
        tmpDir = tempfile.mkdtemp(prefix='sprintfont_mcp_test_')
        try:
            path = os.path.join(tmpDir, 'c2.txt')
            self.callTool('saveTextIoFile', {'path': path, 'layer': 'C2'})
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            self.assertIn('GROUP;', content)
            self.assertIn('TRACK,LAYER=3', content)
        finally:
            shutil.rmtree(tmpDir, ignore_errors=True)

    #测试：文本类字段入口消毒(add/update一致)与换行防护，序列化不得产生断行记录
    def testTextSanitize(self):
        self.doInitialize()
        #addText: 非法字符与换行统一替换为下划线
        ret = self.callTool('addText', {'layer': 2, 'pos': [10, 2], 'text': 'A;B,C\nD\rE', 'height': 1.5})
        elems = self.callTool('getElements', {'type': 'TEXT'})
        self.assertEqual(elems['elements'][0]['text'], 'A_B_C_D_E')
        #导出的Text-IO文本记录必须保持单行完整
        exported = self.callTool('exportTextIo')
        self.assertIn('TEXT=|A_B_C_D_E|;', exported['text'])

        #updateElements的text/name消毒，与add入口一致
        textIdx = ret['index']
        ret = self.callTool('updateElements', {'indices': [textIdx], 'text': 'X;Y', 'name': 'N,1'})
        self.assertEqual(ret['elements'][0]['text'], 'X_Y')
        self.assertEqual(ret['elements'][0]['name'], 'N_1')

        #addComponent的comment/package/idText消毒
        ret = self.callTool('addComponent', {'comment': 'C;1', 'package': 'P,2', 'idText': 'R;1',
            'smdPads': [{'layer': 1, 'pos': [30, 10], 'sizeX': 1.0, 'sizeY': 0.6}]})
        comp = self.server.textIo.elements[ret['index']]
        self.assertEqual(comp.comment, 'C_1')
        self.assertEqual(comp.package, 'P_2')
        self.assertEqual(comp.idText.text, 'R_1')

        #序列化兜底：直接构造含换行的文本元素(绕过MCP入口)，str()输出仍是单行
        t = SprintText()
        t.text = 'L1\nL2'
        t.height = 1.0
        out = str(t)
        self.assertNotIn('\n', out)
        self.assertIn('TEXT=|L1_L2|;', out)

    #测试：bbox守卫必须覆盖全部四个坐标，任一坐标非有限都不得进入JSON输出
    def testBboxGuardCoversAllCoords(self):
        def makeText():
            t = SprintText()
            t.height = 1.0
            #初始外框为正负无穷，updateBbox一次后得到有限外框[4,4,6,6]
            t.updateBbox(5, 5, 1)
            return t

        self.assertEqual(elementToDict(makeText(), 0)['bbox'], [4.0, 4.0, 6.0, 6.0])
        for attr in ('xMin', 'yMin', 'xMax', 'yMax'):
            for badValue in (float('nan'), float('inf')):
                elem = makeText()
                setattr(elem, attr, badValue)
                self.assertNotIn('bbox', elementToDict(elem, 0),
                    'bbox must be omitted when {}.{} is non-finite'.format(attr, badValue))

        #board级外框同样必须四值全查
        self.server.textIo.xMax = float('nan')
        self.doInitialize()
        info = self.callTool('getBoardInfo')
        self.assertNotIn('bbox', info)

    #测试：insert_new增量按计数(multiset)判同——原位复制出的完全相同元素也必须计入新增
    def testGetNewElementsSinceMultiset(self):
        snapshot = [str(elem) for elem in self.server.textIo.elements]
        #原位复制一个焊盘，其序列化与已有元素完全相同
        cloned = copy.deepcopy(self.server.textIo.getPads()[0])
        self.server.textIo.add(cloned)
        newElems = self.server.getNewElementsSince(snapshot)
        self.assertEqual(len(newElems), 1)
        self.assertIs(newElems[0], cloned)
        #与当前板图完全一致的快照不应产生任何增量
        self.assertEqual(self.server.getNewElementsSince(
            [str(elem) for elem in self.server.textIo.elements]), [])


if __name__ == '__main__':
    unittest.main(verbosity=2)
