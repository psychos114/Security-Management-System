import re

from backend.app.agentic_rag.hybrid_retriever import (
    HybridRetriever,
)


def print_results(results):
    if not results:
        print("\n没有找到相关资料。")
        return

    print(
        f"\n融合检索返回 {len(results)} 条资料："
    )

    for item in results:
        print("\n" + "=" * 70)

        methods = " + ".join(
            item["retrieval_methods"]
        )

        print(
            f"最终排名：{item['rank']}"
        )
        print(
            f"融合分值：{item['fusion_score']}"
        )
        print(
            f"检索来源：{methods}"
        )
        print(
            f"资料编号：{item['doc_code']}"
        )
        print(
            f"标题：{item['title']}"
        )
        print(
            f"分类：{item['category']}"
        )

        if item["semantic_rank"] is not None:
            print(
                f"语义检索排名："
                f"{item['semantic_rank']}"
            )
            print(
                f"语义相似度："
                f"{item['semantic_score']}"
            )

        if item["keyword_rank"] is not None:
            print(
                f"关键词检索排名："
                f"{item['keyword_rank']}"
            )
            print(
                f"关键词分值："
                f"{item['keyword_score']}"
            )

        if item["semantic_snippet"]:
            print(
                f"语义命中内容："
                f"{item['semantic_snippet']}"
            )

        if item["keyword_snippet"]:
            print(
                f"关键词命中内容："
                f"{item['keyword_snippet']}"
            )


def main():
    print("FAISS + SQLite混合检索测试")
    print("中文关键词最好不少于3个字符")
    print("问题位置输入 exit 可以退出")

    retriever = HybridRetriever()

    while True:
        question = input(
            "\n请输入完整问题："
        ).strip()

        if question.lower() == "exit":
            print("测试结束")
            break

        if not question:
            print("问题不能为空。")
            continue

        keyword_text = input(
            "请输入关键词，用逗号分隔："
        ).strip()

        keywords = [
            item.strip()
            for item in re.split(
                r"[,，;；]+",
                keyword_text,
            )
            if item.strip()
        ]

        try:
            results = retriever.search(
                query=question,
                keywords=keywords,
                top_k=5,
            )

            print_results(results)

        except Exception as error:
            print("\n混合检索失败")
            print(
                f"错误类型："
                f"{type(error).__name__}"
            )
            print(
                f"错误信息：{error}"
            )


if __name__ == "__main__":
    main()