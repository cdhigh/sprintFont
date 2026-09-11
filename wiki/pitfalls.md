# pitfalls.md — 踩坑记录与技术陷阱

> 本文件由 AI Agent 自动维护。写入格式：日期 + 简明结论 + 原因/位置。
> 改动相关模块前先扫一眼本文件，避免重复踩坑。

## 文件格式坑（Sprint-Layout 文本设计格式固有）

- 2026-09-02: 旋转角单位在不同元素上不统一——焊盘 0.01°（sprint_pad.py）、TEXT 输出 0.001°，且解析时 TEXT/ID_TEXT 单位不同，还有 `>359 则 /10` 的修正补丁（sprint_textio_parser.py:283-287）。做角度相关改动时必须逐元素核对，不能假设统一单位。
- 2026-09-02: 输入文件编码回退链 latin-1 → utf-8 → locale 中 latin-1 永不抛 UnicodeDecodeError，utf-8/locale 分支实际是死代码；utf-8 文件中的非 ASCII 字符会变 mojibake（sprint_textio_parser.py:47-58）。[待确认] 是否要改成 utf-8 优先。
- 2026-09-02: Sprint 坐标原点左下 Y 向上，KiCad/SVG/freerouting 原点左上 Y 向下——所有格式转换都要 Y 取负（sprint_export_dsn.py、sprint_import_ses.py、svg_to_polygon.py、font_to_polygon.py 各自处理）。
- 2026-09-11: DXF 导出必须默认翻转 Y 轴 (mirrorY=True)——Sprint-Layout 屏幕视图中原点在左上且 Y 向下，AutoCAD DXF 遵循标准笛卡尔坐标系（原点左下、Y 向上），若不翻转会导致导出图元在 CAD/Viewer 中上下颠倒（sprint_to_dxf.py）。
- 2026-09-02: Sprint 文本绕左下角旋转，KiCad 文本绕中心对齐旋转，且 Sprint-Layout 无法计算文本实际宽度——导入封装后文本位置可能需要手工调整（README 注2），代码不做补偿。
- 2026-09-02: 角度正方向相反——KiCad 逆时针为正，Sprint 顺时针为正（kicad_definitions.py 头部注释）；freerouting 中 PTH 与 SMD 焊盘旋转方向也相反，DSN 导出统一用 `360-rotation`（sprint_export_dsn.py:302-304）。

## 外部软件/服务坑

- 2026-09-02: 嘉立创导出画布字段名由 `CANVAS~` 变更为 `CA~`（sprint_to_lceda.py:67 已用新名）；导入侧按 `~` 切分、不依赖首字段，新旧格式均兼容。
- 2026-09-02: 立创 API 带 `?version=6.4.19.5` 参数时返回的 JSON 结构不同，需回退读 `result.packageDetail.dataStr`（lceda_to_sprint.py:252-260）。
- 2026-09-02: 立创封装坐标单位是 pixel(=10mil)，换算用 `mil2mm = 值/3.937`（lceda_to_sprint.py:63），不要按 px=25.4/96 处理。
- 2026-09-02: freerouting 的 DSN 兼容性 workaround（sprint_export_dsn.py）：image 里的 track 必须两两拆成独立 line，否则被当成封闭路径；`autoroute_settings` 段整块注释禁用——存在时 freerouting 经常报奇怪错误；等径钻孔视为开孔而非焊盘；单面焊盘在对面层加钻孔 keepout。
- 2026-09-02: SES 导入的鼠线修剪需要浮点防护：坐标 round(2) + 0.1mm 邻近阈值 + 用过孔坐标替换 track 端点，否则连通集合并不起来（sprint_import_ses.py:188-259）。
- 2026-09-02: Win10/11 下从插件返回后 Sprint-Layout 因输入法(TSF)锁死是 Sprint-Layout 自身阻塞机制的缺陷，代码无解；官方 workaround 是启动插件前切英文键盘（README 第3.8条）。

## 内部实现坑

- 2026-09-02: `.pickle` 文件是 DSN 导出时 pickle 的整个 SprintExportDsn 实例，SES 导入必需（README 明确警告勿删）；Python 版本升级或 sprint_struct 类结构变化会使旧 pickle 无法加载——改 sprint_struct 类的 `__init__`/属性时要想到这一点。
- 2026-09-02: app/pcb_enhancements.py 顶部的 `RETURN_CODE_INSERT_ALL=11 / RETURN_CODE_REPLACE_ALL=12` 是无效占位死代码，真实退出码 2/1 定义在 sprintFont.py:68-78，勿在别处复用 11/12。
- 2026-09-02: tests/test_svg_export.py 目前是坏的：调用了不存在的 `SprintTextIO.parse()`（正确入口是 SprintTextIoParser），修复前不要以此脚本报错判断 SVG 导出功能有问题。
- 2026-09-02: SprintGroup/SprintComponent/SprintTextIO 的 `__init__` 写了 `super().__init__(self)`（把实例自己当 layerIdx 传入）——潜在笔误，因 Component 重载了 layerIdx 属性、Group/TextIO 不依赖该属性才未爆发；改这几个类时留意。
- 2026-09-02: SprintPolygon.devour（内孔合并）假定多边形为凸多边形（sprint_polygon.py:163-184）——为字体空洞服务的设计，喂凹多边形结果不可靠。
- 2026-09-02: 泪滴没有专门标记，removeTeardrops 靠"多边形包含焊盘中心+走线端点且面积在焊盘面积 1/15~4 倍"的启发式识别（teardrop.py），可能误删小多边形或删不掉，故删除前有确认框。
- 2026-09-02: font_to_polygon 对"楷体_GB2312"跳过 devour 内孔合并——该字体字形不规范有重叠，正常合并流程会失败（font_to_polygon.py:182-184）。
- 2026-09-02: mergeConnectedTracks 不合并在焊盘/覆铜内的端点和有名字的 track（sprint_textio.py:298-333）——弧形走线转换依赖此前提，改动会破坏圆弧功能。
- 2026-09-02: 大量裸 `except: pass` 静默吞错（输出写出、备份、字体加载等）——插件无反应时先怀疑输出文件写出失败，可用 DEBUG_IN_FILE（sprintFont.py:43，默认注释）或 Standalone 模式排查。
- 2026-09-02: 子线程直接改 Tk 状态栏文本（版本检查线程，sprintFont.py:880-885）——靠"状态栏只在启动时写一次"规避竞争，不要推广到其他控件。
- 2026-09-02: 模态窗口(Toplevel)内 messagebox 需 `after(10)` 延迟弹出，否则卡死（wire_pair_tuner.py:90-92）。
- 2026-09-02: ttk combobox 下拉弹窗字体必须用私有命令 `tk.call("ttk::combobox::PopdownWindow", ...)` 修改（sprintFont.py:125-128）。
- 2026-09-02: 硬编码路径两处换机器必改：buildcxfreeze.bat 的 `C:\Python38`、pybabel_auto_translate.py 的 autopo 工具目录。
- 2026-09-02: 打包产物 build/exe.win32-3.8/ 内含 lib/ui/*.frm 与 i18n/，运行时按 sys.executable 定位资源（MODULE_PATH）——打包后目录结构不能拆散。
- 2026-09-02: VB6 的 .frm 文件被 VB 当成模块打开时，用文本编辑器把 Unix 换行改回 DOS 换行即可恢复（develop.md）。
