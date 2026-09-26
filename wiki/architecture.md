# architecture.md — 系统架构和模块关系

> 本文件由 AI Agent 自动维护。最后更新：2026-09-12

## 1. 系统分层

```
ui/sprint_font_ui.py  ← Vb6Tkinter 从 ui/main.frm 生成的界面骨架（Application_ui + Statusbar + Tooltip）
        │
sprintFont.py :: Application  ← 唯一业务主类，9 个 Tab 的逻辑全在此，
        │                       tabStrip_NotebookTabChanged 按 Tab 索引分发
        ├─ app/config_manager.py         配置读写 + gettext 国际化
        ├─ app/font_operations.py        字体扫描 + 文本→多边形
        ├─ app/footprint_svg_handler.py  封装/SVG/二维码导入分流
        ├─ app/autorouter_handler.py     DSN 导出 / SES 导入
        ├─ app/pcb_enhancements.py       泪滴 / 弧形走线 / 批量修改
        ├─ conversion/*                  外部格式互转（KiCad/立创/SVG/OpenSCAD/网表）
        └─ sprint_struct/*               PCB 数据模型 + 核心算法
                │
utils/*  公共底层：comm_utils(几何函数库) / vector2d / version_check / widget_right_click
```

- app/ 下各 handler 互不依赖，均为"主程序组装参数 → 单个 handler 执行 → 返回 TextIO/字符串"的单向委托。
- 公共底座是 `sprint_struct`（数据模型）和 `utils/comm_utils`（几何/类型转换）。

## 2. Sprint-Layout 插件协议（核心机制）

Sprint-Layout 通过"命令行参数 + 临时文本文件 + 进程退出码"三件套与插件通讯：

- **输入**：`argv[1]` = Sprint-Layout 生成的临时文件，内容为选中元素的"文本设计格式"导出；`/W:` `/H:` = 板宽高（0.1µm，÷10000 → mm）；`/A` = 整板导出。**只有整板导出（未选中任何元素）才允许 DSN/SES 自动布线功能**。
- **输出**：结果以 UTF-8 写到"输入文件名 + `_out` 后缀"的文件。
- **退出码**（sprintFont.py:68-78）：0=中止；1=完全替换所选元素；2=绝对添加；3=相对替换（新元素粘鼠标）；4=相对添加（粘鼠标）。生成类功能用 4，泪滴添加用 2，删除/替换类用 1。
- 无命令行参数 = Standalone 模式，大部分按钮禁用，可用"另存为"导出文本再由 Sprint-Layout 的"导入：文本设计格式文件"手动导入。
- 输入文件在写输出前会备份到 `%APPDATA%\Roaming\sprintFont\backup_*.txt`（默认保留 5 份）。

## 3. 核心数据模型（sprint_struct/）

- 顶层容器 `SprintTextIO`：元素列表 + 增删/按层按类型查询/焊盘元件归类（`categorizePads`/`categorizeComponents`，用 `hash(str(序列化))` 判同）/`mergeConnectedTracks`（合并首尾相连走线，端点落在焊盘/覆铜内或有名字的不合并）。
- 元素类：`SprintTrack`（折线导线）、`SprintPad`（通孔 PAD / 贴片 SMDPAD，FORM 1-9 形状常量）、`SprintPolygon`（类型码 ZONE，覆铜/禁止区，`encircle` 射线法判含）、`SprintText`、`SprintCircle`（圆/圆弧，SVG 圆弧参数与 Sprint 逆时针约定的换算在 comm_utils.svgArcToCenterParam）、`SprintGroup`（GROUP/END_GROUP）、`SprintComponent`（元件，layerIdx 是由焊盘层推断的计算属性）。
- **"文本设计格式"**：一行一个元素 `TYPE,key=value,...;`，字符串值用 `|...|` 包裹（如 `NAME=|R1|`），坐标为 0.1µm 整数。类型码：TRACK / PAD / SMDPAD / ZONE / TEXT / CIRCLE / GROUP / BEGIN_COMPONENT（内含 ID_TEXT/VALUE_TEXT）等。读入 `sprint_textio_parser.py`（按类型码 handler 字典分发），写出为各元素类的 `__str__`。
- 板层常量（sprint_element.py）：1=C1 正面铜、2=S1 正面丝印、3=C2 背面铜、4=S2 背面丝印、5=I1、6=I2 内层铜、7=U 板框；含与 KiCad 层名的双向映射。
- **单位铁律**：内部一律 mm 浮点，仅序列化时 ×10000 转 0.1µm 整数。角度单位不统一是格式固有坑（见 pitfalls.md）。
- **Y 轴**：Sprint 原点左下 Y 向上；KiCad/SVG/freerouting 原点左上 Y 向下，格式转换时 Y 取负。
- 文件编码：读入按 latin-1 → utf-8 → locale 回退（实际 latin-1 永不失败，见 pitfalls.md）。

