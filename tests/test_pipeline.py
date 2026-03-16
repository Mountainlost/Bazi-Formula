import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
USER_INPUT_DIR = ROOT / "用户输入"


def _subprocess_env() -> dict[str, str]:
    env = os.environ.copy()
    existing = env.get("PYTHONPATH", "")
    src_path = str(ROOT / "src")
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    env["PYTHONPATH"] = src_path if not existing else os.pathsep.join([src_path, existing])
    return env


def test_full_pipeline_generates_consistent_outputs(tmp_path: Path) -> None:
    input_path = tmp_path / "user_001.json"
    input_path.write_text(
        (USER_INPUT_DIR / "user_001.json").read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    chart_path = tmp_path / "chart.json"
    rules_path = tmp_path / "rules.json"
    report_path = tmp_path / "report.json"
    markdown_path = tmp_path / "最终报告.md"
    audit_path = tmp_path / "audit.json"

    commands = [
        [sys.executable, "-m", "bazi.cli", "calc", "--input", str(input_path), "--output", str(chart_path)],
        [sys.executable, "-m", "bazi.cli", "judge", "--chart", str(chart_path), "--output", str(rules_path)],
        [
            sys.executable,
            "-m",
            "bazi.cli",
            "report",
            "--chart",
            str(chart_path),
            "--rules",
            str(rules_path),
            "--output",
            str(report_path),
        ],
        [
            sys.executable,
            "-m",
            "bazi.cli",
            "audit",
            "--chart",
            str(chart_path),
            "--rules",
            str(rules_path),
            "--report",
            str(report_path),
            "--output",
            str(audit_path),
        ],
    ]

    for command in commands:
        result = subprocess.run(
            command,
            cwd=ROOT,
            env=_subprocess_env(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="ignore",
        )
        assert result.returncode == 0, result.stderr

    chart = json.loads(chart_path.read_text(encoding="utf-8"))
    rules = json.loads(rules_path.read_text(encoding="utf-8"))
    report = json.loads(report_path.read_text(encoding="utf-8"))
    audit = json.loads(audit_path.read_text(encoding="utf-8"))

    markdown_path_candidates = [markdown_path, tmp_path / "鏈€缁堟姤鍛?md"]
    markdown_text = None
    for candidate in markdown_path_candidates:
        if candidate.exists():
            markdown_text = candidate.read_text(encoding="utf-8")
            break
    assert markdown_text is not None

    assert chart["engine_version"] == "bazi-engine-real-calc-py310-v2"
    assert rules["rules_version"] == "bazi-rules-shen-sha-v5"
    assert report["report_version"] == "bazi-report-structured-v5"
    assert audit["audit_version"] == "bazi-audit-evidence-v5"

    assert rules["final_useful_god_v0"]["status"] == "determined"
    assert rules["final_useful_god_v0"]["primary_element"] == "metal"
    assert rules["final_useful_god_v0"]["secondary_elements"] == ["earth"]

    assert report["annual_reading_summary"] == rules["annual_reading_v0"]
    assert report["career_reading_summary"] == rules["career_reading_v0"]
    assert report["wealth_reading_summary"] == rules["wealth_reading_v0"]
    assert report["relationship_reading_summary"] == rules["relationship_reading_v0"]
    assert report["shen_sha_summary"] == rules["shen_sha_v0"]
    assert report["final_report_v0"]["career"]["text"].startswith("事业部分当前只基于既有规则做受控整合。")
    assert report["final_report_v0"]["wealth"]["text"].startswith("财运部分当前只基于既有规则做受控整合。")
    assert report["final_report_v0"]["relationship"]["text"].startswith("婚恋部分当前只基于既有规则做受控整合。")
    assert rules["career_reading_v0"]["conclusion"] in report["final_report_v0"]["career"]["text"]
    assert rules["wealth_reading_v0"]["conclusion"] in report["final_report_v0"]["wealth"]["text"]
    assert rules["relationship_reading_v0"]["conclusion"] in report["final_report_v0"]["relationship"]["text"]
    assert "具体事件预测" in report["final_report_v0"]["career"]["text"]
    assert "具体事件预测" in report["final_report_v0"]["relationship"]["text"]
    assert [item["year"] for item in report["final_report_v0"]["future_five_years"]["entries"]] == [2026, 2027, 2028, 2029, 2030]
    assert report["final_report_v0"]["career"]["text"] in markdown_text
    assert report["final_report_v0"]["wealth"]["text"] in markdown_text
    assert report["final_report_v0"]["relationship"]["text"] in markdown_text
    assert audit["passed"] is True
