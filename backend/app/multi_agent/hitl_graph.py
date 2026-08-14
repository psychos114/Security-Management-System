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
from backend.app.multi_agent.checkpoint import (
    sqlite_checkpointer,
)
from backend.app.multi_agent.graph import (
    security_agent_graph,
)
from backend.app.multi_agent.state import (
    SecurityAgentState,
)


def build_security_agent_hitl_graph(
    checkpointer=None,
):
    """建立带持久化人工确认的多Agent流程。"""

    builder = StateGraph(
        SecurityAgentState
    )

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

    if checkpointer is None:
        checkpointer = sqlite_checkpointer

    return builder.compile(
        checkpointer=checkpointer
    )


security_agent_hitl_graph = (
    build_security_agent_hitl_graph()
)