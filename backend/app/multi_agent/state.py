from typing import Literal
from uuid import uuid4

from langchain_core.messages import HumanMessage
from langgraph.graph import MessagesState


AgentName = Literal[
    "supervisor",
    "emergency_agent",
    "inspection_agent",
    "complaint_report_agent",
    "fire_compliance_agent",
    "finish",
]

InputSource = Literal[
    "text",
    "inspection_image",
]

RiskLevel = Literal[
    "unknown",
    "low",
    "medium",
    "high",
    "critical",
]


RoutingMethod = Literal[
    "pending",
    "safety_rule",
    "source_rule",
    "ai",
    "keyword_fallback",
]


RetrievalMethod = Literal[
    "not_started",
    "hybrid_search",
]


AnswerStatus = Literal[
    "not_started",
    "generated",
    "evidence_insufficient",
    "model_error",
    "validation_failed",
]


ConfirmationStatus = Literal[
    "not_required",
    "pending",
    "approved",
    "rejected",
]


WebSearchStatus = Literal[
    "not_started",
    "not_required",
    "disabled",
    "required",
    "completed",
    "no_results",
    "failed",
]


class SecurityAgentState(MessagesState):
    """所有Agent共用的任务状态。"""

    # 一、请求基本信息
    request_id: str
    user_question: str
    input_source: InputSource
    visual_analysis_id: str
    visual_analysis: dict[str, object]
    initiator_user_id: int
    initiator_role_code: str
    initiator_display_name: str

    # 二、调度信息
    category: str
    risk_level: RiskLevel
    next_agent: AgentName
    route_history: list[str]
    routing_method: RoutingMethod
    routing_reason: str

    # 三、检索计划
    search_query: str
    search_keywords: list[str]
    allowed_knowledge_categories: list[str]

    # 四、知识检索结果
    retrieval_method: RetrievalMethod
    retrieval_attempts: int
    retrieved_documents: list[dict[str, object]]
    allowed_doc_codes: list[str]

    # 成功打开的完整资料
    document_open_attempts: int
    opened_documents: list[dict[str, object]]
    opened_doc_codes: list[str]

    # 只有成功打开资料后才能建立引用
    citations: list[dict[str, object]]
    evidence_sufficient: bool

    # 五、受控网页搜索
    web_search_allowed: bool
    web_search_required: bool
    web_search_reason: str
    web_search_status: WebSearchStatus
    web_search_attempts: int
    web_search_query: str
    web_search_results: list[dict[str, object]]
    web_citations: list[dict[str, object]]
    web_evidence_sufficient: bool

    # 六、回答信息
    answer_status: AnswerStatus
    answer_generation_attempts: int
    used_doc_codes: list[str]
    answer_validation_passed: bool
    draft_answer: str
    final_answer: str

    # 七、安全和人工确认信息
    requires_human_confirmation: bool
    pending_action: dict[str, object] | None
    confirmation_status: ConfirmationStatus
    allowed_confirmer_role_codes: list[str]
    confirmed_by: str
    confirmed_by_user_id: int | None
    confirmation_note: str
    confirmation_audit: list[dict[str, object]]

    # 八、错误记录
    errors: list[str]


def create_initial_state(
    question: str,
    *,
    initiator_user_id: int = 0,
    initiator_role_code: str = "system",
    initiator_display_name: str = "系统测试",
    input_source: InputSource = "text",
    visual_analysis_id: str = "",
    visual_analysis: (
        dict[str, object] | None
    ) = None,
    web_search_allowed: bool = False,
) -> SecurityAgentState:
    """根据用户问题创建一份新的任务工作单。"""

    return {
        "messages": [
            HumanMessage(content=question)
        ],
        "request_id": str(uuid4()),
        "user_question": question,
        "input_source": input_source,
        "visual_analysis_id": visual_analysis_id,
        "visual_analysis": (
            visual_analysis or {}
        ),
        "initiator_user_id": (
            initiator_user_id
        ),
        "initiator_role_code": (
            initiator_role_code
        ),
        "initiator_display_name": (
            initiator_display_name
        ),
        "category": "unclassified",
        "risk_level": "unknown",
        "next_agent": "supervisor",
        "route_history": [],
        "routing_method": "pending",
        "routing_reason": "",
        "search_query": "",
        "search_keywords": [],
        "allowed_knowledge_categories": [],
        "retrieval_method": "not_started",
        "retrieval_attempts": 0,
        "retrieved_documents": [],
        "allowed_doc_codes": [],
        "document_open_attempts": 0,
        "opened_documents": [],
        "opened_doc_codes": [],
        "citations": [],
        "evidence_sufficient": False,
        "web_search_allowed": web_search_allowed,
        "web_search_required": False,
        "web_search_reason": "",
        "web_search_status": "not_started",
        "web_search_attempts": 0,
        "web_search_query": "",
        "web_search_results": [],
        "web_citations": [],
        "web_evidence_sufficient": False,
        "answer_status": "not_started",
        "answer_generation_attempts": 0,
        "used_doc_codes": [],
        "answer_validation_passed": False,
        "draft_answer": "",
        "final_answer": "",
        "requires_human_confirmation": False,
        "pending_action": None,
        "confirmation_status": "not_required",
        "allowed_confirmer_role_codes": [],
        "confirmed_by": "",
        "confirmed_by_user_id": None,
        "confirmation_note": "",
        "confirmation_audit": [],
        "errors": [],
    }
