import _project_path  # noqa: F401

from backend.app.multi_agent.graph import security_agent_graph
from backend.app.multi_agent.state import create_initial_state


TEST_CASES = [
    {
        "question": "住院部三楼发生火灾，请立即处理。",
        "expected_agent": "emergency_agent",
        "expected_category": "emergency",
        "expected_risk": "critical",
        "expected_confirmation": True,
    },
    {
        "question": "请根据这张巡检照片判断哪里存在漏检。",
        "expected_agent": "inspection_agent",
        "expected_category": "inspection",
        "expected_risk": "medium",
        "expected_confirmation": False,
    },
    {
        "question": "医护人员投诉保安未按要求登记，请处理。",
        "expected_agent": "complaint_report_agent",
        "expected_category": "complaint_report",
        "expected_risk": "medium",
        "expected_confirmation": False,
    },
    {
        "question": "请查询深圳消防法规中的消防巡检条款。",
        "expected_agent": "fire_compliance_agent",
        "expected_category": "fire_compliance",
        "expected_risk": "medium",
        "expected_confirmation": False,
    },
    {
        "question": "今天天气怎么样？",
        "expected_agent": None,
        "expected_category": "general",
        "expected_risk": "low",
        "expected_confirmation": False,
    },
]


for index, test_case in enumerate(TEST_CASES, start=1):
    print("\n" + "=" * 60)
    print(f"开始测试第 {index} 个问题")

    initial_state = create_initial_state(
        test_case["question"]
    )

    final_state = security_agent_graph.invoke(initial_state)

    assert final_state["category"] == test_case["expected_category"]
    assert final_state["risk_level"] == test_case["expected_risk"]

    assert (
        final_state["requires_human_confirmation"]
        is test_case["expected_confirmation"]
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

    assert final_state["next_agent"] == "finish"
    assert final_state["final_answer"]

    print("问题：", test_case["question"])
    print("分类：", final_state["category"])
    print("风险：", final_state["risk_level"])
    print("路线：", final_state["route_history"])
    print(
        "需要人工确认：",
        final_state["requires_human_confirmation"],
    )
    print("最终回答：", final_state["final_answer"])
    print("本条测试通过")


print("\n第4关全部测试通过")
