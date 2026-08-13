from backend.app.multi_agent.state import SecurityAgentState


# 消防法规类关键词
FIRE_COMPLIANCE_KEYWORDS = (
    "消防法规",
    "消防条例",
    "消防规范",
    "消防规定",
    "消防条款",
    "深圳消防",
    "法律依据",
    "法规依据",
)


# 巡检类关键词
INSPECTION_KEYWORDS = (
    "巡检",
    "漏检",
    "检查点",
    "风险点",
    "隐患",
    "照片",
    "图片",
)


# 投诉和日报类关键词
COMPLAINT_REPORT_KEYWORDS = (
    "投诉",
    "回访",
    "满意度",
    "责任部门",
    "超时",
    "SLA",
    "日报",
    "工作总结",
)


# 突发事件类关键词
EMERGENCY_KEYWORDS = (
    "火灾",
    "人员冲突",
    "打架",
    "设备故障",
    "停电",
    "困梯",
    "漏水",
    "车辆事故",
    "病人外出",
    "患者外出",
    "病人摔倒",
    "患者摔倒",
    "需要抢救",
    "患者抢救",
)


def supervisor_node(state: SecurityAgentState):
    """根据用户问题，决定下一步交给哪个专业 Agent。"""

    question = state["user_question"].strip()

    print("\n调度 Agent 正在分析：", question)

    # 消防法规判断必须放在火灾事件判断之前。
    # 否则“消防法规中的火灾条款”可能被错误分给突发事件 Agent。
    if any(keyword in question for keyword in FIRE_COMPLIANCE_KEYWORDS):
        return {
            "category": "fire_compliance",
            "risk_level": "medium",
            "next_agent": "fire_compliance_agent",
            "route_history": state["route_history"] + ["supervisor"],
        }

    if any(keyword in question for keyword in INSPECTION_KEYWORDS):
        return {
            "category": "inspection",
            "risk_level": "medium",
            "next_agent": "inspection_agent",
            "route_history": state["route_history"] + ["supervisor"],
        }

    if any(keyword in question for keyword in COMPLAINT_REPORT_KEYWORDS):
        return {
            "category": "complaint_report",
            "risk_level": "medium",
            "next_agent": "complaint_report_agent",
            "route_history": state["route_history"] + ["supervisor"],
        }

    if any(keyword in question for keyword in EMERGENCY_KEYWORDS):
        critical_keywords = (
            "火灾",
            "需要抢救",
            "患者抢救",
        )

        risk_level = (
            "critical"
            if any(keyword in question for keyword in critical_keywords)
            else "high"
        )

        return {
            "category": "emergency",
            "risk_level": risk_level,
            "next_agent": "emergency_agent",
            "route_history": state["route_history"] + ["supervisor"],
            "requires_human_confirmation": True,
        }

    return {
        "category": "general",
        "risk_level": "low",
        "next_agent": "finish",
        "route_history": state["route_history"] + ["supervisor"],
    }


def emergency_agent_node(state: SecurityAgentState):
    """模拟突发事件 Agent。"""

    print("突发事件 Agent 收到任务")

    return {
        "draft_answer": (
            "突发事件 Agent 已收到任务；"
            "当前尚未接入应急预案知识库。"
        ),
        "route_history": state["route_history"] + ["emergency_agent"],
        "requires_human_confirmation": True,
    }


def inspection_agent_node(state: SecurityAgentState):
    """模拟巡检与图片分析 Agent。"""

    print("巡检图片 Agent 收到任务")

    return {
        "draft_answer": (
            "巡检图片 Agent 已收到任务；"
            "当前尚未接入图片识别和巡检知识库。"
        ),
        "route_history": state["route_history"] + ["inspection_agent"],
    }


def complaint_report_agent_node(state: SecurityAgentState):
    """模拟投诉与日报 Agent。"""

    print("投诉日报 Agent 收到任务")

    return {
        "draft_answer": (
            "投诉日报 Agent 已收到任务；"
            "当前尚未接入投诉数据和日报生成工具。"
        ),
        "route_history": state["route_history"]
        + ["complaint_report_agent"],
    }


def fire_compliance_agent_node(state: SecurityAgentState):
    """模拟消防法规 Agent。"""

    print("消防法规 Agent 收到任务")

    return {
        "draft_answer": (
            "消防法规 Agent 已收到任务；"
            "当前尚未接入深圳消防法规知识库。"
        ),
        "route_history": state["route_history"]
        + ["fire_compliance_agent"],
    }


def finalize_answer_node(state: SecurityAgentState):
    """统一整理流程的最终结果。"""

    print("结果整理节点正在工作")

    draft_answer = state["draft_answer"]

    if not draft_answer:
        draft_answer = (
            "当前问题没有匹配到专业 Agent，"
            "请补充更具体的安管业务信息。"
        )

    return {
        "final_answer": draft_answer,
        "next_agent": "finish",
        "route_history": state["route_history"] + ["finalize_answer"],
    }