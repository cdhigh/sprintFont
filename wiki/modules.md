# modules.md — 文件职责速查表

> 本文件由 AI Agent 自动维护。最后更新：2026-09-02
> 用途：LLM 查"某功能在哪个文件"，避免为定位代码而通读整个工程。

## 根目录

| 文件 | 职责 |
|---|---|
| sprintFont.py | **主入口**（约1400行）。唯一业务主类 `Application(Application_ui)`：9 个 Tab 的事件逻辑、插件协议（输入解析/输出写出/退出码）、备份与文本历史、版本检查调度。版本号 `__Version__` 在文件头部（setup_cxfreeze.py 从这里正则提取） |
| setup_cxfreeze.py | cx_Freeze 打包脚本；include i18n/、include_msvcr、Win32GUI、app.ico |
| buildcxfreeze.bat | 一键打包（硬编码 C:\Python38，32位）；产物在 build/exe.win32-3.8/ |
| pybabel_extract.bat / pybabel_compile.bat | i18n 词条提取/编译（见 conventions.md） |
| pybabel_auto_translate.py | 调作者私有 autopo 工具 AI 机翻 po（硬编码本地路径，换机器要改） |
| requirements.txt | qrcode / fonttools / packaging / cx_freeze |
| develop.md | 开发环境注意事项（Python≥3.6、依赖、VB 窗体换行坑） |
| README.md | 用户手册（功能用法+截图+版本日志），不是开发文档 |
| app.ico | 打包图标 |

## app/ — 业务处理器（主程序与底层模块之间的中间层）

| 文件 | 职责 |
|---|---|
| config_manager.py | `ConfigManager`：config.json 读写（全字符串存储+范围钳制）、%APPDATA% 目录定位、gettext 初始化（全局 `_()`）、restoreConfig 恢复 UI 状态 |
| font_operations.py | `FontOperations`：扫描系统/用户/插件目录字体（fontTools lazy 模式，异步填充下拉框）、generatePolygons 文本→多边形、invertFontBackground 负像镂空、`\uXXXX` 符号转义 |
| footprint_svg_handler.py | `FootprintSvgHandler`：按输入分流 kicad_mod / 立创在线 ID / 立创本地 json / SVG / 二维码（qrcode 库 SvgPathImage） |
| autorouter_handler.py | `AutorouterHandler`：exportDsn（写 .dsn + **pickle exporter 到 .pickle**）、importSes（反序列化 pickle + SprintImportSes） |
| pcb_enhancements.py | `PcbEnhancements`：addTeardrops / removeTeardrops（启发式识别已有泪滴）/ convertRoundedTrack / doBulkEdit（If/Then 批量修改，含 evalCondition 通用比较） |

## sprint_struct/ — PCB 数据模型与核心算法（最底层、最常引用）

| 文件 | 职责 |
|---|---|
| sprint_element.py | 元素基类 `SprintElement` + **板层常量**（LAYER_C1/S1/C2/S2/I1/I2/U）+ KiCad 层名映射 + mm2um01 单位换算 |
| sprint_textio.py | 顶层容器 `SprintTextIO`：元素增删/查询/归类/mergeConnectedTracks；文本设计格式的**写出** |
| sprint_textio_parser.py | `SprintTextIoParser`：文本设计格式的**读入**（按类型码分发），角度单位补丁在此 |
| sprint_track.py | 折线导线 `SprintTrack`（points/width/序列化 `TRACK,...P0=x/y;`） |
| sprint_pad.py | `SprintPad`：通孔/贴片焊盘，FORM 1-9 形状常量，via/thermal 属性，DSN padstack 命名 |
| sprint_polygon.py | 覆铜多边形 `SprintPolygon`（ZONE）：hatch/encircle 射线法/devour 内孔合并（假定凸多边形） |
| sprint_text.py | 文本 `SprintText`；toComponentText 输出 ID_TEXT/VALUE_TEXT（背面自动 MIRROR_HORZ） |
| sprint_circle.py | 圆/圆弧 `SprintCircle`：KiCad 顺时针与 Sprint 逆时针角度约定适配 |
| sprint_component.py | 元件 `SprintComponent`：idText/valueText、正反面推断、同型判等 toStr(forCompare=True) |
| sprint_group.py | GROUP/END_GROUP 锁定组容器 |
| sprint_export_dsn.py | `SprintExportDsn`：TextIO → Specctra DSN（Freerouting 输入），含多个 freerouting 兼容 workaround |
| sprint_import_ses.py | `SprintImportSes`：SES → 走线/过孔/元件位移，Y 取负，鼠线修剪（浮点 round(2)+0.1mm 邻近阈值） |
| font_to_polygon.py | fontTools 字形路径 → 多边形（M/L/Q/C/Z 拍平、Y 翻转、背面镜像、devour 合并；楷体_GB2312 例外处理） |
| teardrop.py | 泪滴生成（切线定位五点 + 三次贝塞尔；移植自 NilujePerchut/kicad_scripts）与启发式识别 |
| rounded_track.py | 直角走线→弧形走线：切线内切圆 / 三点圆 / 二阶贝塞尔三种算法 |
| wire_pair_tuner.py | 差分线长度匹配交互窗口（蛇形线振幅反解 + 二分查找消除残差） |

