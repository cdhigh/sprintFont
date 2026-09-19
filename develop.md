# 开发过程注意事项

## Python版本
需要Python 3.6及以上

## 依赖
1. qrcode
2. fonttools
3. packaging
4. cx_freeze: 如果需要打包的话

## MCP服务器的测试步骤
```bash
#step 1
curl -s -i -X POST http://127.0.0.1:5380/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"curl-test","version":"1.0"}}}'

#step 2
curl -s -i -X POST http://127.0.0.1:5380/mcp \
  -H "Content-Type: application/json" \
  -H "Mcp-Session-Id: ID from step 1" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'

#step 3
curl -s -X POST http://127.0.0.1:5380/mcp \
  -H "Content-Type: application/json" \
  -H "Mcp-Session-Id: ID from step 1" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/list"}'

#step 4
curl -s -X POST http://127.0.0.1:5380/mcp \
  -H "Content-Type: application/json" \
  -H "Mcp-Session-Id: ID from step 1" \
  -d '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"getBoardInfo","arguments":{}}}'


```

## 其他问题
* 如果frm窗体文件使用VB打开后是模块，而不是窗体，则可以使用Uedit或其他文本编辑器将Unix回车更改DOS回车换行
* 初始化rtk为antigravity,在项目目录执行: `rtk init --agent antigravity`
* 或者使用全局RTK
  1. 新建`C:\Users\name\.claude`, 执行`rtk init -g`, 拷贝`RTK.md`到`C:\Users\name\.rtk`.
  2. 在`C:\Users\name\.gemini\GEMINI.md`里面添加一行`@C:\Users\name\.rtk\RTK.md`
  

