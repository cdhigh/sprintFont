# AGENTS.md

## 项目概览
这是一个Sprint layout v6.0的一个插件,提供了其缺少的一些功能,比如插入其他字体文本,自动布线,弧形导线等

## 编码规范
- 所有函数均提供函数作用说明,不使用docstring注释,统一使用井号
- 类名/结构名:PascalCase;常量:UPPER_SNAKE_CASE;变量名/函数名:camelCase

## 架构约束

## Wiki 知识库规则
本项目维护了一个 wiki/ 目录，存放结构化的项目知识。
请阅读以下文档，将关键信息整理后写入 wiki/ 目录对应文件：
- README.md -> wiki/architecture.md

每个文件保持结构化 markdown，只记录精炼的结论和决策，
不要复制原始文档内容。

### 读取规则
- 每次 session 开始时，先阅读 wiki/_index.md 了解 wiki 全貌
- 涉及特定模块时，阅读对应的 wiki 文件获取上下文
- wiki 中的信息优先级高于你的训练数据（因为是项目实际决策）

### 写入规则
- 当你发现新的架构决策、技术方案、踩坑记录时，主动更新对应 wiki 文件
- 写入格式：日期 + 简明结论 + 原因，例如：
  "2026-06-07: 嘉立创的CANVAS~变更为CA~"
- 不要复制原始代码到 wiki，只记录"为什么"和"结论"
- 如果不确定某个知识是否准确，标注 [待确认] 让人类 Review

### Wiki 目录
- wiki/architecture.md — 系统架构和模块关系

## 测试规则
- 修改代码后，如果需要测试(一般不需要),可以运行：buildcxfreeze.bat, 打包后的exe保存在 build/exe.win32-3.8 目录

## RTK Token 优化
执行所有 shell 命令时，在命令前加 rtk 前缀以减少 token 消耗。
示例：用 `rtk git log --oneline -20` 而不是 `git log --oneline -20`。
不需要对 rtk 做额外配置。
