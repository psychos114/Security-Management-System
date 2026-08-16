from pathlib import Path
from tempfile import gettempdir

from fastapi.testclient import TestClient

from backend.app.core.config import (
    DEMO_AUTH_PASSWORD,
)
from backend.app.main import app


PROJECT_ROOT = Path(__file__).resolve().parent
TEST_IMAGE = (
    PROJECT_ROOT
    / "test_images"
    / "inspection_test.jpg"
)

client = TestClient(app)


def login(
    username: str,
) -> str:
    response = client.post(
        "/api/auth/login",
        json={
            "username": username,
            "password": DEMO_AUTH_PASSWORD,
        },
    )

    assert response.status_code == 200, (
        response.text
    )

    return response.json()[
        "access_token"
    ]


def get_temporary_files():
    temporary_directory = Path(
        gettempdir()
    )

    return {
        path.resolve()
        for path in temporary_directory.glob(
            "security_inspection_*"
        )
    }


print("=" * 70)
print("测试1：登录保安提交巡检照片")

guard_token = login("demo.guard")

temporary_files_before = (
    get_temporary_files()
)

with TEST_IMAGE.open("rb") as image_file:
    response = client.post(
        "/api/inspection-vision/analyze",
        headers={
            "Authorization": (
                f"Bearer {guard_token}"
            )
        },
        files={
            "image": (
                "inspection_test.jpg",
                image_file,
                "image/jpeg",
            )
        },
    )

assert response.status_code == 200, (
    response.text
)

data = response.json()

assert data["analysis_id"]
assert data["analyzed_by"] == "演示保安"
assert data["analyzed_by_role"] == "保安"

print(
    "图片分析编号：",
    data["analysis_id"],
)


print("\n" + "=" * 70)
print("测试2：检查多模态视觉结果")

vision_result = data["result"]

assert vision_result["has_risk"] is True
assert len(vision_result["risks"]) >= 1
assert vision_result["summary"]

print(
    "识别到的风险数量：",
    len(vision_result["risks"]),
)
print(
    "需要人工复核：",
    vision_result[
        "requires_manual_review"
    ],
)


print("\n" + "=" * 70)
print("测试3：检查巡检Agent和RAG结果")

agent_result = data["agent_result"]

assert agent_result["request_id"]
assert (
    agent_result["category"]
    == "inspection"
)
assert (
    agent_result["answer_status"]
    == "generated"
)
assert (
    agent_result[
        "answer_validation_passed"
    ]
    is True
)
assert agent_result["answer"]
assert agent_result["used_doc_codes"]
assert agent_result["citations"]

assert (
    "inspection_agent"
    in agent_result["route_history"]
)
assert (
    "controlled_retrieval"
    in agent_result["route_history"]
)
assert (
    "open_evidence_documents"
    in agent_result["route_history"]
)
assert (
    "inspection_answer"
    in agent_result["route_history"]
)

print(
    "LangGraph任务编号：",
    agent_result["request_id"],
)
print(
    "使用资料：",
    agent_result["used_doc_codes"],
)
print(
    "流程路线：",
    agent_result["route_history"],
)
print(
    "整改建议：\n",
    agent_result["answer"],
)


print("\n" + "=" * 70)
print("测试4：系统没有执行真实动作")

pending_action = agent_result[
    "pending_action"
]

assert (
    pending_action is None
    or pending_action.get("executed")
    is False
)

print("通过：没有执行真实动作")


print("\n" + "=" * 70)
print("测试5：临时图片已经删除")

temporary_files_after = (
    get_temporary_files()
)

assert (
    temporary_files_after
    == temporary_files_before
)

print("通过：没有遗留临时图片")
print("\n第18关测试全部通过")
