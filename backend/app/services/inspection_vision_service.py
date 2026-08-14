import base64
import json
import mimetypes
from pathlib import Path

from openai import OpenAI
from pydantic import ValidationError

from backend.app.core.config import (
    VISION_API_KEY,
    VISION_BASE_URL,
    VISION_MODEL,
)
from backend.app.schemas.inspection_vision import (
    InspectionVisionResult,
)


SUPPORTED_IMAGE_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/gif",
}

MAX_IMAGE_BYTES = 10 * 1024 * 1024


SYSTEM_PROMPT = """
你是医院物业安管系统的巡检照片分析助手。

你只能判断照片中明确可见的内容，不能虚构照片中没有出现的信息。
如果照片模糊、遮挡严重或者无法确定，必须写入 uncertainties。
不得根据患者外貌猜测疾病、身份、年龄或其他敏感信息。

风险类型只能使用：
fire_safety
passage_obstruction
electrical
water_leak
equipment
fall_hazard
vehicle
personnel
other

风险等级只能使用：
low
medium
high
critical

你必须只返回JSON对象，结构如下：
{
  "has_risk": true,
  "summary": "照片整体情况",
  "risks": [
    {
      "risk_type": "fire_safety",
      "location": "风险在照片中的位置",
      "description": "风险的具体描述",
      "visual_evidence": "照片中能够看到的判断依据",
      "severity": "high",
      "confidence": 0.95
    }
  ],
  "uncertainties": [],
  "requires_manual_review": false
}

如果没有发现风险，risks必须是空列表，has_risk必须是false。
confidence必须是0到1之间的数字。
不要输出Markdown，不要在JSON外面添加解释。
""".strip()


class InspectionVisionService:
    """正式的巡检照片分析服务。"""

    def __init__(self):
        self.client = OpenAI(
            api_key=VISION_API_KEY,
            base_url=VISION_BASE_URL,
        )

    @staticmethod
    def image_to_data_url(
        image_path: str | Path,
    ) -> str:
        path = Path(image_path)

        if not path.exists():
            raise FileNotFoundError(
                f"没有找到图片：{path}"
            )

        if not path.is_file():
            raise ValueError(
                f"图片路径不是文件：{path}"
            )

        if path.stat().st_size > MAX_IMAGE_BYTES:
            raise ValueError(
                "图片不能超过10MB"
            )

        mime_type, _ = mimetypes.guess_type(
            path.name
        )

        if mime_type not in SUPPORTED_IMAGE_TYPES:
            raise ValueError(
                "只支持JPG、PNG、WebP和静态GIF图片"
            )

        image_base64 = base64.b64encode(
            path.read_bytes()
        ).decode("utf-8")

        return (
            f"data:{mime_type};base64,"
            f"{image_base64}"
        )

    def analyze(
        self,
        image_path: str | Path,
    ) -> InspectionVisionResult:
        image_data_url = self.image_to_data_url(
            image_path
        )

        response = (
            self.client
            .chat
            .completions
            .create(
                model=VISION_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": SYSTEM_PROMPT,
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": (
                                    "请分析这张医院物业"
                                    "安管巡检照片。"
                                ),
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": image_data_url,
                                    "detail": "high",
                                },
                            },
                        ],
                    },
                ],
                response_format={
                    "type": "json_object",
                },
                temperature=0.1,
                max_tokens=1500,
                stream=False,
            )
        )

        content = (
            response
            .choices[0]
            .message
            .content
            or ""
        ).strip()

        if not content:
            raise RuntimeError(
                "多模态模型返回了空内容"
            )

        try:
            parsed = json.loads(content)
        except json.JSONDecodeError as error:
            raise RuntimeError(
                "多模态模型没有返回合法JSON"
            ) from error

        try:
            result = (
                InspectionVisionResult
                .model_validate(parsed)
            )
        except ValidationError as error:
            raise RuntimeError(
                "多模态模型返回的数据结构不合格"
            ) from error

        requires_manual_review = (
            bool(result.uncertainties)
            or any(
                risk.severity in {
                    "high",
                    "critical",
                }
                or risk.confidence < 0.75
                for risk in result.risks
            )
        )

        return result.model_copy(
            update={
                "requires_manual_review": (
                    requires_manual_review
                )
            }
        )