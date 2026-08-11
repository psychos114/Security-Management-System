from typing import Any

from pydantic import BaseModel
from pydantic import Field
from pydantic import field_validator


class AgentQueryRequest(BaseModel):
    """
    前端提交给Agent的问题。
    """

    question: str = Field(
        min_length=2,
        max_length=2000,
        description="用户提出的安管业务问题",
        examples=[
            "医院发生电梯困人，保安应该怎么处理？"
        ],
    )

    @field_validator("question")
    @classmethod
    def normalize_question(cls, value):
        value = value.strip()

        if not value:
            raise ValueError(
                "问题不能为空"
            )

        return value


class AgentQueryResponse(BaseModel):
    """
    Agent返回给前端的完整结果。
    """

    answer: str
    opened_documents: list[str]
    allowed_documents: list[str]
    tool_calls: int = Field(ge=0)
    rounds: int = Field(ge=1)
    tool_trace: list[
        dict[str, Any]
    ]


class AgentStatusResponse(BaseModel):
    """
    Agent服务状态。
    """

    status: str
    service: str
    model: str
    vector_count: int
    tools: list[str]