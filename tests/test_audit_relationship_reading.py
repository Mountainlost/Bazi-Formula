import json
from pathlib import Path

from bazi.cli import run_calc
from bazi.judge_engine import build_rules_output
from bazi.models import ChartOutput
from bazi.reporter import build_report
from bazi.verifier import audit_outputs

ROOT = Path(__file__).resolve().parents[1]
USER_INPUT_DIR = ROOT / "用户输入"


def _load_chart(tmp_path: Path) -> ChartOutput:
    chart_path = tmp_path / "chart.json"
    run_calc(USER_INPUT_DIR / "user_001.json", chart_path)
    return ChartOutput.model_validate(json.loads(chart_path.read_text(encoding="utf-8")))


def test_audit_rejects_relationship_event_promise(tmp_path: Path) -> None:
    chart = _load_chart(tmp_path)
    rules = build_rules_output(chart).model_dump()
    report = build_report(chart, build_rules_output(chart)).model_dump()

    rules["relationship_reading_v0"]["conclusion"] += " 一定结婚。"

    audit = audit_outputs(
        chart_raw=chart.model_dump(),
        rules_raw=rules,
        report_raw=report,
        chart_exists=True,
        rules_exists=True,
        report_exists=True,
    )

    checks = {item.name: item for item in audit.checks}
    assert audit.passed is False
    assert checks["relationship_reading_not_absolute_verdict"].passed is False


def test_audit_rejects_relationship_shen_sha_overreach(tmp_path: Path) -> None:
    chart = _load_chart(tmp_path)
    rules = build_rules_output(chart)
    report = build_report(chart, rules).model_dump()

    report["final_report_v0"]["relationship"]["text"] += " 天乙贵人定婚恋。"

    audit = audit_outputs(
        chart_raw=chart.model_dump(),
        rules_raw=rules.model_dump(),
        report_raw=report,
        chart_exists=True,
        rules_exists=True,
        report_exists=True,
    )

    checks = {item.name: item for item in audit.checks}
    assert audit.passed is False
    assert checks["final_report_relationship_not_shen_sha_verdict"].passed is False


def test_audit_rejects_relationship_annual_flow_overreach(tmp_path: Path) -> None:
    chart = _load_chart(tmp_path)
    rules = build_rules_output(chart)
    report = build_report(chart, rules).model_dump()

    report["final_report_v0"]["relationship"]["text"] += " 流年骨架定婚恋。"

    audit = audit_outputs(
        chart_raw=chart.model_dump(),
        rules_raw=rules.model_dump(),
        report_raw=report,
        chart_exists=True,
        rules_exists=True,
        report_exists=True,
    )

    checks = {item.name: item for item in audit.checks}
    assert audit.passed is False
    assert checks["final_report_relationship_not_annual_flow_verdict"].passed is False
