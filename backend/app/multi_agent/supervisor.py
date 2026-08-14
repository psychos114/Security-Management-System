import json
from typing import Literal

from openai import OpenAI
from pydantic import BaseModel, Field

from backend.app.core.config import (
    LLM_API_KEY,
    LLM_BASE_URL,
    LLM_MODEL,
)
from backend.app.multi_agent.nodes import (
    supervisor_node as keyword_supervisor_node,
)
from backend.app.multi_agent.state import (
    RiskLevel,
    SecurityAgentState,
)


# AI只允许从下面5个类别中选择
CategoryName = Literal[
    "emergency",
    "inspection",
    "complaint_report",
    "fire_compliance",
    "general",
]


class SupervisorDecision(BaseModel):
    """限制AI调度结果的数据格式。"""

    category: CategoryName
    risk_level: RiskLevel
    reason: str = Field(
        min_length=1,
        max_length=200,
    )


# 类别与专业Agent之间的映射由程序控制
CATEGORY_TO_AGENT = {
    "emergency": "emergency_agent",
    "inspection": "inspection_agent",
    "complaint_report": "complaint_report_agent",
    "fire_compliance": "fire_compliance_agent",
    "general": "finish",
}


# 正在发生并且可能危及生命的事件
CRITICAL_EVENT_KEYWORDS = (
    "发生火灾",
    "已经起火",
    "现场起火",
    "出现明火",
    "大量浓烟",
    "正在冒烟",
    "需要抢救",
    "正在抢救",
    "持刀",
    "持械",
    "严重受伤",
)


# 需要优先进入突发事件流程的其他事件
HIGH_RISK_EVENT_KEYWORDS = (
    "正在打架",
    "人员冲突",
    "突然停电",
    "全院停电",
    "困在电梯",
    "困梯",
    "大量漏水",
    "水管爆裂",
    "车辆相撞",
    "车辆事故",
    "病人外出",
    "患者外出",
    "病人摔倒",
    "患者摔倒",
    "设备突然故障",
)


SUPERVISOR_SYSTEM_PROMPT = """
你是医院物业安管系统中的任务调度Agent。

你的唯一任务是判断用户问题属于哪个业务类别。
你不能回答业务问题，不能调用工具，不能派单，
不能通知人员，也不能声称任何操作已经完成。

允许的category只有：

1. emergency
   正在发生或需要处置的突发事件，例如火灾、冲突、
   设备故障、停电、困梯、漏水、车辆事故、患者违规外出、
   患者摔倒或者患者需要抢救。

2. inspection
   巡检、照片检查、漏检、风险点、隐患和整改建议。

3. complaint_report
   投诉、SLA、责任部门、超时升级、回访、满意度、
   日报、工作总结和整改报告。

4. fire_compliance
   深圳消防法律法规、消防标准、条款、发布日期、
   有效性和官方来源查询。
   询问法规中的“火灾条款”属于这一类，
   不是正在发生的火灾事件。

5. general
   与以上四类无关，或者信息不足以分类的问题。

风险等级只能是：
low、medium、high、critical。

分类原则：

- 正在发生并可能危及生命的事件优先选择emergency。
- 单纯查询消防法规、标准或条款，选择fire_compliance。
- 只根据用户问题分类，不要假设不存在的事实。
- 必须返回一个JSON对象。
- JSON只能包含category、risk_level和reason三个字段。
- 不要输出Markdown代码块，不要输出JSON以外的内容。
""".strip()


def find_safety_route(question: str):
    """在调用AI之前，先检查正在发生的高风险事件。"""

    if any(
        keyword in question
        for keyword in CRITICAL_EVENT_KEYWORDS
    ):
        return {
            "category": "emergency",
            "risk_level": "critical",
            "next_agent": "emergency_agent",
            "requires_human_confirmation": True,
            "routing_reason": (
                "检测到正在发生且可能危及生命的紧急事件，"
                "安全规则优先于AI分类。"
            ),
        }

    if any(
        keyword in question
        for keyword in HIGH_RISK_EVENT_KEYWORDS
    ):
        return {
            "category": "emergency",
            "risk_level": "high",
            "next_agent": "emergency_agent",
            "requires_human_confirmation": True,
            "routing_reason": (
                "检测到正在发生的高风险事件，"
                "安全规则优先于AI分类。"
            ),
        }

    return None

VISUAL_SEVERITY_ORDER = {
    "unknown": 0,
    "low": 1,
    "medium": 2,
    "high": 3,
    "critical": 4,
}


