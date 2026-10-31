# AgentTaskPilot

AgentTaskPilot V0.1 是面向企业业务用户的 AI Agent 需求诊断与任务规划工具。Streamlit 页面默认提供完全本地运行的 Mock 演示，也可在明确授权后调用可选的 DeepSeek 外部模型。

## 环境要求

- Python 3.11+
- uv

## 初始化

PowerShell：

```powershell
$env:UV_CACHE_DIR = "$PWD\.uv-cache"
uv sync --locked
```

项目默认 Mock 模式不需要 API Key。DeepSeek 配置模块只在被显式调用时读取进程环境变量，不会在导入时读取配置，也不会自动加载 `.env`。可在 Windows PowerShell 当前会话中设置：

```powershell
$env:DEEPSEEK_API_KEY = "<your-key>"
$env:DEEPSEEK_MODEL = "deepseek-flash"
$env:DEEPSEEK_BASE_URL = "https://api.deepseek.com"
```

`.env.example` 仅作为变量名参考；不要在其中填写真实密钥，也不要提交本地 `.env`。应用不会从页面收集或展示 API Key。DeepSeek 模式必须由用户主动选择，并在每次提交前明确同意将当前需求发送至外部 API。

## 启动 Streamlit Demo

在 Windows PowerShell 中执行：

```powershell
$env:UV_CACHE_DIR = "$PWD\.uv-cache"
uv sync --locked
uv run streamlit run app.py
```

终端显示本地地址后，在浏览器打开页面。Mock 模式不调用外部服务；DeepSeek 模式会将当前业务需求发送至 DeepSeek API，请勿输入未经授权的企业机密或个人敏感信息。页面数据只保存在当前 Streamlit 会话，不写入本地报告文件；下载由浏览器处理。

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
