from backend.app.multi_agent.state import (
    SecurityAgentState,
)


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


INSPECTION_KEYWORDS = (
    "巡检",
    "漏检",
    "检查点",
    "风险点",
    "隐患",
    "照片",
    "图片",
)


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


def collect_search_keywords(
    question: str,
    rules: tuple,
    default_keywords: tuple[str, ...],
) -> list[str]:
    """根据问题和业务类别生成受控关键词。"""

    keywords = []

    for triggers, search_terms in rules:
        if any(
            trigger in question
            for trigger in triggers
        ):
            for search_term in search_terms:
                if search_term not in keywords:
                    keywords.append(search_term)

    for keyword in default_keywords:
        if keyword not in keywords:
            keywords.append(keyword)

    # FTS5工具最多允许8个关键词
    return keywords[:8]


def supervisor_node(
    state: SecurityAgentState,
):
    """AI不可用时使用的关键词备用调度器。"""

    question = state["user_question"].strip()

    print("\n关键词备用调度器正在分析：", question)

    if any(
        keyword in question
        for keyword in FIRE_COMPLIANCE_KEYWORDS
    ):
        return {
            "category": "fire_compliance",
            "risk_level": "medium",
            "next_agent": "fire_compliance_agent",
            "route_history": (
                state["route_history"]
                + ["supervisor"]
            ),
        }

    if any(
        keyword in question
        for keyword in INSPECTION_KEYWORDS
    ):
        return {
            "category": "inspection",
            "risk_level": "medium",
            "next_agent": "inspection_agent",
            "route_history": (
                state["route_history"]
                + ["supervisor"]
            ),
        }

    if any(
        keyword in question
        for keyword in COMPLAINT_REPORT_KEYWORDS
    ):
        return {
            "category": "complaint_report",
            "risk_level": "medium",
            "next_agent": "complaint_report_agent",
            "route_history": (
                state["route_history"]
                + ["supervisor"]
            ),
        }

    if any(
        keyword in question
        for keyword in EMERGENCY_KEYWORDS
    ):
        critical_keywords = (
            "火灾",
            "需要抢救",
            "患者抢救",
        )

        risk_level = (
            "critical"
            if any(
                keyword in question
                for keyword in critical_keywords
            )
            else "high"
        )

        return {
            "category": "emergency",
            "risk_level": risk_level,
            "next_agent": "emergency_agent",
            "route_history": (
                state["route_history"]
                + ["supervisor"]
            ),
            "requires_human_confirmation": True,
        }

    return {
        "category": "general",
        "risk_level": "low",
        "next_agent": "finish",
        "route_history": (
            state["route_history"]
            + ["supervisor"]
        ),
    }


def emergency_agent_node(
    state: SecurityAgentState,
):
    """为突发事件准备检索计划。"""

    print("突发事件Agent正在准备检索计划")

    question = state["user_question"]

    rules = (
        (
            ("火灾", "起火", "浓烟", "明火"),
            ("疑似火情", "火灾预案", "组织疏散"),
        ),
        (
            ("冲突", "打架", "持刀", "持械"),
            ("人员冲突", "安全距离", "保护现场"),
        ),
        (
            ("设备故障", "设备异常"),
            ("设备故障", "临时警戒"),
        ),
        (
            ("停电", "断电"),
            ("全院停电", "应急照明"),
        ),
        (
            ("困梯", "电梯被困"),
            ("人员被困", "电梯维保"),
        ),
        (
            ("漏水", "水管爆裂", "积水"),
            ("区域漏水", "电气风险"),
        ),
        (
            ("车辆事故", "车辆相撞"),
            ("车辆事故", "保护现场"),
        ),
        (
            ("病人外出", "患者外出"),
            ("患者外出", "外出申请"),
        ),
        (
            ("病人摔倒", "患者摔倒"),
            ("患者摔倒", "呼叫医护"),
        ),
        (
            ("抢救", "危急"),
            ("抢救协助", "保持通道"),
        ),
    )

    keywords = collect_search_keywords(
        question=question,
        rules=rules,
        default_keywords=(
            "突发事件",
            "应急处置",
        ),
    )

    return {
        "search_query": question,
        "search_keywords": keywords,
        "allowed_knowledge_categories": [
            "emergency_response"
        ],
        "route_history": (
            state["route_history"]
            + ["emergency_agent"]
        ),
        "requires_human_confirmation": True,
    }


