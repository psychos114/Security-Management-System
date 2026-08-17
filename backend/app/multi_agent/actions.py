from langgraph.types import interrupt

from backend.app.multi_agent.state import (
    SecurityAgentState,
)

from datetime import datetime
from datetime import timezone

ACTION_LABELS = {
    "create_work_order": "创建处置工单",
    "notify_personnel": "通知相关人员",
    "escalate_event": "升级并上报事件",
}


ACTION_RULES = {
    "create_work_order": (
        "派单",
        "创建工单",
        "生成工单",
        "派工",
    ),
    "notify_personnel": (
        "通知人员",
        "通知相关人员",
        "通知班长",
        "通知安管经理",
        "通知项目经理",
    ),
    "escalate_event": (
        "升级事件",
        "事件升级",
        "上报事件",
        "上报领导",
    ),
}

def get_allowed_confirmer_role_codes(
    risk_level: str,
) -> list[str]:
    """根据风险等级确定允许审批的角色。"""

    if risk_level == "critical":
        return [
            "security_manager",
        ]

    if risk_level == "high":
        return [
            "security_manager",
            "project_manager",
        ]

    return [
        "squad_leader",
        "security_manager",
        "project_manager",
    ]

def collect_action_types(
    state: SecurityAgentState,
) -> list[str]:
    """根据业务类别和问题生成待确认动作。"""

    action_types = []

    # 紧急事件默认建议派单、通知和升级。
    if state["category"] == "emergency":
        action_types.extend([
            "create_work_order",
            "notify_personnel",
            "escalate_event",
        ])

    question = state["user_question"]

    for action_type, keywords in (
        ACTION_RULES.items()
    ):
        if any(
            keyword in question
            for keyword in keywords
        ):
            action_types.append(action_type)

    # 去掉重复动作，同时保持原顺序。
    return list(dict.fromkeys(action_types))


def prepare_pending_action_node(
    state: SecurityAgentState,
):
    """生成动作建议，但不执行任何真实操作。"""

    print("关键动作准备节点正在工作")

    route_history = (
        state["route_history"]
        + ["prepare_action"]
    )

    # 回答没有通过证据检查时，不允许提出动作。
    if state["answer_status"] != "generated":
        return {
            "requires_human_confirmation": False,
            "pending_action": None,
            "confirmation_status": "not_required",
            "route_history": route_history,
        }

    action_types = collect_action_types(state)

    if not action_types:
        return {
            "requires_human_confirmation": False,
            "pending_action": None,
            "confirmation_status": "not_required",
            "route_history": route_history,
        }

    action_labels = [
        ACTION_LABELS[action_type]
        for action_type in action_types
    ]

    allowed_confirmer_role_codes = (
        get_allowed_confirmer_role_codes(
            state["risk_level"]
        )
    )

    pending_action = {
        "action_id": (
            f"{state['request_id']}-A001"
        ),
        "allowed_confirmer_role_codes": (
            allowed_confirmer_role_codes
        ),
        "action_types": action_types,
        "summary": (
            "建议执行："
            + "、".join(action_labels)
        ),
        "category": state["category"],
        "risk_level": state["risk_level"],
        "status": "pending_confirmation",
        "executed": False,
    }

    return {
        "requires_human_confirmation": True,
        "pending_action": pending_action,
        "confirmation_status": "pending",
        "allowed_confirmer_role_codes": (
            allowed_confirmer_role_codes
        ),
        "confirmed_by": "",
        "confirmed_by_user_id": None,
        "confirmation_note": "",
        "route_history": route_history,
    }


def route_after_action_preparation(
    state: SecurityAgentState,
):
    """决定是否进入人工确认节点。"""

    if (
        state["confirmation_status"] == "pending"
        and state["pending_action"] is not None
    ):
        return "human_confirmation"

    return "finish"


def human_confirmation_node(
    state: SecurityAgentState,
):
    """暂停LangGraph，等待人工批准或拒绝。"""

    decision = interrupt({
        "type": "human_confirmation",
        "request_id": state["request_id"],
        "message": "关键动作必须经过人工确认。",
        "pending_action": state["pending_action"],
        "allowed_decisions": [
            "approve",
            "reject",
        ],
    })

    if not isinstance(decision, dict):
        decision = {}

    operator = str(
        decision.get("operator", "")
    ).strip()

    raw_operator_user_id = decision.get(
        "operator_user_id",
        0,
    )

    try:
        operator_user_id = int(
            raw_operator_user_id
        )
    except (TypeError, ValueError):
        operator_user_id = 0

    note = str(
        decision.get("note", "")
    ).strip()

    approved = (
        decision.get("approved") is True
        and bool(operator)
    )

    if not operator:
        operator = "未填写"
        note = (
            "没有填写确认人，"
            "系统按照拒绝处理。"
        )

    pending_action = dict(
        state["pending_action"] or {}
    )

    pending_action["confirmed_by"] = operator
    pending_action["confirmation_note"] = note
    pending_action["executed"] = False

    if approved:
        confirmation_status = "approved"
        pending_action["status"] = (
            "approved_not_executed"
        )

        confirmation_text = (
            "人工确认结果\n"
            f"- 确认人：{operator}\n"
            "- 结果：已批准关键动作建议。\n"
            "- 执行状态：尚未执行。\n"
            "- 说明：当前学习版本只记录审批结果，"
            "尚未连接真实派单、通知或上报系统。"
        )
    else:
        confirmation_status = "rejected"
        pending_action["status"] = "rejected"

        confirmation_text = (
            "人工确认结果\n"
            f"- 确认人：{operator}\n"
            "- 结果：已拒绝关键动作建议。\n"
            "- 执行状态：不会执行。"
        )

    audit_entry = {
        "request_id": state["request_id"],
        "initiator_user_id": state.get(
            "initiator_user_id",
            0,
        ),
        "confirmer_user_id": operator_user_id,
        "confirmer_name": operator,
        "decision": (
            "approved"
            if approved
            else "rejected"
        ),
        "note": note,
        "confirmed_at": (
            datetime.now(
                timezone.utc
            ).isoformat()
        ),
    }

    return {
        "requires_human_confirmation": False,
        "pending_action": pending_action,
        "confirmation_status": confirmation_status,
        "confirmed_by": operator,
        "confirmation_note": note,
        "final_answer": (
            state["final_answer"].rstrip()
            + "\n\n"
            + confirmation_text
        ),
        "route_history": (
            state["route_history"]
            + ["human_confirmation"]
        ),
        "confirmed_by_user_id": (
            operator_user_id
            if operator_user_id > 0
            else None
        ),
        "confirmation_audit": (
            list(
                state.get(
                    "confirmation_audit",
                    [],
                )
            )
            + [audit_entry]
        ),
    }