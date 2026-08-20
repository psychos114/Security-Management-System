import _project_path  # noqa: F401

from pathlib import Path

from backend.app.services.inspection_vision_service import (
    InspectionVisionService,
)


PROJECT_ROOT = Path(__file__).resolve().parent
TEST_IMAGE = (
    PROJECT_ROOT
    / "test_images"
    / "inspection_test.jpg"
)


print("=" * 60)
print("测试1：不存在的图片必须被阻止")

service = InspectionVisionService()

try:
    service.analyze(
        PROJECT_ROOT
        / "test_images"
        / "missing.jpg"
    )
except FileNotFoundError:
    print("通过：不存在的图片已被阻止")
else:
    raise AssertionError(
        "系统没有阻止不存在的图片"
    )


print("\n" + "=" * 60)
print("测试2：正式服务分析巡检照片")

result = service.analyze(TEST_IMAGE)

print(
    result.model_dump_json(
        indent=2,
    )
)

assert result.summary
assert result.has_risk is True
assert len(result.risks) >= 1

for risk in result.risks:
    assert risk.location
    assert risk.description
    assert risk.visual_evidence
    assert 0.0 <= risk.confidence <= 1.0
    assert risk.severity in {
        "low",
        "medium",
        "high",
        "critical",
    }

print("\n识别到的风险数量：", len(result.risks))
print(
    "是否需要人工复核：",
    result.requires_manual_review,
)

print("\n第15关测试全部通过")
