from backend.app.multi_agent.answering import (
    emergency_answer_node,
)
from backend.app.multi_agent.graph import (
    security_agent_graph,
)
from backend.app.multi_agent.state import (
    create_initial_state,
)


TEST_CASES = [
    {
        "name": "突发事件回答",
        "question": (
            "住院部三楼已经起火并出现"
            "大量浓烟，现场应该如何处置？"
        ),
        "expected_category": "emergency",
        "expected_answer_node": (
            "emergency_answer"
        ),
        "expected_prefixes": ("ER-",),
    },
    {
        "name": "巡检文字回答",
        "question": (
            "地下停车场消防车道的照片"
            "应该重点检查哪些漏检项目？"
        ),
        "expected_category": "inspection",
        "expected_answer_node": (
            "inspection_answer"
        ),
        "expected_prefixes": (
            "INS-",
            "MM-GUIDE-",
        ),
    },
    {
        "name": "投诉处理回答",
        "question": (
            "医护人员反映门岗未登记访客，"
            "投诉受理、SLA和回访如何安排？"
        ),
        "expected_category": (
            "complaint_report"
        ),
        "expected_answer_node": (
            "complaint_report_answer"
        ),
        "expected_prefixes": (
            "COMP-GUIDE-",
            "DAILY-GUIDE-",
            "MM-GUIDE-",
        ),
    },
    {
        "name": "深圳消防法规回答",
        "question": (
            "深圳医院消防控制室值班人员"
            "和每日防火巡查适用哪些法规条款？"
        ),
        "expected_category": (
            "fire_compliance"
        ),
        "expected_answer_node": (
            "fire_compliance_answer"
        ),
        "expected_prefixes": ("FIRE-",),
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
        "业务类别：",
        final_state["category"],
    )
    print(
        "回答状态：",
        final_state["answer_status"],
    )
    print(
        "回答模型调用次数：",
        final_state[
            "answer_generation_attempts"
        ],
    )
    print(
        "回答使用资料：",
        final_state["used_doc_codes"],
    )
    print(
        "回答是否通过检查：",
        final_state[
            "answer_validation_passed"
        ],
    )
    print(
        "流程路线：",
        final_state["route_history"],
    )
    print(
        "最终回答：\n",
        final_state["final_answer"],
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
        test_case["expected_answer_node"]
        in final_state["route_history"]
    )

    assert (
        final_state["answer_status"]
        == "generated"
    )

    assert (
        final_state[
            "answer_generation_attempts"
        ]
        == 1
    )

    assert (
        final_state[
            "answer_validation_passed"
        ]
        is True
    )

    assert final_state[
        "used_doc_codes"
    ]

    opened_codes = set(
        final_state["opened_doc_codes"]
    )

    used_codes = set(
        final_state["used_doc_codes"]
    )

    assert used_codes.issubset(
        opened_codes
    )

    for doc_code in used_codes:
        assert doc_code.startswith(
            test_case[
                "expected_prefixes"
            ]
        )

        assert (
            f"[{doc_code}]"
            in final_state[
                "final_answer"
            ]
        )

    assert (
        "参考资料"
        in final_state["final_answer"]
    )

    assert (
        "已派单"
        not in final_state["final_answer"]
    )

    assert (
        "已通知相关人员"
        not in final_state["final_answer"]
    )

    if (
        test_case["expected_category"]
        == "emergency"
    ):
        assert (
            "需要人工确认"
            in final_state["final_answer"]
        )

    if (
        test_case["expected_category"]
        == "inspection"
    ):
        assert (
            "本次没有提供结构化图片分析结果"
            in final_state["final_answer"]
        )

    if (
        test_case["expected_category"]
        == "fire_compliance"
    ):
        documents_by_code = {
            str(
                document["doc_code"]
            ): document
            for document
            in final_state[
                "opened_documents"
            ]
        }

        for doc_code in used_codes:
            document = (
                documents_by_code[
                    doc_code
                ]
            )

            assert (
                document[
                    "legal_citation_ready"
                ]
                is True
            )

            citation = document[
                "citation"
            ]

            assert (
                citation["official_url"]
                in final_state[
                    "final_answer"
                ]
            )

            assert (
                str(
                    citation[
                        "published_date"
                    ]
                )
                in final_state[
                    "final_answer"
                ]
            )

            assert (
                str(
                    citation[
                        "citation_locator"
                    ]
                )
                in final_state[
                    "final_answer"
                ]
            )

    print("本条专业回答测试通过")


print("\n" + "=" * 70)
print("测试证据不足时是否停止生成")


empty_state = create_initial_state(
    "发生火灾应该怎么办？"
)

empty_state.update({
    "category": "emergency",
    "risk_level": "critical",
    "requires_human_confirmation": True,
    "evidence_sufficient": False,
    "opened_documents": [],
    "opened_doc_codes": [],
})


blocked_result = emergency_answer_node(
    empty_state
)


print(
    "证据不足回答状态：",
    blocked_result["answer_status"],
)
print(
    "证据不足提示：",
    blocked_result["draft_answer"],
)


assert (
    blocked_result["answer_status"]
    == "evidence_insufficient"
)

assert (
    blocked_result[
        "answer_validation_passed"
    ]
    is False
)

assert (
    blocked_result.get(
        "answer_generation_attempts",
        0,
    )
    == 0
)

assert (
    "证据不足"
    in blocked_result["draft_answer"]
)


print("证据不足保护测试通过")
print("\n第8关全部测试通过")
