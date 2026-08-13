from backend.app.agentic_rag.tools import (
    RAGToolExecutor,
)
from backend.app.multi_agent.state import (
    SecurityAgentState,
)


_tool_executor = None


def get_tool_executor() -> RAGToolExecutor:
    """只加载一次现有RAG工具和FAISS索引。"""

    global _tool_executor

    if _tool_executor is None:
        _tool_executor = RAGToolExecutor()

    return _tool_executor


def controlled_retrieval_node(
    state: SecurityAgentState,
):
    """执行固定、受限的第一次混合检索。"""

    print("受控混合检索节点正在工作")
    print("语义问题：", state["search_query"])
    print("关键词：", state["search_keywords"])
    print(
        "允许的知识类别：",
        state["allowed_knowledge_categories"],
    )

    route_history = (
        state["route_history"]
        + ["controlled_retrieval"]
    )

    try:
        executor = get_tool_executor()

        tool_result = executor.execute(
            tool_name="hybrid_search",
            arguments={
                "query": (
                    state["search_query"]
                    or state["user_question"]
                ),
                "keywords": state["search_keywords"],
                # 先取得10个候选，再执行类别限制
                "top_k": 10,
            },
        )

        if not tool_result.get("ok"):
            error_message = str(
                tool_result.get(
                    "error_message",
                    "未知检索错误",
                )
            )

            return {
                "retrieval_method": "hybrid_search",
                "retrieval_attempts": (
                    state["retrieval_attempts"] + 1
                ),
                "retrieved_documents": [],
                "allowed_doc_codes": [],
                "evidence_sufficient": False,
                "draft_answer": (
                    "知识库检索失败，暂时不能生成"
                    "有资料依据的正式回答。"
                ),
                "route_history": route_history,
                "errors": state["errors"] + [
                    "controlled retrieval failed: "
                    + error_message
                ],
            }

        raw_results = tool_result.get(
            "result",
            [],
        )

        if not isinstance(raw_results, list):
            raise TypeError(
                "混合检索结果必须是列表"
            )

        allowed_categories = set(
            state["allowed_knowledge_categories"]
        )

        filtered_documents = []

        for item in raw_results:
            if not isinstance(item, dict):
                continue

            if (
                item.get("category")
                not in allowed_categories
            ):
                continue

            filtered_documents.append(
                dict(item)
            )

            # 最终最多保留5份候选资料
            if len(filtered_documents) >= 5:
                break

        allowed_doc_codes = []

        for item in filtered_documents:
            doc_code = str(
                item.get("doc_code", "")
            ).strip().upper()

            if (
                doc_code
                and doc_code
                not in allowed_doc_codes
            ):
                allowed_doc_codes.append(
                    doc_code
                )

        evidence_sufficient = bool(
            filtered_documents
        )

        if evidence_sufficient:
            labels = []

            for item in filtered_documents:
                labels.append(
                    "["
                    + str(item.get("doc_code", ""))
                    + "] "
                    + str(item.get("title", ""))
                )

            draft_answer = (
                "受控混合检索已经找到"
                f"{len(filtered_documents)}份候选资料："
                + "；".join(labels)
                + "。当前还没有打开资料正文，"
                "因此暂不生成正式业务结论。"
            )
        else:
            draft_answer = (
                "本次受控混合检索没有找到"
                "属于当前专业Agent范围的资料，"
                "暂时不能生成有依据的正式回答。"
            )

        return {
            "retrieval_method": "hybrid_search",
            "retrieval_attempts": (
                state["retrieval_attempts"] + 1
            ),
            "retrieved_documents": (
                filtered_documents
            ),
            "allowed_doc_codes": (
                allowed_doc_codes
            ),
            "evidence_sufficient": (
                evidence_sufficient
            ),
            # 这里只找到候选资料，还不能登记正式引用
            "citations": [],
            "draft_answer": draft_answer,
            "route_history": route_history,
        }

    except Exception as error:
        return {
            "retrieval_method": "hybrid_search",
            "retrieval_attempts": (
                state["retrieval_attempts"] + 1
            ),
            "retrieved_documents": [],
            "allowed_doc_codes": [],
            "evidence_sufficient": False,
            "draft_answer": (
                "知识库检索出现异常，暂时不能"
                "生成有资料依据的正式回答。"
            ),
            "route_history": route_history,
            "errors": state["errors"] + [
                (
                    "controlled retrieval exception: "
                    f"{type(error).__name__}: {error}"
                )
            ],
        }