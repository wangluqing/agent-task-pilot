# AgentTaskPilot 工程约束

## 架构

- 使用 Python 3.11+、uv 和 `src` 布局，顶层包名为 `agent_task_pilot`。
- `domain` 只定义领域模型与规则，不依赖 Streamlit、HTTP 客户端或具体 LLM SDK。
- `services` 编排领域能力，只依赖抽象提供方接口。
- `providers` 隔离 Mock 与 DeepSeek 实现；两者必须返回相同的领域契约。
- `renderers` 只消费已验证领域对象，不调用提供方。
- UI、领域、服务、提供方和渲染职责不得混入同一模块。

## 质量命令

在仓库根目录执行：

```powershell
$env:UV_CACHE_DIR = "$PWD\.uv-cache"
uv sync --locked
uv run ruff check .
uv run ruff format --check .
uv run pytest -q
uv run python --version
git diff --check
```

新增行为必须有 pytest 测试；修复缺陷必须增加回归测试。CI 与本地使用相同的 ruff 和 pytest 门禁。

## 安全规则

- API Key 只允许从 `DEEPSEEK_API_KEY` 环境变量读取，禁止写入源码、测试、日志、报告或异常详情。
- `.env`、虚拟环境、缓存、覆盖率文件和本地输出不得提交；`.env.example` 只能包含空值或明显占位符。
- 自动化测试和 CI 禁止访问真实外部 API，必须 mock 网络边界。
- DeepSeek 必须由用户显式选择，每次提交前确认外部数据发送；单次超时 60 秒，自动重试 0 次。
- 默认不记录完整业务需求、完整模型响应、鉴权头或堆栈到用户可见位置。

## 冻结产品规则

- 输入上限 2000 个 Unicode 字符，超限拒绝，不截断。
- 默认 Mock，Mock 输出显著标识为演示。
- Markdown 默认只导出需求摘要。
- 报告使用中文；风险保留可能性和严重性，不计算综合评分。
- AI 提出的业务指标目标值必须标注为建议值。

## 禁止事项

- 不实现多 Agent 编排、企业系统自动操作、登录、支付、复杂数据库或生产级权限系统。
- 未经明确授权不得调用真实 LLM API、部署、创建远程仓库、提交或推送 Git。
- 不得静默回退真实模式为 Mock，不得下载未通过领域校验的报告。
- 不得为通过检查而跳过、弱化或删除测试与质量规则。
