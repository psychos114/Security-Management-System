from typing import Any
from typing import Literal
from uuid import UUID

from pydantic import BaseModel
from pydantic import Field
from pydantic import field_validator


class MultiAgentQueryRequest(BaseModel):
    """前端提交给多Agent系统的问题。"""

    question: str = Field(
        min_length=2,
        max_length=2000,
        description="安管业务问题",
    )

    @field_validator("question")
    @classmethod
    def normalize_question(
        cls,
        value: str,
    ) -> str:
        value = value.strip()

        if not value:
            raise ValueError("问题不能为空")

        return value


class HumanConfirmationRequest(BaseModel):
    """人工确认请求。"""

    request_id: UUID

    approved: bool = Field(
        description=(
            "True表示批准，False表示拒绝"
        ),
    )

    operator: str = Field(
        min_length=2,
        max_length=100,
        description="确认人姓名或岗位",
    )

    note: str = Field(
        default="",
        max_length=500,
        description="人工确认说明",
    )

    @field_validator("operator")
    @classmethod
    def normalize_operator(
        cls,
        value: str,
    ) -> str:
        value = value.strip()

        if len(value) < 2:
            raise ValueError(
                "确认人至少需要填写2个字符"
            )

        return value

    @field_validator("note")
    @classmethod
    def normalize_note(
        cls,
        value: str,
    ) -> str:
        return value.strip()


class MultiAgentResponse(BaseModel):
    """多Agent流程统一返回结果。"""

    request_id: str

    run_status: Literal[
        "completed",
        "awaiting_confirmation",
        "approved",
        "rejected",
    ]

    category: str
    risk_level: str
    answer_status: str
    answer_validation_passed: bool

    answer: str

    used_doc_codes: list[str]
    citations: list[dict[str, Any]]

    requires_human_confirmation: bool
    confirmation_status: str
    confirmed_by: str

    pending_action: (
        dict[str, Any] | None
    )

    route_history: list[str]