## 4. 关键流程

- **自动布线**（三步，借道开源 Freerouting）：
  `AutorouterHandler.exportDsn` → `SprintExportDsn.export()` 写 .dsn（同时把整个 exporter 实例 **pickle** 到同名 .pickle，SES 导入时必需）→ 用户在 Freerouting 布线并导出 .ses → `importSes` 反序列化 pickle 恢复原始板图状态 → `SprintImportSes` 解析 .ses，按 trimRatsnestMode（删已布线飞线/删全部/保留全部）或 trackOnly（仅导走线并粘鼠标）重建板图。
  DSN 限制：仅 F.Cu/B.Cu 两层、元件限正面且名字唯一、U 层最大封闭元素为板框其余变 keepout。
- **字体文本**：fontTools 读 ttf/otf/ttc/otc 字形 → `font_to_polygon.singleWordPolygon` 按平滑度拍平成多边形（Y 翻转 + 背面水平镜像 + 内孔 devour 合并）→ 装入 SprintTextIO；负像背景由 `FontOperations.invertFontBackground` 生成镂空外框。
- **封装导入**：`.kicad_mod` → kicad_pcb 解析（v5/v6），遇 v7/v8 抛 FootPrint8NotSupported 降级 kicad_pcb8；立创封装 → 在线 API（商城编号→uuid→JSON）或本地 json → `LcComponent` 按 shape 类型（TRACK/PAD/ARC/CIRCLE/VIA/RECT）分发解析。
- **导出网表**（v1.9）：`NetlistBuilder` 用并查集对铜层（C1/C2/I1/I2）元素做几何相交判定（过孔连通两面，公差 0.01mm）提取连通性 → Kicad/Lceda 导出器给走线/焊盘标注 net 号。
- **导出**：KicadGenerator 输出完整 `(kicad_pcb ...)` 板文件；LcedaGenerator 输出 EasyEDA JSON；OpenSCADGenerator（merged/layered 两模式）；SVGGenerator；DXFGenerator（输出标准 AC1015/AutoCAD 2000 DXF，纯标准库无外部依赖，支持焊盘/钻孔/走线/圆弧/多边形/文本）。
- **泪滴/弧线/差分线**：`sprint_struct/teardrop.py`（切线几何+贝塞尔拟合）、`rounded_track.py`（切线内切圆/三点圆/贝塞尔三种）、`wire_pair_tuner.py`（独立 Toplevel 窗口，蛇形线振幅反解 + 40 轮二分查找消除长度残差）。

## 5. 双 KiCad 解析器决策

- `kicad_pcb/`（2022-04 版，源自 KiCad 官方 kicad-library-utils）：支持 v5/v6 封装，**主解析器**；DSN/SES 导出导入也只用它的 sexpr 模块。
- `kicad_pcb8/`（2024-03 版 fork）：支持 v7/v8，无 __init__.py，仅被 `conversion/kicad_to_sprint.py` 作为 fallback import。
- 切换机制：kicad_to_sprint.py 先试 kicad_pcb.KicadMod，捕获 FootPrint8NotSupported 后降级 KicadMod8。

## 6. MCP服务器（app/mcp_server.py，2026-09-12新增）