## conversion/ — 外部格式互转

| 文件 | 职责 |
|---|---|
| kicad_definitions.py | KiCad↔Sprint 常量映射：层、焊盘形状（roundrect/custom 降级八角）、角度换算 sprintAngleToKicad |
| kicad_to_sprint.py | `.kicad_mod` → TextIO（kicadModToTextIo）；v8 异常时降级 kicad_pcb8；LAYER_U 层跳过 |
| lceda_to_sprint.py | 立创封装 → TextIO：`LcComponent`（shape 分发解析）、在线 API 两步获取、双节点容错、API 版本 JSON 兼容 |
| sprint_to_kicad.py | TextIO → 完整 `(kicad_pcb ...)` 文件（KicadGenerator），调 NetlistBuilder 标 net |
| sprint_to_lceda.py | TextIO → EasyEDA JSON（LcedaGenerator）；画布字段用新名 `CA~`（旧名 CANVAS~ 已废弃） |
| sprint_to_openscad.py | TextIO → OpenSCAD 脚本（OpenSCADGenerator，merged/layered 两模式） |
| sprint_to_svg.py | TextIO → SVG（SVGGenerator，多边形去重、Y 镜像） |
| svg_to_polygon.py | SVG → TextIO（svgToPolygon）：线条模式(Track 描线) / 多边形模式(Polygon 填充)，fontTools 解析 path |
| netlist_builder.py | `NetlistBuilder` + `UnionFind`：铜层元素几何相交 → 网表（v1.9 新增，kicad/lceda 导出共用） |

## kicad_pcb/ 与 kicad_pcb8/ — KiCad s-expression 解析器（外部代码 fork）

| 目录 | 职责 |
|---|---|
| kicad_pcb/ | 2022-04 版（KiCad 官方 kicad-library-utils），支持 v5/v6：sexpr.py 解析器（DSN/SES 也用）、kicad_mod.py 封装解析（v8 抛 FootPrint8NotSupported）、kicad_sym/lib_table/rulebase/boundingbox/print_color |
| kicad_pcb8/ | 2024-03 版 fork，支持 v7/v8（v6 抛 FootPrint6NotSupported），无 __init__.py，仅被 kicad_to_sprint.py fallback import |

## ui/ — 界面

| 文件 | 职责 |
|---|---|
| main.frm / main.frx / ui.vbp / ui.vbw | VB6 窗体设计源文件（用 Vb6Tkinter 工作流设计界面）；main.frm 被 VB 当模块打开时是换行符问题（Unix→DOS 即可） |
| frmNewVersion.frm | 新版本提示对话框的 VB 窗体 |
| main_frm_readme.md | Vb6Tkinter 六步工作流说明 |
| sprint_font_ui.py | **Vb6Tkinter 生成的 tkinter 界面代码（不要手改生成部分）**：Application_ui + Statusbar + Tooltip；含 XP 的 TCL_LIBRARY 修复 |
| teardrop_image.py / rounded_track_image.py / wire_pair_image.py | GIF 图片的 base64 数据常量（界面图例用） |
| main.log | VB6 缺 MSCOMCTL.OCX 时的加载报错日志，非运行日志 |

## utils/ — 公共底层

| 文件 | 职责 |
|---|---|
| comm_utils.py | 纯函数几何库：两线交点/三点定圆/叉积/svgArcToCenterParam/多边形面积/点到线段距离 + str_to_int/float（逗号小数点兼容） |
| vector2d.py | 极简二维向量类 |
| version_check.py | GitHub version.json 联网检查更新 + VersionDialog 对话框 |
| widget_right_click.py | Text/Entry 右键剪切/复制/粘贴菜单 |

## tests/ — 测试

| 文件 | 职责 |
|---|---|
| runtests.py | 测试入口：`python tests/runtests.py`（TEST_MODULES=['test_base','test_kicad_to_sprint']）；**需先设 KICAD_FOOTPRINT_DIR 环境变量**；桩化 `builtins._` |
| test_base.py | 通用 unittest 基类（日志/断言工具） |
| test_kicad_to_sprint.py | kicad_mod 批量转换冒烟测试 |
| test_svg_export.py | SVG 导出独立脚本，**当前是坏的**（调用了不存在的 textIo.parse()，见 pitfalls.md） |

## 其他目录

| 目录 | 职责 |
|---|---|
| i18n/ | gettext 翻译：messages.pot 模板 + <lang>/LC_MESSAGES/messages.po|.mo，语言 en/zh_cn/de/es/pt/fr/ru/tr |
| docs/ | README 用截图 + Specctra/ELECTRA 规格PDF（DSN/SES 格式参考） |
| build/ | cx_Freeze 打包产物（不入库） |
| wiki/ | 本知识库 |
