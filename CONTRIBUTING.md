# 参与贡献

感谢关注 AgentTaskPilot。提交改动前，请先阅读 `AGENTS.md`、`PRD.md` 和 `IMPLEMENTATION_PLAN.md`，保持领域、服务、提供方、渲染器和 UI 的职责边界。

## 本地检查

在 Windows PowerShell 的仓库根目录执行：

```powershell
$env:UV_CACHE_DIR = "$PWD\.uv-cache"
uv sync --locked
uv run ruff check .
uv run ruff format --check .
uv run pytest -q -p no:cacheprovider
git diff --check
```

新增行为或缺陷修复需要相应的 pytest 测试。测试必须离线，不得要求真实 API Key 或访问 DeepSeek。

## 安全与范围

- 不要提交 `.env`、密钥、真实业务需求、模型原始响应、日志或本地报告。
- 不要在 Issue 或 Pull Request 中粘贴真实凭据和敏感数据。
- 不要静默将 DeepSeek 失败回退为 Mock。
- 不要未经讨论引入登录、支付、数据库、多 Agent 编排或企业系统自动操作。
- 安全漏洞请按 `SECURITY.md` 私密报告。

## Pull Request 建议

- 保持改动小而可独立验证。
- 描述问题、方案、测试命令和真实结果。
- 明确任何未执行的手工或外部验证。
- 不要把“本地门禁通过”表述为“远程 CI 已通过”。

仓库许可证尚未确定；外部贡献和再分发安排应在仓库所有者选择许可证后再最终确认。
