from backend.app.multi_agent.retrieval import (
    get_tool_executor,
)
from backend.app.multi_agent.state import (
    SecurityAgentState,
)


# 每次最多打开3份完整资料
MAX_DOCUMENTS_TO_OPEN = 3


def ensure_doc_code_allowed(
    doc_code: str,
    allowed_doc_codes: list[str],
) -> str:
    """检查资料编号是否在本次检索白名单中。"""

    normalized_code = str(
        doc_code
    ).strip().upper()

    normalized_whitelist = {
        str(item).strip().upper()
        for item in allowed_doc_codes
    }

    if not normalized_code:
        raise ValueError(
            "doc_code不能为空"
        )

    if normalized_code not in normalized_whitelist:
        raise PermissionError(
            "该doc_code没有出现在本次检索结果中，"
            "禁止打开资料："
            + normalized_code
        )

    return normalized_code


def open_evidence_documents_node(
    state: SecurityAgentState,
):
    """打开白名单中的完整资料并建立引用。"""

    print("完整资料证据节点正在工作")

    route_history = (
        state["route_history"]
        + ["open_evidence_documents"]
    )

    allowed_doc_codes = list(
        state["allowed_doc_codes"]
    )

    if not allowed_doc_codes:
        return {
            "document_open_attempts": 0,
            "opened_documents": [],
            "opened_doc_codes": [],
            "citations": [],
            "evidence_sufficient": False,
            "draft_answer": (
                "没有可以打开的候选资料，"
                "暂时不能生成有依据的正式回答。"
            ),
            "route_history": route_history,
        }

    # 只选择排名最前面的3份资料
    requested_doc_codes = (
        allowed_doc_codes[
            :MAX_DOCUMENTS_TO_OPEN
        ]
    )

    executor = get_tool_executor()

    opened_documents = []
    opened_doc_codes = []
    citations = []
    new_errors = list(state["errors"])
    open_attempts = 0

    for requested_code in requested_doc_codes:
        open_attempts += 1

        try:
            # 第一层保护：必须在白名单中
            normalized_code = (
                ensure_doc_code_allowed(
                    doc_code=requested_code,
                    allowed_doc_codes=(
                        allowed_doc_codes
                    ),
                )
            )

            tool_result = executor.execute(
                tool_name=(
                    "open_knowledge_document"
                ),
                arguments={
                    "doc_code": normalized_code,
                },
            )

            if not tool_result.get("ok"):
                raise RuntimeError(
                    str(
                        tool_result.get(
                            "error_message",
                            "打开资料失败",
                        )
                    )
                )

            document = tool_result.get(
                "result"
            )

            if not isinstance(document, dict):
                raise TypeError(
                    "完整资料必须是字典结构"
                )

            returned_code = str(
                document.get(
                    "doc_code",
                    "",
                )
            ).strip().upper()

            # 第二层保护：工具返回的编号必须
            # 和我们申请打开的编号完全一致
            if returned_code != normalized_code:
                raise PermissionError(
                    "工具返回了与申请不一致的"
                    "doc_code"
                )

            # 第三层保护：资料仍然必须属于
            # 当前专业Agent允许的业务范围
            if (
                document.get("category")
                not in state[
                    "allowed_knowledge_categories"
                ]
            ):
                raise PermissionError(
                    "完整资料类别不属于当前"
                    "专业Agent允许的范围"
                )

            full_text = str(
                document.get(
                    "full_text",
                    "",
                )
            ).strip()

            if not full_text:
                raise ValueError(
                    "完整资料正文为空"
                )

            opened_documents.append(
                document
            )

            opened_doc_codes.append(
                returned_code
            )

            citation = document.get(
                "citation"
            )

            if not isinstance(citation, dict):
                raise TypeError(
                    "完整资料缺少引用信息"
                )

            reference_id = str(
                citation.get(
                    "reference_id",
                    "",
                )
            ).strip()

            if not reference_id:
                raise ValueError(
                    "完整资料缺少引用编号"
                )

            citations.append(
                dict(citation)
            )

            print(
                "成功打开资料：",
                returned_code,
                document.get("title", ""),
            )

        except Exception as error:
            print(
                "打开资料失败：",
                requested_code,
                type(error).__name__,
            )

            new_errors.append(
                (
                    "open document failed: "
                    f"{requested_code}: "
                    f"{type(error).__name__}: "
                    f"{error}"
                )
            )

    # 消防法规回答至少需要一份
    # 满足正式法规引用条件的资料
    if state["category"] == "fire_compliance":
        evidence_sufficient = any(
            bool(
                document.get(
                    "legal_citation_ready"
                )
            )
            for document
            in opened_documents
        )
    else:
        evidence_sufficient = bool(
            opened_documents
        )

    if evidence_sufficient:
        reference_labels = [
            str(
                citation.get(
                    "reference_id",
                    "",
                )
            )
            for citation in citations
        ]

        draft_answer = (
            "已成功打开"
            f"{len(opened_documents)}份完整资料，"
            "并建立引用："
            + "、".join(reference_labels)
            + "。当前尚未调用专业Agent"
            "生成最终业务回答。"
        )
    elif opened_documents:
        draft_answer = (
            "已经打开候选资料，但没有找到"
            "满足现行消防法规引用条件的资料，"
            "需要补充资料或进行人工核验。"
        )
    else:
        draft_answer = (
            "候选资料均未能成功打开，"
            "暂时不能生成有依据的正式回答。"
        )

    return {
        "document_open_attempts": (
            state["document_open_attempts"]
            + open_attempts
        ),
        "opened_documents": (
            opened_documents
        ),
        "opened_doc_codes": (
            opened_doc_codes
        ),
        "citations": citations,
        "evidence_sufficient": (
            evidence_sufficient
        ),
        "draft_answer": draft_answer,
        "route_history": route_history,
        "errors": new_errors,
    }