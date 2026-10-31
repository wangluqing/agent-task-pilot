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

## 安全边界

- 当前版本仅适合可信用户在本地使用自己的 DeepSeek API Key（BYOK），不具备公开多用户托管所需的身份认证、租户隔离、配额、审计和服务端授权能力。
- 外发同意由 Streamlit 页面强制执行。`DiagnosisService` 是可复用的应用服务，Python 调用方若绕过页面直接选择 `deepseek`，必须自行取得并记录合法授权。
- `DEEPSEEK_BASE_URL` 仅接受 DeepSeek 官方 `https://api.deepseek.com`（兼容 `/v1` 路径），避免把鉴权头发送到非官方主机。
- 单次请求超时 60 秒、自动重试 0 次、响应体上限约 2 MB，但当前没有费用上限、Token 用量展示或用户配额。启用真实模式前应在 DeepSeek 账户侧设置预算和告警。
- Prompt 防注入提示不是唯一安全边界；模型输出仍需通过固定的 Pydantic 契约校验，并由应用层提供可信模式标识后才能展示和下载。

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
