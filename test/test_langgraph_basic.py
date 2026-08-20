import _project_path  # noqa: F401

from typing import TypedDict

from langgraph.graph import END, START, StateGraph


# State表示整个流程共同使用的数据
class DemoState(TypedDict):
    question: str
    category: str
    result: str


# 第一个节点：接收并分类问题
def classify_question(state: DemoState):
    print("节点1：正在判断问题类型")
    print("收到的问题：", state["question"])

    return {
        "category": "突发事件"
    }


# 第二个节点：根据分类处理问题
def handle_question(state: DemoState):
    print("节点2：正在处理问题")
    print("问题类别：", state["category"])

    return {
        "result": "问题已经交给突发事件处理流程"
    }


# 第三个节点：输出处理结果
def finish_process(state: DemoState):
    print("节点3：流程处理完成")
    print("处理结果：", state["result"])

    return {}


# 创建一张使用DemoState的流程图
builder = StateGraph(DemoState)

# 向流程图中添加三个节点
builder.add_node("classify_question", classify_question)
builder.add_node("handle_question", handle_question)
builder.add_node("finish_process", finish_process)

# 使用边连接节点，规定执行顺序
builder.add_edge(START, "classify_question")
builder.add_edge("classify_question", "handle_question")
builder.add_edge("handle_question", "finish_process")
builder.add_edge("finish_process", END)

# 检查并编译流程图
graph = builder.compile()

# 给流程图传入初始状态并开始运行
final_state = graph.invoke(
    {
        "question": "住院部发生火灾应该怎么办？",
        "category": "",
        "result": "",
    }
)

print("\n最终状态：")
print(final_state)
