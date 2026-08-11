from backend.app.db.connection import (
    get_read_connection,
)


def load_knowledge_chunks():
    """
    从SQLite读取用于RAG的全部知识片段。
    """
    connection = get_read_connection()

    try:
        rows = connection.execute(
            """
            SELECT
                k.id AS chunk_id,
                k.chunk_no,
                k.heading,
                k.content,

                d.id AS document_id,
                d.doc_code,
                d.category,
                d.title,
                d.document_type,
                d.jurisdiction,
                d.summary,
                d.is_official,
                d.requires_human_review,
                d.content_sha256,

                COALESCE(
                    NULLIF(k.citation_locator, ''),
                    NULLIF(d.citation_locator, ''),
                    ''
                ) AS citation_locator,

                s.source_code,
                s.title AS source_title,
                s.issuing_authority,
                s.published_date,
                s.effective_date,
                s.validity_status,
                s.official_url

            FROM knowledge_chunks AS k

            JOIN knowledge_documents AS d
                ON d.id = k.document_id

            LEFT JOIN knowledge_sources AS s
                ON s.id = d.source_id

            ORDER BY
                d.doc_code,
                k.chunk_no
            """
        ).fetchall()

        return [dict(row) for row in rows]
    finally:
        connection.close()

def get_knowledge_chunks_by_ids(chunk_ids):
    """
    根据知识片段ID批量读取正文。

    返回顺序与传入的chunk_ids保持一致。
    """
    if not chunk_ids:
        return []

    normalized_ids = [
        int(chunk_id)
        for chunk_id in chunk_ids
    ]

    placeholders = ",".join(
        "?"
        for _ in normalized_ids
    )

    connection = get_read_connection()

    try:
        rows = connection.execute(
            f"""
            SELECT
                k.id AS chunk_id,
                k.content,
                d.summary

            FROM knowledge_chunks AS k

            JOIN knowledge_documents AS d
                ON d.id = k.document_id

            WHERE k.id IN ({placeholders})
            """,
            normalized_ids,
        ).fetchall()

        records_by_id = {
            row["chunk_id"]: dict(row)
            for row in rows
        }

        return [
            records_by_id[chunk_id]
            for chunk_id in normalized_ids
            if chunk_id in records_by_id
        ]
    finally:
        connection.close()


def search_knowledge_fts(fts_query, limit=5):
    """
    使用SQLite FTS5搜索知识文档。

    bm25分值越小，代表匹配程度越高。
    """
    connection = get_read_connection()

    try:
        rows = connection.execute(
            """
            SELECT
                d.id AS document_id,
                d.doc_code,
                d.category,
                d.title,
                d.document_type,
                d.jurisdiction,
                d.summary,
                d.is_official,
                d.requires_human_review,

                k.id AS chunk_id,

                COALESCE(
                    NULLIF(d.citation_locator, ''),
                    ''
                ) AS citation_locator,

                s.source_code,
                s.title AS source_title,
                s.issuing_authority,
                s.published_date,
                s.effective_date,
                s.validity_status,
                s.official_url,

                bm25(
                    knowledge_fts,
                    6.0,
                    4.0,
                    2.0,
                    1.0,
                    3.0
                ) AS bm25_score,

                snippet(
                    knowledge_fts,
                    3,
                    '【',
                    '】',
                    '…',
                    32
                ) AS snippet

            FROM knowledge_fts

            JOIN knowledge_documents AS d
                ON d.doc_code = knowledge_fts.doc_code

            LEFT JOIN knowledge_chunks AS k
                ON k.id = (
                    SELECT MIN(k2.id)
                    FROM knowledge_chunks AS k2
                    WHERE k2.document_id = d.id
                )

            LEFT JOIN knowledge_sources AS s
                ON s.id = d.source_id

            WHERE knowledge_fts MATCH ?

            ORDER BY
                bm25_score ASC,
                d.doc_code ASC

            LIMIT ?
            """,
            (
                fts_query,
                int(limit),
            ),
        ).fetchall()

        return [
            dict(row)
            for row in rows
        ]
    finally:
        connection.close()


def get_knowledge_document_by_code(doc_code):
    """
    根据资料编号读取完整知识文档和全部知识片段。
    """
    connection = get_read_connection()

    try:
        document_row = connection.execute(
            """
            SELECT
                d.id AS document_id,
                d.doc_code,
                d.category,
                d.title,
                d.document_type,
                d.jurisdiction,
                d.summary,
                d.content AS document_content,
                d.tags_json,
                d.is_official,
                d.requires_human_review,
                d.source_file,
                d.content_sha256,
                d.created_at,

                COALESCE(
                    NULLIF(d.citation_locator, ''),
                    ''
                ) AS citation_locator,

                s.source_code,
                s.title AS source_title,
                s.issuing_authority,
                s.document_number
                    AS source_document_number,
                s.jurisdiction
                    AS source_jurisdiction,
                s.source_type,
                s.published_date,
                s.effective_date,
                s.validity_status,
                s.official_url,
                s.retrieval_date,
                s.notes AS source_notes

            FROM knowledge_documents AS d

            LEFT JOIN knowledge_sources AS s
                ON s.id = d.source_id

            WHERE UPPER(d.doc_code) = UPPER(?)

            LIMIT 1
            """,
            (doc_code,),
        ).fetchone()

        if document_row is None:
            return None

        document = dict(document_row)

        chunk_rows = connection.execute(
            """
            SELECT
                id AS chunk_id,
                chunk_no,
                heading,
                content,
                citation_locator,
                metadata_json

            FROM knowledge_chunks

            WHERE document_id = ?

            ORDER BY
                chunk_no ASC,
                id ASC
            """,
            (document["document_id"],),
        ).fetchall()

        document["chunks"] = [
            dict(row)
            for row in chunk_rows
        ]

        return document
    finally:
        connection.close()