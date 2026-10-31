"""Streamlit entry point for the AgentTaskPilot V0.1 local demo."""

import streamlit as st

from agent_task_pilot.providers import ProviderError
from agent_task_pilot.services import (
    DiagnosisResult,
    DiagnosisService,
    InputValidationError,
)

PAGE_TITLE = "AgentTaskPilot｜企业 AI Agent 需求诊断与任务规划"
MOCK_MODE_LABEL = "Mock（本地演示）"
DEEPSEEK_MODE_LABEL = "DeepSeek（尚未开放）"
DOWNLOAD_FILENAME = "agent_diagnosis_report.md"


def _invalidate_result() -> None:
    """Remove the current session result before changed input can be displayed."""
    st.session_state.pop("diagnosis_result", None)


def _initialize_state() -> None:
    st.session_state.setdefault("diagnosis_result", None)


def _display_report(result: DiagnosisResult) -> None:
    """Display a report without modifying its domain object."""
    report = result.report
    st.success("诊断完成。以下内容为 Mock 演示结果。")

    st.header("诊断结果")
    st.subheader("适用性判断")
    st.write(f"结论：{report.applicability.verdict.value}")
    st.markdown("**判断理由**")
    for index, reason in enumerate(report.applicability.reasons, start=1):
        st.write(f"{index}. {reason}")

    st.markdown("**实施前提**")
    if report.applicability.prerequisites:
        for index, prerequisite in enumerate(report.applicability.prerequisites, start=1):
            st.write(f"{index}. {prerequisite}")
    else:
        st.write("暂无明确前提。")

    st.subheader("任务流程与人工审核")
    for step in report.workflow:
        with st.expander(f"步骤 {step.step}：{step.name}", expanded=True):
            st.write(f"目标：{step.objective}")
            st.markdown("**输入**")
            for item in step.inputs:
                st.write(f"- {item}")
            st.markdown("**动作**")
            for item in step.actions:
                st.write(f"- {item}")
            st.markdown("**输出**")
            for item in step.outputs:
                st.write(f"- {item}")
            st.markdown("**建议工具**")
            for tool in step.suggested_tools:
                st.write(f"{tool.name}｜用途：{tool.purpose}｜所需访问：{tool.required_access}")
            st.markdown("**人工审核点**")
            st.write(f"是否需要：{'是' if step.human_review.required else '否'}")
            if step.human_review.required:
                st.write(f"审核时点：{step.human_review.checkpoint}")
                st.write(f"审核角色：{step.human_review.reviewer}")
                st.write(f"通过标准：{step.human_review.pass_criteria}")

    st.subheader("主要风险")
    for risk in report.risks:
        risk_title = (
            f"{risk.category.value}｜可能性 {risk.likelihood.value}｜严重性 {risk.severity.value}"
        )
        with st.expander(risk_title):
            st.write(f"风险描述：{risk.description}")
            st.write(f"潜在影响：{risk.impact}")
            st.write(f"缓解措施：{risk.mitigation}")

    st.subheader("验收指标建议")
    for metric in report.acceptance_metrics:
        st.write(f"指标：{metric.name}")
        st.write(f"定义：{metric.definition}")
        st.write(f"测量方法：{metric.measurement}")
        st.write(f"建议目标：{metric.target}")

    st.subheader("假设")
    if report.assumptions:
        for index, assumption in enumerate(report.assumptions, start=1):
            st.write(f"{index}. {assumption}")
    else:
        st.write("暂无明确假设。")

    st.subheader("待确认问题")
    if report.open_questions:
        for index, question in enumerate(report.open_questions, start=1):
            st.write(f"{index}. {question}")
    else:
        st.write("暂无待确认问题。")

    st.download_button(
        "下载 Markdown 报告",
        data=result.markdown,
        file_name=DOWNLOAD_FILENAME,
        mime="text/markdown; charset=utf-8",
        key="download_report",
    )


def main() -> None:
    """Render the single-page local demo."""
    st.set_page_config(page_title=PAGE_TITLE, page_icon="🧭", layout="centered")
    _initialize_state()

    st.title(PAGE_TITLE)
    st.warning("当前为 Mock 演示版本：仅使用本地固定规则与模板，不代表真实大模型诊断。")
    st.caption("需求不会写入本地文件，也不会上传至第三方服务。")

    st.text_area(
        "业务需求",
        key="requirement_input",
        height=180,
        placeholder="例如：希望自动识别客服工单类型并推荐处理部门……",
        help="请输入 1–2000 个 Unicode 字符；超限将拒绝且不会截断。",
        on_change=_invalidate_result,
    )
    requirement_length = len(st.session_state.get("requirement_input", "").strip())
    st.caption(f"当前有效字符数：{requirement_length} / 2000")

    selected_mode = st.radio(
        "分析模式",
        options=[MOCK_MODE_LABEL, DEEPSEEK_MODE_LABEL],
        key="analysis_mode",
        horizontal=True,
        on_change=_invalidate_result,
        help="V0.1 本轮只开放无需 API Key 的 Mock 模式。",
    )
    if selected_mode == DEEPSEEK_MODE_LABEL:
        st.info("DeepSeek 模式尚未开放，本页面不会调用任何真实模型或外部 API。")

    submitted = st.button(
        "开始诊断",
        type="primary",
        disabled=selected_mode != MOCK_MODE_LABEL,
        use_container_width=True,
    )
    if submitted:
        _invalidate_result()
        try:
            with st.spinner("正在生成 Mock 诊断报告……"):
                result = DiagnosisService().analyze(
                    st.session_state.get("requirement_input", ""),
                    mode="mock",
                )
            st.session_state["diagnosis_result"] = result
        except InputValidationError as error:
            st.error(str(error))
        except ProviderError as error:
            st.error(error.user_message)
        except Exception:
            st.error("诊断失败，请稍后重试。")

    result = st.session_state.get("diagnosis_result")
    if isinstance(result, DiagnosisResult):
        _display_report(result)


if __name__ == "__main__":
    main()
