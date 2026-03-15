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


def test_audit_rejects_annual_reading_neutral_fallback(tmp_path: Path) -> None:
    chart = _load_chart(tmp_path)
    rules = build_rules_output(chart).model_dump()
    report = build_report(chart, build_rules_output(chart)).model_dump()

    rules["annual_reading_v0"]["entries"][1]["summary"] += " 当前以中性阅读为主。"

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
    assert checks["annual_reading_not_neutral_fallback"].passed is False


def test_audit_rejects_future_five_years_neutral_fallback(tmp_path: Path) -> None:
    chart = _load_chart(tmp_path)
    rules = build_rules_output(chart)
    report = build_report(chart, rules).model_dump()

    report["final_report_v0"]["future_five_years"]["overview"]["text"] += " 当前以中性阅读为主。"

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
    assert checks["final_report_future_five_years_not_neutral_fallback"].passed is False


def test_audit_rejects_future_five_years_mentor_event_promise(tmp_path: Path) -> None:
    chart = _load_chart(tmp_path)
    rules = build_rules_output(chart)
    report = build_report(chart, rules).model_dump()

    report["final_report_v0"]["future_five_years"]["entries"][0]["text"] += " 2030年必有贵人帮你并必然被提携。"

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
    assert checks["final_report_future_five_years_not_absolute_verdict"].passed is False
