import _project_path  # noqa: F401

from pathlib import Path
from uuid import uuid4

from backend.app.multi_agent.hitl_graph import (
    security_agent_hitl_graph,
)
from backend.app.services.inspection_agent_bridge import (
    create_visual_inspection_state,
)
from backend.app.services.inspection_vision_service import (
    InspectionVisionService,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
TEST_IMAGE = (
    PROJECT_ROOT
    / "test_images"
    / "inspection_test.jpg"
)


print("=" * 70)
print("测试1：使用当前视觉模型分析巡检照片")

vision_service = InspectionVisionService()

vision_result = vision_service.analyze(
    TEST_IMAGE
)

assert vision_result.has_risk is True
assert len(vision_result.risks) >= 1

print(
    "图片风险数量：",
    len(vision_result.risks),
)


print("\n" + "=" * 70)
print("测试2：建立图片巡检LangGraph状态")

analysis_id = str(uuid4())

initial_state = (
    create_visual_inspection_state(
        analysis_id=analysis_id,
        result=vision_result,
        initiator_user_id=1,
        initiator_role_code="guard",
        initiator_display_name="演示保安",
    )
)

assert (
    initial_state["input_source"]
    == "inspection_image"
)
assert (
    initial_state["visual_analysis_id"]
    == analysis_id
)
assert initial_state["visual_analysis"]

print(
    "LangGraph任务编号：",
    initial_state["request_id"],
)


print("\n" + "=" * 70)
print("测试3：运行巡检Agent和受控混合RAG")

config = {
    "configurable": {
        "thread_id": (
            initial_state["request_id"]
        )
    }
}

final_state = (
    security_agent_hitl_graph.invoke(
        initial_state,
        config=config,
    )
)

print(
    "业务类别：",
    final_state["category"],
)
print(
    "风险等级：",
    final_state["risk_level"],
)
print(
    "调度方式：",
    final_state["routing_method"],
)
print(
    "流程路线：",
    final_state["route_history"],
)
print(
    "引用资料：",
    final_state["used_doc_codes"],
)
print(
    "最终建议：\n",
    final_state["final_answer"],
)

assert (
    final_state["category"]
    == "inspection"
)
assert (
    final_state["routing_method"]
    == "source_rule"
)
assert (
    "inspection_agent"
    in final_state["route_history"]
)
assert (
    "controlled_retrieval"
    in final_state["route_history"]
)
assert (
    "open_evidence_documents"
    in final_state["route_history"]
)
assert (
    "inspection_answer"
    in final_state["route_history"]
)
assert (
    final_state["answer_status"]
    == "generated"
)
assert (
    final_state[
        "answer_validation_passed"
    ]
    is True
)
assert final_state["used_doc_codes"]
assert final_state["citations"]


print("\n" + "=" * 70)
print("测试4：系统没有执行或准备真实动作")

assert final_state["pending_action"] is None
assert (
    final_state["confirmation_status"]
    == "not_required"
)

print("通过：没有执行真实动作")
print("\n第17关测试全部通过")
