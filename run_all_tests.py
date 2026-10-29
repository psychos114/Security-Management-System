"""批量执行 test/ 下所有回归脚本，输出真实的通过/失败统计表。

用法：  .\.venv\Scripts\python.exe run_all_tests.py
"""
from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PY = ROOT / ".venv" / "Scripts" / "python.exe"
if not PY.exists():  # 兼容非 Windows / 未建 venv 的情况
    PY = Path(sys.executable)

TEST_DIR = ROOT / "test"
SKIP = {"_project_path.py"}
TIMEOUT = 180  # 单个脚本最长 3 分钟


def classify(output: str, returncode: int) -> tuple[str, str]:
    """返回 (结果, 说明)。区分'逻辑失败'与'环境失败'。

    注意：必须先看退出码。测试里大量断言"未登录应返回 401""越权应返回 403"，
    这些 401/403 是预期结果，不能当成鉴权失败。
    """
    if returncode == 0:
        return "通过", ""

    low = output.lower()

    env_markers = [
        ("connectionerror", "后端未启动/连接失败"),
        ("connection refused", "后端未启动/连接失败"),
        ("connecterror", "后端未启动/连接失败"),
        ("httpx.connecterror", "后端未启动/连接失败"),
        ("缺少配置项", "配置缺失"),
        ("filenotfounderror", "测试素材缺失"),
        ("quota", "外部服务额度不足"),
        ("invalid api key", "密钥无效"),
        ("timeout", "超时"),
        ("timed out", "超时"),
        ("model_not_found", "模型名不匹配"),
        ("invalid model", "模型名不匹配"),
        ("no provider supported", "模型名不匹配"),
    ]
    logic_markers = [
        ("assertionerror", "断言失败"),
        ("validation_failed", "内容校验拦截"),
        ("model_error", "模型调用失败"),
        ("keyerror", "字段缺失"),
        ("typeerror", "类型错误"),
        ("importerror", "导入失败"),
        ("modulenotfound", "依赖缺失"),
    ]

    for key, note in env_markers:
        if key in low:
            return "环境失败", note
    for key, note in logic_markers:
        if key in low:
            return "逻辑失败", note

    if returncode == 0:
        return "通过", ""
    return "失败", "退出码非 0"


def main() -> None:
    scripts = sorted(p for p in TEST_DIR.glob("test_*.py") if p.name not in SKIP)
    print(f"共发现 {len(scripts)} 个测试脚本，开始逐个执行\n", flush=True)

    rows: list[tuple[str, str, str, float]] = []

    for idx, script in enumerate(scripts, 1):
        print(f"[{idx}/{len(scripts)}] {script.name} ... ", end="", flush=True)
        started = time.time()
        try:
            proc = subprocess.run(
                [str(PY), str(script)],
                cwd=str(ROOT),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=TIMEOUT,
            )
            out = (proc.stdout or "") + (proc.stderr or "")
            result, note = classify(out, proc.returncode)
        except subprocess.TimeoutExpired:
            result, note = "环境失败", f"超时(>{TIMEOUT}s)"
            out = ""
        elapsed = time.time() - started
        rows.append((script.name, result, note, elapsed))
        print(f"{result}{'（' + note + '）' if note else ''}  {elapsed:.1f}s", flush=True)

        if result != "通过":
            tail = [line for line in out.strip().splitlines() if line.strip()][-6:]
            for line in tail:
                print(f"      | {line[:150]}", flush=True)

    passed = sum(1 for r in rows if r[1] == "通过")
    env_fail = sum(1 for r in rows if r[1] == "环境失败")
    logic_fail = sum(1 for r in rows if r[1] == "逻辑失败")
    other_fail = len(rows) - passed - env_fail - logic_fail

    print("\n" + "=" * 78)
    print(f"{'脚本':<40}{'结果':<10}{'说明'}")
    print("-" * 78)
    for name, result, note, _ in rows:
        print(f"{name:<40}{result:<10}{note}")
    print("-" * 78)
    print(f"总数 {len(rows)}  |  通过 {passed}  |  逻辑失败 {logic_fail}  |  环境失败 {env_fail}  |  其他失败 {other_fail}")
    print("=" * 78)

    report = ROOT / "test_result_summary.txt"
    report.write_text(
        "\n".join(
            [f"{n}\t{r}\t{note}" for n, r, note, _ in rows]
            + ["", f"总数 {len(rows)} 通过 {passed} 逻辑失败 {logic_fail} 环境失败 {env_fail}"]
        ),
        encoding="utf-8",
    )
    print(f"\n明细已写入：{report}")


if __name__ == "__main__":
    main()
