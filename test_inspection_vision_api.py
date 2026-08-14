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
print("测试1：未登录用户不能分析照片")

with TEST_IMAGE.open("rb") as image_file:
    unauthorized_response = client.post(
        "/api/inspection-vision/analyze",
        files={
            "image": (
                "inspection_test.jpg",
                image_file,
                "image/jpeg",
            )
        },
    )

assert unauthorized_response.status_code in {
    401,
    403,
}

print(
    "未登录状态码：",
    unauthorized_response.status_code,
)


print("\n" + "=" * 70)
print("测试2：伪造图片必须被阻止")

guard_token = login("demo.guard")

fake_response = client.post(
    "/api/inspection-vision/analyze",
    headers={
        "Authorization": (
            f"Bearer {guard_token}"
        )
    },
    files={
        "image": (
            "fake.jpg",
            b"this is not a real image",
            "image/jpeg",
        )
    },
)

assert fake_response.status_code == 415, (
    fake_response.text
)

print(
    "伪造图片状态码：",
    fake_response.status_code,
)


print("\n" + "=" * 70)
print("测试3：登录用户分析真实巡检照片")

temporary_files_before = (
    get_temporary_files()
)

with TEST_IMAGE.open("rb") as image_file:
    success_response = client.post(
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

assert success_response.status_code == 200, (
    success_response.text
)

result = success_response.json()

assert result["analysis_id"]
assert (
    result["filename"]
    == "inspection_test.jpg"
)
assert result["analyzed_by"] == "演示保安"
assert result["analyzed_by_role"] == "保安"
assert result["result"]["has_risk"] is True
assert len(result["result"]["risks"]) >= 1

print(
    "分析编号：",
    result["analysis_id"],
)
print(
    "分析人员：",
    result["analyzed_by"],
)
print(
    "风险数量：",
    len(result["result"]["risks"]),
)


print("\n" + "=" * 70)
print("测试4：临时图片必须被删除")

temporary_files_after = (
    get_temporary_files()
)

assert (
    temporary_files_after
    == temporary_files_before
)

print("通过：没有遗留临时图片")


print("\n第16关测试全部通过")