在插件运行期间内嵌一个本地HTTP服务器，把完整的Sprint-Layout Text-IO接口暴露为MCP工具，供外部AI客户端（Claude/ZCode/Cursor等）读取、绘制、修改板图。

- **传输**：Streamable HTTP（协议版本 2025-06-18 / 2025-03-26），纯标准库 `http.server.ThreadingHTTPServer` + 守护线程实现（官方MCP SDK要求Python 3.10+，本项目是3.8+cx_Freeze）。端点 `http://127.0.0.1:<port>/mcp`（默认5380，只绑定回环地址，带Host头校验防DNS重绑定）。响应固定用 application/json 单响应（不用SSE长连接，GET一律405，规范允许）。**2026-09-13决策：不声明、也不实现 2024-11-05**——该版本的传输是HTTP+SSE双端点（GET建立SSE流+endpoint事件，POST回202、响应走SSE推送），与Streamable HTTP不兼容；客户端请求该版本时按规范回退到所支持的最高版本(2025-06-18)，由客户端决定接受或断开。initialize 时签发 Mcp-Session-Id，客户端不带会话头按无状态兼容。会话校验在解析出请求方法后进行、`initialize` 跳过校验（2026-09-13修复：原先在解析前校验，代理转发残留会话头会导致握手被404拒绝）；DELETE 请求按 2025-03-26 规范注销会话并返回204（此前返回405导致标准客户端退出报错）。
- **共享板图**：`Application.initMcpBoard()` 把输入临时文件解析为 `SprintTextIO`（Standalone模式为空板），`SprintMcpServer.textIo` 持有；所有工具调用在 `RLock` 内执行，修改性操作前自动 deepcopy 快照（30步 undo 栈）。注意 undo/importSes/importTextIo(replace) 会整体替换 `textIo` 引用，外部必须经 `mcpServer.textIo` 取当前板图。
- **工具集**（35个）：查询 getBoardInfo(getElements 之外还返回 rules 设计规则：trackWidth/viaDiameter/viaDrill/clearance/smdSmdClearance，LLM手工布线的依据)/getElements(分页+类型/层过滤，回显全部模型字段；2026-09-13增强：depth=0只返回元件/组概要不展开子元素(大板省Token)、indices=[..]直查指定索引详情(忽略其它过滤)、bbox=[xMin,yMin,xMax,yMax]包围盒相交空间过滤(AI局部布线/摆件前查障碍物)，bbox判断用模块级 elementIntersectsBbox，包围盒无效(正负无穷)的元素一律排除)/getNetlist（调 conversion/netlist_builder 提取铜层连通性——**物理接触语义、网络自动编号 Net-N，不是设计意图**，元件子标签"a.b"与 getElements 的 subElements 枚举一致，2026-09-12修复错位bug）/checkDrc（调 conversion/drc_checker：同层**不同网络**元素的间距违规+线宽不足+可选孤立焊盘清单，同网络的有意连接不算违规，违规按严重度排序并带元素标签/实际间隙/要求值/位置，LLM布线后自检用）；绘制 addTrack/addPad/addSmdPad/addZone/addText/addCircle/addComponent（元件=焊盘+丝印+标签打包，addPad 支持热焊盘辐条参数；焊盘name字段是自由标签，不参与网络命名）/batchAdd(2026-09-13新增：一次调用传 tracks/pads/smdPads/zones/texts/circles spec数组批量添加，减少总线布线时的HTTP+LLM往返；**原子化**——先全部构建校验，任一spec非法则整体报错不落板且不消耗撤销快照；整批只占一步undo；返回连续的 indexes 列表，顺序固定为tracks→pads→smdPads→zones→texts→circles、各数组内保持传入顺序)/addStandardFootprint(2026-09-13新增，2026-09-25丝印外框避让修正：参数化标准封装生成器，支持0402/0603/0805/1206、SOIC-8/14/16(1.27)、DIP-8/14/16(2.54,排距7.62)、SOT-23、HEADER-1xN/2xN(2.54,N=1-20)；丝印外框调整至焊盘外侧，避免油墨覆盖铜皮影响可焊性)/importFootprint(2026-09-25新增：支持立创EDA部件号在线解析、本地EasyEDA JSON及KiCad .kicad_mod封装文件导入并支持坐标与旋转)/connectPads(2026-09-25新增：在焊盘间定义飞线/预拉线ratsnest连接或断开，直接打通Freerouting DSN网表提取)；编辑 deleteElements/moveElements/rotateElements/mirrorElements(2026-09-13新增：几何变换走 sprint_struct 各元素类的 rotateBy(angle,cx,cy)/mirrorHorzBy(cx)/mirrorVertBy(cy)方法，工具层只做参数解析与undo快照；rotateElements 任意角、顺时针为正、center缺省=选区外框几何中心；mirrorElements axis='x'水平翻转/axis='y'垂直翻转、绕选区外框中心线、文本字形镜像标志取反+旋转角取反(镜像逆反转方向)、圆弧角度按逆时针为正的存储约定重映射；元件(0,0)自动放置的位号/值标签保持不动、显式坐标的跟随变换；角度方向坑见 pitfalls.md 2026-09-13 pointAfterRotated条目)/groupElements/updateElements(2026-09-12新增：原地改属性免删建，属性清单由 UPDATE_ELEMENT_PROPS 常量统一定义，类型专属属性只应用到匹配元素，2026-09-25支持padId/connectsTo)/undo/clearBoard(2026-09-25正式注册)/setBoardSize(2026-09-25正式注册)；PCB工艺及走线修整 addTeardrops/removeTeardrops(2026-09-25新增：基于sprint_struct.teardrop生成/清理铜皮与焊盘接合处的泪滴)/roundTracks(2026-09-25新增：基于sprint_struct.rounded_track对直角/折线走线进行切线弧或贝塞尔圆角平滑)；导入导出 importTextIo/exportTextIo/exportSvg(2026-09-12新增：调 conversion/sprint_to_svg 出SVG矢量图供视觉验证，含近似文本渲染，可选 returnText 内联返回)/loadTextIoFile/saveTextIoFile；外部自动布线交接 exportDsn/importSes（直接调 SprintExportDsn/SprintImportSes，绕开带Tk弹窗的 AutorouterHandler，DSN/pickle 文件写出逻辑与 AutorouterHandler 相同；自动布线器只能人工操作，MCP描述不引导LLM去运行它）；回写 applyToSprintLayout。
- **回写Sprint-Layout**：MCP线程不碰Tk——applyToSprintLayout 或 Export页"Apply to Sprint-Layout"按钮只置 `mcpExitRequest` 标志，主线程 `pollMcpEvents`(500ms轮询) 执行 `applyMcpBoard`：**2026-09-25三层智能回写防护**：
  1) **未修改**：若 `isBoardModified()` 判定板图尺寸与图元内容相对启动时未发生任何变动，不写输出文件，直接以退出码0(`RETURN_CODE_NONE`)安全退出，Sprint-Layout原板100%保持原生状态；
  2) **纯新增图元**：若 `isPureAddition()` 判定原板旧图元完全未动、仅在末尾追加新图元（如绘制新封装/芯片/丝印），`mode='auto'` 自动降级为 `insert_new`，仅将新增的图元写入输出文件，并以退出码2(`RETURN_CODE_INSERT_ALL`)追加，彻底杜绝整板重新序列化对原板带来的潜在风险；
  3) **破坏性修改**：若旧图元发生过修改/移动/删除（如加泪滴/平滑圆角/删改器件走线），整板启动时以退出码1(`RETURN_CODE_REPLACE_ALL`)整板替换；部分选择启动时走 `insert_new`。
  Standalone 模式禁止回写（saveTextIoFile 后手动导入）。
