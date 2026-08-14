from typing import Literal

from pydantic import BaseModel
from pydantic import Field
from pydantic import model_validator


RiskType = Literal[
    "fire_safety",
    "passage_obstruction",
    "electrical",
    "water_leak",
    "equipment",
    "fall_hazard",
    "vehicle",
    "personnel",
    "other",
]

RiskSeverity = Literal[
    "low",
    "medium",
    "high",
    "critical",
]


class VisualRiskItem(BaseModel):
    """照片中识别到的一项安全风险。"""

    risk_type: RiskType

    location: str = Field(
        min_length=1,
        max_length=200,
    )

    description: str = Field(
        min_length=1,
        max_length=500,
    )

    visual_evidence: str = Field(
        min_length=1,
        max_length=500,
    )

    severity: RiskSeverity

    confidence: float = Field(
        ge=0.0,
        le=1.0,
    )


class InspectionVisionResult(BaseModel):
    """巡检照片的结构化分析结果。"""

    has_risk: bool

    summary: str = Field(
        min_length=1,
        max_length=500,
    )

    risks: list[VisualRiskItem] = Field(
        default_factory=list,
        max_length=10,
    )

    uncertainties: list[str] = Field(
        default_factory=list,
        max_length=10,
    )

    requires_manual_review: bool = False

    @model_validator(mode="after")
    def keep_risk_status_consistent(
        self,
    ):
        # 只要风险列表不为空，就认为发现了风险。
        self.has_risk = bool(self.risks)
        return self