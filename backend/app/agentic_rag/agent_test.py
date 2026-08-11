from backend.app.agentic_rag.agent import (
    AgenticRAGService,
)


def print_result(result):
    print("\n" + "=" * 70)
    print("Agent最终回答：")
    print(result["answer"])

    print("\n" + "=" * 70)
    print("工具执行轨迹：")

    for item in result["tool_trace"]:
        print(
            f"第{item['round']}轮："
            f"{item['tool_name']}，"
            f"成功={item['ok']}"
        )

        if item.get("doc_codes"):
            print(
                "  检索结果："
                + ", ".join(
                    item["doc_codes"]
                )
            )

        if item.get("opened_doc_code"):
            print(
                "  打开资料："
                + item["opened_doc_code"]
            )

        if item.get("error_type"):
            print(
                "  错误："
                + item["error_type"]
                + " - "
                + item["error_message"]
            )

    print("\n运行统计：")
    print(
        f"模型轮数：{result['rounds']}"
    )
    print(
        f"工具调用数："
        f"{result['tool_calls']}"
    )
    print(
        "已经打开的资料："
        + ", ".join(
            result["opened_documents"]
        )
    )


def main():
    print("Agentic RAG交互测试")
    print("输入 exit 可以退出")
    print(
        "每个问题可能需要多轮模型和工具调用，"
        "请耐心等待。"
    )

    agent = AgenticRAGService()

    while True:
        question = input(
            "\n请输入问题："
        ).strip()

        if question.lower() == "exit":
            print("测试结束")
            break

        try:
            result = agent.ask(
                question
            )

            print_result(result)

        except Exception as error:
            print("\nAgent运行失败")
            print(
                f"错误类型："
                f"{type(error).__name__}"
            )
            print(
                f"错误信息：{error}"
            )
            print(
                "不要发送.env文件或真实密钥。"
            )


if __name__ == "__main__":
    main()