---
name: cost-aware-delegation
description: 子Agent优先调度、省主模型Token、/dispatch。Use when the user wants most reading, research, analysis, writing, implementation, document production or verification done by subagents, with file handoffs and short receipts to the current main agent.
---

# 子 Agent 优先调度

目标：交付合格的结果，同时降低主模型累计 Token；子模型用量单列，不作为本模式的优化目标。

## 分工

- 主模型明确目标、派工、处理关键分歧和最终交付，不亲自重做完整执行流程。
- general 默认承担资料阅读、检索、分析、方案起草、翻译、编码、文档制作、执行与验证；explore 用于快速只读定位。
- 一步即可完成的小任务直接处理；其余按明确任务委派，例如读完指定文件并给出分析、实现某项功能并通过测试、制作一份文档。每个任务完成即回报主模型；任务内部的连续工具操作无需逐步回报。

## 交接

每次 subagent 调用说明任务 ID、材料路径、目标、输出位置和验收标准；工作相关的领域技能由执行者按需加载。

每个任务均返回回执，主模型逐任务验收后推进依赖任务。完整正文、分析、代码和检查记录写入文件；回执通常不超过 200 字，包含状态、产物路径、最多三条关键结论、验证结果与待决定的问题，重要失败项完整列出。主模型需要交付长文时，优先提供文件，而非把全文重新生成一遍。

需要完整复核时，交给另一个 general 检查原始材料和产物，并返回简短检查单；主模型根据回执和检查单验收，仅在冲突、异常或决定性证据处局部查看，不重复读取全文或重写全部产物。

沿用已配置的子模型，常规调用不传 model 或 variant；遵守已有项目规则。独立工作可并行，通常最多两个；失败时给出具体缺陷再纠错，默认最多一次。