def get_visual_risk_level(
    state: SecurityAgentState,
) -> RiskLevel:
    """从结构化图片结果计算任务风险等级。"""

    visual_analysis = state.get(
        "visual_analysis",
        {},
    )

    if not isinstance(
        visual_analysis,
        dict,
    ):
        return "unknown"

    risks = visual_analysis.get(
        "risks",
        [],
    )

    if not isinstance(risks, list):
        return "unknown"

    severities = []

    for risk in risks:
        if not isinstance(risk, dict):
            continue

        severity = str(
            risk.get(
                "severity",
                "unknown",
            )
        )

        if severity in VISUAL_SEVERITY_ORDER:
            severities.append(severity)

    if not severities:
        return "low"

    highest_severity = max(
        severities,
        key=lambda value: (
            VISUAL_SEVERITY_ORDER[value]
        ),
    )

    if highest_severity in {
        "high",
        "critical",
    }:
        return highest_severity

    # 只要照片发现了风险，
    # 普通巡检任务最低按medium处理。
    return "medium"


def find_visual_inspection_route(
    state: SecurityAgentState,
):
    """已知来自巡检照片时，固定进入巡检Agent。"""

    if (
        state.get("input_source")
        != "inspection_image"
    ):
        return None

    return {
        "category": "inspection",
        "risk_level": (
            get_visual_risk_level(state)
        ),
        "next_agent": "inspection_agent",
        "routing_reason": (
            "任务来源是已经完成结构化识别的"
            "巡检照片，按照来源规则进入巡检Agent。"
        ),
    }

def normalize_risk_level(
    category: str,
    ai_risk_level: RiskLevel,
) -> RiskLevel:
    """使用程序规则限制不同类别的最低风险等级。"""

    if category == "emergency":
        if ai_risk_level == "critical":
            return "critical"

        return "high"

    if category in {
        "inspection",
        "complaint_report",
        "fire_compliance",
    }:
        return "medium"

    return "low"


class AISupervisorService:
    """调用大模型完成受控任务分类。"""

    def __init__(self):
        self.client = OpenAI(
            api_key=LLM_API_KEY,
            base_url=LLM_BASE_URL,
        )

    def classify(
        self,
        question: str,
    ) -> SupervisorDecision:
        """让AI返回固定格式的分类结果。"""

        response = self.client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": SUPERVISOR_SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": question,
                },
            ],
            response_format={
                "type": "json_object",
            },
            max_tokens=500,
            stream=False,
            extra_body={
                "thinking": {
                    "type": "disabled",
                }
            },
        )

        content = (
            response
            .choices[0]
            .message
            .content
            or ""
        )

        parsed_result = json.loads(content)

        return SupervisorDecision.model_validate(
            parsed_result
        )


ai_supervisor_service = AISupervisorService()


def ai_supervisor_node(
    state: SecurityAgentState,
):
    """LangGraph中的AI调度节点。"""

    question = state["user_question"].strip()

    print("\nAI调度节点收到问题：", question)

    # 第一层：紧急事件安全规则
    safety_route = find_safety_route(question)

    if safety_route is not None:
        print("使用安全规则完成调度")

        return {
            **safety_route,
            "routing_method": "safety_rule",
            "route_history": (
                state["route_history"]
                + ["supervisor"]
            ),
        }
    
    visual_route = (
        find_visual_inspection_route(
            state
        )
    )

    if visual_route is not None:
        print(
            "使用图片来源规则进入巡检Agent"
        )

        return {
            **visual_route,
            "routing_method": "source_rule",
            "route_history": (
                state["route_history"]
                + ["supervisor"]
            ),
        }

    # 第二层：使用大模型分类
    try:
        decision = ai_supervisor_service.classify(
            question
        )

        category = decision.category

        risk_level = normalize_risk_level(
            category=category,
            ai_risk_level=decision.risk_level,
        )

        next_agent = CATEGORY_TO_AGENT[category]

        print("AI分类结果：", category)
        print("AI分类理由：", decision.reason)

        return {
            "category": category,
            "risk_level": risk_level,
            "next_agent": next_agent,
            "routing_method": "ai",
            "routing_reason": decision.reason,
            "route_history": (
                state["route_history"]
                + ["supervisor"]
            ),
            "requires_human_confirmation": (
                category == "emergency"
            ),
        }

    # 第三层：AI不可用时，使用原来的关键词规则
    except Exception as error:
        print(
            "AI调度失败，正在使用关键词备用规则：",
            type(error).__name__,
        )

        fallback_result = keyword_supervisor_node(
            state
        )

        return {
            **fallback_result,
            "routing_method": "keyword_fallback",
            "routing_reason": (
                "AI调度暂时不可用，"
                "系统使用关键词备用规则。"
            ),
            "errors": state["errors"] + [
                (
                    "AI supervisor failed: "
                    f"{type(error).__name__}: {error}"
                )
            ],
        }