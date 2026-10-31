"""Deterministic and injection-resistant Markdown report rendering."""

import html
import re

from agent_task_pilot.domain import AgentReport, HumanReview

MOCK_MARKER = "【Mock 演示结果】"
REDACTION_MARKER = "[敏感信息已隐藏]"

_SENSITIVE_PATTERNS = (
    re.compile(r"(?i)authorization\s*:\s*(?:bearer\s+)?\S+"),
    re.compile(r"(?i)bearer\s+[a-z0-9._~+/=-]+"),
    re.compile(r"(?i)(?:api[_ -]?key|secret|token)\s*[:=]\s*\S+"),
    re.compile(r"(?i)traceback\s*\(most recent call last\)\s*:?.*"),
)
_MARKDOWN_SPECIAL = re.compile(r"([\\`*_{\[\]()#+.!|>~-])")
_LINE_BREAKS = re.compile(r"\r\n?|\n")


class MarkdownRenderer:
    """Render a validated AgentReport without I/O or external side effects."""

    def render(self, report: AgentReport) -> str:
        """Convert a validated report into deterministic Chinese Markdown."""
        lines: list[str] = []
        append = lines.append

        append(f"# {self._safe_text(report.title)}")
        append("")
        append(f"**模式标识：** {self._mode_label(report)}")
        append("")

        append("## 1. 需求摘要")
        append("")
        append(self._safe_text(report.requirement_summary))
        append("")

        append("## 2. 适用性分析")
        append("")
        append(f"**结论：** {self._safe_text(report.applicability.verdict.value)}")
        append("")
        append("### 2.1 判断理由")
        append("")
        self._append_numbered(lines, report.applicability.reasons)
        append("")
        append("### 2.2 实施前提")
        append("")
        self._append_optional_numbered(lines, report.applicability.prerequisites, "暂无明确前提。")
        append("")

        append("## 3. 任务流程")
        append("")
        for workflow_step in report.workflow:
            append(
                f"### 3.{workflow_step.step} 步骤 {workflow_step.step}："
                f"{self._safe_text(workflow_step.name)}"
            )
            append("")
            append(f"**目标：** {self._safe_text(workflow_step.objective)}")
            append("")
            self._append_labelled_list(lines, "输入", workflow_step.inputs)
            self._append_labelled_list(lines, "动作", workflow_step.actions)
            self._append_labelled_list(lines, "输出", workflow_step.outputs)
            append("**建议工具：**")
            append("")
            for tool_index, tool in enumerate(workflow_step.suggested_tools, start=1):
                append(f"{tool_index}. **名称：** {self._safe_text(tool.name)}")
                append(f"   - **用途：** {self._safe_text(tool.purpose)}")
                append(f"   - **所需访问：** {self._safe_text(tool.required_access)}")
            append("")
            self._append_human_review(lines, workflow_step.human_review)
            append("")

        append("## 4. 主要风险与缓解措施")
        append("")
        for risk_index, risk in enumerate(report.risks, start=1):
            append(f"### 4.{risk_index} {self._safe_text(risk.category.value)}")
            append("")
            append(f"- **风险描述：** {self._safe_text(risk.description)}")
            append(f"- **潜在影响：** {self._safe_text(risk.impact)}")
            append(f"- **可能性：** {self._safe_text(risk.likelihood.value)}")
            append(f"- **严重性：** {self._safe_text(risk.severity.value)}")
            append(f"- **缓解措施：** {self._safe_text(risk.mitigation)}")
            append("")

        append("## 5. 验收指标建议")
        append("")
        for metric_index, metric in enumerate(report.acceptance_metrics, start=1):
            append(f"### 5.{metric_index} {self._safe_text(metric.name)}")
            append("")
            append(f"- **定义：** {self._safe_text(metric.definition)}")
            append(f"- **测量方法：** {self._safe_text(metric.measurement)}")
            append(f"- **建议目标：** {self._safe_text(metric.target)}")
            append("")

        append("## 6. 假设")
        append("")
        self._append_optional_numbered(lines, report.assumptions, "暂无明确假设。")
        append("")

        append("## 7. 待确认问题")
        append("")
        self._append_optional_numbered(lines, report.open_questions, "暂无待确认问题。")
        append("")

        append("## 8. 使用限制")
        append("")
        append("- 本报告仅用于需求诊断与方案讨论，不代表自动执行授权或最终业务决策。")
        append("- 报告仅包含领域模型中的需求摘要，不包含用户原始需求全文。")
        append("- 所有建议指标均为建议值，需由业务负责人审核后才能成为正式验收目标。")
        if self._is_mock(report):
            append(f"- {MOCK_MARKER}内容由固定规则与模板生成，不代表真实模型分析或实测结果。")

        return "\n".join(lines).rstrip() + "\n"

    def _mode_label(self, report: AgentReport) -> str:
        if self._is_mock(report):
            return MOCK_MARKER
        return "未在报告字段中声明"

    @staticmethod
    def _is_mock(report: AgentReport) -> bool:
        return MOCK_MARKER in report.title or any(
            MOCK_MARKER in item for item in report.assumptions
        )

    @classmethod
    def _safe_text(cls, value: str) -> str:
        """Redact secrets and neutralize user-controlled Markdown/HTML syntax."""
        redacted = value
        for pattern in _SENSITIVE_PATTERNS:
            redacted = pattern.sub(REDACTION_MARKER, redacted)
        single_line = _LINE_BREAKS.sub(" ↩ ", redacted)
        escaped_html = html.escape(single_line, quote=True)
        return _MARKDOWN_SPECIAL.sub(r"\\\1", escaped_html)

    @classmethod
    def _append_numbered(cls, lines: list[str], values: list[str]) -> None:
        for index, value in enumerate(values, start=1):
            lines.append(f"{index}. {cls._safe_text(value)}")

    @classmethod
    def _append_optional_numbered(
        cls, lines: list[str], values: list[str], empty_message: str
    ) -> None:
        if values:
            cls._append_numbered(lines, values)
        else:
            lines.append(empty_message)

    @classmethod
    def _append_labelled_list(cls, lines: list[str], label: str, values: list[str]) -> None:
        lines.append(f"**{label}：**")
        lines.append("")
        for value in values:
            lines.append(f"- {cls._safe_text(value)}")
        lines.append("")

    @classmethod
    def _append_human_review(cls, lines: list[str], review: HumanReview) -> None:
        lines.append("**人工审核点：**")
        lines.append("")
        lines.append(f"- **是否需要：** {'是' if review.required else '否'}")
        if review.required:
            lines.append(f"- **审核时点：** {cls._safe_text(review.checkpoint or '')}")
            lines.append(f"- **审核角色：** {cls._safe_text(review.reviewer or '')}")
            lines.append(f"- **通过标准：** {cls._safe_text(review.pass_criteria or '')}")
