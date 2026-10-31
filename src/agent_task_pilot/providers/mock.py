"""Deterministic, offline diagnostic provider for demonstrations and tests."""

from enum import StrEnum

from agent_task_pilot.domain import AgentReport

MOCK_NOTICE = "【Mock 演示结果】本报告由本地固定规则与模板生成，未调用真实 AI 模型。"
SUMMARY_LIMIT = 120


class MockScenario(StrEnum):
    """Stable scenario identifiers used by the local rule matcher."""

    CUSTOMER_TICKET = "客服工单分类"
    KNOWLEDGE_QA = "企业知识库问答"
    FIXED_REPORT = "固定格式报表汇总"
    GENERIC = "通用场景"


SCENARIO_RULES: tuple[tuple[MockScenario, tuple[str, ...]], ...] = (
    (MockScenario.CUSTOMER_TICKET, ("客服", "工单", "ticket")),
    (MockScenario.KNOWLEDGE_QA, ("知识库", "知识问答", "问答")),
    (MockScenario.FIXED_REPORT, ("固定格式报表", "报表", "汇总")),
)


class MockProvider:
    """Generate repeatable Agent reports using only local rules and templates."""

    def diagnose(self, validated_requirement: str) -> AgentReport:
        """Return a new validated report for the first matching scenario rule."""
        scenario = self._match_scenario(validated_requirement)
        summary = self._summarize(validated_requirement)
        return AgentReport.model_validate(self._build_report(scenario, summary))

    @staticmethod
    def _match_scenario(validated_requirement: str) -> MockScenario:
        normalized = validated_requirement.casefold()
        for scenario, keywords in SCENARIO_RULES:
            if any(keyword.casefold() in normalized for keyword in keywords):
                return scenario
        return MockScenario.GENERIC

    @staticmethod
    def _summarize(validated_requirement: str) -> str:
        compact = " ".join(validated_requirement.split())
        if len(compact) <= SUMMARY_LIMIT:
            return compact
        return f"{compact[: SUMMARY_LIMIT - 1]}…"

    def _build_report(self, scenario: MockScenario, summary: str) -> dict[str, object]:
        scenario_content = self._scenario_content(scenario)
        return {
            "title": f"{MOCK_NOTICE} {scenario.value}诊断报告",
            "requirement_summary": f"规则匹配场景：{scenario.value}；有限摘要：{summary}",
            "applicability": scenario_content["applicability"],
            "workflow": scenario_content["workflow"],
            "risks": self._common_risks(),
            "acceptance_metrics": scenario_content["acceptance_metrics"],
            "assumptions": [
                MOCK_NOTICE,
                f"仅依据固定关键词规则匹配到“{scenario.value}”，不代表真实业务理解。",
                *scenario_content["assumptions"],
            ],
            "open_questions": scenario_content["open_questions"],
        }

    @staticmethod
    def _scenario_content(scenario: MockScenario) -> dict[str, object]:
        if scenario is MockScenario.CUSTOMER_TICKET:
            return _customer_ticket_content()
        if scenario is MockScenario.KNOWLEDGE_QA:
            return _knowledge_qa_content()
        if scenario is MockScenario.FIXED_REPORT:
            return _fixed_report_content()
        return _generic_content()

    @staticmethod
    def _common_risks() -> list[dict[str, object]]:
        return [
            {
                "category": "隐私",
                "description": "业务输入可能包含个人信息或企业敏感数据。",
                "impact": "敏感数据可能被不当展示、传递或保留。",
                "likelihood": "中",
                "severity": "高",
                "mitigation": "输入前脱敏，并限制处理和展示范围。",
            },
            {
                "category": "权限",
                "description": "建议工具可能访问超出任务所需范围的数据。",
                "impact": "可能发生越权读取或操作。",
                "likelihood": "低",
                "severity": "高",
                "mitigation": "采用最小权限和只读访问，并保留审计记录。",
            },
            {
                "category": "错误输出",
                "description": "规则或生成内容可能产生错误、遗漏或过时结论。",
                "impact": "错误结果可能影响后续业务决策。",
                "likelihood": "中",
                "severity": "中",
                "mitigation": "关键结果必须人工复核，失败时不得自动执行。",
            },
        ]


