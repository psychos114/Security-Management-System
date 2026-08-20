import _project_path  # noqa: F401

import base64
import mimetypes
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI


PROJECT_ROOT = Path(__file__).resolve().parent
ENV_FILE = PROJECT_ROOT / ".env"
IMAGE_FILE = (
    PROJECT_ROOT
    / "test_images"
    / "inspection_test.jpg"
)

load_dotenv(ENV_FILE)


def get_required_setting(name):
    value = os.getenv(name, "").strip()

    if not value:
        raise RuntimeError(
            f"缺少配置项：{name}"
        )

    return value


def image_to_data_url(image_path):
    if not image_path.exists():
        raise FileNotFoundError(
            f"没有找到测试图片：{image_path}"
        )

    mime_type, _ = mimetypes.guess_type(
        image_path.name
    )

    if mime_type not in {
        "image/jpeg",
        "image/png",
        "image/webp",
        "image/gif",
    }:
        raise ValueError(
            "测试图片必须是JPG、PNG、WebP或GIF格式"
        )

    image_base64 = base64.b64encode(
        image_path.read_bytes()
    ).decode("utf-8")

    return (
        f"data:{mime_type};base64,"
        f"{image_base64}"
    )


base_url = get_required_setting(
    "VISION_BASE_URL"
)
api_key = get_required_setting(
    "VISION_API_KEY"
)
model = get_required_setting(
    "VISION_MODEL"
)

image_data_url = image_to_data_url(
    IMAGE_FILE
)

client = OpenAI(
    api_key=api_key,
    base_url=base_url,
)

print("正在调用多模态模型……")
print(f"使用模型：{model}")

response = client.chat.completions.create(
    model=model,
    messages=[
        {
            "role": "system",
            "content": (
                "你是医院物业安管巡检助手。"
                "你只能根据照片中明确可见的内容判断，"
                "不能虚构照片中没有出现的信息。"
            ),
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": (
                        "请检查这张巡检照片，"
                        "并按以下格式回答：\n"
                        "1. 是否发现风险：\n"
                        "2. 风险位置：\n"
                        "3. 风险描述：\n"
                        "4. 判断依据：\n"
                        "5. 无法确定的内容："
                    ),
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": image_data_url
                    },
                },
            ],
        },
    ],
    max_tokens=600,
)

answer = response.choices[0].message.content

print("\n多模态模型回答：")
print(answer)
print("\n第14关多模态连接测试成功")
