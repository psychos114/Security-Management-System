from backend.app.agentic_rag.document_reader import (
    KnowledgeDocumentReader,
)


def print_document(document):
    print("\n" + "=" * 70)
    print(
        f"资料编号：{document['doc_code']}"
    )
    print(
        f"标题：{document['title']}"
    )
    print(
        f"分类：{document['category']}"
    )
    print(
        f"辖区：{document['jurisdiction']}"
    )
    print(
        f"知识片段数量："
        f"{document['chunk_count']}"
    )
    print(
        f"是否官方资料："
        f"{document['is_official']}"
    )
    print(
        f"是否需要人工复核："
        f"{document['requires_human_review']}"
    )
    print(
        f"是否满足法规引用条件："
        f"{document['legal_citation_ready']}"
    )

    citation = document["citation"]

    print("\n引用信息：")
    print(
        f"引用编号："
        f"{citation['reference_id']}"
    )
    print(
        f"法规或来源名称："
        f"{citation['source_title']}"
    )
    print(
        f"发布机关："
        f"{citation['issuing_authority']}"
    )
    print(
        f"文号："
        f"{citation['document_number']}"
    )
    print(
        f"条款或位置："
        f"{citation['citation_locator']}"
    )
    print(
        f"发布日期："
        f"{citation['published_date']}"
    )
    print(
        f"有效状态："
        f"{citation['validity_status']}"
    )
    print(
        f"官方链接："
        f"{citation['official_url']}"
    )

    if document["warnings"]:
        print("\n安全提醒：")

        for warning in document["warnings"]:
            print(f"- {warning}")

    print("\n正文预览：")

    preview = document["full_text"][:1000]
    print(preview)

    if len(document["full_text"]) > 1000:
        print("\n……正文预览已截断")


def main():
    print("完整知识资料读取测试")
    print("输入检索结果中的doc_code")
    print("输入 exit 可以退出")

    reader = KnowledgeDocumentReader()

    while True:
        doc_code = input(
            "\n请输入资料编号："
        ).strip()

        if doc_code.lower() == "exit":
            print("测试结束")
            break

        try:
            document = reader.open_document(
                doc_code
            )

            print_document(document)

        except Exception as error:
            print("\n打开资料失败")
            print(
                f"错误类型："
                f"{type(error).__name__}"
            )
            print(
                f"错误信息：{error}"
            )


if __name__ == "__main__":
    main()