- **UI**：MCP的端口在**设置对话框**中配置（状态栏齿轮打开），服务器由对话框中的 "Start MCP Server" 按钮手动启动；配置键 mcpPort 存放在 `initMcpBoard()` 创建的无控件变量 mcpPortVar 中。
- **生命周期（2026-09-12定稿）**：MCP**不自动启动**、无 mcpEnabled 配置项——用户打开设置对话框点击 **"Start MCP Server"按钮** 手动启动（同步加载板图+开服，成功后对话框关闭并弹出模态状态窗口，端口写入配置），**服务器仅在模态状态窗口显示期间运行**（窗口的接受/取消都会退出整个插件，因此无需独立的停止入口）；状态栏不再轮播MCP状态（STABAR_INFO_MCP槽位已移除）。mcpEnabledVar 已删除，仅保留 mcpPort 配置键。
- **交互模型（2026-09-12定稿，2026-09-25增强）**：MCP一旦启动成功就弹出**模态状态窗口**（app/mcp_status_window.py，McpStatusWindow）。窗口显示服务器状态/连接地址（点击复制）+ **LLM交互概要日志**（mcp_server 的 addLogEntry/drainLogEntries 线程安全日志：连接、每次工具调用的名称/ok或error/耗时/参数摘要，上限500条，窗口300ms轮询增量显示）。底部两个按钮：**接受** = `cmdAccept`（初始或无修改时禁用置灰不可点击，300ms轮询检测到发生实质修改后才点亮启用；点击后纯新增以退出码2追加，改动旧图元以退出码1替换）；**取消** = `cmdCancel`（未修改直接以0退出免弹窗提示；发生修改后弹窗确认后以0退出放弃修改）。Standalone模式接受按钮禁用。
- **坐标系（MCP工具参数）**：与 Text-IO 文件格式及内部模型一致——原点左上、X右Y下、mm；焊盘/文本旋转顺时针为正；圆弧起止角0°在3点钟方向、逆时针为正。

