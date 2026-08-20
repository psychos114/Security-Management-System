import _project_path  # noqa: F401

import json
from types import SimpleNamespace
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.app.api import (
    multi_agent as multi_agent_api,
)
from backend.app.core.config import (
    DEMO_AUTH_PASSWORD,
)
from backend.app.main import app


client = TestClient(app)


QUESTION = "医院发生电梯困人，应该如何处置？"


def login() -> str:
    response = client.post(
        "/api/auth/login",
        json={
            "username": "demo.guard",
            "password": DEMO_AUTH_PASSWORD,
        },
    )

    assert response.status_code == 200, (
        response.text
    )

    return response.json()["access_token"]


def parse_events(response) -> list[dict]:
    return [
        json.loads(line)
        for line in response.text.splitlines()
        if line.strip()
    ]


print("=" * 70)
print("测试1：未登录用户不能调用流式问答")


unauthorized_response = client.post(
    "/api/multi-agent/query/stream",
    json={
        "question": QUESTION,
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
print("测试2：登录用户能够接收完整流事件")


captured = {}


def fake_graph_stream(
    initial_state,
    *,
    config,
    stream_mode,
    subgraphs,
):
    assert config["configurable"]["thread_id"]
    assert stream_mode == "updates"
    assert subgraphs is True

    final_state = dict(initial_state)
    final_state.update({
        "category": "emergency",
        "risk_level": "high",
        "answer_status": "generated",
        "answer_validation_passed": True,
        "final_answer": (
            "请先安抚被困人员，并联系电梯维保人员。"
            "\n\n依据资料编号：[ER-001]"
        ),
        "used_doc_codes": ["ER-001"],
        "citations": [
            {
                "doc_code": "ER-001",
                "title": "电梯困人处置资料",
            }
        ],
        "requires_human_confirmation": True,
        "confirmation_status": "pending",
        "confirmed_by": "",
        "pending_action": {
            "action_type": "notify_personnel",
            "executed": False,
        },
        "route_history": [
            "supervisor",
            "emergency_agent",
            "controlled_retrieval",
            "open_evidence_documents",
            "emergency_answer",
            "finalize_answer",
            "prepare_action",
        ],
    })

    captured["state"] = final_state

    yield (
        ("answer_pipeline",),
        {
            "supervisor": {},
        },
    )

    yield (
        (),
        {
            "prepare_action": {},
        },
    )


def fake_get_state(config):
    assert config["configurable"]["thread_id"]

    return SimpleNamespace(
        values=captured["state"],
    )


token = login()


with (
    patch.object(
        multi_agent_api
        .security_agent_hitl_graph,
        "stream",
        side_effect=fake_graph_stream,
    ),
    patch.object(
        multi_agent_api
        .security_agent_hitl_graph,
        "get_state",
        side_effect=fake_get_state,
    ),
    patch.object(
        multi_agent_api,
        "STREAM_CHUNK_DELAY_SECONDS",
        0,
    ),
):
    response = client.post(
        "/api/multi-agent/query/stream",
        headers={
            "Authorization": (
                f"Bearer {token}"
            ),
        },
        json={
            "question": QUESTION,
        },
    )


assert response.status_code == 200, (
    response.text
)

assert (
    response.headers["content-type"]
    .startswith("application/x-ndjson")
)

events = parse_events(response)
event_types = [
    event["type"]
    for event in events
]

assert event_types[0] == "start"
assert "status" in event_types
assert "metadata" in event_types
assert "answer_delta" in event_types
assert event_types[-1] == "complete"

streamed_answer = "".join(
    event["data"]["text"]
    for event in events
    if event["type"] == "answer_delta"
)

complete_result = events[-1][
    "data"
]["result"]

assert streamed_answer == (
    complete_result["answer"]
)

assert (
    complete_result["run_status"]
    == "awaiting_confirmation"
)

assert complete_result[
    "used_doc_codes"
] == ["ER-001"]

assert complete_result[
    "pending_action"
]["executed"] is False

print(
    "事件顺序：",
    event_types,
)

print(
    "流式回答字符数：",
    len(streamed_answer),
)

print("\n多Agent流式API测试全部通过")
