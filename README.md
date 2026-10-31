# AgentTaskPilot

AgentTaskPilot V0.1 是面向企业业务用户的 AI Agent 需求诊断与任务规划工具。用户输入一段业务需求后，系统生成结构化中文报告，帮助团队在开发前讨论 Agent 适用性、实施流程、工具、人工审核、风险和验收指标。

它不是会自主执行业务的 Agent：不会操作企业系统、调用报告中的建议工具，也不提供多 Agent 编排、登录、数据库或生产级权限管理。

## V0.1 能力

- 校验 1–2000 个 Unicode 字符的业务需求，超限拒绝而不截断。
- 输出“适合 / 有条件适合 / 不适合”的判断、理由和实施前提。
- 规划连续编号的任务流程、建议工具和人工审核点。
- 分别识别隐私、权限和错误输出风险，并保留可能性与严重性。
- 提供可测量的验收指标建议；目标值始终标注为建议值。
- 默认使用离线、确定性的 Mock 模式，无需 API Key。
- 可选使用 DeepSeek；外部响应必须通过 Pydantic 领域校验。
- 在浏览器中下载 UTF-8 Markdown 报告，不写入服务器本地文件。
- 摘要是有限的业务概括，不是脱敏、保密或防止词语重合的保证；不要输入秘密或敏感数据。服务层会尽量阻止完整连续需求原文进入报告，极短输入仍可能与场景词语自然重合。

## 前置要求

