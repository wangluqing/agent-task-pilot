"""Streamlit entry point for the AgentTaskPilot V0.1 local demo."""

import hashlib

import streamlit as st

from agent_task_pilot.providers import ProviderError
from agent_task_pilot.services import (
    DiagnosisResult,
    DiagnosisService,
    InputValidationError,
)

PAGE_TITLE = "AgentTaskPilot｜企业 AI Agent 需求诊断与任务规划"
MOCK_MODE_LABEL = "Mock（本地演示）"
DEEPSEEK_MODE_LABEL = "DeepSeek（外部模型）"
DOWNLOAD_FILENAME = "agent_diagnosis_report.md"


def _clear_outcome() -> None:
    """Remove report and safe error state from the current session."""
    st.session_state.pop("diagnosis_result", None)
    st.session_state.pop("result_mode", None)
    st.session_state.pop("diagnosis_error", None)


def _invalidate_context() -> None:
    """Invalidate results, pending work, and consent after context changes."""
    _clear_outcome()
    st.session_state.pop("pending_diagnosis", None)
    st.session_state["deepseek_consent"] = False
    st.session_state["request_in_progress"] = False


def _requirement_fingerprint(requirement: str) -> str:
    """Bind one consent event to one exact input without duplicating its text."""
    return hashlib.sha256(requirement.encode("utf-8")).hexdigest()


def _queue_diagnosis() -> None:
    """Consume current consent and queue exactly one diagnosis execution."""
    _clear_outcome()
    mode_label = st.session_state.get("analysis_mode", MOCK_MODE_LABEL)
    requirement = st.session_state.get("requirement_input", "")
    if mode_label == DEEPSEEK_MODE_LABEL and not st.session_state.get("deepseek_consent", False):
        st.session_state["diagnosis_error"] = "请先明确同意将当前业务需求发送至 DeepSeek API。"
        return

    mode = "deepseek" if mode_label == DEEPSEEK_MODE_LABEL else "mock"
    st.session_state["pending_diagnosis"] = {
        "mode": mode,
        "requirement_fingerprint": _requirement_fingerprint(requirement),
    }
    st.session_state["request_in_progress"] = True
    st.session_state["deepseek_consent"] = False


def _initialize_state() -> None:
    st.session_state.setdefault("diagnosis_result", None)
    st.session_state.setdefault("deepseek_consent", False)
    st.session_state.setdefault("request_in_progress", False)


def _display_report(result: DiagnosisResult, mode: str) -> None:
    """Display a report without modifying its domain object."""
    report = result.report
    if mode == "deepseek":
        st.success(
            "DeepSeek 外部模型分析已完成。结果仅供辅助评估，"
            "不保证业务判断准确，也不构成专业咨询结论。"
        )
    else:
        st.success("诊断完成。以下内容为 Mock 本地模板演示结果。")

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
    """Render the single-page Mock and explicitly authorized DeepSeek demo."""
    st.set_page_config(page_title=PAGE_TITLE, page_icon="🧭", layout="centered")
    _initialize_state()

    st.title(PAGE_TITLE)
    st.caption("应用不持久化业务需求或报告；下载仅由浏览器处理。")

    st.text_area(
        "业务需求",
        key="requirement_input",
        height=180,
        placeholder="例如：希望自动识别客服工单类型并推荐处理部门……",
        help="请输入 1–2000 个 Unicode 字符；超限将拒绝且不会截断。",
        on_change=_invalidate_context,
    )
    requirement_length = len(st.session_state.get("requirement_input", "").strip())
    st.caption(f"当前有效字符数：{requirement_length} / 2000")

    selected_mode = st.radio(
        "分析模式",
        options=[MOCK_MODE_LABEL, DEEPSEEK_MODE_LABEL],
        key="analysis_mode",
        horizontal=True,
        on_change=_invalidate_context,
        help="Mock 完全本地运行；DeepSeek 会将当前需求发送至外部 API。",
    )
    if selected_mode == DEEPSEEK_MODE_LABEL:
        st.warning(
            "DeepSeek 是外部模型服务：当前业务需求将发送至 DeepSeek API。"
            "不得输入未经授权的企业机密、个人敏感信息或其他受限制数据。"
        )
        st.info(
            "模型输出仅供辅助分析，不保证业务判断准确，也不构成法律、合规、安全或其他专业咨询结论。"
        )
        st.checkbox(
            "我已确认当前需求可发送至 DeepSeek API，并明确同意本次外部数据发送。",
            key="deepseek_consent",
        )
    else:
        st.warning(
            "当前为 Mock 本地模板演示：不调用模型或外部网络，结果不代表真实语义理解或大模型诊断。"
        )

    request_in_progress = st.session_state.get("request_in_progress", False)
    deepseek_without_consent = selected_mode == DEEPSEEK_MODE_LABEL and not st.session_state.get(
        "deepseek_consent", False
    )
    st.button(
        "开始诊断",
        type="primary",
        disabled=request_in_progress or deepseek_without_consent,
        use_container_width=True,
        on_click=_queue_diagnosis,
    )

    pending = st.session_state.pop("pending_diagnosis", None)
    if isinstance(pending, dict):
        requirement = st.session_state.get("requirement_input", "")
        current_mode = "deepseek" if selected_mode == DEEPSEEK_MODE_LABEL else "mock"
        authorization_is_current = pending.get("mode") == current_mode and pending.get(
            "requirement_fingerprint"
        ) == _requirement_fingerprint(requirement)
        try:
            if not authorization_is_current:
                st.session_state["diagnosis_error"] = "提交上下文已变化，请重新确认当前需求后再试。"
            else:
                spinner_message = (
                    "正在调用 DeepSeek 外部模型，请勿重复提交……"
                    if current_mode == "deepseek"
                    else "正在生成 Mock 诊断报告……"
                )
                with st.spinner(spinner_message):
                    result = DiagnosisService().analyze(requirement, mode=current_mode)
                st.session_state["diagnosis_result"] = result
                st.session_state["result_mode"] = current_mode
                st.session_state.pop("diagnosis_error", None)
        except InputValidationError as error:
            st.session_state["diagnosis_error"] = str(error)
        except ProviderError as error:
            st.session_state["diagnosis_error"] = error.user_message
        except Exception:
            st.session_state["diagnosis_error"] = "诊断失败，请稍后重试。"
        finally:
            st.session_state["request_in_progress"] = False
        st.rerun()

    error_message = st.session_state.get("diagnosis_error")
    if isinstance(error_message, str):
        st.error(error_message)

    result = st.session_state.get("diagnosis_result")
    result_mode = st.session_state.get("result_mode")
    if isinstance(result, DiagnosisResult) and result_mode in {"mock", "deepseek"}:
        _display_report(result, result_mode)


if __name__ == "__main__":
    main()
