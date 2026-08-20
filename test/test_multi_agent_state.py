import _project_path  # noqa: F401

from langgraph.graph import END, START, StateGraph

from backend.app.multi_agent.state import (
    SecurityAgentState,
    create_initial_state,
)


def mock_supervisor(state: SecurityAgentState):
    """暂时使用固定规则模拟调度 Agent。"""

    print("调度节点收到问题：", state["user_question"])

    if "火灾" in state["user_question"]:
        return {
            "category": "emergency",
            "risk_level": "critical",
            "next_agent": "emergency_agent",
            "route_history": state["route_history"] + ["supervisor"],
            "requires_human_confirmation": True,
        }

    return {
        "category": "general",
        "risk_level": "low",
        "next_agent": "finish",
        "route_history": state["route_history"] + ["supervisor"],
    }


# 创建测试流程图
builder = StateGraph(SecurityAgentState)

# 目前只添加一个模拟调度节点
builder.add_node("mock_supervisor", mock_supervisor)

# 规定流程顺序
builder.add_edge(START, "mock_supervisor")
builder.add_edge("mock_supervisor", END)

# 编译流程图
graph = builder.compile()

# 创建初始工作单
initial_state = create_initial_state(
    "住院部三楼发生火灾，请立即处理。"
)

# 运行流程
final_state = graph.invoke(initial_state)

# 自动检查结果
assert final_state["category"] == "emergency"
assert final_state["risk_level"] == "critical"
assert final_state["next_agent"] == "emergency_agent"
assert final_state["requires_human_confirmation"] is True
assert final_state["route_history"] == ["supervisor"]

print("\n共享状态测试通过")
print("请求编号：", final_state["request_id"])
print("问题类别：", final_state["category"])
print("风险等级：", final_state["risk_level"])
print("下一位 Agent：", final_state["next_agent"])
print("流转记录：", final_state["route_history"])
print("需要人工确认：", final_state["requires_human_confirmation"])
