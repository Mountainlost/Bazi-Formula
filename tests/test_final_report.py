import json
from pathlib import Path

from bazi.cli import run_calc
from bazi.judge_engine import build_rules_output
from bazi.models import ChartOutput
from bazi.reporter import build_report

ROOT = Path(__file__).resolve().parents[1]
USER_INPUT_DIR = ROOT / "用户输入"


def _load_chart(tmp_path: Path) -> ChartOutput:
    chart_path = tmp_path / "chart.json"
    run_calc(USER_INPUT_DIR / "user_001.json", chart_path)
    return ChartOutput.model_validate(json.loads(chart_path.read_text(encoding="utf-8")))


def test_final_report_v0_is_written_for_user_001(tmp_path: Path) -> None:
    chart = _load_chart(tmp_path)
    rules = build_rules_output(chart)
    report = build_report(chart, rules)

    final_report = report.final_report_v0
    assert final_report.method == "final_report_v0"
    assert final_report.summary.text
    assert final_report.career.text
    assert final_report.wealth.text
    assert final_report.relationship.text
    assert final_report.future_five_years.overview.text
    assert final_report.limitations
    assert final_report.evidence_refs
    assert final_report.career.evidence_refs
    assert final_report.wealth.evidence_refs
    assert final_report.relationship.evidence_refs


def test_final_report_v0_only_restates_existing_rules(tmp_path: Path) -> None:
    chart = _load_chart(tmp_path)
    rules = build_rules_output(chart)
    report = build_report(chart, rules)

    assert report.career_reading_summary == rules.career_reading_v0
    assert report.wealth_reading_summary == rules.wealth_reading_v0
    assert report.relationship_reading_summary == rules.relationship_reading_v0
    assert rules.career_reading_v0.conclusion in report.final_report_v0.career.text
    assert rules.wealth_reading_v0.conclusion in report.final_report_v0.wealth.text
    assert rules.relationship_reading_v0.conclusion in report.final_report_v0.relationship.text
    assert "受控版 v0" in report.final_report_v0.career.text
    assert "受控版 v0" in report.final_report_v0.wealth.text
    assert "具体事件预测" in report.final_report_v0.career.text
    assert "受控版 v0" in report.final_report_v0.relationship.text
    assert "具体事件预测" in report.final_report_v0.relationship.text


def test_final_report_v0_does_not_upgrade_candidate_or_independent_layers(tmp_path: Path) -> None:
    chart = _load_chart(tmp_path)
    rules = build_rules_output(chart)
    report = build_report(chart, rules)

    texts = "\n".join(
        [
            report.final_report_v0.summary.text,
            report.final_report_v0.career.text,
            report.final_report_v0.wealth.text,
            report.final_report_v0.relationship.text,
            report.final_report_v0.future_five_years.overview.text,
            *(item.text for item in report.final_report_v0.future_five_years.entries),
        ]
    )

    for forbidden in (
        "候选用神已定",
        "候选用神就是最终用神",
        "调候候选已定为最终用神",
        "一定升职",
        "一定创业成功",
        "必然换工作",
        "一定结婚",
        "一定遇到正缘",
        "必然分手",
        "大吉",
        "应期已定",
    ):
        assert forbidden not in texts
