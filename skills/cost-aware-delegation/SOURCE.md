# 设计来源

本 Skill 以中文独立编写，采用本仓库 MIT 许可证。

设计参考：[obra/superpowers](https://github.com/obra/superpowers)，参考时其许可证为 MIT。

固定核验版本：`2ce8aa15d05bd57213e6f746f953aafb7ded7a8b`。

相关文件：[subagent-driven-development/SKILL.md](https://github.com/obra/superpowers/blob/2ce8aa15d05bd57213e6f746f953aafb7ded7a8b/skills/subagent-driven-development/SKILL.md)。主要借鉴文件化任务交接、完整报告落盘和短回执的设计思路，未包含上游代码、脚本或原文段落。

本地设计差异：

- 通用任务，不限软件实现计划。
- 每个明确任务完成均回报主模型；不逐工具步骤回报。
- 执行与完整复核均可交给 general。
- 使用者自行配置子模型；调用不强制覆盖模型。
- 不依赖上游插件、Bash 脚本或 worktree 流程。

本文件是来源声明，不要求执行时额外加载上游技能，也不赋予任何超出项目规则的权限。