def _tool(name: str, purpose: str, required_access: str) -> dict[str, str]:
    return {"name": name, "purpose": purpose, "required_access": required_access}


def _review(checkpoint: str, reviewer: str, pass_criteria: str) -> dict[str, object]:
    return {
        "required": True,
        "checkpoint": checkpoint,
        "reviewer": reviewer,
        "pass_criteria": pass_criteria,
    }


def _customer_ticket_content() -> dict[str, object]:
    return {
        "applicability": {
            "verdict": "有条件适合",
            "reasons": [
                "工单分类可按已批准的分类体系形成结构化建议。",
                "分类结果可在流转前设置人工审核。",
            ],
            "prerequisites": ["业务方提供稳定的工单分类体系和人工标注样本。"],
        },
        "workflow": [
            {
                "step": 1,
                "name": "读取并预处理工单",
                "objective": "形成可分类且已脱敏的工单文本。",
                "inputs": ["单条客服工单"],
                "actions": ["移除无关格式并对敏感字段脱敏"],
                "outputs": ["待分类文本"],
                "suggested_tools": [
                    _tool("文本预处理工具", "清理与脱敏工单文本", "只读访问单条工单")
                ],
                "human_review": {"required": False},
            },
            {
                "step": 2,
                "name": "生成分类建议",
                "objective": "依据已批准分类体系给出类别和队列建议。",
                "inputs": ["待分类文本", "分类体系"],
                "actions": ["匹配类别并形成可复核的分流建议"],
                "outputs": ["建议类别和处理队列"],
                "suggested_tools": [
                    _tool("分类规则服务", "读取分类与队列映射", "只读访问已发布规则")
                ],
                "human_review": _review(
                    "工单进入处理队列之前", "客服组长", "类别与工单内容一致且无敏感信息泄露"
                ),
            },
        ],
        "acceptance_metrics": [
            {
                "name": "工单分类准确率",
                "definition": "正确分类工单数占人工抽检工单数的比例。",
                "measurement": "在人工标注测试集上计算正确数/总数。",
                "target": "建议值：分类准确率不低于 90%，最终值由业务负责人批准。",
            }
        ],
        "assumptions": ["存在可供维护的工单类别与队列映射。"],
        "open_questions": ["分类体系负责人和低置信度转人工阈值分别是什么？"],
    }


def _knowledge_qa_content() -> dict[str, object]:
    return {
        "applicability": {
            "verdict": "有条件适合",
            "reasons": [
                "知识库问答可限定在经过批准的企业资料范围内。",
                "答案可附来源并对关键内容设置人工复核。",
            ],
            "prerequisites": ["知识文档具有明确权限、版本和责任人。"],
        },
        "workflow": [
            {
                "step": 1,
                "name": "检索授权知识",
                "objective": "查找与问题相关且用户有权访问的内容。",
                "inputs": ["用户问题", "授权知识范围"],
                "actions": ["按权限过滤并检索相关文档片段"],
                "outputs": ["候选知识片段和来源"],
                "suggested_tools": [
                    _tool("企业知识检索", "检索并返回来源", "按用户权限只读访问知识库")
                ],
                "human_review": {"required": False},
            },
            {
                "step": 2,
                "name": "形成引用式答案",
                "objective": "基于候选资料形成可追溯的回答建议。",
                "inputs": ["候选知识片段和来源"],
                "actions": ["整理答案并标注依据和不确定内容"],
                "outputs": ["回答建议和来源引用"],
                "suggested_tools": [
                    _tool("答案编排组件", "组织答案与来源", "只处理已授权检索结果")
                ],
                "human_review": _review(
                    "高风险答案发布之前", "知识库内容负责人", "答案与有效来源一致且权限符合要求"
                ),
            },
        ],
        "acceptance_metrics": [
            {
                "name": "答案来源覆盖率",
                "definition": "包含有效来源引用的答案数占抽检答案总数的比例。",
                "measurement": "人工抽检答案并核对引用链接和文档版本。",
                "target": "建议值：来源覆盖率达到 100%，最终值由业务负责人批准。",
            }
        ],
        "assumptions": ["知识库文档可检索且具有有效版本标记。"],
        "open_questions": ["哪些知识域允许自动回答，哪些必须转人工？"],
    }


