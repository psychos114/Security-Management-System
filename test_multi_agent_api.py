from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


QUESTION = (
    "住院部三楼已经起火并出现大量浓烟，"
    "系统应该如何处置？"
)


print("=" * 70)
print("测试1：通过API提交紧急事件")


query_response = client.post(
    "/api/multi-agent/query",
    json={
        "question": QUESTION,
    },
)


print(
    "提问接口状态码：",
    query_response.status_code,
)

assert query_response.status_code == 200, (
    query_response.text
)


query_result = query_response.json()


print(
    "流程状态：",
    query_result["run_status"],
)

print(
    "请求编号：",
    query_result["request_id"],
)

print(
    "待确认动作：",
    query_result["pending_action"],
)


assert (
    query_result["run_status"]
    == "awaiting_confirmation"
)

assert (
    query_result["confirmation_status"]
    == "pending"
)

assert (
    query_result["pending_action"]
    is not None
)

assert (
    query_result["pending_action"][
        "executed"
    ]
    is False
)


print("\n" + "=" * 70)
print("测试2：通过API批准关键动作")


confirm_response = client.post(
    "/api/multi-agent/confirm",
    json={
        "request_id": (
            query_result["request_id"]
        ),
        "approved": True,
        "operator": "安管经理",
        "note": "已经通过电话核实现场情况",
    },
)


print(
    "确认接口状态码：",
    confirm_response.status_code,
)

assert confirm_response.status_code == 200, (
    confirm_response.text
)


confirm_result = confirm_response.json()


print(
    "人工确认状态：",
    confirm_result["confirmation_status"],
)

print(
    "动作是否执行：",
    confirm_result["pending_action"][
        "executed"
    ],
)


assert (
    confirm_result["run_status"]
    == "approved"
)

assert (
    confirm_result["confirmation_status"]
    == "approved"
)

assert (
    confirm_result["confirmed_by"]
    == "安管经理"
)

assert (
    confirm_result["pending_action"][
        "executed"
    ]
    is False
)


print("\n" + "=" * 70)
print("测试3：阻止重复确认")


duplicate_response = client.post(
    "/api/multi-agent/confirm",
    json={
        "request_id": (
            query_result["request_id"]
        ),
        "approved": True,
        "operator": "项目经理",
        "note": "尝试重复确认",
    },
)


print(
    "重复确认状态码：",
    duplicate_response.status_code,
)


assert duplicate_response.status_code == 409


print("\n第10关接口测试全部通过")