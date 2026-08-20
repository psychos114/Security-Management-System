import _project_path  # noqa: F401

from fastapi import HTTPException
from fastapi.testclient import TestClient

from backend.app.core.config import (
    DEMO_AUTH_PASSWORD,
)
from backend.app.core.security import (
    require_task_confirmation,
)
from backend.app.main import app
from backend.app.schemas.auth import (
    AuthenticatedUser,
)


client = TestClient(app)


def login(
    username: str,
) -> tuple[str, AuthenticatedUser]:
    """登录并返回令牌与用户信息。"""

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

    user = AuthenticatedUser.model_validate(
        result["user"]
    )

    return (
        result["access_token"],
        user,
    )


print("=" * 70)
print("测试1：未登录用户不能调用多Agent普通问答")


response = client.post(
    "/api/multi-agent/query",
    json={
        "question": "医院发生火灾应该怎么办？",
    },
)

assert response.status_code in {
    401,
    403,
}, response.text

print(
    "通过，状态码：",
    response.status_code,
)


print("\n" + "=" * 70)
print("测试2：未登录用户不能调用旧版Agent问答")


response = client.post(
    "/api/agent/query",
    json={
        "question": "医院发生火灾应该怎么办？",
    },
)

assert response.status_code in {
    401,
    403,
}, response.text

print(
    "通过，状态码：",
    response.status_code,
)


print("\n" + "=" * 70)
print("测试3：未登录用户不能读取Agent详细状态")


response = client.get(
    "/api/agent/status"
)

assert response.status_code in {
    401,
    403,
}, response.text

print(
    "通过，状态码：",
    response.status_code,
)


print("\n" + "=" * 70)
print("测试4：未登录用户不能读取系统概览")


response = client.get(
    "/api/system/overview"
)

assert response.status_code in {
    401,
    403,
}, response.text

print(
    "通过，状态码：",
    response.status_code,
)


print("\n" + "=" * 70)
print("测试5：保安不能读取系统概览")


guard_token, guard_user = login(
    "demo.guard"
)

response = client.get(
    "/api/system/overview",
    headers={
        "Authorization": (
            f"Bearer {guard_token}"
        ),
    },
)

assert response.status_code == 403, (
    response.text
)

print("通过：保安读取系统概览被阻止")


print("\n" + "=" * 70)
print("测试6：项目经理可以读取系统概览")


project_token, _project_user = login(
    "demo.project"
)

response = client.get(
    "/api/system/overview",
    headers={
        "Authorization": (
            f"Bearer {project_token}"
        ),
    },
)

assert response.status_code == 200, (
    response.text
)

print("通过：项目经理可以读取系统概览")


print("\n" + "=" * 70)
print("测试7：安管经理可以审批保安发起的严重任务")


_security_token, security_user = login(
    "demo.security"
)

guard_task_state = {
    "risk_level": "critical",
    "initiator_user_id": guard_user.id,
    "allowed_confirmer_role_codes": [
        "security_manager",
    ],
}

require_task_confirmation(
    user=security_user,
    task_state=guard_task_state,
)

print("通过：安管经理可以审批保安发起的严重任务")


print("\n" + "=" * 70)
print("测试8：严重任务不能由发起人自己审批")


self_approval_task_state = {
    "risk_level": "critical",
    "initiator_user_id": (
        security_user.id
    ),
    "allowed_confirmer_role_codes": [
        "security_manager",
    ],
}

try:
    require_task_confirmation(
        user=security_user,
        task_state=(
            self_approval_task_state
        ),
    )

except HTTPException as error:
    assert error.status_code == 403

    print(
        "通过：自我审批被阻止，状态码：",
        error.status_code,
    )

else:
    raise AssertionError(
        "系统没有阻止严重任务自我审批"
    )


print("\n" + "=" * 70)
print("测试9：旧任务缺少发起人身份时不能审批")


legacy_task_state = {
    "risk_level": "critical",
    "allowed_confirmer_role_codes": [
        "security_manager",
    ],
}

try:
    require_task_confirmation(
        user=security_user,
        task_state=legacy_task_state,
    )

except HTTPException as error:
    assert error.status_code == 403

    print(
        "通过：旧任务被阻止，状态码：",
        error.status_code,
    )

else:
    raise AssertionError(
        "系统没有阻止缺少发起人的旧任务"
    )


print("\n" + "=" * 70)
print("安全边界测试全部通过")
