# general-sub-agent-skills-test

帮助你在 OpenChamber / OpenCode 中调用已配置的 sub-agent 或 general-agent，完成复杂工作，降低主模型处理负担。它本质上是一段可复用的调度提示词，封装成 Skill，避免每次重复输入。

**核心方式：子 Agent 完成执行、完整产物写文件、每项任务返回短回执、主模型逐任务验收。**

> 优化指标是主模型累计 Token，不是所有模型的总 Token，也不保证降低实际费用。当前实现属于实验性流程，真实验证的局限见 [验证说明](docs/VALIDATION.md)。

## 快速使用

安装后，在支持自定义命令的输入框中输入：

```text
/dispatch 你的具体任务
```

例如：

```text
/dispatch 阅读 papers/example.pdf，生成带证据定位的分析报告并保存到 outputs/。每个明确任务完成后回报结论、验证结果和问题。
```

```text
/dispatch 为当前项目增加 CSV 批量导入功能，完成实现和相关测试。只修改本功能相关文件，逐任务回报，最终交付代码和验证结果。
```

也可以明确点名技能：

```text
请加载 cost-aware-delegation，按子 Agent 优先模式完成：……
```

## 安装

本工程针对 **OpenCode V2**。OpenChamber 作为客户端使用时，实际加载取决于其连接的 OpenCode 服务。其他平台需要适配，不保证直接识别这些文件。

### 项目内安装

将下面两项复制到你实际工作的项目：

| 本仓库文件 | 目标项目位置 |
| --- | --- |
| `skills/cost-aware-delegation/` 整个目录 | `.opencode/skills/cost-aware-delegation/` |
| `commands/dispatch.md` | `.opencode/commands/dispatch.md` |

例如在 PowerShell 中，从本仓库目录运行，先把 `$Project` 设为目标项目的相对路径：

```powershell
$Project = '../your-project'
New-Item -ItemType Directory -Force "$Project/.opencode/skills" | Out-Null
New-Item -ItemType Directory -Force "$Project/.opencode/commands" | Out-Null
Copy-Item -Recurse 'skills/cost-aware-delegation' "$Project/.opencode/skills/"
Copy-Item 'commands/dispatch.md' "$Project/.opencode/commands/dispatch.md"
```

已有同名 Skill 或命令时先比较，不要盲目覆盖。上述命令不读取或改动模型配置。

### 全局安装

也可把同样两项分别放入 `~/.config/opencode/skills/` 与 `~/.config/opencode/commands/`。这两条是 OpenCode 约定的用户相对位置，不含机器专属路径。

OpenCode V2 支持命令自动重载。若未出现入口，先检查当前服务、权限、文件发现和同名覆盖，不要为此自动重启正在工作的会话。

## 前提：先配置执行 Agent

- 当前主 Agent 能调用 `skill` 和 `subagent` 工具。
- `general` 可执行多步骤任务；`explore` 可用于只读定位。
- **自行给子 Agent 配置合适的模型。** 本仓库不附带服务商、模型、端点或凭据，不替你选择订阅。
- 没配置子 Agent 模型时，它可能继承主模型；不能据 Agent 名称推断它更便宜。
- 文件读写、网络和执行权限由运行环境及项目规则控制；Skill 不授予新权限。
- 阅读、工程等领域的专用技能按任务另行安装，不包含在本工程中。

不需要导入开发者的全局指令、配置文件或其他仓库。前述安装文件就是运行所需的提示词部分。

## 分工与质量

| 工作 | 默认执行者 |
| --- | --- |
| 明确交付目标、派工、关键分歧与最终把关 | 主 Agent |
| 阅读、检索、分析、写作、翻译、编码、文档制作和验证 | general |
| 快速只读定位 | explore |
| 完整产物复核 | 另一个 general，向主 Agent 交检查单 |

**每个任务都要回报，不是每个工具步骤都回报。** 读完指定文件并分析，应返回；实现某项功能并完成测试，应返回；任务内部的翻页、检索、修改或测试命令不必逐次中转。

完整产物保存在文件中。回执通常不超过 200 字，重要失败项不受这一建议限制。主模型逐任务验收后推进依赖工作，不重写全部产物。见 [任务示例](examples/task-brief.md) 与 [回执示例](examples/task-receipt.md)。

## 开发与检查

仅需 Python 3.10+，检查与测试均使用标准库，不安装依赖、不访问网络、不调用模型：

```text
python -B scripts/check_public_release.py
python -B -m unittest discover -s tests -v
```

若项目要求虚拟环境，在你自己的指定环境中运行上述命令。所有测试输入都是合成材料，不包含真实文件路径或会话日志。

```text
skills/     核心调度 Skill 与公开来源说明
commands/   /dispatch 入口
docs/       设计、验证、隐私发布说明
examples/   合成任务、回执和用量示例
scripts/    本地离线检查与主模型用量汇总
tests/      不调用模型的回归测试
```

## 透明度与隐私

- [开发设计](docs/DEVELOPMENT.md)：分工、交接和历史取舍。
- [验证说明](docs/VALIDATION.md)：真实验证的匿名摘要，以及为什么不承诺固定节省率。
- [发布隐私说明](docs/PRIVACY.md)：白名单发布、Git 元数据和检查边界。
- 不发布本机配置、原始记录、论文、译文、服务地址或模型账户信息。
- 隐私扫描是辅助检查，不是对任何未来提交都绝对安全的保证。

## 许可与来源

采用 [MIT License](LICENSE)。设计借鉴 Superpowers 的文件交接与短回执机制，并非安装或复制其完整插件；详见 [来源说明](skills/cost-aware-delegation/SOURCE.md)。

OpenCode V2 官方文档：[Skills](https://opencode.ai/v2/docs/skills)、[Commands](https://opencode.ai/v2/docs/commands)、[Agents](https://opencode.ai/v2/docs/agents)。