def inspection_agent_node(
    state: SecurityAgentState,
):
    """为巡检任务准备检索计划。"""

    print("巡检Agent正在准备检索计划")

    question = state["user_question"]

    rules = (
        (
            ("走廊", "病区"),
            ("病区走廊", "照片巡检"),
        ),
        (
            ("消防通道", "楼梯", "疏散通道"),
            ("消防通道", "楼梯间"),
        ),
        (
            ("消防控制室", "控制室"),
            ("消防控制室", "人工复核"),
        ),
        (
            ("配电", "应急供电"),
            ("配电区域", "应急供电"),
        ),
        (
            ("电梯厅", "电梯"),
            ("电梯厅", "可见异常"),
        ),
        (
            ("停车场", "车库", "车辆通道"),
            ("停车场", "车辆通道"),
        ),
        (
            ("供氧", "医用气体"),
            ("中心供氧", "医用气体"),
        ),
    )

    keywords = collect_search_keywords(
        question=question,
        rules=rules,
        default_keywords=(
            "照片巡检",
            "遗漏检查",
            "巡检清单",
        ),
    )

    return {
        "search_query": question,
        "search_keywords": keywords,
        "allowed_knowledge_categories": [
            "inspection",
            "multimodal",
        ],
        "route_history": (
            state["route_history"]
            + ["inspection_agent"]
        ),
    }


def complaint_report_agent_node(
    state: SecurityAgentState,
):
    """为投诉或日报任务准备检索计划。"""

    print("投诉日报Agent正在准备检索计划")

    question = state["user_question"]

    rules = (
        (
            ("投诉", "反映", "反馈"),
            ("投诉受理", "责任部门"),
        ),
        (
            ("SLA", "超时", "时限"),
            ("超时升级", "解决时限"),
        ),
        (
            ("回访", "满意度"),
            ("回访满意度", "再次打开"),
        ),
        (
            ("日报", "总结", "工作计划"),
            ("日报模板", "工作总结"),
        ),
        (
            ("纸质", "OCR", "通知"),
            ("纸质通知", "OCR录入"),
        ),
    )

    keywords = collect_search_keywords(
        question=question,
        rules=rules,
        default_keywords=(
            "投诉处理",
            "SLA管理",
            "日报生成",
        ),
    )

    return {
        "search_query": question,
        "search_keywords": keywords,
        "allowed_knowledge_categories": [
            "complaint",
            "daily_report",
            "multimodal",
        ],
        "route_history": (
            state["route_history"]
            + ["complaint_report_agent"]
        ),
    }


def fire_compliance_agent_node(
    state: SecurityAgentState,
):
    """为深圳消防法规查询准备检索计划。"""

    print("消防法规Agent正在准备检索计划")

    question = state["user_question"]

    rules = (
        (
            ("深圳", "深圳市"),
            ("深圳消防", "消防条例"),
        ),
        (
            ("控制室", "值班人员"),
            ("消防控制室", "值班人员"),
        ),
        (
            ("巡查", "检查"),
            ("每日防火巡查", "消防检查"),
        ),
        (
            ("医院", "医疗机构"),
            ("医疗机构消防", "医院消防"),
        ),
        (
            ("高层", "物业"),
            ("高层建筑", "物业职责"),
        ),
    )

    keywords = collect_search_keywords(
        question=question,
        rules=rules,
        default_keywords=(
            "深圳消防法规",
            "消防安全管理",
            "法规条款",
        ),
    )

    return {
        "search_query": question,
        "search_keywords": keywords,
        "allowed_knowledge_categories": [
            "fire_assistant"
        ],
        "route_history": (
            state["route_history"]
            + ["fire_compliance_agent"]
        ),
    }


def finalize_answer_node(
    state: SecurityAgentState,
):
    """统一整理流程的当前结果。"""

    print("结果整理节点正在工作")

    draft_answer = state["draft_answer"]

    if not draft_answer:
        draft_answer = (
            "当前问题没有匹配到专业Agent，"
            "请补充更具体的安管业务信息。"
        )

    return {
        "final_answer": draft_answer,
        "next_agent": "finish",
        "route_history": (
            state["route_history"]
            + ["finalize_answer"]
        ),
    }