## 7. 设置对话框（app/settings_dialog1.py，2026-09-12新增）

- **设计**：由 Vb6Tkinter 可视化设计（`ui/frmSettings.frm`）生成 `SettingsDialog_ui` 骨架（app/settings_dialog1.py），业务逻辑写在同文件手写的 `SettingsDialog` 子类中——与主界面"生成/手写分离"同一工作流。
- **入口**：状态栏最右侧齿轮图标（tkinter.Label，`pack(side=RIGHT, before=填充Label)` 插入）。曾实现过Windows系统菜单入口（ctypes挂钩窗口过程），因稳定性考虑已移除，只保留齿轮（用户决策 2026-09-12，技术要点留档见 pitfalls.md）。
- **模态对话框**：界面语种（第一项 **Auto=配置中写空字符串**，运行时跟随系统语言；指定语种保存后**重启插件生效**——UI文案在控件创建时固化，动态下拉列表不随 retranslateUi 翻译，运行时切换会残留旧语言）、MCP 使能/端口（LabelFrame组）、立创EDA节点(auto/cn/global)、更新检查频率(0/7/30/90天)；`lblMcpEndPoint` 单击/双击复制 MCP 连接地址到剪贴板。
- **值语义**："打开时读入、点Ok才统一写回"——对话框控件绑定自己的变量（txtMcpPortVar），restoreValues 从应用变量填入，cmdSettingsOk_Cmd 统一写回 `app.mcpPortVar` 并保存配置；"Start MCP Server"按钮走 cmdMcpStart_Cmd（写端口→startMcpServer→成功后关闭对话框）；Cancel 直接销毁无需还原逻辑。
- **MCP启停的唯一入口**是 `Application.applyMcpSettings()`：按变量当前值启动/停止/重启服务器（端口未变且在运行时不动作），启动失败弹窗提示（程序启动时的自动开启为静默模式，只写状态栏）。
- 共享 StringVar 上注册的 trace_add 在对话框销毁时必须 trace_remove；本对话框的 txtMcpPortVar 由对话框自持、trace 回调也属对话框，随销毁一起释放（教训见 pitfalls.md）。

## 8. 架构决策记录（日期 + 结论 + 原因）

