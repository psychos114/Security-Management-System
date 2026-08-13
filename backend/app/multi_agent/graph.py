from langgraph.graph import (
    END,
    START,
    StateGraph,
)

from backend.app.multi_agent.nodes import (
    complaint_report_agent_node,
    emergency_agent_node,
    finalize_answer_node,
    fire_compliance_agent_node,
    inspection_agent_node,
)
from backend.app.multi_agent.retrieval import (
    controlled_retrieval_node,
)
from backend.app.multi_agent.state import (
    SecurityAgentState,
)
from backend.app.multi_agent.supervisor import (
    ai_supervisor_node,
)
from backend.app.multi_agent.evidence import (
    open_evidence_documents_node,
)

def route_to_next_node(
    state: SecurityAgentState,
):
    """读取调度结果，返回下一节点名称。"""

    return state["next_agent"]


def build_security_agent_graph():
    """建立医院安管系统多Agent流程图。"""

    builder = StateGraph(
        SecurityAgentState
    )

    builder.add_node(
        "supervisor",
        ai_supervisor_node,
    )

    builder.add_node(
        "emergency_agent",
        emergency_agent_node,
    )
    builder.add_node(
        "inspection_agent",
        inspection_agent_node,
    )
    builder.add_node(
        "complaint_report_agent",
        complaint_report_agent_node,
    )
    builder.add_node(
        "fire_compliance_agent",
        fire_compliance_agent_node,
    )

    builder.add_node(
        "controlled_retrieval",
        controlled_retrieval_node,
    )
    
    builder.add_node(
        "open_evidence_documents",
        open_evidence_documents_node,
    )

    builder.add_node(
        "finalize_answer",
        finalize_answer_node,
    )

    builder.add_edge(
        START,
        "supervisor",
    )

    builder.add_conditional_edges(
        "supervisor",
        route_to_next_node,
        {
            "emergency_agent": (
                "emergency_agent"
            ),
            "inspection_agent": (
                "inspection_agent"
            ),
            "complaint_report_agent": (
                "complaint_report_agent"
            ),
            "fire_compliance_agent": (
                "fire_compliance_agent"
            ),
            "finish": "finalize_answer",
        },
    )

    # 四个专业Agent都先进入统一检索节点
    builder.add_edge(
        "emergency_agent",
        "controlled_retrieval",
    )
    builder.add_edge(
        "inspection_agent",
        "controlled_retrieval",
    )
    builder.add_edge(
        "complaint_report_agent",
        "controlled_retrieval",
    )
    builder.add_edge(
        "fire_compliance_agent",
        "controlled_retrieval",
    )

    builder.add_edge(
        "controlled_retrieval",
        "open_evidence_documents",
    )

    builder.add_edge(
        "open_evidence_documents",
        "finalize_answer",
    )

    builder.add_edge(
        "finalize_answer",
        END,
    )

    return builder.compile()


security_agent_graph = (
    build_security_agent_graph()
)