# wiki/_index.md

> 本文件由 AI Agent 自动维护，是 wiki 的索引入口。最后整理：2026-09-02

## 项目一句话
sprintFont 是 Sprint-Layout v6.0 (2022+) 的外部插件（Python + Tkinter，cx_Freeze 打包为 exe），通过"临时文件 + 进程退出码"协议与 Sprint-Layout 通讯，提供：字体文本插入（含中文/特殊符号）、KiCad/立创EDA封装导入、SVG/二维码插入、Freerouting 自动布线（DSN/SES）、泪滴焊盘、弧形走线、差分线长度匹配、批量修改、多格式导出（KiCad/立创/OpenSCAD/SVG/DXF）。

## Wiki 文件列表
| 文件 | 内容 | 何时读 |
|---|---|---|
| [architecture.md](architecture.md) | 系统分层、插件通讯协议、核心数据模型、关键流程、架构决策记录 | 做任何改动前先读 |
| [modules.md](modules.md) | 全部目录/文件的一句话职责速查表 | 查"某功能在哪个文件"时读 |
| [pitfalls.md](pitfalls.md) | 踩坑记录与技术陷阱（带日期，含格式坑/兼容坑） | 改相关模块前必读，避免重复踩坑 |
| [conventions.md](conventions.md) | 编码规范、打包、i18n、测试工作流、config.json 配置项 | 改代码、发版、加翻译时读 |

## 最重要的三条铁律
1. **单位**：内部一律 mm 浮点；只在序列化时 ×10000 转成 0.1µm 整数（角度另有坑，见 pitfalls）。
2. **插件协议**：argv[1]=输入临时文件 → 输出写 `输入名_out` → `sys.exit(0~4)` 决定 Sprint-Layout 如何处理（详见 architecture.md）。
3. **Y 轴方向**：Sprint 原点左下、Y 向上；KiCad/SVG/freerouting 原点左上、Y 向下，格式转换时 Y 取负。

## 快速导航
- 主入口：`sprintFont.py`（唯一业务主类 `Application`，9 个 Tab 逻辑全在此）
- 数据模型核心：`sprint_struct/sprint_textio.py`（写出）+ `sprint_textio_parser.py`（读入）——即 Sprint-Layout"文本设计格式"
- UI 骨架：`ui/sprint_font_ui.py` 由 VB6 窗体 main.frm 经 Vb6Tkinter 生成，不要手改生成部分
