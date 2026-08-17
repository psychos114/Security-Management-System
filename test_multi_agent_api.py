from fastapi.testclient import TestClient

from backend.app.core.config import (
    DEMO_AUTH_PASSWORD,
)
from backend.app.main import app


client = TestClient(app)


QUESTION = (
    "住院部三楼已经起火并出现大量浓烟，"
    "系统应该如何处置？"
)


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

    result = response.json()

    assert result["token_type"] == "bearer"
    assert result["access_token"]

    return result["access_token"]


print("=" * 70)
print("测试1：创建待确认任务")


guard_token = login(
    "demo.guard"
)


query_response = client.post(
    "/api/multi-agent/query",
    headers={
        "Authorization": (
            f"Bearer {guard_token}"
        ),
    },
    json={
        "question": QUESTION,
    },
)

assert query_response.status_code == 200, (
    query_response.text
)

query_result = query_response.json()

assert (
    query_result["run_status"]
    == "awaiting_confirmation"
)

request_id = query_result["request_id"]

print("待确认任务：", request_id)


print("\n" + "=" * 70)
print("测试2：未登录用户不能确认")


unauthorized_response = client.post(
    "/api/multi-agent/confirm",
    json={
        "request_id": request_id,
        "approved": True,
        "note": "未登录尝试确认",
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
print("测试3：保安没有确认权限")



guard_response = client.post(
    "/api/multi-agent/confirm",
    headers={
        "Authorization": (
            f"Bearer {guard_token}"
        )
    },
    json={
        "request_id": request_id,
        "approved": True,
        "note": "保安尝试确认",
    },
)

assert guard_response.status_code == 403

print(
    "保安确认状态码：",
    guard_response.status_code,
)


print("\n" + "=" * 70)
print("测试4：安管经理可以确认")


manager_token = login(
    "demo.security"
)

manager_response = client.post(
    "/api/multi-agent/confirm",
    headers={
        "Authorization": (
            f"Bearer {manager_token}"
        )
    },
    json={
        "request_id": request_id,
        "approved": True,
        "note": "安管经理已经核实现场",
    },
)

assert manager_response.status_code == 200, (
    manager_response.text
)

manager_result = manager_response.json()

assert (
    manager_result["run_status"]
    == "approved"
)

assert (
    manager_result["confirmed_by"]
    == "演示安管经理"
)

assert (
    manager_result["pending_action"][
        "executed"
    ]
    is False
)

print(
    "确认人：",
    manager_result["confirmed_by"],
)

print(
    "真实动作是否执行：",
    manager_result["pending_action"][
        "executed"
    ],
)


print("\n" + "=" * 70)
print("测试5：阻止重复确认")


duplicate_response = client.post(
    "/api/multi-agent/confirm",
    headers={
        "Authorization": (
            f"Bearer {manager_token}"
        )
    },
    json={
        "request_id": request_id,
        "approved": True,
        "note": "尝试重复确认",
    },
)

assert duplicate_response.status_code == 409

print(
    "重复确认状态码：",
    duplicate_response.status_code,
)


print("\n第13关认证和权限测试全部通过")