import _project_path  # noqa: F401

from langgraph.types import Command

from uuid import uuid4

from backend.app.multi_agent.hitl_graph import (
    security_agent_hitl_graph,
)
from backend.app.multi_agent.state import (
    create_initial_state,
)


QUESTION = (
    "住院部三楼已经起火并出现大量浓烟，"
    "系统应该如何处置？"
)


def run_confirmation_test(
    case_name: str,
    approved: bool,
):
    print("\n" + "=" * 70)
    print("测试：", case_name)

    config = {
        "configurable": {
            "thread_id": (
                f"human-confirmation-"
                f"{case_name}-{uuid4()}"
            )
        }
    }

    # 第一次运行：应在人工确认节点暂停。
    paused_state = (
        security_agent_hitl_graph.invoke(
            create_initial_state(QUESTION),
            config=config,
        )
    )

    interrupts = paused_state.get(
        "__interrupt__",
        [],
    )

    assert interrupts
    assert (
        paused_state["confirmation_status"]
        == "pending"
    )
    assert (
        paused_state["pending_action"]
        is not None
    )
    assert (
        paused_state["pending_action"][
            "executed"
        ]
        is False
    )

    print("流程已暂停：是")
    print(
        "待确认动作：",
        paused_state["pending_action"],
    )

    # 模拟安管经理作出人工决定。
    final_state = (
        security_agent_hitl_graph.invoke(
            Command(
                resume={
                    "approved": approved,
                    "operator": "安管经理",
                    "note": (
                        "已经核实现场情况。"
                    ),
                }
            ),
            config=config,
        )
    )

    expected_status = (
        "approved"
        if approved
        else "rejected"
    )

    assert (
        final_state["confirmation_status"]
        == expected_status
    )
    assert (
        final_state["pending_action"][
            "executed"
        ]
        is False
    )
    assert (
        "human_confirmation"
        in final_state["route_history"]
    )

    if approved:
        assert (
            final_state["pending_action"][
                "status"
            ]
            == "approved_not_executed"
        )
        assert (
            "尚未执行"
            in final_state["final_answer"]
        )
    else:
        assert (
            final_state["pending_action"][
                "status"
            ]
            == "rejected"
        )
        assert (
            "不会执行"
            in final_state["final_answer"]
        )

    print(
        "人工确认结果：",
        final_state["confirmation_status"],
    )
    print(
        "动作是否执行：",
        final_state["pending_action"][
            "executed"
        ],
    )


run_confirmation_test(
    case_name="approve",
    approved=True,
)

run_confirmation_test(
    case_name="reject",
    approved=False,
)

print("\n第9关全部测试通过")
