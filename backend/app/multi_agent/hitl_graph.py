from langgraph.checkpoint.memory import (
    InMemorySaver,
)
from langgraph.graph import (
    END,
    START,
    StateGraph,
)

from backend.app.multi_agent.actions import (
    human_confirmation_node,
    prepare_pending_action_node,
    route_after_action_preparation,
)
from backend.app.multi_agent.graph import (
    security_agent_graph,
)
from backend.app.multi_agent.state import (
    SecurityAgentState,
)


def build_security_agent_hitl_graph():
    """建立带人工确认的多Agent流程。"""

    builder = StateGraph(SecurityAgentState)

    # 先运行第8关已经完成的完整回答流程。
    builder.add_node(
        "answer_pipeline",
        security_agent_graph,
    )

    builder.add_node(
        "prepare_action",
        prepare_pending_action_node,
    )

    builder.add_node(
        "human_confirmation",
        human_confirmation_node,
    )

    builder.add_edge(
        START,
        "answer_pipeline",
    )

    builder.add_edge(
        "answer_pipeline",
        "prepare_action",
    )

    builder.add_conditional_edges(
        "prepare_action",
        route_after_action_preparation,
        {
            "human_confirmation": (
                "human_confirmation"
            ),
            "finish": END,
        },
    )

    builder.add_edge(
        "human_confirmation",
        END,
    )

    # 保存流程状态，人工确认后才能继续运行。
    checkpointer = InMemorySaver()

    return builder.compile(
        checkpointer=checkpointer
    )


security_agent_hitl_graph = (
    build_security_agent_hitl_graph()
)