- 2026-09-25: MCP回写增加纯新增图元自动识别与安全追加(isPureAddition)——当AI仅绘制新封装/放置器件而未修改原板任何旧图元时，mode='auto'自动降级为insert_new，临时输出文件仅写入新增图元并返回退出码2(RETURN_CODE_INSERT_ALL)，彻底避免整板重写对原板带来的潜在风险。
- 2026-09-25: MCP回写增加双层未修改防护(isBoardModified)——无修改时点击Accept或调用applyToSprintLayout不写输出文件并直接以退出码0(RETURN_CODE_NONE)安全退出，确保Sprint-Layout原板100%不受反向序列化影响；同时未修改时点击Cancel/按Esc/关窗直接退出，免去二次确认弹窗。
- 2026-09-25: MCP服务器工具集扩展至35个，修复MCP标准兼容性并补齐PCB核心辅助工具——补充CORS暴露头与版本响应头；JSON Schema补全array类型items定义；标准阻容及IC封装外框避让焊盘以防丝印覆盖阻焊；新增connectPads(引脚网络与飞线连接，直通DSN导出)、addTeardrops/removeTeardrops(泪滴生成与清理)、roundTracks(走线圆角平滑)及importFootprint(立创/KiCad/JSON封装导入)；纯底层算法调用，避免在MCP线程中引入Tk弹窗。
- 2026-09-12: MCP服务器用纯标准库 http.server 实现而非官方 mcp SDK——运行环境是 Python 3.8 + cx_Freeze，SDK要求3.10+且引入大量依赖；Streamable HTTP 用 application/json 单响应而非SSE长连接，线程模型简单且兼容官方客户端。
- 2026-09-12: 设置对话框改为 Vb6Tkinter 可视化设计（ui/frmSettings.frm → app/settings_dialog.py 的 SettingsDialog_ui 骨架 + 手写 SettingsDialog 子类），替换最初手绘布局的版本；值语义用"打开读入/确定写回"，省去取消还原逻辑；端点标签支持点击复制到剪贴板。
- 2026-09-12: 回写Sprint-Layout的新增元素判定用"顶层元素序列化字符串比对"而非引入元素ID——Text-IO序列化是确定性的，改动最小；局限：部分选择模式下修改/移动已有元素会表现为"旧元素仍在+新元素插入"造成重复，故insert_new只推荐添加类操作，修改请用整板模式。
- 2026-09-13: 上述字符串比对细化为multiset计数判同（getNewElementsSince）——纯集合判同会漏掉"原位复制出的完全相同元素"（回写时静默丢失）；仍不采用元素ID，因为undo/importSes/importTextIo(replace)会整体替换textIo引用、id全变会把整板误判为新增。同日：整板replace回写增加前提"输入板图解析成功"——解析失败时 applyMcpBoard 强制降级insert_new，MCP侧 getBoardInfo.applyMode 同步改报、toolApplyToSprintLayout 对显式replace报错（详见pitfalls.md）。
- 2026-09-12: exportDsn/importSes 在 MCP 中直接调用 sprint_struct 底层类而不复用 AutorouterHandler——后者硬编码 tkinter.messagebox 弹窗，不能在HTTP线程中调用。
- 2026-09-12: 语种切换采用"保存后重启生效"而非运行时 retranslateUi——动态下拉列表(cmbLayerList等)与右键菜单的词条不在 retranslateUi 覆盖范围内，运行时切换会得到混合语言界面；且插件本身生命周期短，重开即生效。
- 2026-09-12: 设置入口为状态栏齿轮 + 模态设置对话框；曾实现系统菜单入口(ctypes挂钩窗口过程)，因稳定性顾虑当日移除（技术要点留档pitfalls）。Export页不放置任何MCP控件，配置集中在设置对话框。
- 2026-09-12: MCP生命周期简化定稿：取消自动启动（原"延时3s后台启动"方案废弃，连同epoch/后台线程守卫机制一并删除），改为设置对话框中"Start MCP Server"按钮手动启动；**服务器生命周期=模态状态窗口显示期间**（接受/取消都退出插件，无需停止入口）；mcpEnabled配置项与状态栏MCP状态轮播随之移除。启动路径现在完全不涉及MCP（延迟导入保留在getMcpServer，用户点启动按钮时才付出约0.6s导入+板图解析，getfqdn反向DNS坑见pitfalls）。
- 2026-09-12: MCP交互模型定稿为"模态状态窗口+接受/取消"：插件进程被Sprint-Layout挂起等待退出，MCP期间的全部产物都在插件进程内，人工点击"接受"是唯一的回写确认点（整板REPLACE_ALL），"取消"丢弃修改退出(RETURN_CODE_NONE)；交互概要日志让用户可见LLM做了什么。状态窗口为手写Toplevel(app/mcp_status_window.py)，如需Vb6Tkinter重设计可移植（同设置对话框流程）。
- 2026-09-12: MCP的工具描述与指引**不引导LLM操作自动布线器**——自动布线器(Freerouting等)只能人工操作，DSN/SES 仅作为人工交接文件保留（exportDsn/importSes 描述明确"由用户手动操作"）；同时 getBoardInfo 暴露 PcbRule 设计规则（线宽/过孔/间隙），供 LLM 手工布线时遵循，getNetlist 描述明确"物理接触语义、非设计意图、网络自动编号"，焊盘 name 描述明确"自由标签、非网络名"，避免 LLM 误解能力边界。
- 2026-09-12: checkDrc 用"先划网络再查间距"而非裸几何距离——Sprint-Layout 无网络概念，若不区分网络，每个有意的焊盘-走线搭接都会被误报为间距违规；故复用 NetlistBuilder 的物理接触连通性划分网络，只检查**同层不同网络**的元素对（不同的网络元件间距用 rule.clearance，SMD-SMD 对用 rule.smdSmdClearance），另查线宽不足与孤立焊盘（单元素网络）。局限：覆铜按实心多边形（忽略hatch）、圆不导电不参与、无过孔环宽/孔径检查、O(n²)大板慢——这些边界都写进了工具描述。

