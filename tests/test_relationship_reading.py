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


def test_relationship_reading_v0_is_written(tmp_path: Path) -> None:
    chart = _load_chart(tmp_path)
    rules = build_rules_output(chart)

    relationship = rules.relationship_reading_v0
    assert relationship.method == "relationship_reading_v0"
    assert relationship.status == "determined"
    assert relationship.base_support in {"positive", "favorable"}
    assert relationship.partner_support in {"mixed", "positive", "favorable"}
    assert relationship.stability_tendency in {"positive", "favorable"}
    assert relationship.current_phase == "cautious"
    assert relationship.future_tendency == "favorable"
    assert relationship.conclusion
    assert relationship.notes
    assert relationship.evidence_refs


def test_relationship_reading_v0_uses_controlled_non_event_conclusion(tmp_path: Path) -> None:
    chart = _load_chart(tmp_path)
    rules = build_rules_output(chart)
    report = build_report(chart, rules)

    conclusion = rules.relationship_reading_v0.conclusion
    assert "关系推进" in conclusion
    assert "当前阶段" in conclusion
    assert "未来几年" in conclusion
    assert report.relationship_reading_summary == rules.relationship_reading_v0
    assert conclusion in report.final_report_v0.relationship.text

    for forbidden in (
        "一定结婚",
        "一定遇到正缘",
        "必然分手",
        "一定复合",
        "正缘必到",
    ):
        assert forbidden not in conclusion
        assert forbidden not in report.final_report_v0.relationship.text


def test_relationship_reading_v0_does_not_change_final_useful_god(tmp_path: Path) -> None:
    chart = _load_chart(tmp_path)
    rules = build_rules_output(chart)

    assert rules.final_useful_god_v0.status == "determined"
    assert rules.final_useful_god_v0.primary_element == "metal"
    assert rules.final_useful_god_v0.secondary_elements == ["earth"]
