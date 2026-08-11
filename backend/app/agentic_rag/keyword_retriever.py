import re

from backend.app.db.knowledge_repository import (
    search_knowledge_fts,
)


class KeywordRetriever:
    """
    SQLite FTS5关键词检索器。
    """

    def normalize_keywords(self, keywords):
        """
        将字符串或关键词列表整理成统一格式。
        """
        if isinstance(keywords, str):
            keywords = re.split(
                r"[,，;；\n]+",
                keywords,
            )

        if not isinstance(
            keywords,
            (list, tuple),
        ):
            raise ValueError(
                "keywords必须是字符串或关键词列表"
            )

        normalized = []

        for keyword in keywords:
            keyword = re.sub(
                r"\s+",
                " ",
                str(keyword),
            ).strip()

            if not keyword:
                continue

            if keyword not in normalized:
                normalized.append(keyword)

        if not normalized:
            raise ValueError(
                "至少需要提供一个关键词"
            )

        # 当前FTS使用trigram分词。
        # 中文检索词最好不少于3个字符。
        searchable = [
            keyword
            for keyword in normalized
            if len(keyword) >= 3
        ]

        if not searchable:
            raise ValueError(
                "关键词过短。中文关键词请至少输入3个字符，"
                "例如使用“火灾处置”，不要只输入“火灾”。"
            )

        # 防止一次传入过多关键词。
        return searchable[:8]

    def quote_fts_term(self, term):
        """
        将关键词转换为安全的FTS5短语。
        """
        escaped = term.replace(
            '"',
            '""',
        )

        return f'"{escaped}"'

    def build_fts_query(self, keywords):
        """
        使用OR连接关键词。

        只要资料命中任意一个关键词，
        就可以进入候选结果。
        """
        terms = [
            self.quote_fts_term(keyword)
            for keyword in keywords
        ]

        return " OR ".join(terms)

    def search(self, keywords, top_k=5):
        """
        执行关键词搜索。
        """
        normalized_keywords = (
            self.normalize_keywords(keywords)
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

        fts_query = self.build_fts_query(
            normalized_keywords
        )

        rows = search_knowledge_fts(
            fts_query=fts_query,
            limit=top_k,
        )

        results = []

        for position, row in enumerate(
            rows,
            start=1,
        ):
            bm25_score = float(
                row["bm25_score"]
            )

            results.append({
                "rank": position,
                "keyword_score": round(
                    -bm25_score,
                    4,
                ),
                "matched_keywords": (
                    normalized_keywords
                ),
                "document_id": (
                    row["document_id"]
                ),
                "chunk_id": row["chunk_id"],
                "doc_code": row["doc_code"],
                "category": row["category"],
                "title": row["title"],
                "summary": row["summary"],
                "snippet": row["snippet"],
                "citation_locator": (
                    row["citation_locator"]
                ),
                "source_title": (
                    row["source_title"]
                ),
                "issuing_authority": (
                    row["issuing_authority"]
                ),
                "published_date": (
                    row["published_date"]
                ),
                "effective_date": (
                    row["effective_date"]
                ),
                "validity_status": (
                    row["validity_status"]
                ),
                "official_url": (
                    row["official_url"]
                ),
                "is_official": (
                    row["is_official"]
                ),
                "requires_human_review": (
                    row[
                        "requires_human_review"
                    ]
                ),
            })

        return results