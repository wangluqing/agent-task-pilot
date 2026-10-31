"""Streamlit AppTest coverage for the single-page Mock demo."""

import ast
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from agent_task_pilot.services import DiagnosisService

APP_PATH = Path(__file__).parents[1] / "app.py"
VALID_REQUIREMENT = "某企业每天处理约500条客服工单，希望自动分类并保留人工审核。"


def _app() -> AppTest:
    return AppTest.from_file(str(APP_PATH), default_timeout=10).run()


def _visible_text(app: AppTest) -> str:
    element_types = (
        "text",
        "markdown",
        "warning",
        "info",
        "success",
        "caption",
        "title",
        "header",
        "subheader",
    )
    return "\n".join(
        str(element.value) for element_type in element_types for element in app.get(element_type)
    )


def test_initial_page_has_no_report_or_download() -> None:
    app = _app()

    assert not app.exception
    assert len(app.text_area) == 1
    assert len(app.button) == 1
    assert len(app.download_button) == 0
    assert "诊断结果" not in [header.value for header in app.header]


def test_valid_input_shows_complete_report_and_download() -> None:
    app = _app()

    app.text_area[0].input(VALID_REQUIREMENT).run()
    app.button[0].click().run()

    assert not app.exception
    assert len(app.download_button) == 1
    assert "诊断结果" in [header.value for header in app.header]
    subheaders = [item.value for item in app.subheader]
    assert subheaders == [
        "适用性判断",
        "任务流程与人工审核",
        "主要风险",
        "验收指标建议",
        "假设",
        "待确认问题",
    ]
    visible = _visible_text(app)
    assert "有条件适合" in visible
    assert "建议值" in visible
    assert "人工审核" in visible


@pytest.mark.parametrize(
    ("requirement", "message"),
    [
        (" \t\n ", "请输入业务需求，内容不能仅包含空白字符。"),
        ("需" * 2001, "业务需求不能超过 2000 个字符，请精简后重试。"),
    ],
)
def test_invalid_input_shows_safe_message_without_result(requirement: str, message: str) -> None:
    app = _app()

    app.text_area[0].input(requirement).run()
    app.button[0].click().run()

    assert not app.exception
    assert [error.value for error in app.error] == [message]
    assert len(app.download_button) == 0
    assert "诊断结果" not in [header.value for header in app.header]


def test_changing_input_invalidates_old_result_and_download() -> None:
    app = _app()
    app.text_area[0].input(VALID_REQUIREMENT).run()
    app.button[0].click().run()
    assert len(app.download_button) == 1

    app.text_area[0].input("修改后的知识库问答需求").run()

    assert not app.exception
    assert len(app.download_button) == 0
    assert "诊断结果" not in [header.value for header in app.header]


def test_switching_mode_invalidates_result_and_disables_submission() -> None:
    app = _app()
    app.text_area[0].input(VALID_REQUIREMENT).run()
    app.button[0].click().run()
    assert len(app.download_button) == 1

    app.radio[0].set_value("DeepSeek（尚未开放）").run()

    assert not app.exception
    assert len(app.download_button) == 0
    assert app.button[0].disabled is True
    assert any("尚未开放" in info.value for info in app.info)


def test_failed_submission_removes_previous_success() -> None:
    app = _app()
    app.text_area[0].input(VALID_REQUIREMENT).run()
    app.button[0].click().run()
    assert len(app.download_button) == 1

    app.text_area[0].input(" ").run()
    app.button[0].click().run()

    assert len(app.download_button) == 0
    assert len(app.error) == 1


def test_mock_notice_is_prominent() -> None:
    app = _app()
    initial_text = _visible_text(app)
    assert "Mock 演示版本" in initial_text
    assert "不代表真实大模型诊断" in initial_text

    app.text_area[0].input(VALID_REQUIREMENT).run()
    app.button[0].click().run()
    assert "Mock 演示结果" in _visible_text(app)


def test_download_uses_service_markdown_without_rebuilding() -> None:
    app = _app()
    expected = DiagnosisService().analyze(VALID_REQUIREMENT).markdown

    app.text_area[0].input(VALID_REQUIREMENT).run()
    app.button[0].click().run()

    download = app.download_button[0]
    assert download.label == "下载 Markdown 报告"
    assert app.session_state["diagnosis_result"].markdown == expected

    tree = ast.parse(APP_PATH.read_text(encoding="utf-8"))
    download_call = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "download_button"
    )
    keywords = {keyword.arg: keyword.value for keyword in download_call.keywords}
    assert ast.dump(keywords["data"]) == ast.dump(
        ast.Attribute(
            value=ast.Name(id="result", ctx=ast.Load()),
            attr="markdown",
            ctx=ast.Load(),
        )
    )
    assert isinstance(keywords["file_name"], ast.Name)
    assert keywords["file_name"].id == "DOWNLOAD_FILENAME"

    filename_assignment = next(
        node
        for node in tree.body
        if isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Name) and target.id == "DOWNLOAD_FILENAME"
            for target in node.targets
        )
    )
    assert isinstance(filename_assignment.value, ast.Constant)
    assert filename_assignment.value.value == "agent_diagnosis_report.md"


def test_app_does_not_access_network_or_deepseek(monkeypatch: pytest.MonkeyPatch) -> None:
    def forbidden(*args: object, **kwargs: object) -> None:
        raise AssertionError("UI attempted external network access")

    monkeypatch.setattr("requests.sessions.Session.request", forbidden)
    monkeypatch.setattr("urllib.request.urlopen", forbidden)
    app = _app()

    app.text_area[0].input(VALID_REQUIREMENT).run()
    app.button[0].click().run()

    assert not app.exception
    assert len(app.download_button) == 1

    tree = ast.parse(APP_PATH.read_text(encoding="utf-8"))
    imported_roots = {
        alias.name.split(".", maxsplit=1)[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    imported_roots.update(
        node.module.split(".", maxsplit=1)[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    )
    assert imported_roots <= {"agent_task_pilot", "streamlit"}
