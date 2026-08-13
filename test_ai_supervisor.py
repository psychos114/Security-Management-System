from backend.app.multi_agent.graph import (
    security_agent_graph,
)
from backend.app.multi_agent.state import (
    create_initial_state,
)


# 第一项由安全规则处理，不调用AI
SAFETY_CASE = {
    "question": (
        "住院部三楼发生火灾并伴有大量浓烟，"
        "请立即处理。"
    ),
    "expected_category": "emergency",
    "expected_agent": "emergency_agent",
    "expected_risk": "critical",
}


# 下面四项必须由AI理解语义并完成调度
AI_CASES = [
    {
        "question": (
            "请根据我上传的地下车库疏散通道照片，"
            "判断现场是否存在遗漏的检查项目。"
        ),
        "expected_category": "inspection",
        "expected_agent": "inspection_agent",
    },
    {
        "question": (
            "一名护士反映门岗多次没有核验探视人员，"
            "请登记并安排后续回复。"
        ),
        "expected_category": "complaint_report",
        "expected_agent": "complaint_report_agent",
    },
    {
        "question": (
            "深圳医院消防控制室值班人员"
            "应遵守哪些法规要求？请说明依据。"
        ),
        "expected_category": "fire_compliance",
        "expected_agent": "fire_compliance_agent",
    },
    {
        "question": (
            "请介绍一下这个系统可以做什么。"
        ),
        "expected_category": "general",
        "expected_agent": None,
    },
]


print("=" * 60)
print("测试安全规则")

safety_state = security_agent_graph.invoke(
    create_initial_state(
        SAFETY_CASE["question"]
    )
)

print("调度方式：", safety_state["routing_method"])
print("调度理由：", safety_state["routing_reason"])
print("流程路线：", safety_state["route_history"])

assert (
    safety_state["routing_method"]
    == "safety_rule"
)
assert (
    safety_state["category"]
    == SAFETY_CASE["expected_category"]
)
assert (
    safety_state["risk_level"]
    == SAFETY_CASE["expected_risk"]
)
assert (
    SAFETY_CASE["expected_agent"]
    in safety_state["route_history"]
)
assert (
    safety_state["requires_human_confirmation"]
    is True
)

print("安全规则测试通过")


for index, test_case in enumerate(
    AI_CASES,
    start=1,
):
    print("\n" + "=" * 60)
    print(f"测试第 {index} 个AI分类问题")

    final_state = security_agent_graph.invoke(
        create_initial_state(
            test_case["question"]
        )
    )

    print("问题：", test_case["question"])
    print("分类：", final_state["category"])
    print("风险：", final_state["risk_level"])
    print("调度方式：", final_state["routing_method"])
    print("调度理由：", final_state["routing_reason"])
    print("流程路线：", final_state["route_history"])

    if final_state["routing_method"] != "ai":
        print("错误记录：", final_state["errors"])

    assert final_state["routing_method"] == "ai", (
        "本题没有成功使用AI调度，"
        "请查看上方错误记录。"
    )

    assert (
        final_state["category"]
        == test_case["expected_category"]
    )

    if test_case["expected_agent"] is not None:
        assert (
            test_case["expected_agent"]
            in final_state["route_history"]
        )
    else:
        assert final_state["route_history"] == [
            "supervisor",
            "finalize_answer",
        ]

    print("本条AI调度测试通过")


print("\n第5关全部测试通过")