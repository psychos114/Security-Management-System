import hashlib
from datetime import datetime
from datetime import timezone

from backend.app.core.config import (
    DATABASE_PATH,
)
from backend.app.core.config import (
    EMBEDDING_MODEL,
)
from backend.app.core.config import (
    VECTOR_INDEX_PATH,
)
from backend.app.db.knowledge_repository import (
    load_knowledge_chunks,
)
from backend.app.agentic_rag.embeddings import (
    EmbeddingService,
)
from backend.app.agentic_rag.vector_store import (
    create_index,
)
from backend.app.agentic_rag.vector_store import (
    load_vector_store,
)
from backend.app.agentic_rag.vector_store import (
    save_vector_store,
)


def build_embedding_text(item):
    """
    组合用于向量化的文字。
    """
    parts = [
        f"文档编号：{item['doc_code']}",
        f"文档标题：{item['title']}",
        f"知识分类：{item['category']}",
        f"适用地区：{item['jurisdiction']}",
        f"小节标题：{item['heading']}",
        f"内容摘要：{item['summary']}",
        f"正文：{item['content']}",
    ]

    if item["citation_locator"]:
        parts.append(
            f"引用位置："
            f"{item['citation_locator']}"
        )

    if item["source_title"]:
        parts.append(
            f"资料来源："
            f"{item['source_title']}"
        )

    return "\n".join(parts)


def calculate_content_hash(chunks):
    """
    计算知识库内容指纹。
    """
    digest = hashlib.sha256()

    for item in chunks:
        values = [
            str(item["chunk_id"]),
            item["doc_code"],
            item["content"],
            item["content_sha256"],
        ]

        for value in values:
            digest.update(
                value.encode("utf-8")
            )
            digest.update(b"\0")

    return digest.hexdigest()


def build_metadata(chunks):
    """
    建立FAISS序号与SQLite资料的映射。
    """
    metadata = []

    for vector_id, item in enumerate(chunks):
        metadata.append({
            "vector_id": vector_id,
            "chunk_id": item["chunk_id"],
            "document_id": item["document_id"],
            "doc_code": item["doc_code"],
            "category": item["category"],
            "title": item["title"],
            "chunk_no": item["chunk_no"],
            "heading": item["heading"],
            "jurisdiction": item["jurisdiction"],
            "citation_locator": (
                item["citation_locator"]
            ),
            "source_code": item["source_code"],
            "source_title": item["source_title"],
            "issuing_authority": (
                item["issuing_authority"]
            ),
            "published_date": (
                item["published_date"]
            ),
            "effective_date": (
                item["effective_date"]
            ),
            "validity_status": (
                item["validity_status"]
            ),
            "official_url": item["official_url"],
            "is_official": item["is_official"],
            "requires_human_review": (
                item["requires_human_review"]
            ),
        })

    return metadata


def main():
    print("=" * 60)
    print("医院物业安管系统——构建FAISS知识索引")
    print("=" * 60)
    print()

    print("1. 正在读取SQLite知识资料……")
    chunks = load_knowledge_chunks()

    if not chunks:
        raise RuntimeError(
            "SQLite中没有知识片段"
        )

    print(
        f"   已读取{len(chunks)}个知识片段"
    )
    print()

    print("2. 正在整理向量化文字……")

    texts = [
        build_embedding_text(item)
        for item in chunks
    ]

    metadata = build_metadata(chunks)

    print(
        f"   已整理{len(texts)}条文字"
    )
    print()

    print("3. 正在调用ModelScope……")

    embedding_service = EmbeddingService()

    embeddings = embedding_service.embed_texts(
        texts
    )

    dimension = len(embeddings[0])

    print()
    print(
        f"   向量数量：{len(embeddings)}"
    )
    print(
        f"   向量维度：{dimension}"
    )
    print()

    print("4. 正在创建并保存FAISS索引……")

    index = create_index(embeddings)

    manifest = {
        "index_type": "faiss.IndexFlatIP",
        "embedding_model": EMBEDDING_MODEL,
        "vector_dimension": dimension,
        "vector_count": len(embeddings),
        "database_filename": DATABASE_PATH.name,
        "content_hash": calculate_content_hash(
            chunks
        ),
        "built_at": datetime.now(
            timezone.utc
        ).isoformat(),
    }

    files = save_vector_store(
        base_path=VECTOR_INDEX_PATH,
        index=index,
        metadata=metadata,
        manifest=manifest,
    )

    for name, file_path in files.items():
        print(f"   {name}: {file_path}")

    print()
    print("5. 正在重新加载索引验证……")

    loaded = load_vector_store(
        VECTOR_INDEX_PATH
    )

    if loaded["index"].ntotal != len(chunks):
        raise RuntimeError(
            "重新加载后的向量数量不正确"
        )

    if len(loaded["metadata"]) != len(chunks):
        raise RuntimeError(
            "重新加载后的资料映射数量不正确"
        )

    print(
        f"   FAISS向量数量："
        f"{loaded['index'].ntotal}"
    )

    print(
        f"   资料映射数量："
        f"{len(loaded['metadata'])}"
    )

    print()
    print("=" * 60)
    print("FAISS知识索引构建成功")
    print(
        f"共有{loaded['index'].ntotal}"
        f"个知识向量"
    )
    print("=" * 60)


if __name__ == "__main__":
    main()