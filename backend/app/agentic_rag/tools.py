import json

from backend.app.agentic_rag.hybrid_retriever import (
    HybridRetriever,
)


RAG_TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "hybrid_search",
            "description": (
                "默认的知识库检索工具。"
                "同时结合FAISS语义检索和SQLite关键词检索。"
                "适合绝大多数安管、应急、巡检、投诉和消防问题。"
                "中文关键词应尽量不少于3个字符。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": (
                            "用户提出的完整自然语言问题。"
                        ),
                    },
                    "keywords": {
                        "type": "array",
                        "description": (
                            "从问题中提取的3至6个关键词或短语。"
                        ),
                        "items": {
                            "type": "string",
                        },
                        "minItems": 1,
                        "maxItems": 8,
                    },
                    "top_k": {
                        "type": "integer",
                        "description": (
                            "返回结果数量，默认5，最大10。"
                        ),
                        "minimum": 1,
                        "maximum": 10,
                        "default": 5,
                    },
                },
                "required": [
                    "query",
                    "keywords",
                ],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "semantic_search",
            "description": (
                "使用FAISS执行语义检索。"
                "适合用户没有使用资料原文词语，"
                "但问题含义与知识库内容相近的情况。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": (
                            "需要进行语义检索的完整问题。"
                        ),
                    },
                    "top_k": {
                        "type": "integer",
                        "description": (
                            "返回结果数量，默认5，最大10。"
                        ),
                        "minimum": 1,
                        "maximum": 10,
                        "default": 5,
                    },
                },
                "required": [
                    "query",
                ],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "keyword_search",
            "description": (
                "使用SQLite FTS5执行精确关键词检索。"
                "适合检索明确的法规名称、资料编号、"
                "事件名称、岗位名称和专业术语。"
                "中文关键词应尽量不少于3个字符。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "keywords": {
                        "type": "array",
                        "description": (
                            "需要检索的关键词或短语列表。"
                        ),
                        "items": {
                            "type": "string",
                        },
                        "minItems": 1,
                        "maxItems": 8,
                    },
                    "top_k": {
                        "type": "integer",
                        "description": (
                            "返回结果数量，默认5，最大10。"
                        ),
                        "minimum": 1,
                        "maximum": 10,
                        "default": 5,
                    },
                },
                "required": [
                    "keywords",
                ],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "open_knowledge_document",
            "description": (
                "根据doc_code打开一份完整知识资料。"
                "doc_code必须来自前面的知识库检索结果，"
                "不能自行猜测或编造。"
                "回答问题前，应至少打开一份相关资料。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "doc_code": {
                        "type": "string",
                        "description": (
                            "检索结果中真实存在的资料编号，"
                            "例如ER-005或FIRE-003。"
                        ),
                    },
                },
                "required": [
                    "doc_code",
                ],
                "additionalProperties": False,
            },
        },
    },
]


