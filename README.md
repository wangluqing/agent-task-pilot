# AgentTaskPilot

AgentTaskPilot V0.1 是面向企业业务用户的 AI Agent 需求诊断与任务规划工具。当前提供无需 API Key、完全本地运行的 Streamlit Mock 演示页面。

## 环境要求

- Python 3.11+
- uv

## 初始化

PowerShell：

```powershell
$env:UV_CACHE_DIR = "$PWD\.uv-cache"
uv sync --locked
```

项目默认 Mock 模式不需要 API Key。未来启用 DeepSeek 时，复制 `.env.example` 为本地 `.env` 并通过安全方式设置 `DEEPSEEK_API_KEY`；不要提交 `.env`。应用不会从页面收集 API Key。

## 启动 Streamlit Demo

在 Windows PowerShell 中执行：

```powershell
$env:UV_CACHE_DIR = "$PWD\.uv-cache"
uv sync --locked
uv run streamlit run app.py
```

终端显示本地地址后，在浏览器打开页面。当前仅开放 Mock 模式，不调用 DeepSeek 或其他外部服务。页面数据只保存在当前 Streamlit 会话，不写入本地报告文件；下载由浏览器处理。

## 质量检查

```powershell
$env:UV_CACHE_DIR = "$PWD\.uv-cache"
uv run ruff check .
uv run ruff format --check .
uv run pytest -q
uv run python --version
git diff --check
```

CI 不配置真实 API Key，也不允许访问真实外部 API。

## 目录结构

```text
src/agent_task_pilot/
├── domain/       # 领域模型与规则
├── providers/    # Mock 与外部模型适配器
├── renderers/    # Markdown 等输出渲染
└── services/     # 应用服务编排
tests/            # 自动化测试
app.py            # Streamlit 单页应用入口
```

产品范围和冻结决策见 `PRD.md`，分阶段实施任务见 `IMPLEMENTATION_PLAN.md`，工程约束见 `AGENTS.md`。
