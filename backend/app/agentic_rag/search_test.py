from backend.app.agentic_rag.retriever import (
    SemanticRetriever,
)


def print_results(query, results):
    print()
    print("=" * 72)
    print(f"检索问题：{query}")
    print(f"命中数量：{len(results)}")
    print("=" * 72)

    if not results:
        print("没有找到相关资料。")
        return

    for position, item in enumerate(
        results,
        start=1,
    ):
        print()
        print(
            f"{position}. "
            f"[{item['doc_code']}] "
            f"{item['title']}"
        )

        print(
            f"   相似度：{item['score']}"
        )

        print(
            f"   分类：{item['category']}"
        )

        if item["citation_locator"]:
            print(
                "   引用位置："
                f"{item['citation_locator']}"
            )

        if item["source_title"]:
            print(
                "   资料来源："
                f"{item['source_title']}"
            )

        if item["validity_status"]:
            print(
                "   有效状态："
                f"{item['validity_status']}"
            )

        if item["official_url"]:
            print(
                "   官方链接："
                f"{item['official_url']}"
            )

        print(
            f"   内容摘要：{item['snippet']}"
        )


def main():
    print("=" * 72)
    print("医院物业安管系统——FAISS语义检索测试")
    print("=" * 72)
    print("输入自然语言问题进行搜索。")
    print("输入 exit 退出。")

    retriever = SemanticRetriever()

    print(
        "索引加载成功："
        f"{retriever.index.ntotal}个向量"
    )

    while True:
        print()

        query = input(
            "请输入检索问题："
        ).strip()

        if not query:
            continue

        if query.lower() in {
            "exit",
            "quit",
            "退出",
        }:
            print("检索测试结束。")
            break

        try:
            results = retriever.search(
                query=query,
                top_k=5,
            )
        except Exception as error:
            print(
                f"检索失败：{error}"
            )
            continue

        print_results(
            query,
            results,
        )


if __name__ == "__main__":
    main()