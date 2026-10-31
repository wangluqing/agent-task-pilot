"""Tests for deterministic and safe Markdown report rendering."""

from copy import deepcopy

import pytest

from agent_task_pilot.domain import AgentReport
from agent_task_pilot.providers import MockProvider
from agent_task_pilot.providers.mock import MOCK_NOTICE
from agent_task_pilot.renderers import MarkdownRenderer


def test_minimal_valid_report_renders(minimal_report_data: dict[str, object]) -> None:
    report = AgentReport.model_validate(minimal_report_data)

    rendered = MarkdownRenderer().render(report)

    assert rendered.startswith("# 客服工单分流 Agent 诊断报告\n")
    assert "## 1. 需求摘要" in rendered
    assert "## 8. 使用限制" in rendered
    assert rendered.endswith("\n")


def test_full_report_contains_all_required_sections(
    full_report_data: dict[str, object],
) -> None:
    report = AgentReport.model_validate(full_report_data)

    rendered = MarkdownRenderer().render(report)

    expected_sections = [
        "## 1. 需求摘要",
        "## 2. 适用性分析",
        "### 2.1 判断理由",
        "### 2.2 实施前提",
        "## 3. 任务流程",
        "## 4. 主要风险与缓解措施",
        "## 5. 验收指标建议",
        "## 6. 假设",
        "## 7. 待确认问题",
        "## 8. 使用限制",
    ]
    positions = [rendered.index(section) for section in expected_sections]
    assert positions == sorted(positions)
    assert "建议工具" in rendered
    assert "人工审核点" in rendered
    assert "缓解措施" in rendered


def test_mock_notice_is_prominently_preserved() -> None:
    report = MockProvider().diagnose("建立企业知识库问答助手")

    rendered = MarkdownRenderer().render(report, mode_label="【Mock 演示结果】")

    assert MOCK_NOTICE in rendered
    assert "**模式标识：** 【Mock 演示结果】" in rendered
    assert rendered.count("【Mock 演示结果】") >= 3


def test_trusted_deepseek_mode_label_does_not_depend_on_report_fields(
    minimal_report_data: dict[str, object],
) -> None:
    data = deepcopy(minimal_report_data)
    data["title"] = "模型自称【Mock 演示结果】但应用模式优先"
    report = AgentReport.model_validate(data)

    rendered = MarkdownRenderer().render(
        report,
        mode_label="DeepSeek 真实模型分析",
    )

    assert "**模式标识：** DeepSeek 真实模型分析" in rendered
    assert "**模式标识：** 【Mock 演示结果】" not in rendered
    assert "内容由固定规则与模板生成" not in rendered


def test_missing_trusted_mode_never_uses_model_claim() -> None:
    report = MockProvider().diagnose("建立企业知识库问答助手")

    rendered = MarkdownRenderer().render(report)

    assert "**模式标识：** 未由可信应用层指定" in rendered
    assert "**模式标识：** 【Mock 演示结果】" not in rendered


def test_invisible_and_bidirectional_controls_are_removed(
    minimal_report_data: dict[str, object],
) -> None:
    data = deepcopy(minimal_report_data)
    data["requirement_summary"] = "正常文本\x00\x1b\u202e伪装文本\u2066结束"
    report = AgentReport.model_validate(data)

    rendered = MarkdownRenderer().render(report)

    assert "正常文本伪装文本结束" in rendered
    assert all(character not in rendered for character in ("\x00", "\x1b", "\u202e", "\u2066"))


def test_metric_remains_explicitly_suggested(
    minimal_report_data: dict[str, object],
) -> None:
    report = AgentReport.model_validate(minimal_report_data)

    rendered = MarkdownRenderer().render(report)

    assert "**建议目标：** 建议值：准确率不低于 90%" in rendered
    assert "所有建议指标均为建议值" in rendered


