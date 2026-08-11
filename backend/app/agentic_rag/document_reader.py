import re

from backend.app.db.knowledge_repository import (
    get_knowledge_document_by_code,
)


class KnowledgeDocumentReader:
    """
    根据doc_code打开完整知识资料。
    """

    DOC_CODE_PATTERN = re.compile(
        r"^[A-Z0-9][A-Z0-9_-]{1,63}$"
    )

    def normalize_doc_code(self, doc_code):
        """
        检查并整理资料编号。
        """
        if not isinstance(doc_code, str):
            raise ValueError(
                "doc_code必须是字符串"
            )

        normalized = doc_code.strip().upper()

        if not normalized:
            raise ValueError(
                "doc_code不能为空"
            )

        if not self.DOC_CODE_PATTERN.fullmatch(
            normalized
        ):
            raise ValueError(
                "doc_code格式不正确"
            )

        return normalized

    def build_warnings(self, document):
        """
        根据资料状态产生安全提醒。
        """
        warnings = []

        is_official = bool(
            document["is_official"]
        )

        requires_review = bool(
            document["requires_human_review"]
        )

        validity_status = (
            document["validity_status"]
        )

        if not is_official:
            warnings.append(
                "该资料不是官方法规原文，"
                "只能作为内部流程或演示资料参考。"
            )

        if requires_review:
            warnings.append(
                "该资料标记为需要人工复核，"
                "不能直接触发关键业务动作。"
            )

        if validity_status == "needs_review":
            warnings.append(
                "该资料的有效性需要重新核验。"
            )

        if validity_status == "historical":
            warnings.append(
                "该资料属于历史资料，"
                "不得作为现行规定直接引用。"
            )

        if (
            is_official
            and not document["official_url"]
        ):
            warnings.append(
                "该官方资料缺少来源链接，"
                "正式回答前需要补充核验。"
            )

        return warnings

    def build_chunks(self, document):
        """
        整理知识片段，并继承文档引用位置。
        """
        chunks = []

        for chunk in document["chunks"]:
            citation_locator = (
                chunk["citation_locator"]
                or document["citation_locator"]
                or ""
            )

            chunks.append({
                "chunk_id": chunk["chunk_id"],
                "chunk_no": chunk["chunk_no"],
                "heading": chunk["heading"],
                "content": chunk["content"],
                "citation_locator": (
                    citation_locator
                ),
            })

        return chunks

    def build_full_text(self, chunks):
        """
        将全部片段组合成一份完整正文。
        """
        sections = []

        for chunk in chunks:
            heading = chunk["heading"].strip()
            content = chunk["content"].strip()

            if heading:
                sections.append(
                    f"## {heading}\n{content}"
                )
            else:
                sections.append(content)

        return "\n\n".join(sections)

    def open_document(self, doc_code):
        """
        打开完整知识资料。
        """
        normalized_code = (
            self.normalize_doc_code(doc_code)
        )

        document = (
            get_knowledge_document_by_code(
                normalized_code
            )
        )

        if document is None:
            raise LookupError(
                f"没有找到资料：{normalized_code}"
            )

        chunks = self.build_chunks(
            document
        )

        full_text = self.build_full_text(
            chunks
        )

        warnings = self.build_warnings(
            document
        )

        legal_citation_ready = bool(
            document["is_official"]
            and document["official_url"]
            and document["published_date"]
            and document["validity_status"]
            == "active"
        )

        citation = {
            "reference_id": (
                f"[{document['doc_code']}]"
            ),
            "document_title": (
                document["title"]
            ),
            "source_title": (
                document["source_title"]
            ),
            "issuing_authority": (
                document["issuing_authority"]
            ),
            "document_number": (
                document[
                    "source_document_number"
                ]
            ),
            "citation_locator": (
                document["citation_locator"]
            ),
            "published_date": (
                document["published_date"]
            ),
            "effective_date": (
                document["effective_date"]
            ),
            "validity_status": (
                document["validity_status"]
            ),
            "official_url": (
                document["official_url"]
            ),
        }

        return {
            "doc_code": document["doc_code"],
            "category": document["category"],
            "title": document["title"],
            "document_type": (
                document["document_type"]
            ),
            "jurisdiction": (
                document["jurisdiction"]
            ),
            "summary": document["summary"],
            "tags_json": document["tags_json"],
            "is_official": bool(
                document["is_official"]
            ),
            "requires_human_review": bool(
                document[
                    "requires_human_review"
                ]
            ),
            "legal_citation_ready": (
                legal_citation_ready
            ),
            "citation": citation,
            "warnings": warnings,
            "chunk_count": len(chunks),
            "chunks": chunks,
            "full_text": full_text,
        }