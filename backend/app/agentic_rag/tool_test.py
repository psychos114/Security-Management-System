from backend.app.agentic_rag.tools import (
    RAG_TOOL_DEFINITIONS,
    RAGToolExecutor,
)


def print_registered_tools():
    print("已经注册的AI工具：")

    for tool in RAG_TOOL_DEFINITIONS:
        function = tool["function"]

        print(
            f"- {function['name']}"
        )


def print_search_response(
    title,
    response,
):
    print("\n" + "=" * 70)
    print(title)

    if not response["ok"]:
        print("工具执行失败")
        print(
            f"错误类型："
            f"{response['error_type']}"
        )
        print(
            f"错误信息："
            f"{response['error_message']}"
        )
        return None

    results = response["result"]

    print(
        f"返回资料数量：{len(results)}"
    )

    for item in results[:3]:
        print(
            f"- {item['doc_code']} "
            f"{item['title']}"
        )

    if results:
        return results[0]["doc_code"]

    return None


def print_document_response(response):
    print("\n" + "=" * 70)
    print("完整资料读取测试")

    if not response["ok"]:
        print("工具执行失败")
        print(
            f"错误类型："
            f"{response['error_type']}"
        )
        print(
            f"错误信息："
            f"{response['error_message']}"
        )
        return

    document = response["result"]
    citation = document["citation"]

    print(
        f"资料编号："
        f"{document['doc_code']}"
    )
    print(
        f"标题："
        f"{document['title']}"
    )
    print(
        f"片段数量："
        f"{document['chunk_count']}"
    )
    print(
        f"引用编号："
        f"{citation['reference_id']}"
    )
    print(
        f"来源名称："
        f"{citation['source_title']}"
    )
    print(
        f"发布日期："
        f"{citation['published_date']}"
    )
    print(
        f"来源链接："
        f"{citation['official_url']}"
    )
    print(
        f"正文长度："
        f"{len(document['full_text'])}"
    )


def main():
    print_registered_tools()

    executor = RAGToolExecutor()

    keyword_response = executor.execute(
        tool_name="keyword_search",
        arguments={
            "keywords": [
                "超时升级",
                "SLA",
                "安管经理",
            ],
            "top_k": 3,
        },
    )

    print_search_response(
        "1. 关键词工具测试",
        keyword_response,
    )

    semantic_response = executor.execute(
        tool_name="semantic_search",
        arguments={
            "query": (
                "医院的电梯里有人被困，"
                "保安应该如何处理？"
            ),
            "top_k": 3,
        },
    )

    print_search_response(
        "2. 语义工具测试",
        semantic_response,
    )

    hybrid_response = executor.execute(
        tool_name="hybrid_search",
        arguments={
            "query": (
                "巡检发现消防通道堆放杂物，"
                "应该怎么整改？"
            ),
            "keywords": [
                "消防通道",
                "堆放杂物",
                "立即清理",
            ],
            "top_k": 3,
        },
    )

    first_doc_code = print_search_response(
        "3. 混合工具测试",
        hybrid_response,
    )

    if first_doc_code:
        document_response = executor.execute(
            tool_name=(
                "open_knowledge_document"
            ),
            arguments={
                "doc_code": first_doc_code,
            },
        )

        print_document_response(
            document_response
        )

    unknown_response = executor.execute(
        tool_name="made_up_tool",
        arguments={},
    )

    print("\n" + "=" * 70)
    print("5. 不存在的工具测试")
    print(
        f"执行成功："
        f"{unknown_response['ok']}"
    )
    print(
        f"错误类型："
        f"{unknown_response['error_type']}"
    )

    print("\n全部工具调度测试结束")


if __name__ == "__main__":
    main()