def _fixed_report_content() -> dict[str, object]:
    return {
        "applicability": {
            "verdict": "有条件适合",
            "reasons": [
                "固定格式报表具有明确字段和可重复的汇总规则。",
                "汇总结果可与源数据进行勾稽检查。",
            ],
            "prerequisites": ["业务方提供稳定的数据字典、计算口径和报表模板。"],
        },
        "workflow": [
            {
                "step": 1,
                "name": "校验报表输入",
                "objective": "确认输入字段、期间和口径完整。",
                "inputs": ["待汇总结构化数据", "数据字典"],
                "actions": ["检查字段类型、缺失值和统计期间"],
                "outputs": ["校验结果和可汇总数据"],
                "suggested_tools": [
                    _tool("数据校验工具", "检查输入结构和质量", "只读访问指定数据集")
                ],
                "human_review": {"required": False},
            },
            {
                "step": 2,
                "name": "汇总并复核报表",
                "objective": "按固定口径生成可核对的报表结果。",
                "inputs": ["可汇总数据", "固定报表模板"],
                "actions": ["执行确定性汇总并核对合计值"],
                "outputs": ["报表草稿和勾稽结果"],
                "suggested_tools": [
                    _tool("表格计算组件", "执行固定公式和汇总", "写入临时报表草稿")
                ],
                "human_review": _review(
                    "报表发布之前", "报表责任人", "字段完整、口径一致且合计值通过勾稽检查"
                ),
            },
        ],
        "acceptance_metrics": [
            {
                "name": "报表勾稽通过率",
                "definition": "通过预定义勾稽规则的报表数占生成报表总数的比例。",
                "measurement": "执行固定勾稽规则并记录通过与失败数量。",
                "target": "建议值：发布前勾稽通过率达到 100%，最终值由业务负责人批准。",
            }
        ],
        "assumptions": ["输入数据为结构化数据且统计口径已获批准。"],
        "open_questions": ["数据字典、计算口径和模板分别由谁维护？"],
    }


def _generic_content() -> dict[str, object]:
    return {
        "applicability": {
            "verdict": "有条件适合",
            "reasons": [
                "当前输入未命中内置演示场景，固定模板无法判断真实业务适用性。",
                "仍可用通用评估流程帮助人工澄清任务边界。",
            ],
            "prerequisites": ["由业务和技术负责人共同完成人工适用性评估。"],
        },
        "workflow": [
            {
                "step": 1,
                "name": "人工澄清需求",
                "objective": "明确业务目标、输入、输出和禁止操作。",
                "inputs": ["有限需求摘要"],
                "actions": ["由业务负责人补充场景、数据和验收约束"],
                "outputs": ["经确认的需求边界"],
                "suggested_tools": [_tool("需求澄清清单", "记录范围与假设", "不需要访问企业系统")],
                "human_review": _review(
                    "进入技术设计之前", "业务负责人", "目标、边界、数据和责任人均已明确"
                ),
            },
            {
                "step": 2,
                "name": "人工评估 Agent 适用性",
                "objective": "判断任务是否可控、可审核和可验收。",
                "inputs": ["经确认的需求边界"],
                "actions": ["评估确定性、权限、风险和人工审核要求"],
                "outputs": ["人工评估结论"],
                "suggested_tools": [_tool("Agent 评估清单", "辅助人工评审", "不需要外部网络访问")],
                "human_review": _review(
                    "决定是否立项之前", "业务与技术负责人", "形成书面适用性结论和控制措施"
                ),
            },
        ],
        "acceptance_metrics": [
            {
                "name": "需求澄清完成率",
                "definition": "已确认的需求澄清项占预定义清单项的比例。",
                "measurement": "由业务负责人逐项检查目标、数据、权限、审核和验收字段。",
                "target": "建议值：进入设计前完成率达到 100%，最终值由业务负责人批准。",
            }
        ],
        "assumptions": ["通用模板不代表对该业务场景进行了真实语义分析。"],
        "open_questions": ["业务目标、数据来源、允许操作和最终责任人分别是什么？"],
    }
