from backend.app.multi_agent.graph import (
    security_agent_graph,
)
from backend.app.multi_agent.state import (
    create_initial_state,
)


TEST_CASES = [
    {
        "name": "突发事件检索",
        "question": (
            "住院部三楼已经起火并出现大量浓烟，"
            "应该如何处置？"
        ),
        "expected_category": "emergency",
        "expected_agent": "emergency_agent",
        "allowed_categories": {
            "emergency_response"
        },
        "allowed_prefixes": (
            "ER-",
        ),
    },
    {
        "name": "巡检资料检索",
        "question": (
            "地下停车场消防车道的巡检照片"
            "应该重点检查哪些遗漏项目？"
        ),
        "expected_category": "inspection",
        "expected_agent": "inspection_agent",
        "allowed_categories": {
            "inspection",
            "multimodal",
        },
        "allowed_prefixes": (
            "INS-",
            "MM-GUIDE-",
        ),
    },
    {
        "name": "投诉资料检索",
        "question": (
            "医护人员反映门岗没有登记访客，"
            "投诉受理、SLA和回访应该如何安排？"
        ),
        "expected_category": "complaint_report",
        "expected_agent": (
            "complaint_report_agent"
        ),
        "allowed_categories": {
            "complaint",
            "daily_report",
            "multimodal",
        },
        "allowed_prefixes": (
            "COMP-GUIDE-",
            "DAILY-GUIDE-",
            "MM-GUIDE-",
        ),
    },
    {
        "name": "消防法规检索",
        "question": (
            "深圳医院消防控制室值班和"
            "每日防火巡查适用哪些法规条款？"
        ),
        "expected_category": "fire_compliance",
        "expected_agent": (
            "fire_compliance_agent"
        ),
        "allowed_categories": {
            "fire_assistant"
        },
        "allowed_prefixes": (
            "FIRE-",
        ),
    },
]


for index, test_case in enumerate(
    TEST_CASES,
    start=1,
):
    print("\n" + "=" * 70)
    print(
        f"测试 {index}："
        f"{test_case['name']}"
    )

    final_state = (
        security_agent_graph.invoke(
            create_initial_state(
                test_case["question"]
            )
        )
    )

    print(
        "业务分类：",
        final_state["category"],
    )
    print(
        "调度方式：",
        final_state["routing_method"],
    )
    print(
        "检索关键词：",
        final_state["search_keywords"],
    )
    print(
        "检索方式：",
        final_state["retrieval_method"],
    )
    print(
        "检索次数：",
        final_state["retrieval_attempts"],
    )
    print(
        "流程路线：",
        final_state["route_history"],
    )
    print(
        "允许打开的资料：",
        final_state["allowed_doc_codes"],
    )

    if final_state["errors"]:
        print(
            "错误记录：",
            final_state["errors"],
        )

    assert (
        final_state["category"]
        == test_case["expected_category"]
    )

    assert (
        test_case["expected_agent"]
        in final_state["route_history"]
    )

    assert (
        "controlled_retrieval"
        in final_state["route_history"]
    )

    assert (
        final_state["retrieval_method"]
        == "hybrid_search"
    )

    assert (
        final_state["retrieval_attempts"]
        == 1
    )

    assert (
        final_state["evidence_sufficient"]
        is True
    )

    assert final_state[
        "retrieved_documents"
    ]

    assert final_state[
        "allowed_doc_codes"
    ]

    # 检索片段暂时不能登记为正式引用
    assert final_state["citations"] == []

    for document in final_state[
        "retrieved_documents"
    ]:
        print(
            "候选资料：",
            document["doc_code"],
            document["title"],
            document["category"],
        )

        assert (
            document["category"]
            in test_case[
                "allowed_categories"
            ]
        )

        assert str(
            document["doc_code"]
        ).startswith(
            test_case["allowed_prefixes"]
        )

    retrieved_codes = [
        str(document["doc_code"])
        for document
        in final_state[
            "retrieved_documents"
        ]
    ]

    assert (
        final_state["allowed_doc_codes"]
        == retrieved_codes
    )

    print("本条受控检索测试通过")


print("\n第6关全部测试通过")