- Windows 10/11 和 PowerShell
- Python 3.11 或更高版本
- [Git](https://git-scm.com/download/win)
- [uv](https://docs.astral.sh/uv/getting-started/installation/)

如果尚未安装 uv，可在 PowerShell 中使用其官方安装脚本：

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
uv --version
```

## 克隆与安装

仓库地址：`https://github.com/wangluqing/agent-task-pilot`

```powershell
git clone https://github.com/wangluqing/agent-task-pilot.git
Set-Location agent-task-pilot
$env:UV_CACHE_DIR = "$PWD\.uv-cache"
uv sync --locked
uv run python --version
```

`uv sync --locked` 使用已提交的 `uv.lock`，不会在同步时擅自改写锁文件。

## 启动与使用 Mock 模式

Mock 是默认模式，不需要 API Key，也不会调用模型或外部网络：

```powershell
$env:UV_CACHE_DIR = "$PWD\.uv-cache"
uv run streamlit run app.py
```

浏览器打开终端显示的本地地址后，可使用以下虚构需求体验：

> 某虚构企业每天收到约 500 条客服工单，希望辅助识别问题类型、推荐处理部门，并让客服主管审核高风险工单。

选择默认的“Mock（本地演示）”，点击“开始诊断”。Mock 报告是固定规则生成的演示结果，不代表真实大模型理解或生产效果。

## 配置 DeepSeek 模式

DeepSeek 是可选的外部模型模式。API Key 只从当前进程环境读取；不要把真实密钥写入源码、`.env.example`、日志、Issue 或提交历史。

```powershell
$env:DEEPSEEK_API_KEY = "<your-key>"
$env:DEEPSEEK_MODEL = "deepseek-flash"
$env:DEEPSEEK_BASE_URL = "https://api.deepseek.com"
uv run streamlit run app.py
```

在页面选择 DeepSeek 后，每次提交都必须主动勾选本次外发同意。当前需求将发送给 DeepSeek API，可能产生费用；不得输入未经授权的企业机密、个人敏感信息或其他受限制数据。提交、修改需求或切换模式后，同意状态都会失效。

应用不会自动加载 `.env`。如需清除当前 PowerShell 会话中的 Key：

```powershell
Remove-Item Env:DEEPSEEK_API_KEY -ErrorAction SilentlyContinue
```

## 报告与下载

成功报告包含八个 Markdown 主章节：

1. 需求摘要（不包含完整原始需求）
2. 适用性分析
3. 任务流程
4. 主要风险与缓解措施
5. 验收指标建议
6. 假设
7. 待确认问题
8. 使用限制

页面上的“下载 Markdown 报告”使用服务层已经生成并验证的同一份内容，文件名固定为 `agent_diagnosis_report.md`；下载不会再次调用模型。

## 测试与质量检查

```powershell
$env:UV_CACHE_DIR = "$PWD\.uv-cache"
uv sync --locked
uv run ruff check .
uv run ruff format --check .
uv run pytest -q -p no:cacheprovider
uv run python --version
git diff --check
```

自动化测试使用 Fake Provider/Transport，不需要真实 Key，也不调用真实 DeepSeek API。GitHub Actions 执行相同的 Ruff 和 pytest 门禁；远程 CI 是否通过应以仓库实际运行记录为准。

## 常见问题

### 找不到 `uv`

重新打开 PowerShell，并运行 `uv --version`。仍不可用时按 uv 官方安装文档检查 PATH。

### `uv sync --locked` 提示锁文件不一致

确认检出的是完整仓库且 `pyproject.toml`、`uv.lock` 来自同一提交。普通使用者不要手工编辑锁文件。

### Streamlit 页面没有自动打开

复制终端中的 `Local URL` 到浏览器。确认本机防火墙没有阻止本地端口。

### Mock 模式要求 API Key 或访问网络

这是非预期行为。确认页面选择的是“Mock（本地演示）”，并提交可复现信息；不要在 Issue 中粘贴真实 Key 或业务数据。

### DeepSeek 提示配置缺失

在启动 Streamlit 的同一个 PowerShell 会话中设置 `DEEPSEEK_API_KEY`，然后重启应用。页面不提供 Key 输入框。

### DeepSeek 鉴权、限流、超时或解析失败

检查账户状态、配额和官方服务状态，稍后重新授权并提交。系统不会静默回退到 Mock，也不会开放失败报告的下载。

## 安全与部署边界

- 当前版本仅适合可信用户在本地使用自己的 API Key（BYOK）。
- Streamlit UI 负责一次性外发授权；直接调用 `DiagnosisService` 的集成方必须自行取得合法授权。
- 当前没有身份认证、租户隔离、服务端权限、配额、审计、费用上限或 Token 用量展示。
- 单次 DeepSeek 请求超时 60 秒、自动重试 0 次、响应体上限约 2 MB。
- Prompt 防注入不是唯一安全边界；模型输出还必须通过领域校验和安全渲染。
- 公开 GitHub 源码仓库不等于可以安全公开部署为多用户 SaaS。V0.1 不建议直接暴露到公网供不受信任用户使用。

漏洞报告方式和密钥泄露处置见 [SECURITY.md](SECURITY.md)，参与开发见 [CONTRIBUTING.md](CONTRIBUTING.md)。

## 项目结构

```text
src/agent_task_pilot/
├── domain/       # Pydantic 领域模型与规则
├── providers/    # Mock 与 DeepSeek 适配器
├── renderers/    # Markdown 安全渲染
└── services/     # 输入校验与诊断编排
tests/            # 离线自动化测试
app.py            # Streamlit 单页入口
```

## 已知限制

- Mock 只按本地规则和模板匹配，不进行真实语义推理。
- DeepSeek 输出可能不准确，不能替代业务、法务、合规、安全或技术评审。
- 不保证适用于特定行业法规，也没有经过生产环境效果验证。
- 不持久化历史报告，不支持团队协作、用户账户或企业系统集成。
- 没有内置费用预算、调用统计和在线漏洞扫描。

## 许可证

Copyright 2026 Jack Wang.

本项目采用 [Apache License 2.0](LICENSE)。该许可证允许在遵守许可证条款的前提下使用、修改和分发本项目，并包含明确的专利授权。AgentTaskPilot 不是 Apache Software Foundation 的官方项目，项目名称和说明也不表示 ASF 认可或赞助。

当前仓库没有需要放入 NOTICE 的已知第三方归属声明；如果未来复制或分发带有 NOTICE/归属要求的第三方内容，必须保留相应声明并重新评估是否添加 `NOTICE`。

产品范围见 [PRD.md](PRD.md)，实施计划见 [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md)，工程约束见 [AGENTS.md](AGENTS.md)。
