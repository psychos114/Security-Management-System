from pathlib import Path
from tempfile import TemporaryDirectory

from langgraph.types import Command

from backend.app.multi_agent.checkpoint import (
    create_sqlite_checkpointer,
)
from backend.app.multi_agent.hitl_graph import (
    build_security_agent_hitl_graph,
)
from backend.app.multi_agent.state import (
    create_initial_state,
)


QUESTION = (
    "住院部三楼已经起火并出现大量浓烟，"
    "系统应该如何处置？"
)


print("=" * 70)
print("测试1：建立任务并暂停")


with TemporaryDirectory() as temp_directory:
    test_database_path = (
        Path(temp_directory)
        / "checkpoint_test.db"
    )

    saver_one, connection_one = (
        create_sqlite_checkpointer(
            test_database_path
        )
    )

    graph_one = (
        build_security_agent_hitl_graph(
            checkpointer=saver_one
        )
    )

    initial_state = create_initial_state(
        QUESTION
    )

    request_id = initial_state[
        "request_id"
    ]

    config = {
        "configurable": {
            "thread_id": request_id,
        }
    }

    paused_state = graph_one.invoke(
        initial_state,
        config=config,
    )

    assert paused_state.get(
        "__interrupt__"
    )

    assert (
        paused_state[
            "confirmation_status"
        ]
        == "pending"
    )

    assert (
        paused_state["pending_action"][
            "executed"
        ]
        is False
    )

    print(
        "任务已经暂停：",
        request_id,
    )

    # 关闭第一次连接，模拟后端停止。
    connection_one.close()


    print("\n" + "=" * 70)
    print("测试2：重新建立Graph并读取任务")

    saver_two, connection_two = (
        create_sqlite_checkpointer(
            test_database_path
        )
    )

    try:
        graph_two = (
            build_security_agent_hitl_graph(
                checkpointer=saver_two
            )
        )

        snapshot = graph_two.get_state(
            config
        )

        assert snapshot.values

        assert (
            snapshot.values[
                "confirmation_status"
            ]
            == "pending"
        )

        assert (
            "human_confirmation"
            in snapshot.next
        )

        print(
            "重启后读取到状态：",
            snapshot.values[
                "confirmation_status"
            ],
        )


        print("\n" + "=" * 70)
        print("测试3：恢复并批准任务")

        final_state = graph_two.invoke(
            Command(
                resume={
                    "approved": True,
                    "operator": "安管经理",
                    "note": (
                        "后端重启后完成确认"
                    ),
                }
            ),
            config=config,
        )

        assert (
            final_state[
                "confirmation_status"
            ]
            == "approved"
        )

        assert (
            final_state["pending_action"][
                "executed"
            ]
            is False
        )

        assert (
            "human_confirmation"
            in final_state[
                "route_history"
            ]
        )

        print(
            "恢复后的确认状态：",
            final_state[
                "confirmation_status"
            ],
        )

        print(
            "真实动作是否执行：",
            final_state[
                "pending_action"
            ]["executed"],
        )

    finally:
        connection_two.close()


print("\n第12关持久化测试全部通过")