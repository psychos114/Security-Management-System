from backend.app.agentic_rag.keyword_retriever import (
    KeywordRetriever,
)
from backend.app.agentic_rag.retriever import (
    SemanticRetriever,
)


class HybridRetriever:
    """
    将FAISS语义检索和SQLite关键词检索合并。
    """

    RRF_CONSTANT = 60

    def __init__(self):
        self.semantic_retriever = (
            SemanticRetriever()
        )
        self.keyword_retriever = (
            KeywordRetriever()
        )

    def create_record(self, item):
        """
        创建统一的检索结果结构。
        """
        return {
            "chunk_id": item.get("chunk_id"),
            "doc_code": item.get("doc_code"),
            "category": item.get("category"),
            "title": item.get("title"),
            "summary": item.get("summary"),
            "citation_locator": item.get(
                "citation_locator"
            ),
            "source_title": item.get(
                "source_title"
            ),
            "issuing_authority": item.get(
                "issuing_authority"
            ),
            "published_date": item.get(
                "published_date"
            ),
            "effective_date": item.get(
                "effective_date"
            ),
            "validity_status": item.get(
                "validity_status"
            ),
            "official_url": item.get(
                "official_url"
            ),
            "is_official": item.get(
                "is_official"
            ),
            "requires_human_review": item.get(
                "requires_human_review"
            ),

            "semantic_rank": None,
            "semantic_score": None,
            "semantic_snippet": None,

            "keyword_rank": None,
            "keyword_score": None,
            "keyword_snippet": None,

            "_fusion_score": 0.0,
        }

    def fill_missing_fields(
        self,
        record,
        item,
    ):
        """
        用另一种检索结果补全缺少的字段。
        """
        fields = [
            "chunk_id",
            "category",
            "title",
            "summary",
            "citation_locator",
            "source_title",
            "issuing_authority",
            "published_date",
            "effective_date",
            "validity_status",
            "official_url",
            "is_official",
            "requires_human_review",
        ]

        for field in fields:
            old_value = record.get(field)
            new_value = item.get(field)

            if (
                old_value is None
                or old_value == ""
            ):
                record[field] = new_value

    def rrf_score(self, rank):
        """
        根据排名计算RRF分值。
        """
        return 1.0 / (
            self.RRF_CONSTANT + rank
        )

    def search(
        self,
        query,
        keywords,
        top_k=5,
    ):
        """
        执行混合检索。

        query：
            完整的自然语言问题。

        keywords：
            由人工或未来的Agent提取出的关键词。
        """
        query = query.strip()

        if not query:
            raise ValueError(
                "检索问题不能为空"
            )

        try:
            top_k = int(top_k)
        except (TypeError, ValueError) as error:
            raise ValueError(
                "top_k必须是整数"
            ) from error

        top_k = min(
            max(top_k, 1),
            10,
        )

        # 多取一些候选资料，再进行融合排序。
        candidate_k = min(
            max(top_k * 2, 5),
            10,
        )

        semantic_results = (
            self.semantic_retriever.search(
                query=query,
                top_k=candidate_k,
            )
        )

        keyword_results = (
            self.keyword_retriever.search(
                keywords=keywords,
                top_k=candidate_k,
            )
        )

        merged = {}

        # 处理FAISS语义检索结果。
        seen_semantic_docs = set()

        for semantic_rank, item in enumerate(
            semantic_results,
            start=1,
        ):
            doc_code = item["doc_code"]

            # 同一份文档只计算一次语义排名。
            if doc_code in seen_semantic_docs:
                continue

            seen_semantic_docs.add(doc_code)

            if doc_code not in merged:
                merged[doc_code] = (
                    self.create_record(item)
                )
            else:
                self.fill_missing_fields(
                    merged[doc_code],
                    item,
                )

            record = merged[doc_code]

            record["semantic_rank"] = (
                semantic_rank
            )
            record["semantic_score"] = (
                item.get("score")
            )
            record["semantic_snippet"] = (
                item.get("snippet")
            )

            record["_fusion_score"] += (
                self.rrf_score(
                    semantic_rank
                )
            )

        # 处理SQLite关键词检索结果。
        seen_keyword_docs = set()

        for keyword_rank, item in enumerate(
            keyword_results,
            start=1,
        ):
            doc_code = item["doc_code"]

            if doc_code in seen_keyword_docs:
                continue

            seen_keyword_docs.add(doc_code)

            if doc_code not in merged:
                merged[doc_code] = (
                    self.create_record(item)
                )
            else:
                self.fill_missing_fields(
                    merged[doc_code],
                    item,
                )

            record = merged[doc_code]

            record["keyword_rank"] = (
                keyword_rank
            )
            record["keyword_score"] = (
                item.get("keyword_score")
            )
            record["keyword_snippet"] = (
                item.get("snippet")
            )

            record["_fusion_score"] += (
                self.rrf_score(
                    keyword_rank
                )
            )

        ranked_records = sorted(
            merged.values(),
            key=lambda record: (
                -record["_fusion_score"],
                record["doc_code"],
            ),
        )

        final_results = []

        for final_rank, record in enumerate(
            ranked_records[:top_k],
            start=1,
        ):
            result = dict(record)

            raw_fusion_score = result.pop(
                "_fusion_score"
            )

            result["rank"] = final_rank
            result["fusion_score"] = round(
                raw_fusion_score,
                6,
            )

            retrieval_methods = []

            if result["semantic_rank"] is not None:
                retrieval_methods.append(
                    "semantic"
                )

            if result["keyword_rank"] is not None:
                retrieval_methods.append(
                    "keyword"
                )

            result["retrieval_methods"] = (
                retrieval_methods
            )

            final_results.append(result)

        return final_results