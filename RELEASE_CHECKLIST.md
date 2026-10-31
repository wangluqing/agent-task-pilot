# AgentTaskPilot V0.1 发布检查清单

所有项目默认未完成。执行 T14 时应记录日期、提交、执行人和真实证据，不得用推测替代验证。

## 许可证与仓库治理

- [ ] 仓库所有者已明确选择 MIT、Apache-2.0 或其他许可证。
- [ ] 已添加与人工决定一致的 `LICENSE`；如选 Apache-2.0，已评估是否需要 `NOTICE`。
- [ ] 已复核 README、SECURITY 和 CONTRIBUTING，不含虚构联系人或效果声明。
- [ ] 默认分支确认为 `main`，并按需要配置分支保护和必需状态检查。
- [ ] GitHub Private vulnerability reporting、Dependabot alerts 和安全更新由所有者在仓库设置中确认。

## 安全与隐私

- [ ] `git status --porcelain` 无意外文件。
- [ ] 检查当前树与 Git 可访问历史中的密钥模式；命中项已人工判定且不输出秘密。
- [ ] `.env.example` 只含空值或公开默认值，`.env` 和本地秘密文件未被跟踪。
- [ ] 自动化测试、CI、Issue 模板和文档不含真实 API Key、客户数据或模型原始响应。
- [ ] DeepSeek 每次提交前的主动授权、授权失效和无 Mock 回退路径已有证据。
- [ ] 已向使用者说明本地 BYOK 与公开多用户 SaaS 的区别。

## 自动化质量门禁

- [ ] `uv sync --locked`
- [ ] `uv run ruff check .`
- [ ] `uv run ruff format --check .`
- [ ] `uv run pytest -q -p no:cacheprovider`
- [ ] `uv run python --version`，版本满足 Python 3.11+
- [ ] `git diff --check`
- [ ] GitHub Actions 在目标提交上真实运行成功；未运行时明确标记为未验证。

## 功能验收

- [ ] F01 输入空值、Unicode 空白和 2000/2001 字符边界有证据。
- [ ] F02 适用性三态、理由和有条件前提有证据。
- [ ] F03 连续流程、工具和人工审核结构有证据。
- [ ] F04 隐私、权限、错误输出风险有证据。
- [ ] F05 可测量指标及“建议值”标识有证据。
- [ ] F06 Markdown 八章节、摘要导出和下载不重复调用有证据。
- [ ] F07 Mock 离线、确定性和演示标识有证据。
- [ ] F08 DeepSeek 使用 Fake Provider/Transport 完成成功与错误矩阵验收。

## 本地发布冒烟

- [ ] 在干净临时目录克隆目标提交并按 README 执行 `uv sync --locked`。
- [ ] 未设置 API Key 时启动 Streamlit 并完成一次 Mock 诊断和 Markdown 下载。
- [ ] 检查下载文件名、UTF-8 内容、八个章节和 Mock 标识。
- [ ] 浏览器人工交互若未执行，明确记录为未执行。
- [ ] 真实 DeepSeek 冒烟仅在单独授权和安全测试数据条件下执行；默认发布验收不调用付费 API。

## 发布材料与限制

- [ ] 发布说明列出 V0.1 功能：输入校验、诊断报告、Mock、可选 DeepSeek、风险与指标、Markdown 下载。
- [ ] 发布说明列出已知限制：无生产权限系统、租户隔离、持久化、用量统计、费用控制和生产效果验证。
- [ ] 没有虚构客户、评价、准确率、节省成本或生产验证结果。
- [ ] 公开源码仓库不被描述为已具备公开 SaaS 部署安全能力。
- [ ] 创建标签、GitHub Release、推送或部署前再次取得人工授权。
