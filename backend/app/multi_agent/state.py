from typing import Literal
from uuid import uuid4

from langchain_core.messages import HumanMessage
from langgraph.graph import MessagesState


# 系统中允许出现的下一站
AgentName = Literal[
    "supervisor",
    "emergency_agent",
    "inspection_agent",
    "complaint_report_agent",
    "fire_compliance_agent",
    "finish",
]


# 系统内部统一使用的风险等级
RiskLevel = Literal[
    "unknown",
    "low",
    "medium",
    "high",
    "critical",
]


class SecurityAgentState(MessagesState):
    """所有 Agent 共用的任务状态。"""

    # 一、请求基本信息
    request_id: str
    user_question: str

    # 二、调度信息
    category: str
    risk_level: RiskLevel
    next_agent: AgentName
    route_history: list[str]

    # 三、知识检索信息
    retrieved_documents: list[dict[str, object]]
    citations: list[dict[str, str]]
    evidence_sufficient: bool

    # 四、回答信息
    draft_answer: str
    final_answer: str

    # 五、安全和人工确认信息
    requires_human_confirmation: bool
    pending_action: dict[str, object] | None

    # 六、错误记录
    errors: list[str]


def create_initial_state(question: str) -> SecurityAgentState:
    """根据用户问题创建一份全新的任务工作单。"""

    return {
        "messages": [HumanMessage(content=question)],
        "request_id": str(uuid4()),
        "user_question": question,
        "category": "unclassified",
        "risk_level": "unknown",
        "next_agent": "supervisor",
        "route_history": [],
        "retrieved_documents": [],
        "citations": [],
        "evidence_sufficient": False,
        "draft_answer": "",
        "final_answer": "",
        "requires_human_confirmation": False,
        "pending_action": None,
        "errors": [],
    }