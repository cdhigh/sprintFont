# architecture.md — 系统架构和模块关系

> 本文件由 AI Agent 自动维护。最后更新：2026-09-02

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
- **导出**：KicadGenerator 输出完整 `(kicad_pcb ...)` 板文件；LcedaGenerator 输出 EasyEDA JSON；OpenSCADGenerator（merged/layered 两模式）；SVGGenerator。
- **泪滴/弧线/差分线**：`sprint_struct/teardrop.py`（切线几何+贝塞尔拟合）、`rounded_track.py`（切线内切圆/三点圆/贝塞尔三种）、`wire_pair_tuner.py`（独立 Toplevel 窗口，蛇形线振幅反解 + 40 轮二分查找消除长度残差）。

## 5. 双 KiCad 解析器决策

- `kicad_pcb/`（2022-04 版，源自 KiCad 官方 kicad-library-utils）：支持 v5/v6 封装，**主解析器**；DSN/SES 导出导入也只用它的 sexpr 模块。
- `kicad_pcb8/`（2024-03 版 fork）：支持 v7/v8，无 __init__.py，仅被 `conversion/kicad_to_sprint.py` 作为 fallback import。
- 切换机制：kicad_to_sprint.py 先试 kicad_pcb.KicadMod，捕获 FootPrint8NotSupported 后降级 KicadMod8。

## 6. 架构决策记录（日期 + 结论 + 原因）

- 2026-09-02: 初始整理。app/ 层是从 sprintFont.py 拆出的业务 handler（UI 与逻辑分离的重构产物），后续新功能应放进 app/ 或 conversion/，不要继续膨胀 sprintFont.py。
- 2026-09-02: DSN 导出附带 pickle 整个 exporter 实例而非单独数据文件——为了 SES 导入时能原样恢复 textIo/元件表/焊盘映射；代价是 Python 版本或类结构变化会导致旧 pickle 失效。
- 2026-09-02: 双 KiCad 解析器并存而非原地升级 kicad_pcb/——两版格式差异大，fork 降级切换改动最小。
- 2026-09-02: 元件/焊盘判同用 `hash(str(序列化))`——跨进程不稳定但单次运行内一致，且 DSN→pickle→SES 往返在同一 Python 版本内成立，属刻意取舍。
- 2026-09-02: UI 用 VB6 + Vb6Tkinter 可视化设计再生成 tkinter 代码——生成/手写分离（ui/sprint_font_ui.py 生成部分不要手改 + sprintFont.py 手写业务逻辑）。
- 2026-09-02: 字体扫描用 daemon 线程 + queue + after(500ms) 轮询异步填充下拉框——扫描全部系统字体慢，不能阻塞界面启动。

## 7. 外部交互

- 立创EDA API：中文节点 `https://lceda.cn/api/...`，国际节点 `https://easyeda.com/api/...`（由系统语言或配置项 easyEdaSite=cn/global 选择）。两步：商城编号(C+数字) → svgs 接口取 component_uuid → components 接口取封装 JSON（dataStr.shape，`~` 分隔的命令行）。urllib + 浏览器 UA/Referer 伪装，超时 5s，故意不发 Accept-Encoding 免解压。
- 版本检查：`raw.githubusercontent.com/cdhigh/sprintFontRelease` 的 version.json，默认 30 天周期，可 skipVersion 跳过。
- 运行时数据目录：`%APPDATA%\Roaming\sprintFont\`（config.json + backup_*.txt 历史备份）。
