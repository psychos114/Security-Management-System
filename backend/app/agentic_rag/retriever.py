import re

import faiss
import numpy as np

from backend.app.agentic_rag.embeddings import (
    EmbeddingService,
)
from backend.app.agentic_rag.vector_store import (
    load_vector_store,
)
from backend.app.core.config import (
    VECTOR_INDEX_PATH,
)
from backend.app.db.knowledge_repository import (
    get_knowledge_chunks_by_ids,
)


class SemanticRetriever:
    """
    FAISS语义检索器。
    """

    def __init__(self):
        loaded = load_vector_store(
            VECTOR_INDEX_PATH
        )

        self.index = loaded["index"]
        self.metadata = loaded["metadata"]
        self.manifest = loaded["manifest"]

        self.embedding_service = (
            EmbeddingService()
        )

        if self.index.ntotal != len(
            self.metadata
        ):
            raise RuntimeError(
                "FAISS向量数量与资料映射数量不一致"
            )

        if (
            self.manifest["vector_count"]
            != self.index.ntotal
        ):
            raise RuntimeError(
                "索引说明中的向量数量不一致"
            )

    def search(self, query, top_k=5):
        """
        根据自然语言问题搜索相关知识。
        """
        query = query.strip()

        if not query:
            raise ValueError(
                "检索问题不能为空"
            )

        try:
            top_k = int(top_k)
        except ValueError as error:
            raise ValueError(
                "top_k必须是整数"
            ) from error

        top_k = min(
            max(top_k, 1),
            10,
        )

        query_embedding = (
            self.embedding_service.embed_query(
                query
            )
        )

        query_vector = np.asarray(
            [query_embedding],
            dtype=np.float32,
        )

        if query_vector.shape[1] != self.index.d:
            raise RuntimeError(
                "查询向量维度与FAISS索引不一致："
                f"查询={query_vector.shape[1]}，"
                f"索引={self.index.d}"
            )

        # 与建立索引时保持相同的归一化方式
        faiss.normalize_L2(query_vector)

        result_count = min(
            top_k,
            self.index.ntotal,
        )

        scores, index_ids = self.index.search(
            query_vector,
            result_count,
        )

        candidates = []

        for score, index_id in zip(
            scores[0],
            index_ids[0],
        ):
            if index_id < 0:
                continue

            if index_id >= len(self.metadata):
                raise RuntimeError(
                    f"无效的向量序号：{index_id}"
                )

            item_metadata = dict(
                self.metadata[index_id]
            )

            expected_vector_id = (
                item_metadata["vector_id"]
            )

            if expected_vector_id != index_id:
                raise RuntimeError(
                    "向量序号与资料映射不一致"
                )

            candidates.append({
                "index_id": int(index_id),
                "score": float(score),
                "metadata": item_metadata,
            })

        chunk_ids = [
            item["metadata"]["chunk_id"]
            for item in candidates
        ]

        chunk_records = (
            get_knowledge_chunks_by_ids(
                chunk_ids
            )
        )

        chunks_by_id = {
            item["chunk_id"]: item
            for item in chunk_records
        }

        results = []

        for candidate in candidates:
            metadata = candidate["metadata"]

            chunk = chunks_by_id.get(
                metadata["chunk_id"]
            )

            if not chunk:
                continue

            normalized_content = re.sub(
                r"\s+",
                " ",
                chunk["content"],
            ).strip()

            snippet = normalized_content[:260]

            if len(normalized_content) > 260:
                snippet += "……"

            results.append({
                "score": round(
                    candidate["score"],
                    4,
                ),
                "chunk_id": metadata["chunk_id"],
                "doc_code": metadata["doc_code"],
                "category": metadata["category"],
                "title": metadata["title"],
                "heading": metadata["heading"],
                "summary": chunk["summary"],
                "snippet": snippet,
                "content": chunk["content"],
                "citation_locator": (
                    metadata["citation_locator"]
                ),
                "source_title": (
                    metadata["source_title"]
                ),
                "issuing_authority": (
                    metadata["issuing_authority"]
                ),
                "published_date": (
                    metadata["published_date"]
                ),
                "effective_date": (
                    metadata["effective_date"]
                ),
                "validity_status": (
                    metadata["validity_status"]
                ),
                "official_url": (
                    metadata["official_url"]
                ),
                "is_official": (
                    metadata["is_official"]
                ),
                "requires_human_review": (
                    metadata[
                        "requires_human_review"
                    ]
                ),
            })

        return results