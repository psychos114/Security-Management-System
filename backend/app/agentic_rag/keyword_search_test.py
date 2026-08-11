import re

from backend.app.agentic_rag.keyword_retriever import (
    KeywordRetriever,
)


def print_results(results):
    if not results:
        print("\n没有找到相关资料。")
        return

    print(f"\n共返回 {len(results)} 条资料：")

    for item in results:
        print("\n" + "=" * 70)
        print(
            f"排名：{item['rank']}"
        )
        print(
            f"关键词分值："
            f"{item['keyword_score']}"
        )
        print(
            f"资料编号：{item['doc_code']}"
        )
        print(
            f"分类：{item['category']}"
        )
        print(
            f"标题：{item['title']}"
        )
        print(
            f"命中位置：{item['snippet']}"
        )

        if item["citation_locator"]:
            print(
                f"引用位置："
                f"{item['citation_locator']}"
            )

        if item["published_date"]:
            print(
                f"发布日期："
                f"{item['published_date']}"
            )

        if item["official_url"]:
            print(
                f"来源链接："
                f"{item['official_url']}"
            )


def main():
    print("SQLite FTS5关键词检索测试")
    print("多个关键词之间请使用逗号分隔")
    print("中文关键词最好不少于3个字符")
    print("输入 exit 可以退出")

    retriever = KeywordRetriever()

    while True:
        raw_text = input(
            "\n请输入关键词："
        ).strip()

        if raw_text.lower() == "exit":
            print("测试结束")
            break

        if not raw_text:
            print("请输入关键词。")
            continue

        keywords = [
            item.strip()
            for item in re.split(
                r"[,，;；]+",
                raw_text,
            )
            if item.strip()
        ]

        try:
            results = retriever.search(
                keywords=keywords,
                top_k=5,
            )

            print_results(results)

        except Exception as error:
            print("\n关键词检索失败")
            print(
                f"错误类型："
                f"{type(error).__name__}"
            )
            print(
                f"错误信息：{error}"
            )


if __name__ == "__main__":
    main()