- 2026-09-11: DXF 导出采用纯 Python 生成标准 AC1015 (AutoCAD 2000) ASCII 格式——无需额外第三方依赖(ezdxf)，保证 cx_Freeze 打包体积小且最大兼容各类 CAD 软件(AutoCAD, SolidWorks, FreeCAD, Fusion360)。
- 2026-09-02: 初始整理。app/ 层是从 sprintFont.py 拆出的业务 handler（UI 与逻辑分离的重构产物），后续新功能应放进 app/ 或 conversion/，不要继续膨胀 sprintFont.py。
- 2026-09-02: DSN 导出附带 pickle 整个 exporter 实例而非单独数据文件——为了 SES 导入时能原样恢复 textIo/元件表/焊盘映射；代价是 Python 版本或类结构变化会导致旧 pickle 失效。
- 2026-09-02: 双 KiCad 解析器并存而非原地升级 kicad_pcb/——两版格式差异大，fork 降级切换改动最小。
- 2026-09-02: 元件/焊盘判同用 `hash(str(序列化))`——跨进程不稳定但单次运行内一致，且 DSN→pickle→SES 往返在同一 Python 版本内成立，属刻意取舍。
- 2026-09-02: UI 用 VB6 + Vb6Tkinter 可视化设计再生成 tkinter 代码——生成/手写分离（ui/sprint_font_ui.py 生成部分不要手改 + sprintFont.py 手写业务逻辑）。
- 2026-09-02: 字体扫描用 daemon 线程 + queue + after(500ms) 轮询异步填充下拉框——扫描全部系统字体慢，不能阻塞界面启动。

## 9. 外部交互

- 立创EDA API：中文节点 `https://lceda.cn/api/...`，国际节点 `https://easyeda.com/api/...`（由系统语言或配置项 easyEdaSite=cn/global 选择）。两步：商城编号(C+数字) → svgs 接口取 component_uuid → components 接口取封装 JSON（dataStr.shape，`~` 分隔的命令行）。urllib + 浏览器 UA/Referer 伪装，超时 5s，故意不发 Accept-Encoding 免解压。
- 版本检查：`raw.githubusercontent.com/cdhigh/sprintFontRelease` 的 version.json，默认 30 天周期，可 skipVersion 跳过。
- 运行时数据目录：`%APPDATA%\Roaming\sprintFont\`（config.json + backup_*.txt 历史备份）。