def test_multiple_steps_and_human_review_render_correctly(
    full_report_data: dict[str, object],
) -> None:
    report = AgentReport.model_validate(full_report_data)

    rendered = MarkdownRenderer().render(report)

    assert "### 3.1 步骤 1：工单分类" in rendered
    assert "### 3.2 步骤 2：形成分流建议" in rendered
    assert "- **审核时点：** 低置信度分类结果" in rendered
    assert "- **审核角色：** 客服组长" in rendered
    assert "- **通过标准：** 类别与工单内容一致" in rendered
    assert rendered.count("- **是否需要：** 否") == 1


def test_empty_assumptions_and_questions_render_explicit_empty_states(
    minimal_report_data: dict[str, object],
) -> None:
    report = AgentReport.model_validate(minimal_report_data)

    rendered = MarkdownRenderer().render(report)

    assert "暂无明确假设。" in rendered
    assert "暂无待确认问题。" in rendered


def test_user_controlled_markdown_html_and_fences_cannot_break_structure(
    minimal_report_data: dict[str, object],
) -> None:
    malicious = "# 伪造标题\n- 伪造列表\n```python\n<script>alert('x')</script>"
    data = deepcopy(minimal_report_data)
    data["title"] = malicious
    data["requirement_summary"] = malicious
    data["workflow"][0]["name"] = malicious
    report = AgentReport.model_validate(data)

    rendered = MarkdownRenderer().render(report)

    headings = [line for line in rendered.splitlines() if line.startswith("#")]
    assert headings[0].startswith("# \\# 伪造标题")
    assert "\n# 伪造标题" not in rendered
    assert "\n- 伪造列表" not in rendered
    assert "<script>" not in rendered
    assert "&lt;script&gt;" in rendered
    assert "\n```" not in rendered
    assert "\\`\\`\\`python" in rendered
    assert " ↩ " in rendered


def test_sensitive_and_debug_content_is_redacted(
    minimal_report_data: dict[str, object],
) -> None:
    data = deepcopy(minimal_report_data)
    data["title"] = "Authorization: Bearer super-secret-token"
    data["requirement_summary"] = "API_KEY=real-secret-value"
    data["assumptions"] = ["Traceback (most recent call last): private stack"]
    report = AgentReport.model_validate(data)

    rendered = MarkdownRenderer().render(report)

    assert "super-secret-token" not in rendered
    assert "real-secret-value" not in rendered
    assert "private stack" not in rendered
    assert rendered.count("敏感信息已隐藏") == 3


def test_original_requirement_is_not_available_to_renderer() -> None:
    original_requirement = "完整原始需求：客户身份证号和全部内部处理规则"
    report = MockProvider().diagnose("建立企业知识库问答助手")

    rendered = MarkdownRenderer().render(report)

    assert original_requirement not in rendered
    assert "不包含用户原始需求全文" in rendered


def test_rendering_is_deterministic() -> None:
    report = MockProvider().diagnose("按固定格式汇总月度报表")
    renderer = MarkdownRenderer()

    first = renderer.render(report)
    second = renderer.render(report)

    assert first == second


def test_chinese_english_long_text_and_line_breaks_are_preserved_safely(
    minimal_report_data: dict[str, object],
) -> None:
    data = deepcopy(minimal_report_data)
    long_text = "中 English 123 & details " * 80
    data["requirement_summary"] = f"第一行\n{long_text}\n最后一行"
    report = AgentReport.model_validate(data)

    rendered = MarkdownRenderer().render(report)

    assert "第一行 ↩ 中 English 123 &amp; details" in rendered
    assert "最后一行" in rendered
    assert long_text not in rendered
    assert len(rendered) > len(long_text)


def test_renderer_has_no_network_file_write_or_model_side_effects(
    minimal_report_data: dict[str, object], monkeypatch: pytest.MonkeyPatch
) -> None:
    report = AgentReport.model_validate(minimal_report_data)

    def forbidden(*args: object, **kwargs: object) -> None:
        raise AssertionError("Renderer attempted an external side effect")

    monkeypatch.setattr("builtins.open", forbidden)
    monkeypatch.setattr("socket.create_connection", forbidden)
    monkeypatch.setattr("socket.socket.connect", forbidden)

    rendered = MarkdownRenderer().render(report)

    assert "## 1. 需求摘要" in rendered
