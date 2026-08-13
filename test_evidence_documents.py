from backend.app.multi_agent.evidence import (
    ensure_doc_code_allowed,
)
from backend.app.multi_agent.graph import (
    security_agent_graph,
)
from backend.app.multi_agent.state import (
    create_initial_state,
)


TEST_CASES = [
    {
        "name": "内部应急资料",
        "question": (
            "住院部三楼已经起火并出现"
            "大量浓烟，应该如何处置？"
        ),
        "expected_category": "emergency",
        "expected_prefix": "ER-",
    },
    {
        "name": "深圳消防法规资料",
        "question": (
            "深圳医院消防控制室值班人员"
            "和每日防火巡查适用哪些法规条款？"
        ),
        "expected_category": (
            "fire_compliance"
        ),
        "expected_prefix": "FIRE-",
    },
]


last_state = None


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

    last_state = final_state

    print(
        "业务类别：",
        final_state["category"],
    )
    print(
        "候选白名单：",
        final_state["allowed_doc_codes"],
    )
    print(
        "成功打开：",
        final_state["opened_doc_codes"],
    )
    print(
        "打开次数：",
        final_state[
            "document_open_attempts"
        ],
    )
    print(
        "证据是否充分：",
        final_state[
            "evidence_sufficient"
        ],
    )
    print(
        "流程路线：",
        final_state["route_history"],
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
        "controlled_retrieval"
        in final_state["route_history"]
    )

    assert (
        "open_evidence_documents"
        in final_state["route_history"]
    )

    assert final_state[
        "allowed_doc_codes"
    ]

    assert final_state[
        "opened_documents"
    ]

    assert final_state[
        "opened_doc_codes"
    ]

    assert final_state[
        "citations"
    ]

    assert (
        final_state["evidence_sufficient"]
        is True
    )

    assert (
        1
        <= len(
            final_state[
                "opened_documents"
            ]
        )
        <= 3
    )

    assert (
        final_state[
            "document_open_attempts"
        ]
        == min(
            3,
            len(
                final_state[
                    "allowed_doc_codes"
                ]
            ),
        )
    )

    whitelist = set(
        final_state["allowed_doc_codes"]
    )

    opened_codes = set(
        final_state["opened_doc_codes"]
    )

    assert opened_codes.issubset(
        whitelist
    )

    reference_ids = {
        str(
            citation["reference_id"]
        )
        for citation
        in final_state["citations"]
    }

    for document in final_state[
        "opened_documents"
    ]:
        doc_code = str(
            document["doc_code"]
        )

        print(
            "完整资料：",
            doc_code,
            document["title"],
        )

        print(
            "资料警告：",
            document["warnings"],
        )

        assert doc_code.startswith(
            test_case["expected_prefix"]
        )

        assert document["full_text"]

        assert (
            f"[{doc_code}]"
            in reference_ids
        )

    if (
        test_case["expected_category"]
        == "fire_compliance"
    ):
        assert any(
            document[
                "legal_citation_ready"
            ]
            is True
            for document
            in final_state[
                "opened_documents"
            ]
        )

    print("本条完整资料测试通过")


print("\n" + "=" * 70)
print("测试伪造doc_code是否会被阻止")

try:
    ensure_doc_code_allowed(
        doc_code="FORGED-999",
        allowed_doc_codes=(
            last_state[
                "allowed_doc_codes"
            ]
        ),
    )

except PermissionError as error:
    print(
        "伪造doc_code已被正确阻止：",
        error,
    )

else:
    raise AssertionError(
        "系统没有阻止伪造doc_code"
    )


print("\n第7关全部测试通过")