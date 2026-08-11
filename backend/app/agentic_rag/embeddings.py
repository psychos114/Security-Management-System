from openai import OpenAI

from backend.app.core.config import (
    EMBEDDING_API_KEY,
)
from backend.app.core.config import (
    EMBEDDING_BASE_URL,
)
from backend.app.core.config import (
    EMBEDDING_BATCH_SIZE,
)
from backend.app.core.config import (
    EMBEDDING_MODEL,
)


class EmbeddingService:
    """
    使用ModelScope生成文本向量。
    """

    def __init__(self):
        self.model = EMBEDDING_MODEL
        self.batch_size = EMBEDDING_BATCH_SIZE

        self.client = OpenAI(
            api_key=EMBEDDING_API_KEY,
            base_url=EMBEDDING_BASE_URL,
        )

    def embed_texts(self, texts):
        """
        将多条文字分批转换成向量。
        """
        if not texts:
            return []

        embeddings = []

        total_batches = (
            len(texts) + self.batch_size - 1
        ) // self.batch_size

        for batch_number, start in enumerate(
            range(0, len(texts), self.batch_size),
            start=1,
        ):
            batch_texts = texts[
                start:start + self.batch_size
            ]

            print(
                f"正在生成向量："
                f"第{batch_number}/{total_batches}批，"
                f"本批{len(batch_texts)}条"
            )

            try:
                response = (
                    self.client.embeddings.create(
                        model=self.model,
                        input=batch_texts,
                    )
                )
            except Exception as error:
                raise RuntimeError(
                    f"第{batch_number}批向量生成失败："
                    f"{error}"
                ) from error

            ordered_data = sorted(
                response.data,
                key=lambda item: item.index,
            )

            if len(ordered_data) != len(batch_texts):
                raise RuntimeError(
                    "向量接口返回数量不正确："
                    f"输入{len(batch_texts)}条，"
                    f"返回{len(ordered_data)}条"
                )

            embeddings.extend(
                item.embedding
                for item in ordered_data
            )

        if len(embeddings) != len(texts):
            raise RuntimeError(
                "向量数量与知识片段数量不一致"
            )

        dimensions = {
            len(item)
            for item in embeddings
        }

        if len(dimensions) != 1:
            raise RuntimeError(
                "不同知识片段的向量维度不一致"
            )

        return embeddings

    def embed_query(self, query):
        """
        后续搜索时，将用户问题转换成向量。
        """
        query = query.strip()

        if not query:
            raise ValueError("查询问题不能为空")

        response = self.client.embeddings.create(
            model=self.model,
            input=[query],
        )

        if not response.data:
            raise RuntimeError(
                "向量接口没有返回查询向量"
            )

        return response.data[0].embedding