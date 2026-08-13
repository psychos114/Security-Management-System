from langgraph.graph import END, START, StateGraph

from backend.app.multi_agent.nodes import (
    complaint_report_agent_node,
    emergency_agent_node,
    finalize_answer_node,
    fire_compliance_agent_node,
    inspection_agent_node,
    supervisor_node,
)
from backend.app.multi_agent.state import SecurityAgentState


def route_to_next_node(state: SecurityAgentState):
    """读取调度 Agent 的决定，返回下一节点名称。"""

    return state["next_agent"]


def build_security_agent_graph():
    """建立医院安管系统的多 Agent 流程图。"""

    builder = StateGraph(SecurityAgentState)

    # 添加调度节点
    builder.add_node("supervisor", supervisor_node)

    # 添加四个专业 Agent 节点
    builder.add_node("emergency_agent", emergency_agent_node)
    builder.add_node("inspection_agent", inspection_agent_node)
    builder.add_node(
        "complaint_report_agent",
        complaint_report_agent_node,
    )
    builder.add_node(
        "fire_compliance_agent",
        fire_compliance_agent_node,
    )

    # 添加统一结果整理节点
    builder.add_node("finalize_answer", finalize_answer_node)

    # 所有任务首先进入调度 Agent
    builder.add_edge(START, "supervisor")

    # 根据next_agent字段选择不同路线
    builder.add_conditional_edges(
        "supervisor",
        route_to_next_node,
        {
            "emergency_agent": "emergency_agent",
            "inspection_agent": "inspection_agent",
            "complaint_report_agent": "complaint_report_agent",
            "fire_compliance_agent": "fire_compliance_agent",
            "finish": "finalize_answer",
        },
    )

    # 四个专业 Agent 完成工作后，都进入结果整理节点
    builder.add_edge("emergency_agent", "finalize_answer")
    builder.add_edge("inspection_agent", "finalize_answer")
    builder.add_edge(
        "complaint_report_agent",
        "finalize_answer",
    )
    builder.add_edge(
        "fire_compliance_agent",
        "finalize_answer",
    )

    # 结果整理完成后结束
    builder.add_edge("finalize_answer", END)

    return builder.compile()


# 创建一份可以直接调用的流程图
security_agent_graph = build_security_agent_graph()