class RAGToolExecutor:
    """
    执行Agent发出的只读工具调用。
    """

    def __init__(self):
        self.hybrid_retriever = (
            HybridRetriever()
        )

        # 复用混合检索器内部已经创建的对象，
        # 避免重复加载FAISS索引。
        self.semantic_retriever = (
            self.hybrid_retriever
            .semantic_retriever
        )

        self.keyword_retriever = (
            self.hybrid_retriever
            .keyword_retriever
        )

        from backend.app.agentic_rag.document_reader import (
            KnowledgeDocumentReader,
        )

        self.document_reader = (
            KnowledgeDocumentReader()
        )

        self.handlers = {
            "hybrid_search": (
                self.execute_hybrid_search
            ),
            "semantic_search": (
                self.execute_semantic_search
            ),
            "keyword_search": (
                self.execute_keyword_search
            ),
            "open_knowledge_document": (
                self.execute_open_document
            ),
        }

    def compact_search_results(
        self,
        results,
    ):
        """
        删除检索结果中的完整正文，
        防止一次工具调用向AI发送过多内容。

        AI需要正文时，应继续调用
        open_knowledge_document。
        """
        allowed_fields = [
            "rank",
            "fusion_score",
            "semantic_rank",
            "semantic_score",
            "keyword_rank",
            "keyword_score",
            "retrieval_methods",
            "chunk_id",
            "doc_code",
            "category",
            "title",
            "summary",
            "snippet",
            "semantic_snippet",
            "keyword_snippet",
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

        compact_results = []

        for item in results:
            compact_item = {}

            for field in allowed_fields:
                if field in item:
                    compact_item[field] = (
                        item[field]
                    )

            compact_results.append(
                compact_item
            )

        return compact_results

    def get_top_k(self, arguments):
        """
        读取并限制top_k。
        """
        top_k = arguments.get("top_k", 5)

        try:
            top_k = int(top_k)
        except (TypeError, ValueError) as error:
            raise ValueError(
                "top_k必须是整数"
            ) from error

        return min(
            max(top_k, 1),
            10,
        )

    def require_text(
        self,
        arguments,
        field_name,
    ):
        """
        检查必填文本参数。
        """
        value = arguments.get(field_name)

        if not isinstance(value, str):
            raise ValueError(
                f"{field_name}必须是字符串"
            )

        value = value.strip()

        if not value:
            raise ValueError(
                f"{field_name}不能为空"
            )

        return value

    def execute_hybrid_search(
        self,
        arguments,
    ):
        query = self.require_text(
            arguments,
            "query",
        )

        keywords = arguments.get(
            "keywords"
        )

        results = (
            self.hybrid_retriever.search(
                query=query,
                keywords=keywords,
                top_k=self.get_top_k(
                    arguments
                ),
            )
        )

        return self.compact_search_results(
            results
        )

    def execute_semantic_search(
        self,
        arguments,
    ):
        query = self.require_text(
            arguments,
            "query",
        )

        results = (
            self.semantic_retriever.search(
                query=query,
                top_k=self.get_top_k(
                    arguments
                ),
            )
        )

        return self.compact_search_results(
            results
        )

    def execute_keyword_search(
        self,
        arguments,
    ):
        keywords = arguments.get(
            "keywords"
        )

        results = (
            self.keyword_retriever.search(
                keywords=keywords,
                top_k=self.get_top_k(
                    arguments
                ),
            )
        )

        return self.compact_search_results(
            results
        )

    def execute_open_document(
        self,
        arguments,
    ):
        doc_code = self.require_text(
            arguments,
            "doc_code",
        )

        return (
            self.document_reader.open_document(
                doc_code
            )
        )

    def parse_arguments(self, arguments):
        """
        OpenAI兼容接口通常会把工具参数
        作为JSON字符串返回。
        """
        if arguments is None:
            return {}

        if isinstance(arguments, dict):
            return arguments

        if not isinstance(arguments, str):
            raise ValueError(
                "工具参数必须是JSON字符串或字典"
            )

        try:
            parsed = json.loads(arguments)
        except json.JSONDecodeError as error:
            raise ValueError(
                "工具参数不是有效的JSON"
            ) from error

        if not isinstance(parsed, dict):
            raise ValueError(
                "工具参数JSON必须是对象"
            )

        return parsed

    def execute(
        self,
        tool_name,
        arguments,
    ):
        """
        工具统一入口。

        工具执行错误会转成结构化结果，
        让未来的Agent能够选择重试或改用其他工具。
        """
        if tool_name not in self.handlers:
            return {
                "ok": False,
                "tool_name": tool_name,
                "error_type": (
                    "UnknownToolError"
                ),
                "error_message": (
                    f"不存在的工具：{tool_name}"
                ),
            }

        try:
            parsed_arguments = (
                self.parse_arguments(arguments)
            )

            result = self.handlers[
                tool_name
            ](
                parsed_arguments
            )

            return {
                "ok": True,
                "tool_name": tool_name,
                "result": result,
            }

        except Exception as error:
            return {
                "ok": False,
                "tool_name": tool_name,
                "error_type": (
                    type(error).__name__
                ),
                "error_message": str(error),
            }