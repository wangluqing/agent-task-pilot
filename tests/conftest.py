"""Reusable valid report fixtures for domain contract tests."""

from copy import deepcopy

import pytest


@pytest.fixture
def minimal_report_data() -> dict[str, object]:
    """Return the smallest complete report accepted by the V0.1 contract."""
    return {
        "title": "客服工单分流 Agent 诊断报告",
        "requirement_summary": "对中文客服工单进行分类并建议处理队列。",
        "applicability": {
            "verdict": "适合",
            "reasons": ["任务边界明确且输出可由人工复核。"],
            "prerequisites": [],
        },
        "workflow": [
            {
                "step": 1,
                "name": "工单分类",
                "objective": "识别工单所属业务类别。",
                "inputs": ["待处理工单文本"],
                "actions": ["按预定义分类体系生成类别建议"],
                "outputs": ["建议类别"],
                "suggested_tools": [
                    {
                        "name": "文本分类能力",
                        "purpose": "生成工单类别建议",
                        "required_access": "只读访问单条工单文本",
                    }
                ],
                "human_review": {"required": False},
            }
        ],
        "risks": [
            {
                "category": "隐私",
                "description": "工单可能包含个人信息。",
                "impact": "敏感信息可能被不当处理。",
                "likelihood": "中",
                "severity": "高",
                "mitigation": "输入前进行敏感字段脱敏。",
            },
            {
                "category": "权限",
                "description": "系统可能读取超出范围的工单。",
                "impact": "造成越权访问。",
                "likelihood": "低",
                "severity": "高",
                "mitigation": "使用最小权限的只读接口。",
            },
            {
                "category": "错误输出",
                "description": "分类建议可能错误。",
                "impact": "工单进入错误队列。",
                "likelihood": "中",
                "severity": "中",
                "mitigation": "低置信度结果进入人工复核。",
            },
        ],
        "acceptance_metrics": [
            {
                "name": "分类准确率",
                "definition": "正确分类工单数占抽检工单总数的比例。",
                "measurement": "使用人工标注测试集计算正确数/总数。",
                "target": "建议值：准确率不低于 90%。",
            }
        ],
        "assumptions": [],
        "open_questions": [],
    }


@pytest.fixture
def full_report_data(minimal_report_data: dict[str, object]) -> dict[str, object]:
    """Return a richer valid report covering optional contract fields."""
    report = deepcopy(minimal_report_data)
    report["applicability"] = {
        "verdict": "有条件适合",
        "reasons": ["任务可标准化。", "错误结果可在执行前拦截。"],
        "prerequisites": ["建立稳定的工单分类体系。"],
    }
    workflow = report["workflow"]
    assert isinstance(workflow, list)
    workflow[0]["human_review"] = {
        "required": True,
        "checkpoint": "低置信度分类结果",
        "reviewer": "客服组长",
        "pass_criteria": "类别与工单内容一致",
    }
    workflow.append(
        {
            "step": 2,
            "name": "形成分流建议",
            "objective": "给出目标处理队列。",
            "inputs": ["建议类别", "队列映射规则"],
            "actions": ["匹配类别与处理队列"],
            "outputs": ["建议处理队列"],
            "suggested_tools": [
                {
                    "name": "规则查询工具",
                    "purpose": "读取类别与队列映射",
                    "required_access": "只读访问已发布规则",
                }
            ],
            "human_review": {"required": False},
        }
    )
    risks = report["risks"]
    assert isinstance(risks, list)
    risks.append(
        {
            "category": "其他",
            "description": "分类体系发生变化。",
            "impact": "既有规则可能过时。",
            "likelihood": "中",
            "severity": "中",
            "mitigation": "定期复核分类与队列映射。",
        }
    )
    report["assumptions"] = ["企业已有统一工单分类体系。"]
    report["open_questions"] = ["低置信度阈值由谁批准？"]
    return report
