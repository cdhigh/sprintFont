# conventions.md — 编码规范与工作流

> 本文件由 AI Agent 自动维护。最后更新：2026-09-02

## 编码规范（来自 AGENTS.md，必须遵守）

- 所有函数用**井号注释**说明函数作用，不使用 docstring。
- 命名：类名/结构名 PascalCase；常量 UPPER_SNAKE_CASE；变量名/函数名 camelCase。
- 注释与界面文案为中文；代码标识符英文。

## 架构约定

- 新功能放 app/（业务 handler）或 conversion/（格式转换），不要继续膨胀 sprintFont.py；sprint_struct/ 只放数据模型与纯算法。
- app/ 下 handler 之间不互相 import，由 sprintFont.py 组装调度。
- 单位：内部 mm 浮点，序列化才转 0.1µm 整数（mm2um01）；涉及角度先查 pitfalls.md 的单位坑。
- 新增 UI 控件的正规流程是改 ui/main.frm 后重新生成 sprint_font_ui.py（Vb6Tkinter），不要直接手改生成代码；仅事件逻辑写在 sprintFont.py。

## 打包（cx_Freeze）

- 命令：`buildcxfreeze.bat`（= C:\Python38\python.exe setup_cxfreeze.py build，32 位）；产物 `build/exe.win32-3.8/`。
- 版本号唯一来源：sprintFont.py 头部 `__Version__`（setup_cxfreeze.py 正则提取），发版只改这一处。
- 产物必须保留 i18n/ 与 ui/*.frm 相对结构；include_msvcr=True 已带 VC 运行库。
- 用户反馈插件无法启动时优先怀疑缺 VC 运行库 / Windows 通用 C 运行库（README 第3.6条）。

## i18n（gettext + pybabel）

- 流程：`pybabel_extract.bat`（提取+update）→ 手工/机器翻译 po → `pybabel_compile.bat`（编译 mo）。
- 语言：en / zh_cn / de / es / pt / fr / ru / tr；源码中直接用全局 `_()`（config_manager.initI18n 安装）。
- `pybabel_auto_translate.py` 以 zh_cn 为参考机翻其他语种（依赖作者本地 autopo 工具，硬编码路径）。
- 新增语种注意：主界面 6 个 Tab 标题是定宽空格包裹的（如 `"  Font  "`），译文过长会破坏布局，需检查宽度。

## 测试

- 一般不需要测试（AGENTS.md 口径）；需要时 `python tests/runtests.py`，且**必须先设环境变量 `KICAD_FOOTPRINT_DIR`** 指向含 .kicad_mod 的目录。
- TEST_MODULES 只有 test_base 和 test_kicad_to_sprint；test_svg_export.py 是独立脚本且当前是坏的（pitfalls.md）。
- 验证打包功能可跑 buildcxfreeze.bat 后用 exe 实测。

## config.json 配置项（%APPDATA%\Roaming\sprintFont\config.json）

所有值以字符串存储，restoreConfig 逐项 str_to_int/float + 范围钳制（config_manager.py）：

- 全局：language / lastTab / checkUpdateFrequency(30天) / lastCheckUpdate / skipVersion / history(文本历史[]) / historyNum(5) / backupNum(5) / easyEdaSite(cn|global)
- 字体页：font / txtFontSize / height(字高mm) / layer(板层索引) / wordSpacing / lineSpacing / smooth / invertBackground / padding / capLeft / capRight
- 封装页：importFootprintText
- 导出页：exportLayer / exportLayeredScad
- SVG页：svgQrcode / svgMode / svgLayer / svgHeight / svgSmooth
- 自动布线规则：trackWidth(0.3) / viaDiameter(0.6) / viaDrill(0.3) / clearance(0.2) / smdSmdClearance(0.2)；强制 viaDiameter > viaDrill
- 泪滴：teardropHPercent(50) / teardropVPercent(90) / teardropSegs(10) / teardropPadType(0=PTH)
- 弧线：roundedTrackType(0=tangent) / roundedTrackBigDistance(2.0) / roundedTrackSmallDistance(0.3) / roundedTrackSegs(10) / mergeConnectedTracks
- 差分线：wirePairType(0=单侧) / wirePairAmin / wirePairAmax / wirePairSpacing / wirePairSkew
- 批量修改：bulkEditTarget(0=Text)

## 版本/发布

- 编译发布版发布在独立仓库 github.com/cdhigh/sprintFontRelease（version.json 供在线更新检查）。
- 版本日志同时维护在 README.md 第4节。
